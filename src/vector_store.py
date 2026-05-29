import os
import chromadb
from typing import List, Optional
from src.schemas import AnomalyChunk
from src.embeddings import get_embedding

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chromadb")

class VectorStore:
    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="log_anomalies",
            metadata={"hnsw:space": "cosine"}
        )

    def index_anomaly_chunks(self, chunks: List[AnomalyChunk]):
        """
        Embed and index anomaly chunks in local ChromaDB.
        """
        if not chunks:
            return
        
        ids = []
        documents = []
        embeddings = []
        metadatas = []
        
        for chunk in chunks:
            try:
                embedding = get_embedding(chunk.chunk_text)
                if not embedding:
                    continue
                
                ids.append(chunk.chunk_id)
                documents.append(chunk.chunk_text)
                embeddings.append(embedding)
                metadatas.append({
                    "start_ts": chunk.start_ts,
                    "end_ts": chunk.end_ts,
                    "severity": chunk.severity,
                    "keywords": ",".join(chunk.keywords)
                })
            except Exception as e:
                print(f"Skipping indexing chunk {chunk.chunk_id} due to error: {e}")
                continue
            
        if ids:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

    def query_similar_anomalies(self, query_text: str, limit: int = 3) -> List[AnomalyChunk]:
        """
        Query similar historical logs or anomalies.
        """
        query_embedding = get_embedding(query_text)
        if not query_embedding:
            return []
            
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )
        
        anomalies = []
        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            
            for idx in range(len(ids)):
                meta = metadatas[idx]
                anomalies.append(AnomalyChunk(
                    chunk_id=ids[idx],
                    start_ts=meta.get("start_ts", ""),
                    end_ts=meta.get("end_ts", ""),
                    severity=meta.get("severity", ""),
                    keywords=meta.get("keywords", "").split(",") if meta.get("keywords") else [],
                    chunk_text=documents[idx]
                ))
        return anomalies

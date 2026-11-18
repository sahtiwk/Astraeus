"""Versioned local vector storage with bounded writes and explicit failures."""
import os
from dataclasses import dataclass, field
from pathlib import Path
from src.schemas import AnomalyChunk
from src.embeddings import get_embeddings, get_embedding
from src.privacy import redact

DB_PATH = str(Path(__file__).resolve().parents[1] / 'data' / 'chromadb')

@dataclass
class IndexResult:
    indexed: int = 0
    failed: list[str] = field(default_factory=list)


class VectorStore:
    def __init__(self, db_path: str = DB_PATH):
        import chromadb
        from chromadb.config import Settings
        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
        # Do not mix older unredacted/truncated embeddings with the new pipeline.
        self.collection = self.client.get_or_create_collection(
            name='log_anomalies_v2', metadata={'hnsw:space': 'cosine'})

    def index_anomaly_chunks(self, chunks: list[AnomalyChunk], batch_size: int = 32) -> IndexResult:
        if batch_size <= 0:
            raise ValueError('batch_size must be positive')
        result = IndexResult()
        for start in range(0, len(chunks), batch_size):
            batch = list({c.chunk_id: c for c in chunks[start:start+batch_size]}.values())
            try:
                existing = set(self.collection.get(ids=[c.chunk_id for c in batch], include=[])['ids'])
                batch = [c for c in batch if c.chunk_id not in existing]
                if not batch:
                    continue
                documents = [redact(c.chunk_text) for c in batch]
                embeddings = get_embeddings(documents)
                if len(embeddings) != len(batch) or any(not v for v in embeddings):
                    raise ValueError('Missing embeddings')
                self.collection.upsert(ids=[c.chunk_id for c in batch], documents=documents,
                    embeddings=embeddings, metadatas=[dict(start_ts=c.start_ts, end_ts=c.end_ts,
                    severity=c.severity, keywords=','.join(c.keywords), source_id=c.source_id) for c in batch])
                result.indexed += len(batch)
            except Exception:
                result.failed.extend(c.chunk_id for c in batch)
        return result

    def query_similar_anomalies(self, query_text: str, limit: int = 3,
                                exclude_ids: list[str] | None = None,
                                exclude_source_id: str | None = None,
                                exclude_source_ids: list[str] | None = None) -> list[AnomalyChunk]:
        if limit <= 0 or not query_text.strip() or self.collection.count() == 0:
            return []
        excluded = set(exclude_ids or [])
        kwargs = {}
        if exclude_source_ids:
            kwargs['where'] = {'source_id': {'$nin': exclude_source_ids}}
        elif exclude_source_id:
            kwargs['where'] = {'source_id': {'$ne': exclude_source_id}}
        results = self.collection.query(query_embeddings=[get_embedding(redact(query_text))],
            n_results=min(self.collection.count(), limit + len(excluded)), **kwargs)
        found = []
        for cid, document, meta in zip(results['ids'][0], results['documents'][0], results['metadatas'][0]):
            if cid in excluded:
                continue
            meta = meta or {}
            found.append(AnomalyChunk(chunk_id=cid, start_ts=meta.get('start_ts',''),
                end_ts=meta.get('end_ts',''), severity=meta.get('severity','LOW'),
                keywords=meta.get('keywords','').split(',') if meta.get('keywords') else [],
                chunk_text=document, source_id=meta.get('source_id','')))
        return found[:limit]

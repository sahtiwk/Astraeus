import os
from typing import List

# Cache the model so we don't reload it from disk on every embedding call
_model = None

def get_embedding(text: str, model: str = "all-MiniLM-L6-v2") -> List[float]:
    """
    Generate embedding for a given text using a local HuggingFace SentenceTransformer model.
    """
    if not text or not text.strip():
        return []
    
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(model)
        
    try:
        embedding = _model.encode(text)
        return embedding.tolist()
    except Exception as e:
        raise RuntimeError(f"Failed to generate embedding: {e}")

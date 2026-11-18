"""Local-only embeddings. Model downloads are a separate setup action."""
import os
from pathlib import Path
from functools import lru_cache
from threading import RLock

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
_LOCK = RLock()
LOCAL_MODEL = Path(__file__).resolve().parents[1] / 'models' / 'embedding'
DEFAULT_MODEL = str(LOCAL_MODEL) if LOCAL_MODEL.is_dir() else 'sentence-transformers/all-MiniLM-L6-v2'


@lru_cache(maxsize=2)
def _load_model(model):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model, local_files_only=True, trust_remote_code=False, device='cpu')


def get_embeddings(texts: list[str], model: str | None = None) -> list[list[float]]:
    if not texts:
        return []
    model = model or os.getenv('ASTRAEUS_EMBEDDING_MODEL', DEFAULT_MODEL)
    with _LOCK:
        try:
            encoder = _load_model(model)
        except Exception as exc:
            raise RuntimeError('Local embedding model unavailable. Install the model during setup or configure ASTRAEUS_EMBEDDING_MODEL to a local folder.') from exc
        import numpy as np
        result = []
        # Token windows cover the whole incident rather than silently truncating it.
        width = max(1, encoder.max_seq_length - 2)
        for text in texts:
            if not text.strip():
                result.append([])
                continue
            tokens = encoder.tokenizer.encode(text, add_special_tokens=False)
            windows = [encoder.tokenizer.decode(tokens[i:i+width]) for i in range(0,len(tokens),width)]
            vectors = encoder.encode(windows, batch_size=16, normalize_embeddings=True, show_progress_bar=False)
            mean = np.mean(vectors, axis=0)
            norm = np.linalg.norm(mean)
            result.append((mean / norm if norm else mean).tolist())
        return result


def get_embedding(text: str, model: str | None = None) -> list[float]:
    return get_embeddings([text], model)[0] if text.strip() else []

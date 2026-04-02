import json
import numpy as np
from . import config

_model = None
_index = None
_metadata: list = []

def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def _index_file():
    return config.INDEX_DIR / "index.faiss"

def _meta_file():
    return config.INDEX_DIR / "metadata.jsonl"

def _get_index():
    global _index, _metadata
    import faiss
    if _index is None:
        if _index_file().exists():
            _index = faiss.read_index(str(_index_file()))
            _metadata = [
                json.loads(ln)
                for ln in _meta_file().read_text(encoding="utf-8").splitlines()
                if ln.strip()
            ]
        else:
            _index    = faiss.IndexFlatL2(384)
            _metadata = []
    return _index

def _save():
    import faiss
    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(_index, str(_index_file()))
    with open(_meta_file(), "w", encoding="utf-8") as f:
        for m in _metadata:
            f.write(json.dumps(m) + "\n")

def add_revision(task_id: str, revision: int, status: str, summary: str) -> None:
    model = _get_model()
    idx   = _get_index()
    text  = f"{task_id} rev{revision} [{status}] {summary}"
    vec   = model.encode([text], normalize_embeddings=True).astype(np.float32)
    idx.add(vec)
    _metadata.append({"task_id": task_id, "revision": revision,
                       "status": status, "summary": summary})
    _save()

def search(query: str, top_k: int = 5) -> list:
    model = _get_model()
    idx   = _get_index()
    if idx.ntotal == 0:
        return []
    vec = model.encode([query], normalize_embeddings=True).astype(np.float32)
    k   = min(top_k, idx.ntotal)
    distances, indices = idx.search(vec, k)
    results = []
    for dist, i in zip(distances[0], indices[0]):
        if i >= 0:
            meta = _metadata[i].copy()
            meta["score"] = float(dist)
            results.append(meta)
    return results

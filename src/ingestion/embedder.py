"""
embedder.py
───────────
Converts text chunks into numerical vectors (embeddings) for semantic search.

What is an embedding?
  A vector is a list of numbers, e.g. [0.12, -0.85, 0.33, ...] with 384 dims.
  Two chunks about similar topics will have vectors that are "close" in space.
  This is what makes semantic search work — "CDD requirements" and
  "customer due diligence obligations" will be close even with different words.

Model used: all-MiniLM-L6-v2
  - Runs locally, no API cost
  - 384 dimensions, fast, good quality for English regulatory text
  - Industry standard for RAG applications
  - Loaded once at startup, reused for all chunks

Why separate from the Claude API?
  Embeddings are a separate concern from generation. We use a small local
  model for embeddings (cheap, fast, no latency) and Claude only for
  reasoning over the retrieved content. This is standard RAG architecture.

What gets saved?
  We pickle the embeddings alongside their chunk metadata so we don't
  re-embed on every run — embedding 10,000 chunks takes ~30 seconds.
"""

import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

# Path to save/load pre-computed embeddings
EMBEDDINGS_CACHE = os.path.join(os.path.dirname(__file__), "../../embeddings_cache.pkl")

# Load model once at module level (expensive to load repeatedly)
_model = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the embedding model (only once per session)."""
    global _model
    if _model is None:
        print("  [Embedder] Loading sentence transformer model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("  [Embedder] Model loaded.")
    return _model


def embed_chunks(chunks: list[dict], force_recompute: bool = False) -> list[dict]:
    """
    Add an 'embedding' field to each chunk dict.

    Uses a cache file so embeddings aren't recomputed on every run.
    Set force_recompute=True to rebuild from scratch.

    Args:
        chunks:          List of chunk dicts from chunker.py
        force_recompute: If True, ignore cache and recompute everything

    Returns:
        Same list of chunk dicts, each now containing:
        { ..., "embedding": np.ndarray of shape (384,) }
    """
    cache_path = os.path.abspath(EMBEDDINGS_CACHE)

    # Return cached embeddings if available
    if os.path.exists(cache_path) and not force_recompute:
        print("  [Embedder] Loading embeddings from cache...")
        with open(cache_path, "rb") as f:
            cached = pickle.load(f)
        if len(cached) == len(chunks):
            print(f"  [Embedder] Cache hit: {len(cached)} embeddings loaded\n")
            return cached
        else:
            print("  [Embedder] Cache size mismatch — recomputing...")

    model = _get_model()
    texts = [chunk["text"] for chunk in chunks]

    print(f"  [Embedder] Embedding {len(texts)} chunks (this may take a minute)...")
    vectors = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,   # L2-normalize for cosine similarity via dot product
    )

    # Attach embedding to each chunk
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = vectors[i]

    # Save to cache
    with open(cache_path, "wb") as f:
        pickle.dump(chunks, f)
    print(f"  [Embedder] Embeddings saved to cache: {cache_path}\n")

    return chunks


def embed_query(query: str) -> np.ndarray:
    """
    Embed a single query string for similarity search.

    Args:
        query: The user's search query or compliance question.

    Returns:
        numpy array of shape (384,) — same space as chunk embeddings.
    """
    model = _get_model()
    vector = model.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vector[0]

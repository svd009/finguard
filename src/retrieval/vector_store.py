"""
vector_store.py
───────────────
Semantic search engine using pre-computed embeddings.

How it works:
  Every chunk has a 384-dimensional embedding vector (from Phase 1).
  When a query comes in, we embed it the same way, then find the chunks
  whose vectors are closest to the query vector — "closest" meaning
  they discuss similar concepts, even with different words.

  Example:
    Query: "customer identity verification"
    Matches: chunks about "CDD", "KYC onboarding", "beneficial owner ID"
    even though none of those contain the word "verification" explicitly.

Why cosine similarity?
  We L2-normalize all vectors in the embedder, so cosine similarity
  reduces to a simple dot product — fast on large arrays with numpy.

What this returns:
  Top-K chunks ranked by similarity score, each with full metadata
  (source filename, page number) needed for citations.
"""

import numpy as np
from config import TOP_K_RESULTS


class VectorStore:
    """
    In-memory vector store for semantic similarity search.

    In production this would be replaced by a dedicated vector database
    (Pinecone, Weaviate, ChromaDB) but for a portfolio project, numpy
    is fast enough for thousands of chunks and has zero infrastructure cost.
    """

    def __init__(self):
        self.chunks = []           # list of chunk dicts with embeddings
        self.matrix = None         # numpy matrix: shape (num_chunks, 384)

    def build(self, chunks: list[dict]):
        """
        Index a list of embedded chunks for fast retrieval.

        Args:
            chunks: Output from embedder.embed_chunks() — each chunk
                    must have an 'embedding' key with a numpy array.
        """
        self.chunks = chunks
        # Stack all embeddings into a single matrix for batch dot product
        self.matrix = np.stack([c["embedding"] for c in chunks])
        print(f"  [VectorStore] Indexed {len(chunks)} chunks | "
              f"Matrix shape: {self.matrix.shape}")

    def search(self, query_embedding: np.ndarray, top_k: int = TOP_K_RESULTS,
               source_filter: str = None) -> list[dict]:
        """
        Find the top-K most semantically similar chunks to a query.

        Args:
            query_embedding: 384-dim vector from embedder.embed_query()
            top_k:           Number of results to return
            source_filter:   Optional — restrict results to one document
                             e.g. source_filter="fatf_aml_recommendations.txt"

        Returns:
            List of result dicts, sorted by score descending:
            [{
                "text":    str,
                "source":  str,
                "page":    int,
                "score":   float,   ← cosine similarity (0.0 to 1.0)
                "rank":    int,     ← 1 = best match
            }, ...]
        """
        if self.matrix is None:
            raise RuntimeError("VectorStore not built — call build() first")

        # Batch cosine similarity: (num_chunks,) scores in one operation
        scores = self.matrix @ query_embedding   # dot product (vectors are normalized)

        # Apply source filter if requested
        if source_filter:
            for i, chunk in enumerate(self.chunks):
                if source_filter not in chunk["source"]:
                    scores[i] = -1.0   # exclude from results

        # Get top-K indices sorted by score (highest first)
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices):
            if scores[idx] < 0:
                continue
            chunk = self.chunks[idx]
            results.append({
                "text":    chunk["text"],
                "source":  chunk["source"],
                "page":    chunk["page"],
                "score":   float(scores[idx]),
                "rank":    rank + 1,
                "type":    "semantic",
            })

        return results

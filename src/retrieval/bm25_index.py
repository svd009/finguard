"""
bm25_index.py
─────────────
Lexical (keyword-based) search using BM25 ranking algorithm.

What is BM25?
  BM25 (Best Match 25) is the gold standard keyword search algorithm,
  used by Elasticsearch and most search engines as their baseline.
  It scores documents by how often query terms appear, adjusted for
  document length (so long documents don't unfairly dominate).

Why do we need this if we already have semantic search?
  Semantic search is great for conceptual similarity but can miss
  exact regulatory terminology. Compliance text is full of precise
  legal terms — "Tier 1 Capital", "CTR", "SAR", "NSFR" — where
  exact matching outperforms semantic similarity.

  Example:
    Query: "LCR calculation formula"
    Semantic search: finds chunks about "liquidity" and "stress testing"
    BM25: finds the exact chunk containing "LCR = Stock of HQLA / ..."

  The combination of both is called Hybrid Search — Phase 2's key insight.

How BM25 tokenizes:
  We lowercase and split on whitespace/punctuation. For regulatory text
  this is sufficient — stemming would help but adds complexity.
"""

import re
from rank_bm25 import BM25Okapi
from config import TOP_K_RESULTS


class BM25Index:
    """Keyword search index over document chunks using BM25Okapi."""

    def __init__(self):
        self.chunks = []
        self.bm25 = None
        self.tokenized_corpus = []

    def build(self, chunks: list[dict]):
        """
        Build the BM25 index from a list of chunk dicts.

        Args:
            chunks: List of chunk dicts (embedding not required here)
        """
        self.chunks = chunks
        self.tokenized_corpus = [self._tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        print(f"  [BM25Index] Indexed {len(chunks)} chunks")

    def search(self, query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
        """
        Find the top-K chunks with the highest BM25 score for a query.

        Args:
            query: Raw query string (not pre-tokenized)
            top_k: Number of results to return

        Returns:
            List of result dicts sorted by BM25 score descending.
        """
        if self.bm25 is None:
            raise RuntimeError("BM25Index not built — call build() first")

        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-K indices
        import numpy as np
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices):
            if scores[idx] <= 0:
                continue   # no keyword overlap at all
            chunk = self.chunks[idx]
            results.append({
                "text":   chunk["text"],
                "source": chunk["source"],
                "page":   chunk["page"],
                "score":  float(scores[idx]),
                "rank":   rank + 1,
                "type":   "lexical",
            })

        return results

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """
        Simple tokenizer: lowercase, split on non-alphanumeric characters.

        "Customer Due Diligence (CDD)" → ["customer", "due", "diligence", "cdd"]
        """
        return re.findall(r'[a-z0-9]+', text.lower())

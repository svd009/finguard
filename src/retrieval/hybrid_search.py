"""
hybrid_search.py
────────────────
Combines semantic (vector) and lexical (BM25) search into one ranked list.

The core problem: no single retrieval method is best for all query types.

  | Query type                        | Best method     |
  |-----------------------------------|-----------------|
  | "what does CDD mean"              | Semantic        |
  | "LCR = HQLA / net cash outflows"  | BM25 (exact)    |
  | "Basel III Tier 1 requirements"   | Both            |
  | "gaps in our AML monitoring"      | Semantic        |
  | "Recommendation 10 FATF"         | BM25 (exact)    |

Fusion method: Reciprocal Rank Fusion (RRF)
  RRF is a simple, robust algorithm that combines ranked lists without
  needing to normalize scores across different scales.

  Formula: RRF_score(doc) = Σ 1 / (k + rank_i)
  where rank_i is the position of the document in each ranked list,
  and k=60 is a smoothing constant (standard value from literature).

  Why RRF over score normalization?
    BM25 scores are unbounded (can be 0 to ~20+).
    Cosine similarity is bounded (0.0 to 1.0).
    Direct weighted averaging across different scales is unreliable.
    RRF only uses rank positions, making it scale-invariant and robust.

  This is the same technique used by enterprise search systems
  (Elasticsearch, Vespa) and recommended in recent RAG research.

Multi-index architecture:
  We maintain SEPARATE indexes for regulatory docs vs internal policies.
  This lets us:
    1. Search only regulations for "what does the law require"
    2. Search only policies for "what do we currently do"
    3. Search both for gap analysis (the core compliance use case)
"""

import numpy as np
from config import TOP_K_RESULTS, BM25_WEIGHT, VECTOR_WEIGHT
from src.retrieval.vector_store import VectorStore
from src.retrieval.bm25_index import BM25Index
from src.ingestion.embedder import embed_query


# RRF smoothing constant — standard value, rarely needs tuning
RRF_K = 60


class HybridSearchEngine:
    """
    Multi-index hybrid search engine combining semantic + lexical retrieval.

    Maintains two separate index pairs:
      - regulations_*  : external regulatory documents (FATF, Basel, KYC, GDPR)
      - policies_*     : internal bank/fintech policy documents

    This separation is critical for compliance gap analysis — we need to
    retrieve from each corpus independently, then compare.
    """

    def __init__(self):
        # Regulatory document indexes
        self.reg_vector  = VectorStore()
        self.reg_bm25    = BM25Index()

        # Internal policy indexes
        self.pol_vector  = VectorStore()
        self.pol_bm25    = BM25Index()

        self._built = False

    def build(self, regulation_chunks: list[dict], policy_chunks: list[dict]):
        """
        Build all four indexes from the two chunk sets.

        Args:
            regulation_chunks: Chunks from documents/regulations/
            policy_chunks:     Chunks from documents/internal_policies/
        """
        print("\n  [HybridSearch] Building regulation indexes...")
        self.reg_vector.build(regulation_chunks)
        self.reg_bm25.build(regulation_chunks)

        print("\n  [HybridSearch] Building policy indexes...")
        self.pol_vector.build(policy_chunks)
        self.pol_bm25.build(policy_chunks)

        self._built = True
        total = len(regulation_chunks) + len(policy_chunks)
        print(f"\n  [HybridSearch] Ready — {total} total chunks indexed\n")

    def search_regulations(self, query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
        """Search only the regulatory documents corpus."""
        return self._hybrid_search(
            query, self.reg_vector, self.reg_bm25, top_k, corpus="regulation"
        )

    def search_policies(self, query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
        """Search only the internal policy documents corpus."""
        return self._hybrid_search(
            query, self.pol_vector, self.pol_bm25, top_k, corpus="policy"
        )

    def search_all(self, query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
        """
        Search both corpora and return unified ranked results.
        Used for general queries that don't need corpus separation.
        """
        reg_results = self.search_regulations(query, top_k)
        pol_results = self.search_policies(query, top_k)

        # Combine and re-rank by RRF score
        combined = reg_results + pol_results
        combined.sort(key=lambda x: x["rrf_score"], reverse=True)
        return combined[:top_k]

    def search_for_gaps(self, topic: str, top_k: int = TOP_K_RESULTS) -> dict:
        """
        The core compliance use case: retrieve matching content from BOTH
        corpora on the same topic so the agent can compare them.

        Returns:
            {
              "topic":       str,
              "regulations": list of result dicts,   ← what the law says
              "policies":    list of result dicts,   ← what we currently do
            }
        """
        return {
            "topic":       topic,
            "regulations": self.search_regulations(topic, top_k),
            "policies":    self.search_policies(topic, top_k),
        }

    def _hybrid_search(self, query: str, vector_store: VectorStore,
                       bm25_index: BM25Index, top_k: int,
                       corpus: str) -> list[dict]:
        """
        Internal: run both search methods and fuse with RRF.

        Steps:
          1. Embed query and run semantic search
          2. Run BM25 keyword search on same query
          3. Apply RRF to merge ranked lists
          4. Return top-K fused results
        """
        if not self._built:
            raise RuntimeError("HybridSearchEngine not built — call build() first")

        # Step 1: Semantic search
        query_vec = embed_query(query)
        semantic_results = vector_store.search(query_vec, top_k=top_k * 2)

        # Step 2: BM25 keyword search
        lexical_results = bm25_index.search(query, top_k=top_k * 2)

        # Step 3: RRF fusion
        fused = self._reciprocal_rank_fusion(semantic_results, lexical_results)

        # Attach corpus label and return top-K
        for r in fused:
            r["corpus"] = corpus

        return fused[:top_k]

    @staticmethod
    def _reciprocal_rank_fusion(list_a: list[dict], list_b: list[dict],
                                 k: int = RRF_K) -> list[dict]:
        """
        Merge two ranked result lists using Reciprocal Rank Fusion.

        Each document gets score = Σ 1/(k + rank) across all lists it appears in.
        Documents appearing in both lists get boosted scores.
        Documents in only one list still appear (not excluded).

        We use (source, page, chunk excerpt) as a document identity key
        since we don't have explicit document IDs.
        """
        scores = {}   # key → rrf_score
        docs   = {}   # key → result dict

        def _key(result: dict) -> str:
            # Unique identifier for a chunk
            return f"{result['source']}::p{result['page']}::{result['text'][:50]}"

        for rank, result in enumerate(list_a):
            key = _key(result)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            docs[key] = result

        for rank, result in enumerate(list_b):
            key = _key(result)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            if key not in docs:
                docs[key] = result

        # Sort by RRF score
        sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        fused = []
        for rank, key in enumerate(sorted_keys):
            result = docs[key].copy()
            result["rrf_score"] = round(scores[key], 6)
            result["rank"] = rank + 1
            fused.append(result)

        return fused

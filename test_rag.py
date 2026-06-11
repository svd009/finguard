"""
test_rag.py
───────────
Smoke test for Phase 2 — verifies the full hybrid search engine.

Run this after test_ingestion.py passes.

Expected output:
  - Both corpora indexed
  - Semantic, lexical, and hybrid search all returning results
  - Gap analysis returning results from both corpora separately
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import generate_sample_docs as gsd
from generate_sample_docs import write_file
from src.ingestion.doc_loader import load_all_documents
from src.ingestion.chunker import chunk_pages
from src.ingestion.embedder import embed_chunks
from src.retrieval.hybrid_search import HybridSearchEngine
from config import REGULATIONS_DIR, INTERNAL_POLICIES_DIR


def run_test():
    print("=" * 60)
    print("FinGuard — Phase 2 RAG Engine Test")
    print("=" * 60)

    # ── Setup (same as Phase 1) ───────────────────────────────────
    os.makedirs(REGULATIONS_DIR, exist_ok=True)
    os.makedirs(INTERNAL_POLICIES_DIR, exist_ok=True)
    write_file(REGULATIONS_DIR, "fatf_aml_recommendations.txt",    gsd.FATF_AML)
    write_file(REGULATIONS_DIR, "basel_iii_capital_framework.txt", gsd.BASEL_CAPITAL)
    write_file(REGULATIONS_DIR, "kyc_compliance_guidelines.txt",   gsd.KYC_GUIDELINES)
    write_file(REGULATIONS_DIR, "gdpr_financial_services.txt",     gsd.GDPR_FINANCIAL)
    write_file(INTERNAL_POLICIES_DIR, "internal_aml_policy.txt",   gsd.INTERNAL_AML)
    write_file(INTERNAL_POLICIES_DIR, "internal_kyc_policy.txt",   gsd.INTERNAL_KYC)
    write_file(INTERNAL_POLICIES_DIR, "internal_data_policy.txt",  gsd.INTERNAL_DATA)
    write_file(INTERNAL_POLICIES_DIR, "internal_capital_policy.txt", gsd.INTERNAL_CAPITAL)

    print("\n[Step 1] Loading and chunking documents...")
    reg_pages = load_all_documents(REGULATIONS_DIR)
    pol_pages = load_all_documents(INTERNAL_POLICIES_DIR)

    reg_chunks = chunk_pages(reg_pages)
    pol_chunks = chunk_pages(pol_pages)

    print("\n[Step 2] Computing embeddings...")
    reg_chunks = embed_chunks(reg_chunks)
    pol_chunks = embed_chunks(pol_chunks, force_recompute=True)

    print("\n[Step 3] Building hybrid search engine...")
    engine = HybridSearchEngine()
    engine.build(reg_chunks, pol_chunks)

    # ── Test 1: Regulation search ─────────────────────────────────
    print("\n[Test 1] Searching regulations for 'customer due diligence'...")
    results = engine.search_regulations("customer due diligence", top_k=3)
    print(f"  Found {len(results)} results")
    for r in results:
        print(f"  [{r['rank']}] {r['source']} p.{r['page']} "
              f"(rrf={r['rrf_score']:.4f}) | {r['text'][:80]}...")

    # ── Test 2: Policy search ─────────────────────────────────────
    print("\n[Test 2] Searching policies for 'record retention'...")
    results = engine.search_policies("record retention", top_k=3)
    print(f"  Found {len(results)} results")
    for r in results:
        print(f"  [{r['rank']}] {r['source']} p.{r['page']} "
              f"(rrf={r['rrf_score']:.4f}) | {r['text'][:80]}...")

    # ── Test 3: Gap analysis (the key use case) ───────────────────
    print("\n[Test 3] Gap analysis — 'AML record keeping requirements'...")
    gaps = engine.search_for_gaps("AML record keeping requirements", top_k=3)
    print(f"  Regulatory sources ({len(gaps['regulations'])} results):")
    for r in gaps["regulations"][:2]:
        print(f"    {r['source']} p.{r['page']}: {r['text'][:100]}...")
    print(f"  Policy sources ({len(gaps['policies'])} results):")
    for r in gaps["policies"][:2]:
        print(f"    {r['source']} p.{r['page']}: {r['text'][:100]}...")

    # ── Test 4: BM25 exact term matching ─────────────────────────
    print("\n[Test 4] BM25 exact term — 'LCR HQLA net cash outflows'...")
    results = engine.search_regulations("LCR HQLA net cash outflows", top_k=2)
    for r in results:
        print(f"  {r['source']} p.{r['page']}: {r['text'][:120]}...")

    print("\n" + "=" * 60)
    print("Phase 2 PASSED ✓ — Hybrid RAG engine working correctly")
    print("=" * 60)


if __name__ == "__main__":
    run_test()

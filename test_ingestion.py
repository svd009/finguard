"""
test_ingestion.py
─────────────────
Quick smoke test for Phase 1 — run this to verify everything works
before moving to Phase 2.

Expected output:
  - Sample documents generated
  - Text extracted and split into chunks
  - Embeddings computed and cached
  - Basic similarity search working
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_sample_docs import write_file
import generate_sample_docs as gsd
from src.ingestion.doc_loader import load_all_documents
from src.ingestion.chunker import chunk_pages
from src.ingestion.embedder import embed_chunks, embed_query
from config import REGULATIONS_DIR, INTERNAL_POLICIES_DIR
import numpy as np


def run_test():
    print("=" * 60)
    print("FinGuard — Phase 1 Ingestion Test")
    print("=" * 60)

    # Step 1: Generate sample documents
    print("\n[Step 1] Generating sample documents...")
    os.makedirs(REGULATIONS_DIR, exist_ok=True)
    os.makedirs(INTERNAL_POLICIES_DIR, exist_ok=True)

    write_file(REGULATIONS_DIR, "fatf_aml_recommendations.txt",   gsd.FATF_AML)
    write_file(REGULATIONS_DIR, "basel_iii_capital_framework.txt", gsd.BASEL_CAPITAL)
    write_file(REGULATIONS_DIR, "kyc_compliance_guidelines.txt",   gsd.KYC_GUIDELINES)
    write_file(REGULATIONS_DIR, "gdpr_financial_services.txt",     gsd.GDPR_FINANCIAL)

    write_file(INTERNAL_POLICIES_DIR, "internal_aml_policy.txt",     gsd.INTERNAL_AML)
    write_file(INTERNAL_POLICIES_DIR, "internal_kyc_policy.txt",      gsd.INTERNAL_KYC)
    write_file(INTERNAL_POLICIES_DIR, "internal_data_policy.txt",     gsd.INTERNAL_DATA)
    write_file(INTERNAL_POLICIES_DIR, "internal_capital_policy.txt",  gsd.INTERNAL_CAPITAL)

    # Step 2: Load documents
    print("\n[Step 2] Loading all documents...")
    reg_pages = load_all_documents(REGULATIONS_DIR)
    pol_pages = load_all_documents(INTERNAL_POLICIES_DIR)
    all_pages = reg_pages + pol_pages
    print(f"  Total sections loaded: {len(all_pages)}")
    assert len(all_pages) > 0, "No documents loaded!"

    # Step 3: Chunk
    print("\n[Step 3] Chunking documents...")
    chunks = chunk_pages(all_pages)
    print(f"  Total chunks created: {len(chunks)}")
    assert len(chunks) > len(all_pages), "Chunking should produce more items than pages"

    # Step 4: Embed
    print("\n[Step 4] Computing embeddings...")
    chunks = embed_chunks(chunks)
    assert "embedding" in chunks[0], "Embedding missing from chunks!"
    print(f"  Embedding shape: {chunks[0]['embedding'].shape}")

    # Step 5: Quick similarity test
    print("\n[Step 5] Quick similarity search test...")
    query = "customer due diligence requirements"
    query_vec = embed_query(query)

    # Cosine similarity (dot product since vectors are L2-normalized)
    scores = [np.dot(query_vec, c["embedding"]) for c in chunks]
    top_idx = int(np.argmax(scores))
    top_chunk = chunks[top_idx]

    print(f"  Query: '{query}'")
    print(f"  Top match (score={scores[top_idx]:.3f}):")
    print(f"    Source: {top_chunk['source']}, page {top_chunk['page']}")
    print(f"    Text preview: {top_chunk['text'][:150]}...")

    print("\n" + "=" * 60)
    print("Phase 1 PASSED ✓ — Ingestion pipeline working correctly")
    print("=" * 60)


if __name__ == "__main__":
    run_test()

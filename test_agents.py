"""
test_agents.py
──────────────
Smoke test for Phase 4 — verifies agents and orchestrator work correctly.

This test makes REAL Claude API calls — it will consume API credits.
Estimated cost: ~$0.10-0.30 for the full test suite.

Tests:
  1. Orchestrator correctly classifies simple vs complex queries
  2. RetrievalAgent answers a factual question with citations
  3. Orchestrator routes a complex query to the audit pipeline
  4. Full audit pipeline produces a report and saves it to disk
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
from src.mcp_server.compliance_tools import ComplianceToolExecutor
from src.agents.orchestrator import Orchestrator, COMPLEX_QUERY_SIGNALS
from config import REGULATIONS_DIR, INTERNAL_POLICIES_DIR, REPORTS_DIR


def setup():
    """Build the full stack — docs → chunks → embeddings → search engine."""
    os.makedirs(REGULATIONS_DIR, exist_ok=True)
    os.makedirs(INTERNAL_POLICIES_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    write_file(REGULATIONS_DIR, "fatf_aml_recommendations.txt",    gsd.FATF_AML)
    write_file(REGULATIONS_DIR, "basel_iii_capital_framework.txt", gsd.BASEL_CAPITAL)
    write_file(REGULATIONS_DIR, "kyc_compliance_guidelines.txt",   gsd.KYC_GUIDELINES)
    write_file(REGULATIONS_DIR, "gdpr_financial_services.txt",     gsd.GDPR_FINANCIAL)
    write_file(INTERNAL_POLICIES_DIR, "internal_aml_policy.txt",   gsd.INTERNAL_AML)
    write_file(INTERNAL_POLICIES_DIR, "internal_kyc_policy.txt",   gsd.INTERNAL_KYC)
    write_file(INTERNAL_POLICIES_DIR, "internal_data_policy.txt",  gsd.INTERNAL_DATA)
    write_file(INTERNAL_POLICIES_DIR, "internal_capital_policy.txt", gsd.INTERNAL_CAPITAL)

    print("[Setup] Loading and indexing documents...")
    reg_chunks = embed_chunks(chunk_pages(load_all_documents(REGULATIONS_DIR)))
    pol_chunks = embed_chunks(chunk_pages(load_all_documents(INTERNAL_POLICIES_DIR)),
                              force_recompute=True)

    engine = HybridSearchEngine()
    engine.build(reg_chunks, pol_chunks)

    executor = ComplianceToolExecutor(engine)
    orchestrator = Orchestrator(executor)
    return orchestrator


def run_test():
    print("=" * 60)
    print("FinGuard — Phase 4 Agents & Orchestrator Test")
    print("=" * 60)
    print("\nNOTE: This test makes real Claude API calls (~$0.10-0.30)")

    orchestrator = setup()

    # ── Test 1: Query classification ─────────────────────────────
    print("\n[Test 1] Query classification (no API calls)...")
    simple_queries = [
        "What does FATF Recommendation 10 say?",
        "What is our current CTR threshold?",
        "What encryption standard do we use?",
    ]
    complex_queries = [
        "Run a full compliance audit",
        "What are our AML compliance gaps?",
        "Analyze our compliance across all regulatory requirements",
    ]

    for q in simple_queries:
        result = orchestrator._classify_query(q)
        assert result == "simple", f"Expected simple, got {result} for: {q}"
        print(f"  ✓ SIMPLE: {q[:60]}")

    for q in complex_queries:
        result = orchestrator._classify_query(q)
        assert result == "complex", f"Expected complex, got {result} for: {q}"
        print(f"  ✓ COMPLEX: {q[:60]}")

    # ── Test 2: Retrieval agent (simple query) ────────────────────
    print("\n[Test 2] RetrievalAgent — simple factual query...")
    result = orchestrator.run(
        "What does FATF Recommendation 10 require for customer due diligence?",
        verbose=True
    )
    assert result["pipeline"] == "retrieval"
    assert len(result["answer"]) > 100
    print(f"\n  Answer preview: {result['answer'][:200]}...")
    print(f"  Sources cited: {len(result['sources'])}")
    for s in result["sources"]:
        print(f"    - {s['source']} p.{s['page']}")

    # ── Test 3: Audit pipeline (complex query) ────────────────────
    print("\n[Test 3] Audit pipeline — AML gap analysis...")
    result = orchestrator.run(
        "Analyze our compliance gaps in AML record keeping and suspicious transaction reporting",
        verbose=True
    )
    assert result["pipeline"] == "audit"
    findings = result["findings"]

    print(f"\n  Risk Level: {findings.get('risk_level', 'N/A')}")
    print(f"  Gaps found: {len(findings.get('gaps', []))}")
    print(f"  Report saved: {result.get('report_path', 'N/A')}")

    if findings.get("gaps"):
        gap = findings["gaps"][0]
        print(f"\n  First gap: {gap.get('area', 'N/A')}")
        print(f"  Severity: {gap.get('severity', 'N/A')}")
        print(f"  Description: {gap.get('gap_description', 'N/A')[:150]}...")

    # Verify report was saved
    assert os.path.exists(result["report_path"]), "Report file not saved!"
    print(f"\n  ✓ Report file exists on disk")

    print("\n" + "=" * 60)
    print("Phase 4 PASSED ✓ — Agents and orchestrator working correctly")
    print("=" * 60)
    print(f"\nFull audit report saved to: {result.get('report_path')}")


if __name__ == "__main__":
    run_test()

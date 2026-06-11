"""
test_mcp.py
───────────
Smoke test for Phase 3 — verifies the MCP tool executor works.

We test the ComplianceToolExecutor directly (no MCP protocol overhead)
since that's what the orchestrator uses internally. The MCP server
wraps the same logic for external protocol-compliant clients.

Expected output:
  - All three tools execute and return structured JSON
  - Gap analysis returns results from both corpora
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import generate_sample_docs as gsd
from generate_sample_docs import write_file
from src.ingestion.doc_loader import load_all_documents
from src.ingestion.chunker import chunk_pages
from src.ingestion.embedder import embed_chunks
from src.retrieval.hybrid_search import HybridSearchEngine
from src.mcp_server.compliance_tools import ComplianceToolExecutor, TOOL_SCHEMAS
from config import REGULATIONS_DIR, INTERNAL_POLICIES_DIR


def setup_engine():
    """Reusable setup — load docs, embed, build search engine."""
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

    reg_chunks = embed_chunks(chunk_pages(load_all_documents(REGULATIONS_DIR)))
    pol_chunks = embed_chunks(chunk_pages(load_all_documents(INTERNAL_POLICIES_DIR)),
                              force_recompute=True)

    engine = HybridSearchEngine()
    engine.build(reg_chunks, pol_chunks)
    return engine


def run_test():
    print("=" * 60)
    print("FinGuard — Phase 3 MCP Tools Test")
    print("=" * 60)

    print("\n[Setup] Building search engine...")
    engine = setup_engine()
    executor = ComplianceToolExecutor(engine)

    # ── Test 1: Tool schemas ──────────────────────────────────────
    print("\n[Test 1] Verifying tool schemas...")
    assert len(TOOL_SCHEMAS) == 3, "Expected 3 tool schemas"
    for schema in TOOL_SCHEMAS:
        assert "name" in schema
        assert "description" in schema
        assert "input_schema" in schema
        print(f"  ✓ Tool: {schema['name']}")

    # ── Test 2: search_regulations tool ──────────────────────────
    print("\n[Test 2] Calling search_regulations tool...")
    result_json = executor.execute("search_regulations", {
        "query": "suspicious transaction reporting requirements",
        "top_k": 3
    })
    results = json.loads(result_json)
    assert len(results) > 0
    print(f"  Returned {len(results)} results")
    print(f"  Top result: [{results[0]['source']} p.{results[0]['page']}]")
    print(f"  Text: {results[0]['text'][:120]}...")

    # ── Test 3: search_policies tool ─────────────────────────────
    print("\n[Test 3] Calling search_policies tool...")
    result_json = executor.execute("search_policies", {
        "query": "record retention period",
        "top_k": 3
    })
    results = json.loads(result_json)
    assert len(results) > 0
    print(f"  Returned {len(results)} results")
    print(f"  Top result: [{results[0]['source']} p.{results[0]['page']}]")
    print(f"  Text: {results[0]['text'][:120]}...")

    # ── Test 4: check_compliance_gap tool (the key one) ───────────
    print("\n[Test 4] Calling check_compliance_gap tool...")
    result_json = executor.execute("check_compliance_gap", {
        "topic": "record keeping retention period AML",
        "top_k": 3
    })
    gap = json.loads(result_json)
    assert "topic" in gap
    assert "regulatory_requirements" in gap
    assert "current_policies" in gap
    print(f"  Topic: {gap['topic']}")
    print(f"  Regulatory results: {len(gap['regulatory_requirements'])}")
    print(f"  Policy results:     {len(gap['current_policies'])}")
    print(f"\n  Regulation says: {gap['regulatory_requirements'][0]['text'][:150]}...")
    print(f"\n  Policy says:     {gap['current_policies'][0]['text'][:150]}...")

    # ── Test 5: Unknown tool error handling ───────────────────────
    print("\n[Test 5] Testing unknown tool error handling...")
    result_json = executor.execute("nonexistent_tool", {})
    error = json.loads(result_json)
    assert "error" in error
    print(f"  ✓ Error handled gracefully: {error['error']}")

    print("\n" + "=" * 60)
    print("Phase 3 PASSED ✓ — MCP tools working correctly")
    print("=" * 60)


if __name__ == "__main__":
    run_test()

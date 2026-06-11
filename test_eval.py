"""
test_eval.py
────────────
Smoke test for Phase 5 — the evaluation framework.

The eval suite test (run_eval_suite) makes NO API calls — it only
tests the RAG retrieval quality against known ground-truth cases.
This runs fully without API credits.

The evaluate_findings test requires API credits for the LLM judge
but gracefully skips it and falls back to rule-based scoring only.
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
from src.mcp_server.compliance_tools import ComplianceToolExecutor
from src.evaluation.eval_framework import EvalFramework, EVAL_TEST_CASES
from config import REGULATIONS_DIR, INTERNAL_POLICIES_DIR


def setup():
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
    return ComplianceToolExecutor(engine)


def run_test():
    print("=" * 60)
    print("FinGuard — Phase 5 Evaluation Framework Test")
    print("=" * 60)

    executor = setup()
    evaluator = EvalFramework()

    # ── Test 1: Eval test cases are well-formed ───────────────────
    print("\n[Test 1] Verifying eval test cases...")
    assert len(EVAL_TEST_CASES) >= 4
    for case in EVAL_TEST_CASES:
        assert "id" in case
        assert "topic" in case
        assert "expected_gaps" in case
        assert "expected_sources" in case
        print(f"  ✓ {case['id']}: {case['description']}")

    # ── Test 2: Rule-based eval on mock findings ──────────────────
    print("\n[Test 2] Rule-based evaluation on mock findings...")

    good_findings = {
        "summary": "Several compliance gaps identified in AML and KYC areas.",
        "risk_level": "HIGH",
        "gaps": [
            {
                "id": "GAP-001",
                "area": "AML Record Retention",
                "severity": "HIGH",
                "regulation_requires": "5 year minimum retention per FATF R.11",
                "policy_currently_does": "3 year retention policy",
                "gap_description": "Record retention period is 2 years shorter than required",
                "recommendation": "Update retention policy to 5 years minimum",
                "regulatory_source": "fatf_aml_recommendations.txt",
                "policy_source": "internal_aml_policy.txt",
            }
        ],
        "compliant_areas": ["PEP screening process"],
        "priority_actions": ["Update retention policy immediately"],
    }

    result = evaluator._rule_based_eval(good_findings, tool_calls=[])
    print(f"  Rule-based score: {result['score']}/10")
    for check, passed in result["checks"].items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
    assert result["score"] >= 7.0, f"Expected score >= 7, got {result['score']}"

    # ── Test 3: Rule-based eval on poor findings ──────────────────
    print("\n[Test 3] Rule-based evaluation on incomplete findings...")
    poor_findings = {
        "summary": "No issues found.",
        "risk_level": "LOW",
        "gaps": [],
        "compliant_areas": [],
        "priority_actions": [],
    }
    result = evaluator._rule_based_eval(poor_findings, tool_calls=[])
    print(f"  Rule-based score: {result['score']}/10 (expected low)")
    assert result["score"] < 7.0, "Poor findings should score below threshold"
    print(f"  ✓ Correctly scored below threshold")

    # ── Test 4: Full eval suite (no API calls needed) ─────────────
    print("\n[Test 4] Running full eval suite against ground truth...")
    suite_results = evaluator.run_eval_suite(executor, verbose=True)

    print(f"\n  Pass rate: {suite_results['pass_rate']*100:.0f}% "
          f"({suite_results['passed_cases']}/{suite_results['total_cases']})")

    assert suite_results["pass_rate"] >= 0.5, \
        f"Expected >= 50% pass rate, got {suite_results['pass_rate']*100:.0f}%"

    # ── Test 5: Full evaluate_findings (graceful API fallback) ────
    print("\n[Test 5] Full evaluate_findings (LLM judge with graceful fallback)...")
    eval_result = evaluator.evaluate_findings(
        findings=good_findings,
        tool_calls=[],
        verbose=True,
    )
    print(f"  Overall score: {eval_result['overall_score']}/10")
    print(f"  Passed: {eval_result['passed']}")
    print(f"  LLM judge: {'ran' if eval_result['llm_judge'] else 'skipped (no credits)'}")

    assert "overall_score" in eval_result
    assert "passed" in eval_result

    print("\n" + "=" * 60)
    print("Phase 5 PASSED ✓ — Evaluation framework working correctly")
    print("=" * 60)
    print(f"\nEval suite pass rate: {suite_results['pass_rate']*100:.0f}%")
    print("Note: LLM judge requires API credits to run — falls back to rule-based scoring")


if __name__ == "__main__":
    run_test()

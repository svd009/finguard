"""
eval_framework.py
─────────────────
Automated evaluation framework for FinGuard's compliance analysis outputs.

What is prompt evaluation?
  Prompt evaluation (evals) is the practice of systematically measuring
  the quality of LLM outputs. It's one of the most important and
  underrated skills in production AI engineering.

  Without evals: you have no idea if your system is actually good.
  With evals:    you can measure quality, catch regressions, and
                 make confident improvements.

Two evaluation methods used here:

  1. RULE-BASED EVALUATION (no API cost)
     Checks structural properties of the output:
     - Did the agent cite sources?
     - Does the JSON have all required fields?
     - Is the risk level a valid value?
     - Are there any findings at all?
     Fast, deterministic, zero cost. Always runs first.

  2. MODEL-AS-JUDGE (uses Claude Haiku)
     Uses Claude to grade Claude's output on qualitative dimensions:
     - Accuracy: Are findings grounded in the retrieved documents?
     - Completeness: Were all major gaps identified?
     - Clarity: Is the report clear to a compliance officer?
     - Actionability: Are recommendations specific and implementable?
     This is the "Discernment" layer from Course 1's 4D Framework.

Why model-as-judge?
  Human evaluation of compliance text is expensive and slow.
  A judge LLM can evaluate thousands of outputs cheaply.
  Research shows LLM judges correlate well with human judgments
  on structured tasks like compliance analysis.
  Used in production by Anthropic, Google, and major AI labs.

Course 2 concepts demonstrated:
  - Structured outputs (eval scores as typed JSON)
  - System prompts for specialized personas (judge persona)
  - Prompt engineering with XML tags and examples
  - Automated test datasets (eval_cases below)
"""

import json
import anthropic
from datetime import datetime
from config import ANTHROPIC_API_KEY, MODEL_FAST, EVAL_PASS_THRESHOLD


JUDGE_SYSTEM_PROMPT = """You are an expert compliance evaluation judge assessing the quality of AI-generated regulatory compliance analysis.

Your role is to objectively evaluate compliance audit outputs on four dimensions.

<evaluation_criteria>

<criterion name="accuracy" weight="30%">
Are the identified gaps accurately grounded in the retrieved regulatory documents?
Do the findings correctly represent what regulations require vs what policies say?
Score 1-10: 1=completely wrong, 5=partially accurate, 10=fully accurate
</criterion>

<criterion name="completeness" weight="30%">
Were all significant compliance gaps identified?
Are there obvious gaps that were missed?
Score 1-10: 1=missed most gaps, 5=found some gaps, 10=comprehensive coverage
</criterion>

<criterion name="clarity" weight="20%">
Is the analysis clear and understandable to a compliance officer?
Are findings specific enough to act on?
Score 1-10: 1=confusing, 5=adequate, 10=crystal clear
</criterion>

<criterion name="actionability" weight="20%">
Are the recommendations specific and implementable?
Do they tell the compliance team exactly what to do?
Score 1-10: 1=vague, 5=somewhat actionable, 10=highly specific
</criterion>

</evaluation_criteria>

<output_format>
Return ONLY valid JSON with no markdown fences:
{
  "scores": {
    "accuracy": <int 1-10>,
    "completeness": <int 1-10>,
    "clarity": <int 1-10>,
    "actionability": <int 1-10>
  },
  "weighted_score": <float, calculated as weighted average>,
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "judge_reasoning": "Brief explanation of overall assessment",
  "pass": <boolean, true if weighted_score >= 7.0>
}
</output_format>"""


# ── Eval test cases ───────────────────────────────────────────────────────────
# These are ground-truth cases used to validate the system.
# Each case has an input topic and expected findings that SHOULD be present.
# This is a mini eval dataset — in production you'd have hundreds of these.

EVAL_TEST_CASES = [
    {
        "id": "EVAL-001",
        "topic": "AML record retention",
        "expected_gaps": [
            "record retention period shorter than regulatory requirement",
            "3 year vs 5 year retention",
        ],
        "expected_sources": [
            "fatf_aml_recommendations.txt",
            "internal_aml_policy.txt",
        ],
        "description": "Tests whether the system catches the 3yr vs 5yr retention gap"
    },
    {
        "id": "EVAL-002",
        "topic": "customer due diligence ongoing monitoring",
        "expected_gaps": [
            "ongoing monitoring",
            "ad-hoc",
            "no formal schedule",
        ],
        "expected_sources": [
            "fatf_aml_recommendations.txt",
            "internal_aml_policy.txt",
        ],
        "description": "Tests detection of missing ongoing CDD review schedule"
    },
    {
        "id": "EVAL-003",
        "topic": "KYC control person identification",
        "expected_gaps": [
            "control person",
            "management responsibility",
        ],
        "expected_sources": [
            "kyc_compliance_guidelines.txt",
            "internal_kyc_policy.txt",
        ],
        "description": "Tests detection of missing control person identification"
    },
    {
        "id": "EVAL-004",
        "topic": "data encryption security standards",
        "expected_gaps": [
            "AES-128",
            "AES-256",
            "encryption",
        ],
        "expected_sources": [
            "gdpr_financial_services.txt",
            "internal_data_policy.txt",
        ],
        "description": "Tests detection of AES-128 vs AES-256 encryption gap"
    },
]


class EvalFramework:
    """
    Automated evaluation framework for FinGuard outputs.

    Runs two-stage evaluation:
      Stage 1: Rule-based checks (fast, free)
      Stage 2: Model-as-judge scoring (slower, small API cost)

    The 4D Framework's DISCERNMENT layer — ensuring outputs meet
    quality standards before being shown to compliance officers.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def evaluate_findings(self, findings: dict, tool_calls: list,
                          verbose: bool = True) -> dict:
        """
        Run full evaluation on a set of compliance findings.

        Args:
            findings:   Parsed findings dict from ReasoningAgent
            tool_calls: Tool calls log (used to verify source citations)
            verbose:    Print evaluation progress

        Returns:
            {
              "rule_based":    dict,   ← structural checks
              "llm_judge":     dict,   ← model-as-judge scores (if API available)
              "overall_score": float,  ← final weighted score
              "passed":        bool,   ← True if score >= EVAL_PASS_THRESHOLD
              "timestamp":     str,
            }
        """
        if verbose:
            print(f"\n  [EvalFramework] Running evaluation...")

        # Stage 1: Rule-based checks
        rule_results = self._rule_based_eval(findings, tool_calls)
        if verbose:
            print(f"  [EvalFramework] Rule-based score: "
                  f"{rule_results['score']:.1f}/10")

        # Stage 2: Model-as-judge (may fail if no API credits)
        llm_results = None
        try:
            llm_results = self._llm_judge_eval(findings, verbose)
            if verbose:
                print(f"  [EvalFramework] LLM judge score: "
                      f"{llm_results.get('weighted_score', 0):.1f}/10")
        except Exception as e:
            if verbose:
                print(f"  [EvalFramework] LLM judge skipped: {str(e)[:60]}")

        # Combine scores
        if llm_results and "weighted_score" in llm_results:
            # Weight: 40% rule-based, 60% LLM judge
            overall = (rule_results["score"] * 0.4 +
                       llm_results["weighted_score"] * 0.6)
        else:
            overall = rule_results["score"]

        passed = overall >= EVAL_PASS_THRESHOLD

        if verbose:
            status = "✓ PASSED" if passed else "✗ FLAGGED FOR REVIEW"
            print(f"  [EvalFramework] Overall: {overall:.1f}/10 — {status}")

        return {
            "rule_based":    rule_results,
            "llm_judge":     llm_results,
            "overall_score": round(overall, 2),
            "passed":        passed,
            "threshold":     EVAL_PASS_THRESHOLD,
            "timestamp":     datetime.now().isoformat(),
        }

    def run_eval_suite(self, tool_executor, verbose: bool = True) -> dict:
        """
        Run the full eval test suite against known ground-truth cases.

        This validates the RAG pipeline quality — do we retrieve the
        right documents for each known compliance gap topic?

        Args:
            tool_executor: ComplianceToolExecutor instance
            verbose:       Print progress

        Returns:
            {
              "cases":        list of individual case results,
              "pass_rate":    float (0.0 to 1.0),
              "total_cases":  int,
              "passed_cases": int,
            }
        """
        if verbose:
            print(f"\n  [EvalFramework] Running eval suite "
                  f"({len(EVAL_TEST_CASES)} test cases)...")

        case_results = []
        passed = 0

        for case in EVAL_TEST_CASES:
            result = self._run_single_case(case, tool_executor, verbose)
            case_results.append(result)
            if result["passed"]:
                passed += 1

        pass_rate = passed / len(EVAL_TEST_CASES)

        if verbose:
            print(f"\n  [EvalFramework] Suite complete: "
                  f"{passed}/{len(EVAL_TEST_CASES)} passed "
                  f"({pass_rate*100:.0f}%)")

        return {
            "cases":        case_results,
            "pass_rate":    pass_rate,
            "total_cases":  len(EVAL_TEST_CASES),
            "passed_cases": passed,
        }

    # ── Private methods ───────────────────────────────────────────────────────

    def _rule_based_eval(self, findings: dict, tool_calls: list) -> dict:
        """
        Stage 1: Rule-based structural evaluation.
        No API calls — purely checks the shape and content of findings.
        """
        checks = {}
        score = 0.0
        max_score = 10.0

        # Check 1: Has required fields (2 points)
        required_fields = ["summary", "risk_level", "gaps",
                           "compliant_areas", "priority_actions"]
        missing = [f for f in required_fields if f not in findings]
        checks["has_required_fields"] = len(missing) == 0
        if checks["has_required_fields"]:
            score += 2.0

        # Check 2: Risk level is valid (1 point)
        valid_risk_levels = {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}
        checks["valid_risk_level"] = findings.get("risk_level") in valid_risk_levels
        if checks["valid_risk_level"]:
            score += 1.0

        # Check 3: Has at least one gap finding (2 points)
        gaps = findings.get("gaps", [])
        checks["has_gaps"] = len(gaps) > 0
        if checks["has_gaps"]:
            score += 2.0

        # Check 4: Gaps have required subfields (2 points)
        gap_fields = ["area", "severity", "gap_description", "recommendation"]
        if gaps:
            all_complete = all(
                all(f in gap for f in gap_fields) for gap in gaps
            )
            checks["gaps_have_required_fields"] = all_complete
            if all_complete:
                score += 2.0
        else:
            checks["gaps_have_required_fields"] = False

        # Check 5: Has source citations (2 points)
        has_sources = any(
            "regulatory_source" in gap or "policy_source" in gap
            for gap in gaps
        )
        checks["has_citations"] = has_sources
        if has_sources:
            score += 2.0

        # Check 6: Has priority actions (1 point)
        checks["has_priority_actions"] = len(
            findings.get("priority_actions", [])
        ) > 0
        if checks["has_priority_actions"]:
            score += 1.0

        return {
            "checks": checks,
            "score":  round(score, 1),
            "max":    max_score,
            "passed": score >= EVAL_PASS_THRESHOLD,
        }

    def _llm_judge_eval(self, findings: dict, verbose: bool) -> dict:
        """
        Stage 2: Model-as-judge evaluation using Claude Haiku.
        Scores findings on accuracy, completeness, clarity, actionability.
        """
        judge_prompt = f"""
<findings_to_evaluate>
{json.dumps(findings, indent=2)[:3000]}
</findings_to_evaluate>

<task>
Evaluate the compliance analysis above according to your scoring criteria.
Return ONLY valid JSON as specified in your system prompt.
</task>"""

        response = self.client.messages.create(
            model=MODEL_FAST,
            max_tokens=800,
            system=JUDGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": judge_prompt}],
        )

        raw = response.content[0].text.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:-1])

        return json.loads(raw)

    def _run_single_case(self, case: dict, tool_executor,
                          verbose: bool) -> dict:
        """
        Run a single eval test case — check if retrieval finds expected content.
        """
        if verbose:
            print(f"\n  [EvalFramework] Case {case['id']}: {case['description']}")

        # Run the gap check tool
        result_json = tool_executor.execute("check_compliance_gap", {
            "topic": case["topic"],
            "top_k": 5,
        })
        gap_data = json.loads(result_json)

        # Collect all retrieved text
        all_text = " ".join([
            r["text"].lower()
            for r in gap_data.get("regulatory_requirements", []) +
                      gap_data.get("current_policies", [])
        ])

        # Check if expected gap keywords appear in retrieved text
        keyword_hits = sum(
            1 for kw in case["expected_gaps"]
            if kw.lower() in all_text
        )
        keyword_score = keyword_hits / len(case["expected_gaps"])

        # Check if expected sources were retrieved
        all_sources = set(
            r["source"]
            for r in gap_data.get("regulatory_requirements", []) +
                      gap_data.get("current_policies", [])
        )
        source_hits = sum(
            1 for s in case["expected_sources"]
            if s in all_sources
        )
        source_score = source_hits / len(case["expected_sources"])

        # Combined score
        case_score = (keyword_score * 0.6 + source_score * 0.4) * 10
        passed = case_score >= EVAL_PASS_THRESHOLD

        if verbose:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status} — keyword hits: {keyword_hits}/{len(case['expected_gaps'])} | "
                  f"source hits: {source_hits}/{len(case['expected_sources'])} | "
                  f"score: {case_score:.1f}/10")

        return {
            "case_id":       case["id"],
            "topic":         case["topic"],
            "keyword_score": round(keyword_score, 2),
            "source_score":  round(source_score, 2),
            "case_score":    round(case_score, 1),
            "passed":        passed,
        }

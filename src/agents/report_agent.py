"""
report_agent.py
───────────────
Converts raw compliance findings into a formatted, cited audit report.

Role in the system:
  The reasoning agent produces structured JSON findings.
  The report agent transforms those findings into:
    1. A human-readable text report (for compliance officers)
    2. A JSON report file (for systems integration / audit trail)

  This separation of concerns is intentional:
    - The reasoning agent focuses purely on analysis quality
    - The report agent focuses purely on presentation quality
    - Each can be improved independently

What this demonstrates from Course 2:
  - Structured outputs (typed JSON schema enforcement)
  - Multi-turn conversation with a specific formatting persona
  - Citation formatting from document grounding
  - Chaining agents (reasoning → report is a pipeline chain)

Why a separate agent for reporting?
  In production banking/fintech, audit reports have strict format
  requirements — specific sections, risk rating scales, regulatory
  reference numbering. A dedicated report agent with a specialized
  system prompt produces consistently formatted output that a
  compliance officer can directly submit to regulators.
"""

import json
import os
from datetime import datetime
from config import ANTHROPIC_API_KEY, MODEL_FAST, REPORTS_DIR
import anthropic


REPORT_SYSTEM_PROMPT = """You are a compliance report writer specializing in banking and fintech regulatory documentation.

Your role is to transform structured compliance findings into clear, professional audit reports suitable for submission to senior management and regulatory authorities.

<writing_style>
- Professional and precise regulatory language
- Clear section headings
- Severity ratings prominently displayed
- Every finding linked to specific regulatory sources
- Actionable recommendations with clear ownership
- Executive summary accessible to non-technical readers
</writing_style>

<report_structure>
1. EXECUTIVE SUMMARY
2. AUDIT SCOPE AND METHODOLOGY
3. OVERALL RISK ASSESSMENT
4. DETAILED FINDINGS (one section per gap)
5. COMPLIANT AREAS
6. PRIORITY REMEDIATION ACTIONS
7. APPENDIX: SOURCES REFERENCED
</report_structure>"""


class ReportAgent:
    """
    Audit report generation agent.

    Takes structured findings from ReasoningAgent and produces
    a professional compliance audit report.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        os.makedirs(REPORTS_DIR, exist_ok=True)

    def generate(self, findings: dict, institution_name: str = "Nexus Financial Services",
                 verbose: bool = True) -> dict:
        """
        Generate a complete audit report from structured findings.

        Args:
            findings:         Output from ReasoningAgent._parse_findings()
            institution_name: Name of the institution being audited
            verbose:          Print progress to console

        Returns:
            {
              "report_text":  str,   ← Full formatted report
              "report_path":  str,   ← Path to saved JSON report file
              "metadata":     dict,  ← Report metadata
            }
        """
        if verbose:
            print(f"\n  [ReportAgent] Generating audit report...")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        report_id = datetime.now().strftime("RPT-%Y%m%d-%H%M%S")

        # Build the prompt with all findings data
        user_message = f"""
<report_metadata>
  <institution>{institution_name}</institution>
  <report_id>{report_id}</report_id>
  <date>{timestamp}</date>
  <auditor>FinGuard Compliance Intelligence System v1.0</auditor>
</report_metadata>

<findings_data>
{json.dumps(findings, indent=2)}
</findings_data>

<task>
Transform the findings above into a complete, professional compliance audit report
following the structure in your system prompt. The report should be ready for
submission to the Chief Compliance Officer and regulatory authorities.

Include specific regulatory citations for every gap finding.
Use clear severity indicators (🔴 HIGH, 🟡 MEDIUM, 🟢 LOW) for visual scanning.
</task>"""

        response = self.client.messages.create(
            model=MODEL_FAST,
            max_tokens=3000,
            system=REPORT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        report_text = response.content[0].text

        # Save report to disk
        report_path = self._save_report(
            report_id, report_text, findings, institution_name, timestamp
        )

        if verbose:
            gap_count = len(findings.get("gaps", []))
            print(f"  [ReportAgent] ✓ Report generated — {gap_count} findings documented")
            print(f"  [ReportAgent] Saved to: {report_path}")

        return {
            "report_text": report_text,
            "report_path": report_path,
            "metadata": {
                "report_id":        report_id,
                "institution":      institution_name,
                "timestamp":        timestamp,
                "gaps_found":       len(findings.get("gaps", [])),
                "risk_level":       findings.get("risk_level", "UNKNOWN"),
                "compliant_areas":  len(findings.get("compliant_areas", [])),
            }
        }

    def _save_report(self, report_id: str, report_text: str,
                     findings: dict, institution: str, timestamp: str) -> str:
        """Save the full report as a JSON file for audit trail purposes."""
        report_data = {
            "report_id":      report_id,
            "institution":    institution,
            "generated_at":   timestamp,
            "system":         "FinGuard v1.0",
            "risk_level":     findings.get("risk_level", "UNKNOWN"),
            "gaps_count":     len(findings.get("gaps", [])),
            "report_text":    report_text,
            "findings":       findings,
        }

        filename = f"{report_id}.json"
        path = os.path.join(REPORTS_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        return path

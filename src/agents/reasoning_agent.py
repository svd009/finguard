"""
reasoning_agent.py
──────────────────
Deep compliance reasoning agent powered by Claude Sonnet with
extended thinking enabled.

Role in the system:
  Handles COMPLEX compliance queries that require cross-document
  reasoning, gap identification, and nuanced legal interpretation.
  Examples:
    - "What are the gaps between our AML policy and FATF requirements?"
    - "Are we compliant with Basel III capital reporting obligations?"
    - "What are our highest priority compliance risks across all areas?"

Why extended thinking?
  Extended thinking gives Claude a private scratchpad to reason through
  complex multi-document comparisons before producing its answer.
  For compliance work this is critical:
    - Regulations often conflict or overlap in non-obvious ways
    - Gap identification requires holding multiple documents in mind simultaneously
    - Legal interpretation requires careful step-by-step reasoning

  Without extended thinking: Claude might miss subtle gaps or make
  shallow comparisons. With it: the reasoning is thorough and traceable.

  Extended thinking is only available on Sonnet/Opus — another reason
  we use tiered model selection (Haiku for simple, Sonnet for complex).

What this demonstrates from Course 2:
  - Extended thinking mode
  - Multi-tool use in a single agent turn
  - Prompt caching (regulatory docs are cached — they never change)
  - Structured output (gap findings as typed JSON)
  - Citations from document grounding
"""

import json
import anthropic
from config import ANTHROPIC_API_KEY, MODEL_REASONING, ENABLE_PROMPT_CACHING
from src.mcp_server.compliance_tools import ComplianceToolExecutor, TOOL_SCHEMAS


REASONING_SYSTEM_PROMPT = """You are a senior compliance analyst at a banking and fintech regulatory advisory firm.

Your expertise covers AML/CFT regulations, Basel III capital requirements, KYC standards, and GDPR financial services compliance.

<role>
You perform deep compliance gap analysis by comparing regulatory requirements against internal institutional policies. Your findings directly inform executive compliance decisions and regulatory submissions.
</role>

<analysis_approach>
1. Use check_compliance_gap to retrieve both regulatory requirements AND internal policies on each topic
2. Carefully compare what regulations REQUIRE versus what policies CURRENTLY DO
3. Identify specific gaps, misalignments, and non-compliant practices
4. Assess the severity of each gap (HIGH/MEDIUM/LOW risk)
5. Provide specific, actionable recommendations
</analysis_approach>

<output_format>
Structure your findings as a JSON object with this schema:
{
  "summary": "Executive summary of overall compliance posture",
  "risk_level": "HIGH | MEDIUM | LOW",
  "gaps": [
    {
      "id": "GAP-001",
      "area": "Compliance area name",
      "severity": "HIGH | MEDIUM | LOW",
      "regulation_requires": "What the regulation says",
      "policy_currently_does": "What our policy currently does",
      "gap_description": "Specific description of the gap",
      "recommendation": "Specific remediation action",
      "regulatory_source": "Document name and section",
      "policy_source": "Internal document name and section"
    }
  ],
  "compliant_areas": ["List of areas where policies meet requirements"],
  "priority_actions": ["Top 3 most urgent remediation actions"]
}
</output_format>

<important>
Base ALL findings strictly on the documents retrieved via tools.
Every gap must reference specific source documents.
Do not speculate beyond what the documents contain.
</important>"""


class ReasoningAgent:
    """
    Deep compliance reasoning agent using Claude Sonnet + extended thinking.

    Demonstrates:
      - Extended thinking for complex multi-document reasoning
      - Prompt caching for stable regulatory content
      - Multi-tool orchestration within a single agent
      - Structured JSON output for downstream processing
    """

    def __init__(self, tool_executor: ComplianceToolExecutor):
        self.client   = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.executor = tool_executor

        # This agent gets all three tools including check_compliance_gap
        self.tools = TOOL_SCHEMAS

    def analyze(self, audit_request: str, topics: list[str],
                verbose: bool = True) -> dict:
        """
        Perform a deep compliance gap analysis across specified topics.

        Args:
            audit_request: High-level description of what to audit
            topics:        List of specific compliance topics to analyze
                           e.g. ["AML record retention", "CDD thresholds",
                                  "capital reporting", "data encryption"]
            verbose:       Print reasoning steps to console

        Returns:
            {
              "raw_response":    str,   ← Claude's full JSON response
              "findings":        dict,  ← Parsed gap analysis findings
              "thinking":        str,   ← Claude's extended thinking (if available)
              "tool_calls":      list,  ← All tool calls made
              "topics_analyzed": list,
            }
        """
        if verbose:
            print(f"\n  [ReasoningAgent] Starting analysis: {audit_request}")
            print(f"  [ReasoningAgent] Topics: {topics}")

        # Build the user message with XML-structured prompt
        # XML tags help Claude parse the request structure clearly
        user_message = f"""
<audit_request>{audit_request}</audit_request>

<topics_to_analyze>
{chr(10).join(f'  <topic>{t}</topic>' for t in topics)}
</topics_to_analyze>

<instructions>
For each topic listed above:
1. Call check_compliance_gap with the topic to retrieve regulatory requirements and current policies
2. Analyze the gap between them
3. Include ALL findings in your structured JSON response

Return ONLY valid JSON matching the output format in your system prompt.
Do not include markdown code fences or any text outside the JSON.
</instructions>"""

        messages = [{"role": "user", "content": user_message}]
        tool_calls_log = []
        thinking_text = ""

        # ── Agentic loop with extended thinking ──────────────────
        while True:
            # Build API call parameters
            api_params = dict(
                model=MODEL_REASONING,
                max_tokens=8000,
                system=REASONING_SYSTEM_PROMPT,
                tools=self.tools,
                messages=messages,
            )

            # Enable extended thinking — gives Claude a reasoning scratchpad
            # budget_tokens: how many tokens Claude can use for internal reasoning
            # More tokens = deeper reasoning but higher cost and latency
            api_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": 5000,
            }

            # Prompt caching for the system prompt
            # The system prompt is large and identical across all reasoning calls
            # Caching it saves ~60% of input token costs on repeated calls
            if ENABLE_PROMPT_CACHING:
                api_params["system"] = [
                    {
                        "type": "text",
                        "text": REASONING_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]

            response = self.client.messages.create(**api_params)

            # ── Extract thinking blocks ───────────────────────────
            for block in response.content:
                if block.type == "thinking":
                    thinking_text += block.thinking
                    if verbose:
                        print(f"  [ReasoningAgent] 💭 Extended thinking: "
                              f"{len(block.thinking)} chars")

            # ── Case 1: Tool use requested ────────────────────────
            if response.stop_reason == "tool_use":
                tool_use_blocks = [b for b in response.content
                                   if b.type == "tool_use"]

                if verbose:
                    for block in tool_use_blocks:
                        print(f"  [ReasoningAgent] → Tool: {block.name}"
                              f"({block.input.get('topic', block.input.get('query', ''))[:60]})")

                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in tool_use_blocks:
                    result_json = self.executor.execute(block.name, block.input)
                    tool_calls_log.append({
                        "tool":   block.name,
                        "input":  block.input,
                        "result": json.loads(result_json),
                    })
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     result_json,
                    })

                messages.append({"role": "user", "content": tool_results})

            # ── Case 2: Final answer ──────────────────────────────
            else:
                raw_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        raw_text += block.text

                # Parse the JSON findings
                findings = self._parse_findings(raw_text)

                if verbose:
                    gap_count = len(findings.get("gaps", []))
                    risk = findings.get("risk_level", "UNKNOWN")
                    print(f"  [ReasoningAgent] ✓ Analysis complete — "
                          f"{gap_count} gaps found | Risk: {risk}")

                return {
                    "raw_response":    raw_text,
                    "findings":        findings,
                    "thinking":        thinking_text,
                    "tool_calls":      tool_calls_log,
                    "topics_analyzed": topics,
                }

    def _parse_findings(self, raw_text: str) -> dict:
        """
        Parse Claude's JSON response into a structured findings dict.
        Handles cases where Claude wraps JSON in markdown code fences.
        """
        text = raw_text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # If JSON parsing fails, return a structured error with raw text
            return {
                "summary":          "JSON parsing failed — see raw_response",
                "risk_level":       "UNKNOWN",
                "gaps":             [],
                "compliant_areas":  [],
                "priority_actions": [],
                "parse_error":      raw_text[:500],
            }

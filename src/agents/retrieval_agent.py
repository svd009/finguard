"""
retrieval_agent.py
──────────────────
Fast factual lookup agent powered by Claude Haiku.

Role in the system:
  Handles SIMPLE compliance queries that need retrieval but not deep
  reasoning. Examples:
    - "What does FATF Recommendation 10 say?"
    - "What is our current CTR threshold?"
    - "What encryption standard do we use for customer data?"

  For these, we don't need extended thinking or complex reasoning —
  just find the right document chunks and summarize them clearly.

Why Haiku and not Sonnet?
  Haiku is ~10x cheaper and ~3x faster than Sonnet.
  For simple retrieval tasks this is more than sufficient.
  The orchestrator routes complex reasoning to Sonnet (reasoning_agent.py).
  This tiered model selection is a real engineering cost-optimization pattern
  used in production AI systems.

How it uses the Claude API:
  1. Receives a query
  2. Calls the MCP tools (search_regulations or search_policies) to get context
  3. Sends retrieved context + query to Claude Haiku
  4. Returns Claude's answer with source citations

This demonstrates: multi-turn tool use, system prompts, structured
prompt engineering with XML tags (Course 2: Tool Use + Prompt Engineering)
"""

import json
import anthropic
from config import ANTHROPIC_API_KEY, MODEL_FAST
from src.mcp_server.compliance_tools import ComplianceToolExecutor, TOOL_SCHEMAS


RETRIEVAL_SYSTEM_PROMPT = """You are a compliance research assistant for a banking and fintech institution.

Your role is to answer specific factual questions about regulatory requirements and internal policies by searching the available document corpus.

<instructions>
- Use the available tools to search for relevant information before answering
- Always cite your sources with document name and page number
- Be precise and factual — do not speculate beyond what the documents say
- If the documents don't contain enough information, say so clearly
- Keep answers concise and direct
</instructions>

<output_format>
Provide your answer followed by a Sources section listing each document referenced.
</output_format>"""


class RetrievalAgent:
    """
    Fast factual retrieval agent using Claude Haiku + tool use.

    Demonstrates:
      - Single and multi-turn conversations with tool use
      - Tool schemas passed to the API
      - Handling tool_use blocks in Claude's response
      - Sending tool_result blocks back to Claude
      - Source citation extraction
    """

    def __init__(self, tool_executor: ComplianceToolExecutor):
        self.client   = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.executor = tool_executor

        # Only expose the two search tools to this agent (not gap analysis)
        # This is "fine-grained tool calling" from Course 2
        self.tools = [s for s in TOOL_SCHEMAS
                      if s["name"] in ("search_regulations", "search_policies")]

    def query(self, question: str, verbose: bool = True) -> dict:
        """
        Answer a factual compliance question using retrieval + Claude Haiku.

        Args:
            question: The compliance question to answer
            verbose:  Print agent reasoning steps to console

        Returns:
            {
              "answer":   str,         ← Claude's answer
              "sources":  list[dict],  ← cited sources
              "tool_calls": list,      ← tools that were called
            }
        """
        if verbose:
            print(f"\n  [RetrievalAgent] Query: {question}")

        messages = [{"role": "user", "content": question}]
        tool_calls_log = []

        # ── Agentic loop ──────────────────────────────────────────
        # Claude may call tools multiple times before giving a final answer.
        # We loop until Claude stops requesting tools (stop_reason != "tool_use")

        while True:
            response = self.client.messages.create(
                model=MODEL_FAST,
                max_tokens=1024,
                system=RETRIEVAL_SYSTEM_PROMPT,
                tools=self.tools,
                messages=messages,
            )

            # ── Case 1: Claude wants to use a tool ────────────────
            if response.stop_reason == "tool_use":
                # Extract all tool use blocks from the response
                tool_use_blocks = [b for b in response.content
                                   if b.type == "tool_use"]

                if verbose:
                    for block in tool_use_blocks:
                        print(f"  [RetrievalAgent] → Tool call: {block.name}"
                              f"({json.dumps(block.input)[:80]}...)")

                # Add Claude's response (with tool_use blocks) to message history
                messages.append({"role": "assistant", "content": response.content})

                # Execute each tool and collect results
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

                # Send tool results back to Claude for the next turn
                messages.append({"role": "user", "content": tool_results})

            # ── Case 2: Claude has a final answer ─────────────────
            else:
                final_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text += block.text

                sources = self._extract_sources(tool_calls_log)

                if verbose:
                    print(f"  [RetrievalAgent] ✓ Answer generated "
                          f"({len(tool_calls_log)} tool calls)")

                return {
                    "answer":     final_text,
                    "sources":    sources,
                    "tool_calls": tool_calls_log,
                }

    def _extract_sources(self, tool_calls_log: list) -> list[dict]:
        """Extract unique source citations from all tool call results."""
        seen = set()
        sources = []
        for call in tool_calls_log:
            result = call.get("result", {})
            # Result may be a list (search) or dict with lists (gap)
            items = result if isinstance(result, list) else []
            for item in items:
                key = (item.get("source", ""), item.get("page", 0))
                if key not in seen:
                    seen.add(key)
                    sources.append({
                        "source": item.get("source", ""),
                        "page":   item.get("page", 0),
                    })
        return sources

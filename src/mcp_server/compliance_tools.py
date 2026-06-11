"""
compliance_tools.py
────────────────────
MCP (Model Context Protocol) server that exposes compliance tools
to Claude as standardized, callable functions.

What is MCP?
  MCP is Anthropic's open protocol for connecting AI models to external
  tools and data sources in a standardized way. Think of it as a USB
  standard — instead of every app building its own Claude integration,
  MCP defines one universal interface.

  Without MCP: Claude calls a Python function directly (tightly coupled)
  With MCP:    Claude calls a tool via protocol (loosely coupled, reusable)

  This matters for fintech/banking because:
    - The same MCP server can serve multiple AI systems (Claude, GPT, etc.)
    - Tools are versioned and auditable (important for compliance!)
    - The server can run as a separate microservice in production

Three tools we expose:
  1. search_regulations   → query the regulatory documents corpus
  2. search_policies      → query the internal policies corpus
  3. check_compliance_gap → run a full gap analysis on a topic

How Claude uses these:
  Claude receives tool schemas (name, description, parameters).
  When it decides to use a tool, it emits a tool_use block.
  We execute the tool and send back a tool_result block.
  Claude then reasons over the result to form its answer.
  This loop is the foundation of all agentic behavior.

Architecture note:
  In this file we define both:
    a) The MCP server (for the protocol-compliant version)
    b) A direct Python interface (for the orchestrator to call internally)
  Both use the same underlying logic — the search engine we built in Phase 2.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# ── Tool schemas ──────────────────────────────────────────────────────────────
# These are sent to Claude so it knows what tools exist and how to call them.
# The descriptions are critical — Claude uses them to decide WHEN to call each tool.

TOOL_SCHEMAS = [
    {
        "name": "search_regulations",
        "description": (
            "Search regulatory documents (FATF AML guidelines, Basel III capital "
            "framework, KYC compliance guidelines, GDPR financial services) to find "
            "what external regulations REQUIRE. Use this when you need to know the "
            "legal or regulatory standard on a specific compliance topic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The compliance topic or requirement to search for."
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default 5).",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_policies",
        "description": (
            "Search internal bank/fintech policy documents to find what the "
            "organization CURRENTLY DOES. Use this when you need to know the "
            "institution's existing procedures, thresholds, or practices on a topic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The policy area or procedure to search for."
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default 5).",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "check_compliance_gap",
        "description": (
            "Run a compliance gap analysis on a specific topic by retrieving "
            "relevant content from BOTH regulatory documents AND internal policies "
            "simultaneously. Returns what the regulation requires AND what the "
            "current policy says, side by side. Use this for identifying gaps, "
            "misalignments, or areas of non-compliance."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": (
                        "The compliance topic to analyze, e.g. 'AML record retention', "
                        "'customer due diligence thresholds', 'capital adequacy reporting'"
                    )
                },
                "top_k": {
                    "type": "integer",
                    "description": "Results per corpus (default 4).",
                    "default": 4
                }
            },
            "required": ["topic"]
        }
    }
]


# ── Direct Python interface (used by the orchestrator) ────────────────────────

class ComplianceToolExecutor:
    """
    Executes compliance tools directly (no MCP protocol overhead).
    Used internally by the agent orchestrator in Phase 4.

    The MCP server below wraps this same class — same logic, two interfaces.
    """

    def __init__(self, search_engine):
        """
        Args:
            search_engine: A built HybridSearchEngine instance from Phase 2.
        """
        self.engine = search_engine

    def search_regulations(self, query: str, top_k: int = 5) -> list[dict]:
        """Search regulatory corpus and return formatted results."""
        results = self.engine.search_regulations(query, top_k=top_k)
        return self._format_results(results)

    def search_policies(self, query: str, top_k: int = 5) -> list[dict]:
        """Search internal policy corpus and return formatted results."""
        results = self.engine.search_policies(query, top_k=top_k)
        return self._format_results(results)

    def check_compliance_gap(self, topic: str, top_k: int = 4) -> dict:
        """
        Run gap analysis — retrieve from both corpora on the same topic.

        Returns structured dict that the reasoning agent will analyze:
        {
          "topic": str,
          "regulatory_requirements": [{"source", "page", "text"}, ...],
          "current_policies":        [{"source", "page", "text"}, ...],
        }
        """
        gap_data = self.engine.search_for_gaps(topic, top_k=top_k)
        return {
            "topic": topic,
            "regulatory_requirements": self._format_results(gap_data["regulations"]),
            "current_policies":        self._format_results(gap_data["policies"]),
        }

    def execute(self, tool_name: str, tool_input: dict) -> str:
        """
        Route a tool call by name and return JSON string result.
        This is what the Claude API tool_result block receives.
        """
        if tool_name == "search_regulations":
            result = self.search_regulations(
                tool_input["query"],
                tool_input.get("top_k", 5)
            )
        elif tool_name == "search_policies":
            result = self.search_policies(
                tool_input["query"],
                tool_input.get("top_k", 5)
            )
        elif tool_name == "check_compliance_gap":
            result = self.check_compliance_gap(
                tool_input["topic"],
                tool_input.get("top_k", 4)
            )
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return json.dumps(result, indent=2)

    @staticmethod
    def _format_results(results: list[dict]) -> list[dict]:
        """Strip embedding vectors and internal fields before sending to Claude."""
        formatted = []
        for r in results:
            formatted.append({
                "source": r.get("source", "unknown"),
                "page":   r.get("page", 0),
                "text":   r.get("text", ""),
                "score":  round(r.get("rrf_score", r.get("score", 0.0)), 4),
            })
        return formatted


# ── MCP Server (protocol-compliant version) ───────────────────────────────────

def create_mcp_server(search_engine) -> Server:
    """
    Create and configure the MCP server with compliance tools.

    The MCP server is the production-grade interface — it speaks the
    standardized MCP protocol so any MCP-compatible client can connect,
    not just our own orchestrator.

    Args:
        search_engine: A built HybridSearchEngine instance.

    Returns:
        Configured MCP Server ready to run.
    """
    server = Server("finguard-compliance")
    executor = ComplianceToolExecutor(search_engine)

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        """Tell MCP clients what tools are available."""
        tools = []
        for schema in TOOL_SCHEMAS:
            tools.append(types.Tool(
                name=schema["name"],
                description=schema["description"],
                inputSchema=schema["input_schema"],
            ))
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        """Execute a tool call and return the result."""
        result_json = executor.execute(name, arguments)
        return [types.TextContent(type="text", text=result_json)]

    return server


async def run_mcp_server(search_engine):
    """Run the MCP server over stdio (standard MCP transport)."""
    server = create_mcp_server(search_engine)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

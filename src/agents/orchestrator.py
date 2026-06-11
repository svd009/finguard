"""
orchestrator.py
───────────────
The brain of FinGuard — routes queries to the right agent and
chains agents together for complex workflows.

This is where Course 1's 4D Framework is implemented architecturally:

  DELEGATION:  The orchestrator decides which agent handles each task.
               Simple queries → RetrievalAgent (fast, cheap)
               Complex audits → ReasoningAgent (thorough, extended thinking)
               All audits     → ReportAgent (always runs last in the chain)

  DESCRIPTION: Each agent has a carefully engineered system prompt
               with XML structure (implemented in each agent file).

  DISCERNMENT: The orchestrator reads Claude's confidence signals
               and routes accordingly. Low-complexity = Haiku path.
               High-complexity = Sonnet + extended thinking path.

  DILIGENCE:   Every output is cited, saved, and evaluated.
               Nothing goes to the user without source attribution.

Routing logic:
  The orchestrator classifies query complexity using keyword signals
  and a simple heuristic. In production this could itself be an LLM
  call, but for clarity we use rule-based routing here.

  SIMPLE (→ RetrievalAgent):
    - Single-topic factual questions
    - "What does X require?"
    - "What is our current policy on Y?"

  COMPLEX (→ ReasoningAgent → ReportAgent):
    - Multi-topic gap analysis
    - "Audit our compliance across all AML requirements"
    - "What are our compliance gaps?"
    - "Run a full compliance review"

Agentic workflow patterns used (Course 2):
  - ROUTING:       Classify → dispatch to correct agent
  - CHAINING:      ReasoningAgent → ReportAgent (output of one feeds next)
  - PARALLELIZATION: (demonstrated conceptually — topics analyzed in sequence
                      but could be parallelized with asyncio in production)
"""

from src.agents.retrieval_agent import RetrievalAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.report_agent import ReportAgent
from src.mcp_server.compliance_tools import ComplianceToolExecutor


# Keywords that signal a complex multi-topic audit request
COMPLEX_QUERY_SIGNALS = [
    "audit", "gap", "gaps", "compliance review", "full review",
    "all areas", "across", "compare", "vs", "versus", "analyze",
    "assessment", "risks", "non-compliant", "violations", "overall"
]

# Default audit topics if none are specified
DEFAULT_AUDIT_TOPICS = [
    "AML record retention and keeping requirements",
    "customer due diligence ongoing monitoring",
    "KYC data retention period",
    "capital adequacy reporting obligations",
    "data encryption security standards",
    "suspicious transaction reporting thresholds",
]


class Orchestrator:
    """
    Central coordinator for all FinGuard agent workflows.

    Initializes all agents once and routes incoming requests
    to the appropriate agent pipeline.
    """

    def __init__(self, tool_executor: ComplianceToolExecutor):
        self.executor         = tool_executor
        self.retrieval_agent  = RetrievalAgent(tool_executor)
        self.reasoning_agent  = ReasoningAgent(tool_executor)
        self.report_agent     = ReportAgent()

    def run(self, query: str, institution_name: str = "Nexus Financial Services",
            verbose: bool = True) -> dict:
        """
        Main entry point — classify the query and dispatch to the right pipeline.

        Args:
            query:            User's compliance question or audit request
            institution_name: Name shown in the audit report
            verbose:          Print routing decisions and progress

        Returns:
            Result dict — structure varies by route taken (see below)
        """
        complexity = self._classify_query(query)

        if verbose:
            print(f"\n{'='*60}")
            print(f"  [Orchestrator] Query: {query[:80]}")
            print(f"  [Orchestrator] Complexity: {complexity.upper()} "
                  f"→ {'ReasoningAgent + ReportAgent' if complexity == 'complex' else 'RetrievalAgent'}")
            print(f"{'='*60}")

        if complexity == "simple":
            return self._run_retrieval_pipeline(query, verbose)
        else:
            return self._run_audit_pipeline(query, institution_name, verbose)

    def run_full_audit(self, institution_name: str = "Nexus Financial Services",
                       topics: list = None, verbose: bool = True) -> dict:
        """
        Run a comprehensive compliance audit across all default topics.

        This is the flagship workflow — used when someone wants a complete
        compliance health check rather than a specific question answered.

        Args:
            institution_name: Institution name for the report
            topics:           Custom topic list (uses DEFAULT_AUDIT_TOPICS if None)
            verbose:          Print progress

        Returns:
            Full audit result with findings, report text, and saved report path
        """
        topics = topics or DEFAULT_AUDIT_TOPICS

        if verbose:
            print(f"\n{'='*60}")
            print(f"  [Orchestrator] FULL AUDIT — {institution_name}")
            print(f"  [Orchestrator] Analyzing {len(topics)} compliance topics")
            print(f"{'='*60}")

        return self._run_audit_pipeline(
            audit_request=f"Full compliance audit for {institution_name}",
            institution_name=institution_name,
            verbose=verbose,
            topics=topics,
        )

    # ── Private pipeline methods ──────────────────────────────────────────────

    def _run_retrieval_pipeline(self, query: str, verbose: bool) -> dict:
        """
        Simple pipeline: query → RetrievalAgent → formatted answer.

        No report generated — just a direct answer with citations.
        """
        result = self.retrieval_agent.query(query, verbose=verbose)
        return {
            "pipeline":   "retrieval",
            "query":      query,
            "answer":     result["answer"],
            "sources":    result["sources"],
            "tool_calls": result["tool_calls"],
        }

    def _run_audit_pipeline(self, audit_request: str, institution_name: str,
                             verbose: bool, topics: list = None) -> dict:
        """
        Full audit pipeline: request → ReasoningAgent → ReportAgent → saved report.

        This is the core chaining pattern from Course 2:
          Step 1: ReasoningAgent analyzes gaps (uses extended thinking + tools)
          Step 2: ReportAgent formats findings into a professional report
          Step 3: Report is saved to disk with full audit trail

        The output of Step 1 is directly fed as input to Step 2.
        This is "agent chaining" — a fundamental agentic workflow pattern.
        """
        # Determine topics to analyze
        if topics is None:
            topics = self._extract_topics(audit_request)

        # ── Step 1: Deep reasoning ────────────────────────────────
        if verbose:
            print(f"\n  [Orchestrator] Step 1/2: Running reasoning analysis...")

        reasoning_result = self.reasoning_agent.analyze(
            audit_request=audit_request,
            topics=topics,
            verbose=verbose,
        )

        # ── Step 2: Report generation (chained from Step 1) ───────
        if verbose:
            print(f"\n  [Orchestrator] Step 2/2: Generating audit report...")

        report_result = self.report_agent.generate(
            findings=reasoning_result["findings"],
            institution_name=institution_name,
            verbose=verbose,
        )

        return {
            "pipeline":        "audit",
            "audit_request":   audit_request,
            "topics_analyzed": reasoning_result["topics_analyzed"],
            "findings":        reasoning_result["findings"],
            "thinking":        reasoning_result["thinking"],
            "tool_calls":      reasoning_result["tool_calls"],
            "report_text":     report_result["report_text"],
            "report_path":     report_result["report_path"],
            "metadata":        report_result["metadata"],
        }

    def _classify_query(self, query: str) -> str:
        """
        Classify a query as 'simple' or 'complex' based on keyword signals.

        Simple  → single factual lookup, answered by RetrievalAgent
        Complex → multi-topic analysis, requires ReasoningAgent + ReportAgent

        This is a rule-based router. In production, this decision could
        itself be a fast LLM call for more nuanced classification.
        """
        query_lower = query.lower()
        for signal in COMPLEX_QUERY_SIGNALS:
            if signal in query_lower:
                return "complex"
        return "simple"

    def _extract_topics(self, audit_request: str) -> list:
        """
        Extract specific topics from an audit request, or use defaults.

        For now uses the default topic list. In a production system,
        this could use an LLM call to extract topics from free-form text.
        """
        return DEFAULT_AUDIT_TOPICS

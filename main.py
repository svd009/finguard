"""
main.py
───────
FinGuard — Agentic Regulatory Compliance Intelligence System
Single entry point for the entire system.

Usage:
  python main.py                          # Full compliance audit (default)
  python main.py --mode audit             # Full compliance audit
  python main.py --mode query             # Interactive Q&A mode
  python main.py --mode eval              # Run evaluation suite only
  python main.py --query "What does..."  # Single query, then exit

This file is the DILIGENCE layer of the 4D Framework:
  - Every run generates a timestamped report saved to disk
  - Every output is evaluated before being shown
  - Full audit trail is maintained in reports/
"""

import sys
import os
import argparse
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from src.ingestion.doc_loader import load_all_documents
from src.ingestion.chunker import chunk_pages
from src.ingestion.embedder import embed_chunks
from src.retrieval.hybrid_search import HybridSearchEngine
from src.mcp_server.compliance_tools import ComplianceToolExecutor
from src.agents.orchestrator import Orchestrator
from src.evaluation.eval_framework import EvalFramework
import generate_sample_docs as gsd
from generate_sample_docs import write_file
from config import REGULATIONS_DIR, INTERNAL_POLICIES_DIR, REPORTS_DIR

console = Console()

INSTITUTION_NAME = "Nexus Financial Services"

BANNER = """
███████╗██╗███╗   ██╗ ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ 
██╔════╝██║████╗  ██║██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗
█████╗  ██║██╔██╗ ██║██║  ███╗██║   ██║███████║██████╔╝██║  ██║
██╔══╝  ██║██║╚██╗██║██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║
██║     ██║██║ ╚████║╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝
╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ 
"""


def initialize_system() -> tuple:
    """
    Boot sequence — load documents, build indexes, initialize all agents.
    Returns (orchestrator, evaluator) ready for use.
    """
    console.print("\n[bold cyan]Initializing FinGuard...[/bold cyan]")

    # ── Step 1: Generate sample documents ────────────────────────
    console.print("  [dim]→ Generating sample regulatory and policy documents...[/dim]")
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

    # ── Step 2: Load and index documents ─────────────────────────
    console.print("  [dim]→ Loading regulatory documents...[/dim]")
    reg_chunks = embed_chunks(chunk_pages(load_all_documents(REGULATIONS_DIR)))

    console.print("  [dim]→ Loading internal policy documents...[/dim]")
    pol_chunks = embed_chunks(
        chunk_pages(load_all_documents(INTERNAL_POLICIES_DIR)),
        force_recompute=True
    )

    # ── Step 3: Build search engine ───────────────────────────────
    console.print("  [dim]→ Building hybrid search indexes...[/dim]")
    engine = HybridSearchEngine()
    engine.build(reg_chunks, pol_chunks)

    # ── Step 4: Initialize agents ─────────────────────────────────
    console.print("  [dim]→ Initializing compliance agents...[/dim]")
    executor     = ComplianceToolExecutor(engine)
    orchestrator = Orchestrator(executor)
    evaluator    = EvalFramework()

    total_docs = (
        len([f for f in os.listdir(REGULATIONS_DIR)]) +
        len([f for f in os.listdir(INTERNAL_POLICIES_DIR)])
    )
    console.print(f"\n  [bold green]✓ System ready[/bold green] — "
                  f"{total_docs} documents indexed | "
                  f"{len(reg_chunks) + len(pol_chunks)} chunks | "
                  f"3 agents initialized\n")

    return orchestrator, evaluator, executor


def run_full_audit(orchestrator: Orchestrator, evaluator: EvalFramework):
    """Run a complete compliance audit and display results."""
    console.print(Panel(
        f"[bold]Full Compliance Audit[/bold]\n"
        f"Institution: {INSTITUTION_NAME}\n"
        f"Scope: AML · KYC · Capital Adequacy · Data Protection",
        title="[bold cyan]AUDIT MODE[/bold cyan]",
        border_style="cyan"
    ))

    # Run the audit pipeline
    result = orchestrator.run_full_audit(
        institution_name=INSTITUTION_NAME,
        verbose=True
    )

    findings = result.get("findings", {})

    # ── Display findings summary ──────────────────────────────────
    risk = findings.get("risk_level", "UNKNOWN")
    risk_color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}.get(risk, "white")

    console.print(f"\n[bold]Overall Risk Level:[/bold] "
                  f"[bold {risk_color}]{risk}[/bold {risk_color}]")
    console.print(f"[bold]Summary:[/bold] {findings.get('summary', 'N/A')}\n")

    # ── Gaps table ────────────────────────────────────────────────
    gaps = findings.get("gaps", [])
    if gaps:
        table = Table(
            title=f"Compliance Gaps Identified ({len(gaps)})",
            box=box.ROUNDED,
            show_lines=True
        )
        table.add_column("ID",          style="dim",    width=8)
        table.add_column("Area",        style="bold",   width=22)
        table.add_column("Severity",    width=10)
        table.add_column("Gap",         width=35)
        table.add_column("Source",      style="dim",    width=20)

        for gap in gaps:
            sev = gap.get("severity", "?")
            sev_color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}.get(sev, "white")
            table.add_row(
                gap.get("id", ""),
                gap.get("area", ""),
                f"[{sev_color}]{sev}[/{sev_color}]",
                gap.get("gap_description", "")[:80] + "...",
                gap.get("regulatory_source", "")[:25],
            )
        console.print(table)

    # ── Priority actions ──────────────────────────────────────────
    actions = findings.get("priority_actions", [])
    if actions:
        console.print("\n[bold]Priority Remediation Actions:[/bold]")
        for i, action in enumerate(actions, 1):
            console.print(f"  {i}. {action}")

    # ── Evaluation ────────────────────────────────────────────────
    console.print("\n[bold cyan]Running quality evaluation...[/bold cyan]")
    eval_result = evaluator.evaluate_findings(
        findings=findings,
        tool_calls=result.get("tool_calls", []),
        verbose=False,
    )

    score = eval_result["overall_score"]
    passed = eval_result["passed"]
    score_color = "green" if passed else "red"
    status = "PASSED ✓" if passed else "FLAGGED FOR HUMAN REVIEW ✗"

    console.print(f"\n[bold]Evaluation Score:[/bold] "
                  f"[bold {score_color}]{score}/10[/bold {score_color}] — {status}")

    # ── Report location ───────────────────────────────────────────
    report_path = result.get("report_path", "")
    if report_path:
        console.print(f"\n[bold]Audit Report Saved:[/bold] [dim]{report_path}[/dim]")

    # ── Extended thinking preview ─────────────────────────────────
    thinking = result.get("thinking", "")
    if thinking:
        preview = thinking[:300] + "..." if len(thinking) > 300 else thinking
        console.print(Panel(
            f"[dim]{preview}[/dim]",
            title="[dim]Extended Thinking Preview (Claude's reasoning)[/dim]",
            border_style="dim"
        ))


def run_query_mode(orchestrator: Orchestrator, evaluator: EvalFramework,
                   single_query: str = None):
    """Interactive Q&A mode — ask compliance questions one at a time."""
    console.print(Panel(
        "Ask compliance questions about regulations and internal policies.\n"
        "Type [bold]exit[/bold] to quit.",
        title="[bold cyan]QUERY MODE[/bold cyan]",
        border_style="cyan"
    ))

    while True:
        if single_query:
            query = single_query
        else:
            console.print("\n[bold cyan]Question:[/bold cyan] ", end="")
            query = input().strip()

        if query.lower() in ("exit", "quit", "q", ""):
            break

        result = orchestrator.run(query, institution_name=INSTITUTION_NAME, verbose=True)

        console.print(Panel(
            result.get("answer", result.get("report_text", "No answer generated")),
            title="[bold green]Answer[/bold green]",
            border_style="green"
        ))

        sources = result.get("sources", [])
        if sources:
            console.print("[dim]Sources:[/dim]")
            for s in sources:
                console.print(f"  [dim]• {s['source']} p.{s['page']}[/dim]")

        if single_query:
            break


def run_eval_mode(evaluator: EvalFramework, executor: ComplianceToolExecutor):
    """Run the evaluation suite and display results."""
    console.print(Panel(
        "Running evaluation suite against ground-truth test cases.\n"
        "Tests retrieval quality — no API credits required.",
        title="[bold cyan]EVAL MODE[/bold cyan]",
        border_style="cyan"
    ))

    suite = evaluator.run_eval_suite(executor, verbose=True)
    
    table = Table(title="Eval Suite Results", box=box.ROUNDED)
    table.add_column("Case ID",     style="dim")
    table.add_column("Topic",       width=35)
    table.add_column("Score",       width=8)
    table.add_column("Status",      width=10)

    for case in suite["cases"]:
        passed = case["passed"]
        color  = "green" if passed else "red"
        table.add_row(
            case["case_id"],
            case["topic"][:40],
            f"{case['case_score']}/10",
            f"[{color}]{'PASS' if passed else 'FAIL'}[/{color}]",
        )

    console.print(table)
    console.print(
        f"\n[bold]Pass Rate:[/bold] "
        f"{suite['passed_cases']}/{suite['total_cases']} "
        f"({suite['pass_rate']*100:.0f}%)"
    )


def main():
    parser = argparse.ArgumentParser(
        description="FinGuard — Agentic Regulatory Compliance Intelligence System"
    )
    parser.add_argument(
        "--mode",
        choices=["audit", "query", "eval"],
        default="audit",
        help="Run mode: audit (full compliance audit), query (Q&A), eval (evaluation suite)"
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Single query to answer (sets mode to query automatically)"
    )
    args = parser.parse_args()

    # Print banner
    console.print(f"[bold cyan]{BANNER}[/bold cyan]")
    console.print(Panel(
        "[bold]Agentic Regulatory Compliance Intelligence System[/bold]\n"
        "Banking & Fintech Edition | Powered by Claude API\n"
        "Multi-index RAG · MCP Tools · Extended Thinking · Prompt Eval",
        border_style="cyan"
    ))

    # Initialize
    orchestrator, evaluator, executor = initialize_system()

    # Route to the right mode
    if args.query:
        run_query_mode(orchestrator, evaluator, single_query=args.query)
    elif args.mode == "query":
        run_query_mode(orchestrator, evaluator)
    elif args.mode == "eval":
        run_eval_mode(evaluator, executor)
    else:
        run_full_audit(orchestrator, evaluator)


if __name__ == "__main__":
    main()

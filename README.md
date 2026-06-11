# FinGuard — Agentic Regulatory Compliance Intelligence System

> **Banking & Fintech Edition** | Built with Claude API, Multi-index RAG, MCP Tools, Extended Thinking, and Automated Evaluation

---

## What It Does

FinGuard is a production-grade AI system that automatically audits a bank or fintech company's internal policies against external regulatory requirements — identifying compliance gaps, assessing risk, and generating cited audit reports.

**The problem it solves:** Banks and fintech companies (Stripe, Plaid, Chime, traditional banks) must align their internal procedures with constantly evolving regulations (FATF AML guidelines, Basel III capital requirements, KYC standards, GDPR). Manual compliance review is expensive, slow, and error-prone. A single missed requirement can result in regulatory fines in the hundreds of millions.

**What FinGuard does:** Feed it your regulatory documents and internal policies. It retrieves relevant clauses from both, reasons over the gaps using extended AI thinking, and produces a structured, cited compliance audit report — fully automatically.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FinGuard System                      │
│                                                         │
│  [1] Document Ingestion Layer                           │
│       PDFs/TXT → chunks → embeddings → indexed          │
│                    ↓                                    │
│  [2] Multi-Index Hybrid RAG Engine                      │
│       BM25 lexical + semantic vector search             │
│       Reciprocal Rank Fusion (RRF) for result merging   │
│       Separate indexes: regulations vs policies         │
│                    ↓                                    │
│  [3] MCP Tool Server                                    │
│       search_regulations · search_policies              │
│       check_compliance_gap                              │
│                    ↓                                    │
│  [4] Agentic Orchestrator                               │
│       Router → classifies query complexity              │
│       Simple  → RetrievalAgent (Haiku, fast + cheap)    │
│       Complex → ReasoningAgent (Sonnet, extended think) │
│                    ↓                                    │
│  [5] Prompt Evaluation Framework                        │
│       Rule-based structural checks                      │
│       Model-as-judge scoring (4 dimensions)             │
│                    ↓                                    │
│  [6] Report Generator                                   │
│       Structured JSON findings → professional report    │
│       Every claim cited to source document + page       │
│                    ↓                                    │
│  [7] Rich CLI Interface                                 │
│       audit · query · eval modes                        │
└─────────────────────────────────────────────────────────┘
```

---

## Course Concepts Demonstrated

This project was built to demonstrate every concept from Anthropic's AI Fluency and Claude API courses:

| Concept | Implementation |
|---|---|
| **4D Framework** (Course 1) | Orchestrator = Delegation; XML prompts = Description; Eval = Discernment; Citations = Diligence |
| **API basics + multi-turn** | All agents use multi-turn conversation loops |
| **System prompts** | Each agent has a specialized system prompt with XML structure |
| **Tool use (single + multi)** | Retrieval agent uses 2 tools; reasoning agent uses all 3 |
| **Agentic tool loop** | Agents loop until `stop_reason != "tool_use"` |
| **RAG (chunking + embeddings)** | Phase 1-2: fixed-size chunking with overlap, all-MiniLM-L6-v2 embeddings |
| **BM25 lexical search** | BM25Okapi index for exact regulatory term matching |
| **Multi-index RAG** | Separate indexes for regulations vs policies |
| **Hybrid search + RRF** | Reciprocal Rank Fusion merges semantic + lexical results |
| **Extended thinking** | ReasoningAgent uses `thinking: {type: "enabled", budget_tokens: 5000}` |
| **Prompt caching** | System prompt cached with `cache_control: {type: "ephemeral"}` |
| **Structured outputs** | Findings returned as typed JSON schema |
| **Citations** | Every gap finding references source document + page |
| **Prompt evaluation** | Rule-based + model-as-judge with 4-dimension scoring |
| **MCP server + client** | `compliance_tools.py` exposes tools via MCP protocol |
| **Agent chaining** | ReasoningAgent → ReportAgent pipeline |
| **Agent routing** | Orchestrator routes simple vs complex queries |
| **Tiered model selection** | Haiku for retrieval/eval, Sonnet for reasoning |

---

## Project Structure

```
finguard/
│
├── documents/
│   ├── regulations/          ← FATF AML, Basel III, KYC, GDPR
│   └── internal_policies/    ← Nexus Financial internal policies
│
├── src/
│   ├── ingestion/
│   │   ├── pdf_loader.py     ← PDF text extraction (PyMuPDF)
│   │   ├── doc_loader.py     ← Unified PDF + TXT loader
│   │   ├── chunker.py        ← Fixed-size overlapping chunking
│   │   └── embedder.py       ← Sentence transformer embeddings
│   │
│   ├── retrieval/
│   │   ├── vector_store.py   ← Semantic search (cosine similarity)
│   │   ├── bm25_index.py     ← Lexical search (BM25Okapi)
│   │   └── hybrid_search.py  ← Multi-index RRF fusion engine
│   │
│   ├── mcp_server/
│   │   └── compliance_tools.py ← MCP server + tool executor
│   │
│   ├── agents/
│   │   ├── retrieval_agent.py  ← Claude Haiku + tool use
│   │   ├── reasoning_agent.py  ← Claude Sonnet + extended thinking
│   │   ├── report_agent.py     ← Audit report generation
│   │   └── orchestrator.py     ← Routing + chaining coordinator
│   │
│   └── evaluation/
│       └── eval_framework.py   ← Rule-based + model-as-judge eval
│
├── reports/                  ← Generated audit reports (JSON)
├── main.py                   ← CLI entry point
├── config.py                 ← Settings and model selection
├── generate_sample_docs.py   ← Realistic regulatory document generator
└── requirements.txt
```

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/svd009/finguard.git
cd finguard
pip install -r requirements.txt
```

### 2. Set up API key

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

Get your key at [console.anthropic.com](https://console.anthropic.com)

### 3. Run

```bash
# Full compliance audit (flagship mode)
python main.py

# Interactive Q&A
python main.py --mode query

# Single question
python main.py --query "What does FATF Recommendation 10 require for CDD?"

# Evaluation suite only (no API credits needed)
python main.py --mode eval
```

---

## Sample Output

```
COMPLIANCE AUDIT REPORT
========================
Institution:  Nexus Financial Services
Risk Level:   HIGH

GAP-001 | AML Record Retention | 🔴 HIGH
  Regulation: FATF R.11 requires minimum 5-year retention
  Policy:     Current policy retains records for 3 years only
  Source:     [fatf_aml_recommendations.txt] [internal_aml_policy.txt]
  Action:     Update retention policy to 5-year minimum immediately

GAP-002 | Ongoing CDD Monitoring | 🔴 HIGH
  Regulation: FATF R.10 requires ongoing monitoring for ALL customers
  Policy:     Reviews conducted ad-hoc only, no formal schedule
  ...

Evaluation Score: 8.4/10 ✓ PASSED
Report saved to: reports/RPT-20250611-143022.json
```

---

## Regulatory Documents Covered

| Document | Source |
|---|---|
| FATF AML/CFT Recommendations | Financial Action Task Force |
| Basel III Capital Framework | Basel Committee on Banking Supervision |
| KYC Compliance Guidelines | Regulatory guidance for FIs and fintechs |
| GDPR Financial Services | EU data protection for financial institutions |

---

## Key Design Decisions

**Why two separate search indexes (regulations vs policies)?**  
Gap analysis requires retrieving from each corpus independently on the same topic. A single combined index would mix regulatory requirements with internal policies, making comparison impossible.

**Why Reciprocal Rank Fusion over weighted score averaging?**  
BM25 scores are unbounded; cosine similarity is bounded [0,1]. Direct averaging across different scales is unreliable. RRF uses only rank positions, making it scale-invariant and robust.

**Why tiered model selection (Haiku vs Sonnet)?**  
Cost and latency optimization. Simple factual retrieval doesn't need Sonnet's reasoning depth. Using Haiku for retrieval and eval cuts costs ~10x while maintaining quality where it matters.

**Why a separate report agent instead of having the reasoning agent write the report?**  
Separation of concerns. The reasoning agent optimizes for analytical depth; the report agent optimizes for presentation quality. Each has a specialized system prompt for its specific task.

---

## Built With

- [Anthropic Claude API](https://docs.anthropic.com) — claude-haiku-4-5, claude-sonnet-4-6
- [sentence-transformers](https://www.sbert.net) — all-MiniLM-L6-v2 embeddings
- [rank-bm25](https://github.com/dorianbrown/rank_bm25) — BM25Okapi lexical search
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) — Model Context Protocol
- [Rich](https://github.com/Textualize/rich) — Terminal UI
- [PyMuPDF](https://pymupdf.readthedocs.io) — PDF processing

---

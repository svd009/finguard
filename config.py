import os
from dotenv import load_dotenv

load_dotenv()

# ── API ──────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ── Models ───────────────────────────────────────────────────────────────────
# Haiku  → fast, cheap → used for retrieval agent and eval grading
# Sonnet → powerful   → used for extended thinking / complex reasoning
MODEL_FAST     = "claude-haiku-4-5"
MODEL_REASONING = "claude-sonnet-4-6"

# ── RAG settings ─────────────────────────────────────────────────────────────
CHUNK_SIZE        = 800    # characters per chunk
CHUNK_OVERLAP     = 150    # overlap between consecutive chunks
TOP_K_RESULTS     = 5      # how many chunks to retrieve per query
BM25_WEIGHT       = 0.4    # weight for lexical search in hybrid fusion
VECTOR_WEIGHT     = 0.6    # weight for semantic search in hybrid fusion

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR              = os.path.dirname(os.path.abspath(__file__))
REGULATIONS_DIR       = os.path.join(BASE_DIR, "documents", "regulations")
INTERNAL_POLICIES_DIR = os.path.join(BASE_DIR, "documents", "internal_policies")
REPORTS_DIR           = os.path.join(BASE_DIR, "reports")

# ── Prompt caching ────────────────────────────────────────────────────────────
# Regulatory documents change rarely → safe to cache their content
ENABLE_PROMPT_CACHING = True

# ── Evaluation ────────────────────────────────────────────────────────────────
EVAL_PASS_THRESHOLD = 7.0   # score out of 10; below this = flag for human review

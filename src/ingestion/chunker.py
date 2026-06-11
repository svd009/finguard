"""
chunker.py
──────────
Splits page-level text into smaller overlapping chunks for RAG retrieval.

Why chunk at all?
  LLMs have context limits. A 600-page PDF cannot fit in one prompt.
  We split documents into chunks (~800 chars) and retrieve only the
  most relevant ones per query — this is the core idea behind RAG.

Why overlap?
  A compliance clause might span a page break or paragraph boundary.
  If we split cleanly at 800 chars, we might cut a sentence in half.
  Overlapping by 150 chars ensures no clause is ever split at a
  critical boundary — both neighboring chunks contain it.

What metadata do we carry forward?
  Every chunk inherits: source filename, page number, chunk index.
  This is what powers citations in the final audit report.

Chunking strategy used: Fixed-size with overlap (simple, reliable)
  More advanced strategies (semantic chunking, recursive splitting)
  exist but fixed-size is standard for regulatory text which has
  consistent density throughout.
"""

from config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Split a list of page-level dicts into overlapping text chunks.

    Args:
        pages: Output from pdf_loader.load_all_pdfs()
               Each item: {"text": str, "page": int, "source": str, ...}

    Returns:
        List of chunk dicts:
        {
          "text":        str,   # the actual chunk content
          "source":      str,   # filename e.g. "fatf_guidelines.pdf"
          "page":        int,   # page number this chunk came from
          "chunk_index": int,   # position of this chunk within its page
          "file_path":   str,   # full path for reference
        }
    """
    chunks = []

    for page in pages:
        text = page["text"]
        page_chunks = _split_text(text, CHUNK_SIZE, CHUNK_OVERLAP)

        for i, chunk_text in enumerate(page_chunks):
            chunks.append({
                "text":        chunk_text,
                "source":      page["source"],
                "page":        page["page"],
                "chunk_index": i,
                "file_path":   page.get("file_path", ""),
            })

    print(f"  [Chunker] Created {len(chunks)} chunks from {len(pages)} pages")
    return chunks


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split a string into overlapping chunks of fixed character size.

    Example with chunk_size=20, overlap=5:
      "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
      → ["ABCDEFGHIJKLMNOPQRST",    (0-20)
         "PQRSTUVWXYZ............"]  (15-35, starts 5 chars before end of previous)

    Args:
        text:       Input string to split.
        chunk_size: Maximum characters per chunk.
        overlap:    Characters to repeat at the start of each new chunk.

    Returns:
        List of string chunks.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence boundary (period + space)
        # This keeps compliance clauses intact where possible
        if end < len(text):
            boundary = text.rfind(". ", start, end)
            if boundary != -1 and boundary > start + (chunk_size // 2):
                end = boundary + 1  # include the period

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move forward by (chunk_size - overlap) to create the overlap
        start = end - overlap

    return chunks

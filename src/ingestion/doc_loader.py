"""
doc_loader.py
─────────────
Unified document loader — handles both PDF files and plain text files.

Why support both?
  Real regulatory documents come as PDFs (Basel III, FATF guidelines).
  Our sample documents are plain text for portability (no PDF generation needed).
  This loader abstracts over both so the rest of the system doesn't care
  what format the source document is in.

In production: drop actual PDFs into the documents/ folders and this
loader picks them up automatically alongside any .txt files.
"""

import os


def load_text_file(file_path: str) -> list[dict]:
    """Load a plain text file as a single 'page'."""
    filename = os.path.basename(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        return []

    # Split on double newlines to simulate page-like sections
    sections = [s.strip() for s in text.split("\n\n\n") if len(s.strip()) > 50]

    pages = []
    for i, section in enumerate(sections):
        pages.append({
            "text":      section,
            "page":      i + 1,
            "source":    filename,
            "file_path": file_path,
        })

    print(f"  [Doc Loader] {filename}: {len(pages)} sections extracted")
    return pages


def load_document(file_path: str) -> list[dict]:
    """Route to the correct loader based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        from src.ingestion.pdf_loader import load_pdf
        return load_pdf(file_path)
    elif ext in (".txt", ".md"):
        return load_text_file(file_path)
    else:
        print(f"  [Doc Loader] Unsupported format skipped: {file_path}")
        return []


def load_all_documents(directory: str) -> list[dict]:
    """Load all supported documents from a directory."""
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")

    all_pages = []
    supported = (".pdf", ".txt", ".md")
    files = [f for f in os.listdir(directory) if f.lower().endswith(supported)]

    if not files:
        print(f"  [Doc Loader] No documents found in {directory}")
        return []

    for filename in sorted(files):
        file_path = os.path.join(directory, filename)
        pages = load_document(file_path)
        all_pages.extend(pages)

    print(f"  [Doc Loader] Total: {len(all_pages)} sections from {len(files)} files\n")
    return all_pages

"""
pdf_loader.py
─────────────
Extracts raw text from PDF files using PyMuPDF (fitz).

Why PyMuPDF?
  - Handles complex financial/regulatory PDFs better than PyPDF2
  - Preserves page structure so we can cite page numbers later
  - Fast even on large documents (Basel III is 600+ pages)

What this module does:
  1. Takes a PDF file path
  2. Opens each page and extracts its text
  3. Returns a list of dicts — one per page — containing:
       { "text": "...", "page": 3, "source": "fatf_guidelines.pdf" }

Why page-level chunks at this stage?
  Page metadata is critical for citations later. We preserve it here
  and carry it through the entire pipeline so audit reports can say
  "Source: fatf_guidelines.pdf, page 23" — not just a vague reference.
"""

import os
import fitz  # PyMuPDF


def load_pdf(file_path: str) -> list[dict]:
    """
    Load a single PDF and return a list of page-level text blocks.

    Args:
        file_path: Absolute or relative path to the PDF file.

    Returns:
        List of dicts: [{"text": str, "page": int, "source": str}, ...]
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    pages = []
    filename = os.path.basename(file_path)

    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()

        # Skip blank pages (common in regulatory PDFs with section dividers)
        if len(text) < 50:
            continue

        pages.append({
            "text": text,
            "page": page_num + 1,   # 1-indexed for human-readable citations
            "source": filename,
            "file_path": file_path,
        })

    doc.close()
    print(f"  [PDF Loader] {filename}: {len(pages)} pages extracted")
    return pages


def load_all_pdfs(directory: str) -> list[dict]:
    """
    Load every PDF in a directory.

    Args:
        directory: Path to a folder containing PDF files.

    Returns:
        Combined list of page-level dicts from all PDFs.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")

    all_pages = []
    pdf_files = [f for f in os.listdir(directory) if f.endswith(".pdf")]

    if not pdf_files:
        print(f"  [PDF Loader] No PDFs found in {directory}")
        return []

    for filename in sorted(pdf_files):
        file_path = os.path.join(directory, filename)
        pages = load_pdf(file_path)
        all_pages.extend(pages)

    print(f"  [PDF Loader] Total: {len(all_pages)} pages from {len(pdf_files)} files\n")
    return all_pages

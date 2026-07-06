"""
tools/pdf_parser.py

Extracts raw text from an uploaded resume PDF using PyMuPDF (fitz).
"""

import fitz  # PyMuPDF

from tools.utils import clean_whitespace


class InvalidPDFError(Exception):
    """Raised when the uploaded file is not a readable PDF."""


class EmptyResumeError(Exception):
    """Raised when a PDF is readable but contains no extractable text."""


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract and clean text content from a PDF file.

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        str: Cleaned resume text.

    Raises:
        InvalidPDFError: If the file cannot be opened as a PDF.
        EmptyResumeError: If no text could be extracted.
    """
    try:
        document = fitz.open(file_path)
    except Exception as exc:
        raise InvalidPDFError(f"Could not open PDF file: {exc}") from exc

    full_text = []

    try:
        for page in document:
            full_text.append(page.get_text())
    finally:
        document.close()

    combined_text = clean_whitespace("\n".join(full_text))

    if not combined_text:
        raise EmptyResumeError(
            "No readable text found in the resume. The PDF may be a "
            "scanned image without a text layer."
        )

    return combined_text


def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    """
    Extract text directly from in-memory PDF bytes (useful for Streamlit
    file uploads that don't need to touch disk first).

    Args:
        pdf_bytes: Raw PDF file bytes.

    Returns:
        str: Cleaned resume text.
    """
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise InvalidPDFError(f"Could not open PDF file: {exc}") from exc

    full_text = []

    try:
        for page in document:
            full_text.append(page.get_text())
    finally:
        document.close()

    combined_text = clean_whitespace("\n".join(full_text))

    if not combined_text:
        raise EmptyResumeError(
            "No readable text found in the resume. The PDF may be a "
            "scanned image without a text layer."
        )

    return combined_text

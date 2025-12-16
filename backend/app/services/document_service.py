import hashlib
from io import BytesIO
from typing import List

import PyPDF2
import docx
from fastapi import UploadFile, HTTPException


def extract_text_from_file(file: UploadFile) -> str:
    try:
        content = file.file.read()
        file.file.seek(0)
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read file")

    filename = (file.filename or "").lower()

    if filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(BytesIO(content))
        text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
        return normalize_text("\n".join(text))

    elif filename.endswith(".docx"):
        doc = docx.Document(BytesIO(content))
        return normalize_text("\n".join(p.text for p in doc.paragraphs))

    elif filename.endswith((".txt", ".md")):
        return normalize_text(content.decode("utf-8", errors="ignore"))

    else:
        raise HTTPException(status_code=400, detail="Unsupported file format")


def normalize_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 150,
) -> List[str]:
    """
    Character-based chunking with safe overlap.
    Tuned for embedding models.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


def compute_file_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

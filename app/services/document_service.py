import hashlib
from io import BytesIO
import PyPDF2
import docx
from fastapi import UploadFile, HTTPException
from typing import List

def extract_text_from_file(file: UploadFile) -> str:
    content = file.file.read()
    file.file.seek(0)

    filename = file.filename.lower()
    if filename.endswith('.pdf'):
        reader = PyPDF2.PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif filename.endswith('.docx'):
        doc = docx.Document(BytesIO(content))
        return "\n".join(para.text for para in doc.paragraphs)
    elif filename.endswith(('.txt', '.md')):
        return content.decode('utf-8')
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format")

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def compute_file_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

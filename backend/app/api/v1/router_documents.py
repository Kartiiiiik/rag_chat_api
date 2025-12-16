from fastapi import APIRouter, UploadFile, File, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.models.document import Document
from app.models.chunk import Chunk
from app.schemas.document import DocumentResponse
from app.services.document_service import extract_text_from_file, chunk_text, compute_file_hash
from app.services.gemini_service import get_embedding
from app.core.limiter import limiter

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # ---------- FILE SIZE ----------
    contents = await file.read()
    size = len(contents)
    await file.seek(0)

    if size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    # ---------- TEXT EXTRACTION ----------
    text = extract_text_from_file(file)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Empty or unreadable file")

    file_hash = compute_file_hash(text)

    if db.query(Document).filter_by(file_hash=file_hash).first():
        raise HTTPException(status_code=409, detail="Document already exists")

    # ---------- CREATE DOCUMENT ----------
    doc = Document(
        filename=file.filename,
        content=text,
        file_hash=file_hash,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # ---------- CHUNKING ----------
    chunks = chunk_text(text)
    chunk_objects = []

    for idx, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        chunk_objects.append(
            Chunk(
                document_id=doc.id,
                content=chunk,
                embedding=embedding,
                chunk_index=idx,
            )
        )

    db.bulk_save_objects(chunk_objects)
    db.commit()

    return doc


@router.get("/", response_model=list[DocumentResponse])
@limiter.limit("30/minute")
async def list_documents(request: Request, db: Session = Depends(get_db)):
    return (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.delete("/{document_id}")
@limiter.limit("20/minute")
async def delete_document(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter_by(id=document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    db.query(Chunk).filter_by(document_id=document_id).delete()
    db.delete(doc)
    db.commit()

    return {"message": "Document deleted"}

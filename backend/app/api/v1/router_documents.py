from fastapi import APIRouter, UploadFile, File, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.models.document import Document
from app.models.chunk import Chunk
from app.schemas.document import DocumentResponse
from app.services.document_service import extract_text_from_file, chunk_text, compute_file_hash
from app.services.gemini_service import get_embedding
from app.core.limiter import limiter
from typing import List

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        # ---------- FILE SIZE ----------
        contents = await file.read()
        size = len(contents)
        
        if size > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")
        
        # Reset file pointer for text extraction
        await file.seek(0)

        # ---------- TEXT EXTRACTION ----------
        text = extract_text_from_file(file)  # Make sure this is async or wrap it
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Empty or unreadable file")

        file_hash = compute_file_hash(text)

        # Check for duplicate
        existing_doc = db.query(Document).filter_by(file_hash=file_hash).first()
        if existing_doc:
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
        if not chunks:
            raise HTTPException(status_code=400, detail="Failed to chunk document")

        chunk_objects = []

        try:
            # Try to use batch embeddings if available
            try:
                from app.services.gemini_service import get_batch_embeddings
                embeddings = get_batch_embeddings(chunks)
            except ImportError:
                # Fallback to individual embeddings
                embeddings = [get_embedding(chunk) for chunk in chunks]

            for idx, (chunk_content, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_objects.append(
                    Chunk(
                        document_id=doc.id,
                        content=chunk_content,
                        embedding=embedding,
                        chunk_index=idx,
                    )
                )

            db.bulk_save_objects(chunk_objects)
            db.commit()
            
        except Exception as e:
            # Rollback on error
            db.rollback()
            db.delete(doc)
            db.commit()
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to process document chunks: {str(e)}"
            )

        return doc
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/", response_model=List[DocumentResponse])
@limiter.limit("30/minute")
async def list_documents(
    request: Request, 
    db: Session = Depends(get_db)
):
    documents = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .all()
    )
    return documents


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

    try:
        # Delete chunks first (foreign key constraint)
        db.query(Chunk).filter_by(document_id=document_id).delete()
        db.delete(doc)
        db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to delete document: {str(e)}"
        )
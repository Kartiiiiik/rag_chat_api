from fastapi import APIRouter, UploadFile, File, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.models import Document, Chunk
from app.schemas.document import DocumentResponse
from app.services import chunk_text, compute_file_hash
from app.api.v1.utils import (
    validate_file_size,
    extract_and_validate_text,
    check_duplicate_document,
    create_document_record,
    validate_chunks,
    process_and_save_chunks,
)
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
    """
    Upload and process a document for RAG system.
    
    - Validates file size (max 10MB)
    - Extracts and validates text content
    - Checks for duplicates
    - Creates document record
    - Chunks text and generates embeddings
    """
    try:
        # Validate file size
        await validate_file_size(file)
        
        # Extract and validate text
        text = extract_and_validate_text(file)
        file_hash = compute_file_hash(text)
        
        # Check for duplicates
        check_duplicate_document(db, file_hash)
        
        # Create document record
        doc = create_document_record(db, file.filename, text, file_hash)
        
        # Chunk and process
        chunks = chunk_text(text)
        validate_chunks(chunks)
        process_and_save_chunks(db, doc, chunks)
        
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
from fastapi import APIRouter, UploadFile, File, Depends, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.models.document import Document
from app.models.chunk import Chunk
from app.schemas.document import DocumentResponse
from app.services.document_service import extract_text_from_file, chunk_text, compute_file_hash
from app.services.gemini_service import get_batch_embeddings
from app.core.limiter import limiter
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


def process_chunks_background(document_id: int, chunks: List[str], db_session):
    """
    Background task to process chunks with embeddings.
    This runs after the response is sent to the user.
    """
    try:
        logger.info(f"Starting background processing for document {document_id} with {len(chunks)} chunks")
        
        # Get embeddings with very conservative settings
        embeddings = get_batch_embeddings(
            chunks,
            batch_size=5,  # Very small batches
            delay_between_batches=4.0,  # 4 seconds between batches
            max_retries=5
        )
        
        if len(embeddings) != len(chunks):
            logger.error(f"Embedding count mismatch: {len(embeddings)} != {len(chunks)}")
            raise ValueError("Embedding count mismatch")
        
        # Create chunk objects
        chunk_objects = []
        for idx, (chunk_content, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_objects.append(
                Chunk(
                    document_id=document_id,
                    content=chunk_content,
                    embedding=embedding,
                    chunk_index=idx,
                )
            )
        
        # Save to database
        db_session.bulk_save_objects(chunk_objects)
        db_session.commit()
        
        logger.info(f"✓ Successfully processed {len(chunk_objects)} chunks for document {document_id}")
        
    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {e}")
        db_session.rollback()
        
        # Mark document as failed (you might want to add a status field to Document model)
        try:
            doc = db_session.query(Document).filter_by(id=document_id).first()
            if doc:
                # If you have a status field: doc.status = "failed"
                # doc.error_message = str(e)
                db_session.commit()
        except Exception as cleanup_error:
            logger.error(f"Failed to update document status: {cleanup_error}")
    
    finally:
        db_session.close()


@router.post("/upload", response_model=DocumentResponse)
@limiter.limit("5/minute")  # Reduced from 10 to be more conservative
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
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
        text = extract_text_from_file(file)
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Empty or unreadable file")

        file_hash = compute_file_hash(text)

        # Check for duplicate
        existing_doc = db.query(Document).filter_by(file_hash=file_hash).first()
        if existing_doc:
            raise HTTPException(
                status_code=409, 
                detail="Document already exists",
                headers={"X-Document-Id": str(existing_doc.id)}
            )

        # ---------- CREATE DOCUMENT ----------
        doc = Document(
            filename=file.filename,
            content=text,
            file_hash=file_hash,
            # If you have a status field: status="processing"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # ---------- CHUNKING ----------
        chunks = chunk_text(text)
        if not chunks:
            db.rollback()
            db.delete(doc)
            db.commit()
            raise HTTPException(status_code=400, detail="Failed to chunk document")

        logger.info(f"Document {doc.id} created with {len(chunks)} chunks, starting background processing")

        # Process chunks in background to avoid timeout
        # Create a new session for background task
        from app.db.database import SessionLocal
        background_db = SessionLocal()
        
        background_tasks.add_task(
            process_chunks_background,
            document_id=doc.id,
            chunks=chunks,
            db_session=background_db
        )

        # Return immediately - chunks will be processed in background
        return doc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/upload-sync", response_model=DocumentResponse)
@limiter.limit("2/minute")  # Even more restrictive for sync upload
async def upload_document_sync(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Synchronous upload that waits for all chunks to be processed.
    Use this only for small documents or when you need immediate processing.
    """
    try:
        contents = await file.read()
        size = len(contents)
        
        if size > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")
        
        await file.seek(0)

        text = extract_text_from_file(file)
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Empty or unreadable file")

        file_hash = compute_file_hash(text)

        existing_doc = db.query(Document).filter_by(file_hash=file_hash).first()
        if existing_doc:
            raise HTTPException(status_code=409, detail="Document already exists")

        doc = Document(
            filename=file.filename,
            content=text,
            file_hash=file_hash,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        chunks = chunk_text(text)
        if not chunks:
            raise HTTPException(status_code=400, detail="Failed to chunk document")

        # Limit chunk size for sync processing
        if len(chunks) > 50:
            db.rollback()
            db.delete(doc)
            db.commit()
            raise HTTPException(
                status_code=400, 
                detail=f"Document too large for sync processing ({len(chunks)} chunks). Use /upload endpoint instead."
            )

        try:
            logger.info(f"Processing {len(chunks)} chunks synchronously for document {doc.id}")
            
            # Process with very conservative settings
            embeddings = get_batch_embeddings(
                chunks,
                batch_size=5,
                delay_between_batches=4.0,
                max_retries=5
            )

            chunk_objects = []
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
            
            logger.info(f"✓ Synchronously processed {len(chunk_objects)} chunks for document {doc.id}")
            
        except Exception as e:
            logger.error(f"Sync processing failed: {e}")
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
        logger.error(f"Sync upload error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/{document_id}/status")
@limiter.limit("60/minute")
async def get_document_status(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    Check if a document's chunks have been processed.
    Useful for polling after background upload.
    """
    doc = db.query(Document).filter_by(id=document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    chunk_count = db.query(Chunk).filter_by(document_id=document_id).count()
    
    # You can enhance this with a status field on Document model
    return {
        "document_id": document_id,
        "filename": doc.filename,
        "chunk_count": chunk_count,
        "is_processed": chunk_count > 0,
        # "status": doc.status if hasattr(doc, 'status') else "unknown",
    }


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
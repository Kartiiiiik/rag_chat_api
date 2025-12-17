from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List

from models import Document, Chunk
from services import get_embedding_service, extract_text_from_file, chunk_text, compute_file_hash


async def validate_file_size(file: UploadFile, max_size_mb: int = 10) -> bytes:
    """
    Validate file size and return contents.
    
    Args:
        file: The uploaded file
        max_size_mb: Maximum allowed file size in MB
        
    Returns:
        File contents as bytes
        
    Raises:
        HTTPException: If file exceeds size limit
    """
    contents = await file.read()
    size = len(contents)
    max_bytes = max_size_mb * 1024 * 1024
    
    if size > max_bytes:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large (max {max_size_mb}MB)"
        )
    
    await file.seek(0)
    return contents


def extract_and_validate_text(file: UploadFile) -> str:
    """
    Extract text from file and validate it's not empty.
    
    Args:
        file: The uploaded file
        
    Returns:
        Extracted text content
        
    Raises:
        HTTPException: If file is empty or unreadable
    """
    text = extract_text_from_file(file)
    
    if not text or not text.strip():
        raise HTTPException(
            status_code=400, 
            detail="Empty or unreadable file"
        )
    
    return text


def check_duplicate_document(db: Session, file_hash: str) -> None:
    """
    Check if document with given hash already exists.
    
    Args:
        db: Database session
        file_hash: Hash of the document content
        
    Raises:
        HTTPException: If duplicate document exists
    """
    existing_doc = db.query(Document).filter_by(file_hash=file_hash).first()
    
    if existing_doc:
        raise HTTPException(
            status_code=409, 
            detail="Document already exists"
        )


def create_document_record(
    db: Session, 
    filename: str, 
    text: str, 
    file_hash: str
) -> Document:
    """
    Create and persist a new document record.
    
    Args:
        db: Database session
        filename: Original filename
        text: Document text content
        file_hash: Hash of the content
        
    Returns:
        Created Document object
    """
    doc = Document(
        filename=filename,
        content=text,
        file_hash=file_hash,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def validate_chunks(chunks: List[str]) -> None:
    """
    Validate that chunks were successfully created.
    
    Args:
        chunks: List of text chunks
        
    Raises:
        HTTPException: If chunking failed
    """
    if not chunks:
        raise HTTPException(
            status_code=400, 
            detail="Failed to chunk document"
        )


def create_chunk_objects(
    document_id: int, 
    chunks: List[str], 
    embeddings: List
) -> List[Chunk]:
    """
    Create Chunk objects with embeddings.
    
    Args:
        document_id: ID of the parent document
        chunks: List of text chunks
        embeddings: List of embedding vectors
        
    Returns:
        List of Chunk objects ready for persistence
    """
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
    
    return chunk_objects


def process_and_save_chunks(
    db: Session, 
    doc: Document, 
    chunks: List[str]
) -> None:
    """
    Generate embeddings and save chunks to database.
    
    Args:
        db: Database session
        doc: Parent document
        chunks: List of text chunks
        
    Raises:
        HTTPException: If processing fails (also rolls back document)
    """
    try:
        embedding_service = get_embedding_service()
        embeddings = embedding_service.get_embeddings(chunks)
        
        chunk_objects = create_chunk_objects(doc.id, chunks, embeddings)
        
        db.bulk_save_objects(chunk_objects)
        db.commit()
        
    except Exception as e:
        db.rollback()
        db.delete(doc)
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document chunks: {str(e)}"
        )





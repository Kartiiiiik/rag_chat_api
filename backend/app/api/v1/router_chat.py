from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.services.gemini_service import generate_response, generate_response_stream
from app.services.rag_service import search_similar_chunks, build_prompt
from typing import List, Optional
import logging

from app.schemas.chat import ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])

logger = logging.getLogger(__name__)

@router.post("/")
async def chat_with_doc(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Handles user queries, searches relevant document chunks, and generates a response.
    Optionally supports streaming responses.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        # Step 1: Search for relevant chunks based on the query
        chunks = search_similar_chunks(db, request.message, document_ids=request.document_ids, limit=5)

        if not chunks:
            raise HTTPException(status_code=404, detail="No relevant content found")

        # Step 2: Build the prompt for the chat model using the relevant chunks
        prompt = build_prompt(request.message, chunks)

        if request.stream:
            return generate_response_stream(prompt)  # Handle streaming if enabled
        
        # For non-streaming, generate a full response
        answer = generate_response(prompt)  # Calls the Gemini API to generate an answer
        
        return {"response": answer}

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


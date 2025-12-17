from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.services.gemini_service import generate_answer, generate_answer_stream
from app.services.rag_service import search_similar_chunks, build_prompt
from typing import List, Optional
import logging

router = APIRouter(prefix="/chat", tags=["chat"])

logger = logging.getLogger(__name__)

@router.post("/")
async def chat_with_doc(
    query: str,
    document_ids: Optional[List[int]] = None,
    limit: int = 5,
    stream: bool = False,
    db: Session = Depends(get_db),
):
    """
    Handles user queries, searches relevant document chunks, and generates a response.
    Optionally supports streaming responses.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        # Step 1: Search for relevant chunks based on the query
        chunks = search_similar_chunks(db, query, document_ids=document_ids, limit=limit)

        if not chunks:
            raise HTTPException(status_code=404, detail="No relevant content found")

        # Step 2: Build the prompt for the chat model using the relevant chunks
        prompt = build_prompt(query, chunks)

        # Step 3: Generate the answer using the Gemini API or other model (for non-streaming)
        if stream:
            return generate_answer_stream(prompt)  # Handle streaming if enabled
        
        # For non-streaming, generate a full response
        answer = generate_answer(prompt)  # Calls the Gemini API to generate an answer
        
        return {"response": answer}

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


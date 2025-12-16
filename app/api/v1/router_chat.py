from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.schemas.chat import ChatRequest, ChatResponse, SourceInfo
from app.services.rag_service import search_similar_chunks, build_prompt
from app.services.gemini_service import generate_response, generate_response_stream
from app.core.limiter import limiter
import asyncio

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
@limiter.limit("20/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    db: Session = Depends(get_db),
):
    if not body.message or not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    chunks = search_similar_chunks(
        db=db,
        query=body.message,
        document_ids=body.document_ids,
        limit=5,  # IMPORTANT: cap context
    )

    if not chunks:
        return ChatResponse(
            response="No relevant information found in documents.",
            sources=[],
        )

    prompt = build_prompt(body.message, chunks)

    # ---------- STREAMING ----------
    if body.stream:
        async def event_stream():
            async for token in generate_response_stream(prompt):
                yield f"data: {token}\n\n"
                await asyncio.sleep(0)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
        )

    # ---------- NON-STREAM ----------
    response_text = await asyncio.to_thread(generate_response, prompt)

    sources = [
        SourceInfo(
            document_id=c.document_id,
            content=c.content[:200] + "...",
            chunk_index=c.chunk_index,
        )
        for c in chunks
    ]

    return ChatResponse(response=response_text, sources=sources)

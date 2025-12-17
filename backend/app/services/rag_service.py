from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.chunk import Chunk
from app.services.SentenceTransformerService import get_embedding_service

def search_similar_chunks(
    db: Session,
    query: str,
    document_ids: Optional[List[int]] = None,
    limit: int = 5,
):
    # Use local embedding service
    embedding_service = get_embedding_service()
    query_embedding = embedding_service.get_embedding(query)

    q = db.query(Chunk)

    if document_ids:
        q = q.filter(Chunk.document_id.in_(document_ids))

    return (
        q.order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
        .all()
    )


def build_prompt(query: str, chunks: List[Chunk]) -> str:
    context_parts = []

    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[Source {i + 1}]\n{chunk.content.strip()}"
        )

    context = "\n\n".join(context_parts)

    return f"""You are a factual assistant.
Answer ONLY using the provided context.
If the answer is not in the context, say: "I don't have enough information to answer that."

Context:
{context}

Question:
{query}

Answer:
"""

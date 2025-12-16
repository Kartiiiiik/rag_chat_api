from sqlalchemy.orm import Session
from app.models.chunk import Chunk
from app.services.gemini_service import get_embedding

def search_similar_chunks(db: Session, query: str, document_ids=None, limit: int = 5):
    query_emb = get_embedding(query, task_type="retrieval_query")
    q = db.query(Chunk)
    if document_ids:
        q = q.filter(Chunk.document_id.in_(document_ids))
    return q.order_by(Chunk.embedding.cosine_distance(query_emb)).limit(limit).all()

def build_prompt(query: str, chunks):
    context = "\n\n".join(f"[Source {i+1}]: {c.content}" for i, c in enumerate(chunks))
    return f"""You are a helpful assistant. Answer based only on the provided context.
If the information is not present, say so clearly.

Context:
{context}

Question: {query}

Answer:"""

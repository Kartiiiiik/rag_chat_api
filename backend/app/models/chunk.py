from sqlalchemy import Column, Integer, Text, ForeignKey, Index
from pgvector.sqlalchemy import Vector
from app.db.base import Base

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=False)
    chunk_index = Column(Integer, nullable=False)

    __table_args__ = (
        Index(
            "ix_chunks_embedding",
            "embedding",
            postgresql_using="ivfflat",
        ),
    )

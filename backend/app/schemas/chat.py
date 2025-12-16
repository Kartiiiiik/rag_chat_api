from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    document_ids: Optional[List[int]] = None
    stream: bool = False

class SourceInfo(BaseModel):
    document_id: int
    content: str
    chunk_index: int

class ChatResponse(BaseModel):
    response: str
    sources: List[SourceInfo]

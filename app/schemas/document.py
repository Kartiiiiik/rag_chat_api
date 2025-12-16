from pydantic import BaseModel
from datetime import datetime
from typing import List

class DocumentResponse(BaseModel):
    id: int
    filename: str
    created_at: datetime

    class Config:
        from_attributes = True

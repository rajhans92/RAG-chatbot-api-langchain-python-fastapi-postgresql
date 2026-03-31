from pydantic import BaseModel
from typing import List, Optional


class HeaderDetail(BaseModel):
    userId: int
    sessionId: int

class HeaderDetailOnlyUser(BaseModel):
    userId: int

class SessionRequest(BaseModel):
    title: str
    modelName: str

class MessageRequest(BaseModel):
    message: str
    documentId: Optional[List[int]] = None
from pydantic import BaseModel
from typing import List


class HeaderDetail(BaseModel):
    userId: int
    sessionId: int

class HeaderDetailOnlyUser(BaseModel):
    userId: int

class SessionRequest(BaseModel):
    title: str
    modelName: str
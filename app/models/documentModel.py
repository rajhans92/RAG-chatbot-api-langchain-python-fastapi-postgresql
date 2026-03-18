from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.helpers.databaseConnection import Base
from datetime import datetime
from pgvector.sqlalchemy import Vector

class Documents(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True),
    user_id = Column(Integer, nullable=False),
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False),
    document_name = Column(Text, nullable=False),
    document_unique_name = Column(Text, nullable=False),
    document_type = Column(Text, nullable=False),
    storage_path = Column(Text, nullable=False),
    document_summary = Column(Text, default=""),
    status = Column(String(50), nullable=False, default="processing"),  # 'processing', 'completed', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)



class DocumentChunks(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True),
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False),
    chunk_text = Column(Text, nullable=False),
    chunk_embedding = Column(Vector(1536), nullable=False),
    chunk_order = Column(Integer, nullable=False)  # To maintain the order of chunks in a document
    metadata = Column(Text, nullable=True)  # Optional metadata for the chunk
    token_count = Column(Integer, nullable=False)  # Number of tokens in the chunk
    created_at = Column(DateTime, default=datetime.utcnow)

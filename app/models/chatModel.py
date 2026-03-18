from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.helpers.databaseConnection import Base
from datetime import datetime
from pgvector.sqlalchemy import Vector

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    model_name = Column(String(255), nullable=False)
    total_tokens_used = Column(Integer, default=0)
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id") ,nullable=False)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    message = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    message_order = Column(Integer, nullable=False)  # To maintain the order of messages in a session
    is_summarized = Column(Integer, default=0)  # 1 for summarized, 0 for not summarized
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatSummary(Base):
    __tablename__ = "chat_summaries"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    summary_text = Column(Text, nullable=False)
    summary_embedding = Column(Vector(1536), nullable=False) 
    message_start_order = Column(Integer, nullable=False)
    message_end_order = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class MemoryEvents(Base):
    __tablename__ = "memory_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)  # 'add', 'update', 'delete'
    text_embedding = Column(Vector(1536), nullable=False) 
    importance_score = Column(Integer, nullable=False)  # 1 to 10
    created_at = Column(DateTime, default=datetime.utcnow)
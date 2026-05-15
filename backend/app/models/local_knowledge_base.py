from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class LocalKnowledgeBase(Base):
    __tablename__ = "local_knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    qa_answer = Column(Text, nullable=True)
    keywords = Column(String(255), nullable=True)
    chapter = Column(String(120), nullable=True)
    sub_chapter = Column(String(120), nullable=True)
    source = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

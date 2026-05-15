from sqlalchemy import BigInteger, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class AIQALog(Base):
    __tablename__ = "ai_qa_logs"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    source = Column(String(30), nullable=False)
    confidence = Column(Numeric(4, 2), nullable=True, default=0.00)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

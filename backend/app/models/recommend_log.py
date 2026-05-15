from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class RecommendLog(Base):
    __tablename__ = "recommend_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    action = Column(String(20), nullable=False, index=True)  # expose/click
    target_type = Column(String(20), nullable=False, index=True)  # content/event/topic
    target_id = Column(Integer, nullable=False, index=True)
    source_scene = Column(String(30), nullable=True)
    explain_json = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

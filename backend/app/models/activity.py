from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    cover_url = Column(String(255), nullable=True)
    location = Column(String(200), nullable=True)
    organizer = Column(String(120), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    max_participants = Column(Integer, nullable=False, default=50)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_featured = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="open")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

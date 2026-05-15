from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    cover_url = Column(String(255), nullable=True)
    content_type = Column(String(30), nullable=False)
    source_site = Column(String(120), nullable=True)
    source_url = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    chapter = Column(String(120), nullable=True)
    sub_chapter = Column(String(120), nullable=True)
    content_hash = Column(String(40), nullable=True)
    quality_score = Column(Float, nullable=False, default=0.0)
    review_status = Column(String(20), nullable=False, default="pending")
    import_batch = Column(String(60), nullable=True)
    is_featured = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="draft")
    published_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

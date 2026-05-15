from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class DiscussionTopic(Base):
    __tablename__ = "discussion_topics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    nickname = Column(String(64), nullable=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    cover_url = Column(String(255), nullable=True)
    image_urls = Column(Text, nullable=True)
    is_featured = Column(Boolean, nullable=False, default=False)
    like_count = Column(Integer, nullable=False, default=0)
    favorite_count = Column(Integer, nullable=False, default=0)
    comment_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

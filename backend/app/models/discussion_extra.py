from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class DiscussionFavorite(Base):
    __tablename__ = "discussion_favorites"
    __table_args__ = (
        UniqueConstraint("topic_id", "user_id", name="uk_topic_user_favorite"),
    )

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class DiscussionTopicTag(Base):
    __tablename__ = "discussion_topic_tags"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, nullable=False, index=True)
    tag = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

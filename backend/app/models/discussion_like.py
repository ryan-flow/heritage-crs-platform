from sqlalchemy import Column, DateTime, Integer, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class DiscussionLike(Base):
    __tablename__ = "discussion_likes"
    __table_args__ = (UniqueConstraint("topic_id", "user_id", name="uk_topic_user_like"),)

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

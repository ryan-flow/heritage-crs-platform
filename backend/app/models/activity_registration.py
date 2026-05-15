from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class ActivityRegistration(Base):
    __tablename__ = "activity_registrations"
    __table_args__ = (
        UniqueConstraint("activity_id", "user_id", name="uk_activity_user"),
    )

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    remark = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="registered")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String(64), unique=True, nullable=False, index=True)
    username = Column(String(64), unique=True, nullable=True, index=True)
    password = Column(String(128), nullable=True)
    nickname = Column(String(64), nullable=True)
    phone = Column(String(20), nullable=True)
    role = Column(String(20), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    preferred_heritage_types = Column(Text, nullable=True)
    preferred_scene_types = Column(Text, nullable=True)
    preferred_regions = Column(Text, nullable=True)

    # CRS 置信度字段（v2.0 新增）
    confidence_score = Column(Float, nullable=False, default=0.0)       # 综合置信度 C (0-100)
    score_explicit = Column(Float, nullable=False, default=0.0)         # 显式偏好分 S_explicit (0-100)
    score_implicit = Column(Float, nullable=False, default=0.0)         # 隐式行为分 S_implicit (0-100)
    score_dialogue = Column(Float, nullable=False, default=0.0)         # 对话语义分 S_dialogue (0-100)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

"""CRS ASK动作记录表

记录用户对ASK提问的回答，用于回溯冷启动过程和分析推荐效果。
"""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CrsAskLog(Base):
    __tablename__ = "crs_ask_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_id = Column(String(36), nullable=False, index=True)     # 关联CrsSession
    ask_id = Column(String(10), nullable=False)                      # ASK模板ID: A01-A05/B01-B05/R01-R03
    attribute = Column(String(30), nullable=False)                   # 提问属性: category/region/scene/level
    question_text = Column(Text, nullable=False)                     # 实际提问文本
    answer = Column(Text, nullable=True)                             # 用户选择的答案
    is_skipped = Column(Boolean, nullable=False, default=False)      # True=跳过/拒绝类回答
    score_delta = Column(Integer, nullable=False, default=0)         # 本次回答带来的置信度增量
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

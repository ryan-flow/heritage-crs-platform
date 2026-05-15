"""CRS对话推荐会话状态表

记录每个用户当前的CRS会话状态，包括当前模式、对话轮次、上次提问属性等。
每个用户同时只维护一个活跃会话。
"""
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CrsSession(Base):
    __tablename__ = "crs_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_id = Column(String(36), nullable=False, unique=True, index=True)  # UUID格式
    mode = Column(String(20), nullable=False, default="cold_start")  # cold_start / mixed / precision
    turn_count = Column(Integer, nullable=False, default=0)          # 当前会话对话轮次
    last_ask_attribute = Column(String(30), nullable=True)           # 上次提问的属性 category/region/scene/level
    last_ask_id = Column(String(10), nullable=True)                  # 上次提问的ASK模板ID A01/B01/R01等
    asked_attributes = Column(Text, nullable=True)                   # 已问属性列表 JSON数组 如["category","region"]
    context_summary = Column(Text, nullable=True)                    # 对话上下文摘要
    is_active = Column(Integer, nullable=False, default=1)           # 1=活跃 0=已结束
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def get_asked_attributes(self) -> list:
        """获取已问属性列表"""
        if not self.asked_attributes:
            result = []
            if self.last_ask_attribute:
                result.append(self.last_ask_attribute)
            return result
        try:
            import json
            return json.loads(self.asked_attributes)
        except Exception:
            result = []
            if self.last_ask_attribute:
                result.append(self.last_ask_attribute)
            return result

    def add_asked_attribute(self, attribute: str) -> None:
        """添加已问属性"""
        attrs = self.get_asked_attributes()
        if attribute not in attrs:
            attrs.append(attribute)
        import json
        self.asked_attributes = json.dumps(attrs, ensure_ascii=False)

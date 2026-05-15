#!/usr/bin/env python3
"""答辩前环境检查：确认KB数据、用户状态、CRS会话"""
import sys
sys.path.insert(0, ".")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.local_knowledge_base import LocalKnowledgeBase
from app.models.user import User
from app.models.ai_qa_log import AIQALog
from app.models.crs_session import CrsSession

engine = create_engine(settings.sqlite_url)
Session = sessionmaker(bind=engine)
db = Session()

kb_count = db.query(LocalKnowledgeBase).filter(LocalKnowledgeBase.status == "active").count()
print(f"KB active records: {kb_count}")

kbs = db.query(LocalKnowledgeBase.question, LocalKnowledgeBase.chapter).filter(LocalKnowledgeBase.status == "active").all()
chapters = {}
for q, ch in kbs:
    chapters.setdefault(ch, []).append(q)
for ch, qs in chapters.items():
    print(f"  [{ch}] {len(qs)}条: {qs[0][:50]}...")

users = db.query(User).all()
for u in users:
    print(f"User[{u.id}]: heritage={u.preferred_heritage_types}, scene={u.preferred_scene_types}, region={u.preferred_regions}")

log_count = db.query(AIQALog).count()
print(f"AIQALog records: {log_count}")

sessions = db.query(CrsSession).all()
for s in sessions:
    print(f"Session[user={s.user_id}]: mode={s.current_mode}, turn={s.turn_count}")

db.close()

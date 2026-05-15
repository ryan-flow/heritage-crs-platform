#!/usr/bin/env python3
"""验证苏绣推荐修复"""
import sys
sys.path.insert(0, ".")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.ai_service import ai_answer

engine = create_engine(settings.sqlite_url)
Session = sessionmaker(bind=engine)
db = Session()

result = ai_answer(db, "苏绣入门可以从哪些小件绣品开始了解", user_id=16)
answer = result["answer"][:150]
cards = result["recommend_cards"]
source = result["source"]
strategy = result["strategy"]
kg_entity = result["kg_entity"]

print(f"source={source}, strategy={strategy}, kg_entity={kg_entity}")
print(f"answer: {answer}")
print(f"cards ({len(cards)}):")
for c in cards:
    ctype = c.get("type", "")
    title = c.get("title", "")
    reason = c.get("reason", "")[:40]
    print(f"  [{ctype}] {title} - {reason}")

db.close()

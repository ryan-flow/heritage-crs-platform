import sys; sys.path.insert(0, ".")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.local_knowledge_base import LocalKnowledgeBase

engine = create_engine(settings.sqlite_url)
db = sessionmaker(bind=engine)()

total = db.query(LocalKnowledgeBase).count()
active = db.query(LocalKnowledgeBase).filter(LocalKnowledgeBase.status == "active").count()
inactive = db.query(LocalKnowledgeBase).filter(LocalKnowledgeBase.status != "active").count()
no_status = db.query(LocalKnowledgeBase).filter(LocalKnowledgeBase.status == None).count()

print(f"Total: {total}, Active: {active}, Inactive: {inactive}, No status: {no_status}")

sample = db.query(LocalKnowledgeBase).limit(3).all()
for s in sample:
    print(f"  id={s.id}, status='{s.status}', question='{s.question[:40]}'")

db.close()

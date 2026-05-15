import sys; sys.path.insert(0, ".")
from app.api.v1.endpoints.admin import list_kb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.sqlite_url)
db = sessionmaker(bind=engine)()

result = list_kb(keyword="", chapter="", status="", page=1, size=5, db=db)
items = result.get("data", {}).get("items", [])
total = result.get("data", {}).get("total", 0)
print(f"Total: {total}, Page items: {len(items)}")
for i in items:
    q = i["question"][:40]
    ch = i["chapter"]
    print(f"  [{i['id']}] {q}... chapter={ch}")

db.close()

import sys, time
sys.path.insert(0, ".")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.ai_service import ai_answer

engine = create_engine(settings.sqlite_url)
db = sessionmaker(bind=engine)()

tests = [
    ("昆曲为什么被称为百戏之祖", "昆曲"),
    ("苏绣入门可以从哪些小件绣品开始了解", "绣"),
    ("端午节为什么属于活态非遗", "端午"),
    ("中医针灸的原理是什么", "针灸"),
]

for q, expected_kw in tests:
    t0 = time.time()
    result = ai_answer(db, q, user_id=16)
    elapsed = time.time() - t0
    answer = result["answer"]
    cards = result["recommend_cards"]
    source = result["source"]
    kg_entity = result["kg_entity"]

    answer_ok = expected_kw in answer
    card_titles = [c.get("title", "")[:20] for c in cards[:3]]
    card_ok = any(expected_kw in t for t in card_titles) or "昆" in q and any("曲" in t for t in card_titles)

    status = "✓" if answer_ok else "✗"
    print(f"{status} [{elapsed:.1f}s] Q: {q[:20]}...")
    print(f"  answer: {answer[:80]}")
    print(f"  cards: {card_titles}")
    print(f"  source={source}, kg={kg_entity}")
    print()

db.close()

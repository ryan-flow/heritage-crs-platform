import sys; sys.path.insert(0, '.')
from app.core.database import get_db
from app.services.knowledge_base import search_local_knowledge

db = next(get_db())

# 测试第1轮的问题
questions = [
    '你最喜欢哪种非遗技艺？',
    '非遗研学为什么比普通参观更有参与感？',
    '非遗传承人老了之后技艺会失传吗？',
    '非遗进校园为什么不是简单办活动？',
]

for q in questions:
    result = search_local_knowledge(db, q)
    print(f'问: {q}')
    print(f'  matched={result.get("matched")} conf={result.get("confidence", 0):.2f} chapter={result.get("chapter", "?")}')
    if result.get('matched'):
        print(f'  answer(前50): {str(result.get("answer",""))[:50]}')
    print()

db.close()

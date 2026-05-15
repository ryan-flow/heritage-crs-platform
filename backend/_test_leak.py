import sys, time
sys.path.insert(0, ".")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.ai_service import ai_answer

engine = create_engine(settings.sqlite_url)
db = sessionmaker(bind=engine)()

tests = [
    "第一次看昆曲演出有什么注意事项",
    "苏绣入门可以从哪些小件绣品开始了解",
    "端午节为什么属于活态非遗",
    "中医针灸的原理是什么",
    "推荐一些传统工艺的内容",
]

for q in tests:
    t0 = time.time()
    result = ai_answer(db, q, user_id=16)
    elapsed = time.time() - t0
    answer = result["answer"]
    source = result["source"]
    strategy = result["strategy"]
    kg = result["kg_entity"]

    has_leak = any(kw in answer for kw in ["指令", "参考信息", "100字", "要求", "纠正", "思考过程"])
    is_long = len(answer) > 150
    is_repeat = answer.count(answer[:10]) > 1 if len(answer) > 10 else False

    status = "✓" if not has_leak and not is_long and not is_repeat else "✗"
    issues = []
    if has_leak: issues.append("指令泄漏")
    if is_long: issues.append(f"过长({len(answer)}字)")
    if is_repeat: issues.append("重复")

    print(f"{status} [{elapsed:.1f}s] Q: {q[:25]}")
    print(f"  answer({len(answer)}字): {answer[:120]}{'...' if len(answer)>120 else ''}")
    if issues:
        print(f"  ⚠ 问题: {', '.join(issues)}")
    print(f"  source={source}, strategy={strategy}, kg={kg}")
    print()

db.close()

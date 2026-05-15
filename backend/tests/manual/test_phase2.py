"""Phase2 测试脚本：追问连贯性+推荐去重验证"""
import sys
sys.path.insert(0, ".")
from app.core.database import SessionLocal
from app.services.ai_service import ai_answer, _build_followup_context

db = SessionLocal()
try:
    # 测试1: 追问关键词是否命中"详细"
    result1 = _build_followup_context("能详细说说吗", [
        {"type": "content", "title": "昆曲入门", "summary": "昆曲基础知识", "reason": "与用户兴趣匹配"},
    ])
    print("=== 测试1: '详细'是否触发追问 ===")
    print("is_followup:", result1["is_followup"])
    print("topic:", result1["topic"])
    print()

    # 测试2: 围绕推荐追问（已有功能，验证未破坏）
    result2 = _build_followup_context("围绕这个方向继续推荐", [
        {"type": "content", "title": "苏绣技法", "summary": "苏绣基础", "reason": "热门推荐"},
        {"type": "event", "title": "周末体验活动", "summary": "线下活动", "reason": "本地推荐"},
    ])
    print("=== 测试2: 围绕推荐追问 ===")
    print("is_followup:", result2["is_followup"])
    print("topic:", result2["topic"])
    print()

    # 测试3: 模拟完整对话——先问问题，再追问
    result3 = ai_answer(db, "昆曲是什么", user_id=None)
    print("=== 测试3: 首次回答 ===")
    print("回答:", result3["answer"][:100])
    cards = result3.get("recommend_cards", [])
    print("推荐卡片:", [c["title"] for c in cards])
    
    # 用上次推荐卡片做追问
    result4 = ai_answer(db, "继续深入了解", user_id=None, context_cards=cards if cards else None)
    print()
    print("=== 测试4: 追问回答 ===")
    print("回答:", result4["answer"][:100])
    print("策略:", result4.get("strategy", ""))

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

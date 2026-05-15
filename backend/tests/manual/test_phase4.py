"""Phase4 测试脚本：豆包参与推荐挑选"""
import sys
sys.path.insert(0, ".")
from app.core.database import SessionLocal
from app.services.ai_service import ai_answer, ai_recommend_with_context

# 测试1: 直接测试 ai_recommend_with_context
print("=== 测试1: 豆包推荐挑选 ===")
candidates = [
    {"id": 1, "type": "content", "title": "昆曲入门指南", "reason": "基础推荐"},
    {"id": 2, "type": "event", "title": "周末苏绣体验活动", "reason": "热门活动"},
    {"id": 3, "type": "topic", "title": "皮影戏讨论帖", "reason": "活跃话题"},
    {"id": 4, "type": "content", "title": "云锦工艺详解", "reason": "高评分内容"},
    {"id": 5, "type": "event", "title": "非遗音乐鉴赏会", "reason": "本周新活动"},
    {"id": 6, "type": "topic", "title": "中医针灸交流", "reason": "近期热帖"},
]
selected = ai_recommend_with_context(
    candidates=candidates,
    question="昆曲为什么被称为百戏之祖",
    strategy_name="intent_driven_rec",
)
for card in selected:
    print(f"  [{card.get('type')}] {card.get('title')} — {card.get('reason')} (ai_selected={card.get('ai_selected', False)})")

print()

# 测试2: 完整 ai_answer 集成测试
db = SessionLocal()
try:
    result = ai_answer(db, "推荐一些适合新手体验的非遗项目", user_id=None)
    print("=== 测试2: 完整集成 ===")
    print("回答:", result["answer"])
    print("策略:", result.get("strategy", ""))
    cards = result.get("recommend_cards", [])
    for card in cards:
        print(f"  [{card.get('type')}] {card.get('title')} — {card.get('reason')}")
        print(f"    ai_selected={card.get('ai_selected', False)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

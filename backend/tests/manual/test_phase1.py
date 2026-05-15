"""Phase1 测试脚本：验证AI+CRS耦合优化效果"""
import sys
sys.path.insert(0, ".")
from app.core.database import SessionLocal
from app.services.ai_service import ai_answer

db = SessionLocal()
try:
    # 测试1: 用户问本地推荐
    result = ai_answer(db, "本地有什么非遗活动推荐吗", user_id=None)
    print("=== 测试1: 本地推荐问题 ===")
    print("回答:", result["answer"])
    print("来源:", result["source"])
    print("推荐卡片数:", len(result.get("recommend_cards", [])))
    print("策略:", result.get("strategy", ""))
    print()

    # 测试2: 用户主动求推荐
    result2 = ai_answer(db, "推荐一些适合新手体验的非遗项目", user_id=None)
    print("=== 测试2: 主动求推荐 ===")
    print("回答:", result2["answer"])
    print("来源:", result2["source"])
    print("策略:", result2.get("strategy", ""))
    print()

    # 测试3: 普通知识问题（应该也有推荐卡片上下文）
    result3 = ai_answer(db, "昆曲为什么被称为百戏之祖", user_id=None)
    print("=== 测试3: 普通知识问题 ===")
    print("回答:", result3["answer"])
    print("来源:", result3["source"])
    print("推荐卡片数:", len(result3.get("recommend_cards", [])))
    has_rec = "推荐" in result3["answer"] or "帮你" in result3["answer"] or "值得看" in result3["answer"]
    print("回答中提及推荐:", has_rec)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

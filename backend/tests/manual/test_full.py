"""全流程集成测试：AI+CRS深度耦合验证"""
import sys
sys.path.insert(0, ".")
from app.core.database import SessionLocal
from app.services.ai_service import ai_answer

db = SessionLocal()
try:
    print("=" * 60)
    print("场景1: 用户问本地推荐（之前黑塔会说'不在服务范围'）")
    print("=" * 60)
    r1 = ai_answer(db, "本地有什么非遗活动推荐吗", user_id=None)
    print(f"回答: {r1['answer']}")
    print(f"策略: {r1.get('strategy', '')}")
    print(f"推荐卡片: {len(r1.get('recommend_cards', []))}张")
    has_reject = "不在" in r1["answer"] or "服务范围" in r1["answer"]
    print(f"是否拒绝: {'X 仍拒绝' if has_reject else 'OK 不再拒绝'}")
    print()

    print("=" * 60)
    print("场景2: 用户主动求推荐")
    print("=" * 60)
    r2 = ai_answer(db, "推荐一些适合新手体验的非遗项目", user_id=None)
    print(f"回答: {r2['answer']}")
    print(f"策略: {r2.get('strategy', '')}")
    cards2 = r2.get("recommend_cards", [])
    ai_sel = sum(1 for c in cards2 if c.get("ai_selected"))
    print(f"推荐卡片: {len(cards2)}张, 豆包挑选: {ai_sel}张")
    for c in cards2:
        print(f"  [{c['type']}] {c['title']} — {c['reason'][:30]}")
    print()

    print("=" * 60)
    print("场景3: 追问'能详细说说吗'（之前上下文脱节）")
    print("=" * 60)
    r3 = ai_answer(db, "能详细说说吗", user_id=None, context_cards=cards2 if cards2 else None)
    print(f"回答: {r3['answer']}")
    print(f"策略: {r3.get('strategy', '')}")
    print(f"推荐卡片: {len(r3.get('recommend_cards', []))}张")
    print()

    print("=" * 60)
    print("场景4: 围绕推荐追问")
    print("=" * 60)
    r4 = ai_answer(db, "围绕这个方向继续推荐", user_id=None, context_cards=cards2 if cards2 else None)
    print(f"回答: {r4['answer']}")
    print(f"策略: {r4.get('strategy', '')}")
    print()

    print("=" * 60)
    print("场景5: 追问建议是否与回答同时生成")
    print("=" * 60)
    r5 = ai_answer(db, "昆曲和京剧有什么区别", user_id=None)
    print(f"回答: {r5['answer'][:80]}...")
    suggestions = r5.get("rewrite_suggestions", [])
    print(f"追问建议({len(suggestions)}条): {suggestions}")
    print()

    print("=" * 60)
    print("[OK] 全流程测试完成")
    print("=" * 60)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

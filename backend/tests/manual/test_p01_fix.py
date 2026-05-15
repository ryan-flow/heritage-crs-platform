"""P0-1修复验证：_calc_explicit_score增加ASK回答增量"""
import sys
sys.path.insert(0, ".")
from app.core.database import SessionLocal
from app.services.recommendation_service import calc_confidence

db = SessionLocal()

# 测试新用户(25) - 之前有3条ASK回答但explicit没算
result = calc_confidence(db, 25)
print("=== user_id=25 修复后 ===")
print(f"confidence: {result['confidence_score']}")
print(f"explicit: {result['score_explicit']}")
print(f"implicit: {result['score_implicit']}")
print(f"dialogue: {result['score_dialogue']}")
print(f"mode: {result['mode']}")
detail_explicit = result.get("detail", {}).get("explicit", {})
print(f"detail.explicit: {detail_explicit}")

# 对比老用户(1)
result2 = calc_confidence(db, 1)
print()
print("=== user_id=1 修复后 ===")
print(f"confidence: {result2['confidence_score']}")
print(f"explicit: {result2['score_explicit']}")
print(f"implicit: {result2['score_implicit']}")
print(f"dialogue: {result2['score_dialogue']}")
print(f"mode: {result2['mode']}")

db.close()

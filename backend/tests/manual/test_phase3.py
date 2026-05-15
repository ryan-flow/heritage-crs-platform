"""Phase3 测试脚本：验证合并调用和追问建议"""
import sys
sys.path.insert(0, ".")
from app.services.ai_service import _ask_doubao_combined

# 测试1: 合并调用是否能同时返回回答+追问建议
print("=== 测试1: 合并调用 ===")
result = _ask_doubao_combined(
    question="昆曲为什么被称为百戏之祖",
    system_prompt="你是非遗导览官「黑塔」。口语化中文，100字以内。",
)
print("回答:", result.get("answer", "")[:120])
print("追问建议:", result.get("followups", []))
print()

# 测试2: 带推荐上下文的合并调用
from app.services.ai_service import _build_recommend_context_for_ai
cards = [
    {"type": "content", "title": "昆曲入门指南", "reason": "与用户兴趣匹配"},
    {"type": "event", "title": "周末昆曲体验活动", "reason": "华南地区线下活动"},
]
rec_ctx = _build_recommend_context_for_ai(cards, {"strategy": "intent_driven_rec"})

print("=== 测试2: 带推荐上下文的合并调用 ===")
result2 = _ask_doubao_combined(
    question="推荐一些昆曲相关的活动",
    context=rec_ctx,
    system_prompt="你是非遗导览官「黑塔」。口语化中文，100字以内。",
)
print("回答:", result2.get("answer", "")[:120])
print("追问建议:", result2.get("followups", []))

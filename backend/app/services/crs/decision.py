"""CRS 决策引擎

ASK-REC 五策略决策：cold_start_ask / mixed / precision / intent_driven_rec / recovery_ask
"""

import logging

from app.models.crs_session import CrsSession
from app.services.recommendation_service import _determine_mode, CRS_THRESHOLD_COLD
from app.services.crs.ask_templates import ASK_TEMPLATES, RECOMMEND_INTENT_TERMS

logger = logging.getLogger(__name__)


def _decision(strategy: str, mode: str, note: str,
              ask_prompt: str = "", ask_options: list | None = None,
              ask_id: str = "", ask_attribute: str = "", score_delta: int = 0) -> dict:
    return {
        "strategy": strategy, "mode": mode,
        "ask_prompt": ask_prompt, "ask_options": ask_options or [],
        "ask_id": ask_id, "ask_attribute": ask_attribute,
        "score_delta": score_delta, "strategy_note": note,
    }


def crs_decide(
    question: str, confidence_result: dict, session: CrsSession | None,
    rec_payload: dict, kb_result: dict, is_followup: bool = False,
) -> dict:
    q = (question or "").strip()
    c = confidence_result.get("confidence_score", 0)
    mode = confidence_result.get("mode", "cold_start")
    turn_count = (session.turn_count if session else 0) or 0

    # 追问意图 → 直接推荐
    if is_followup:
        return _decision("intent_driven_rec", mode, "围绕刚才的推荐继续探索，黑塔帮你规划下一步了解路径。")

    # 用户主动求推荐
    if any(term in q for term in RECOMMEND_INTENT_TERMS):
        return _decision("intent_driven_rec", mode, "黑塔识别到你在主动求推荐，已优先整理可直接行动的内容。")

    # 连续3轮无互动且置信度低 → 恢复ASK
    if turn_count >= 3 and c < CRS_THRESHOLD_COLD:
        ask = ASK_TEMPLATES["R01"]
        return _decision("recovery_ask", mode, "黑塔发现对话几轮了还没找到你的方向，换种方式再试试。",
                         ask["prompt"], ask["options"], "R01", ask["attribute"], ask["score_delta"])

    # 追问节奏控制：连续ASK后穿插推荐，避免疲劳
    last_ask_id = (session.last_ask_id or "") if session else ""
    consecutive_ask = last_ask_id != "" and mode == "cold_start" and turn_count > 0 and turn_count % 2 == 0

    # 冷启动纯提问
    if mode == "cold_start" and not consecutive_ask:
        ask_id = select_cold_start_ask(session)
        ask = ASK_TEMPLATES[ask_id]
        return _decision("cold_start_ask", mode, "黑塔先了解你的兴趣方向，再缩小推荐范围。",
                         ask["prompt"], ask["options"], ask_id, ask["attribute"], ask["score_delta"])

    # 冷启动偶数轮穿插推荐
    if mode == "cold_start" and consecutive_ask:
        return _decision("mixed", mode, "黑塔先给你看看当前方向的推荐内容。")

    # 混合模式
    if mode == "mixed":
        ask_id = select_mixed_ask(session, q)
        ask = ASK_TEMPLATES[ask_id]
        return _decision("mixed", mode, "黑塔一边推荐一边追问，帮你找到更精准的方向。",
                         ask["prompt"], ask["options"], ask_id, ask["attribute"], ask["score_delta"])

    # 精准推荐
    return _decision("precision", mode, "黑塔已比较了解你的偏好，直接推荐最匹配的内容。")


def select_cold_start_ask(session: CrsSession | None) -> str:
    """冷启动ASK选择：A01(类目) → A02(地区) → A03(场景) → A04(程度) → A05(备选)"""
    asked = set(session.get_asked_attributes()) if session else set()
    for attr, ask_id in [("category", "A01"), ("region", "A02"), ("scene", "A03"), ("level", "A04"), ("category", "A05")]:
        if attr not in asked or ask_id == "A05":
            return ask_id
    return "A01"


def select_mixed_ask(session: CrsSession | None, question: str) -> str:
    """混合模式ASK选择：根据当前对话内容智能选择追问方向"""
    asked = set(session.get_asked_attributes()) if session else set()
    if any(kw in question for kw in ["活动", "线下", "参加", "体验"]):
        return "B02" if "scene" not in asked else "B05"
    if any(kw in question for kw in ["地区", "地方", "哪里", "本地"]):
        return "B03" if "region" not in asked else "B01"
    if any(kw in question for kw in ["工艺", "戏曲", "民俗", "类型"]):
        return "B01" if "category" not in asked else "B04"
    return "B01"


def generate_ask_transition(ask_id: str, answer: str, is_skip: bool) -> str:
    """ASK回答 → 黑塔过渡语"""
    if is_skip:
        return "好的，我们继续。"

    template = ASK_TEMPLATES.get(ask_id, {})
    attribute = template.get("attribute", "")

    if attribute == "category":
        feedback = {
            "传统工艺": "了解了，你对手工技艺感兴趣。",
            "手工艺与技法": "了解了，你对手工技艺感兴趣。",
            "戏曲音乐": "好，戏曲和音乐类我会重点推给你。",
            "戏曲与音乐": "好，戏曲和音乐类我会重点推给你。",
            "民俗节俗": "明白了，民俗和节庆方向。",
            "节俗与信仰": "明白了，民俗和节庆方向。",
            "饮食医药": "了解，传统医药和饮食文化方向。",
            "医药与饮食": "了解，传统医药和饮食文化方向。",
            "好，从热门开始": "好的，我先带你看看最热门的几个方向。",
            "随便推荐": "好，我来帮你挑几个有意思的。",
        }
        return feedback.get(answer, f"记下了——{answer}，我来帮你找这个方向的内容。")

    if attribute == "region":
        return f"明白，{answer}风格的非遗，我来找找。"

    if attribute == "scene":
        feedback = {
            "从内容科普开始": "好，先从了解知识入手。",
            "找线下活动": "明白，我帮你留意附近的活动。",
            "看看社区讨论": "好的，社区里有不少有趣的话题。",
            "继续了解当前话题": "好，我们接着聊。",
            "看看推荐内容": "好，我帮你整理几篇值得看的内容。",
            "找线下活动参加": "好，我帮你找找附近可以参加的活动。",
        }
        return feedback.get(answer, "好的，记住了。")

    if attribute == "level":
        feedback = {
            "完全陌生，从头了解": "没关系，我从基础讲起。",
            "有点了解，想深入": "好，我会推荐更深入的内容。",
            "比较熟悉，找新方向": "了解，帮你开拓新视野。",
        }
        return feedback.get(answer, "好的，记住了。")

    return f"好的，已记住——{answer}。"

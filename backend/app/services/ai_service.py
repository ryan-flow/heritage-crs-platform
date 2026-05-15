"""AI问答服务

五级回退策略：KB润色 → 豆包直答 → 联网+豆包 → 兜底
CRS对话推荐：基于3维置信度的ASK-REC状态机
"""

from sqlalchemy.orm import Session
import json
import random
import re
import uuid
import logging

from app.models.ai_qa_log import AIQALog
from app.models.crs_session import CrsSession
from app.models.user import User
from app.core.config import settings
from app.services.doubao_client import ask_doubao, ask_doubao_stream
from app.services.knowledge_base import search_local_knowledge
from app.services.recommendation_service import (
    generate_ai_recommend_cards,
    generate_recommendation_payload,
    calc_confidence,
    _safe_json_loads,
    _determine_mode,
    CRS_THRESHOLD_COLD,
    CRS_THRESHOLD_MIXED,
)
from app.services.knowledge_graph import kg_service
from app.services.web_search_service import search_web_brief

from app.services.crs.session import (
    get_or_create_session as _get_or_create_session,
    update_session_mode as _update_session_mode,
    process_ask_answer,
)
from app.services.crs.decision import crs_decide as _crs_decide
from app.services.crs.preference import (
    append_preference as _append_preference,
    apply_answer_to_preference as _apply_answer_to_preference,
    sync_kg_entity_to_preference as _sync_kg_entity_to_preference,
    sync_kb_chapter_to_preference as _sync_kb_chapter_to_preference,
    sync_question_to_preferences as _sync_question_to_preferences,
    auto_create_ask_log as _auto_create_ask_log,
)
from app.services.crs.questions import (
    generate_recommended_questions as _generate_recommended_questions,
    rewrite_suggestions as _rewrite_suggestions,
)
from app.services.crs.constants import (
    VAGUE_FOLLOWUP_MAX_LEN,
    HISTORY_TRUNCATE_LEN,
    AI_DIALOG_SCORE_DELTA,
    SPECIFIC_TERMS,
    CONTENT_CHAPTERS,
    KG_ENTITY_HINTS,
)
from app.services.crs.ask_templates import (
    ASK_TEMPLATES,
    SKIP_ANSWERS,
    RECOMMEND_INTENT_TERMS,
    CLARIFY_TERMS,
)
from app.services.crs.mappings import (
    OPTION_TO_PREFERENCE,
    KG_ENTITY_TO_CATEGORY,
    KB_CHAPTER_TO_PREFERENCE,
    QUESTION_HERITAGE_MAP,
    QUESTION_SCENE_MAP,
    QUESTION_REGION_MAP,
)

logger = logging.getLogger(__name__)

FALLBACK_ANSWERS = {
    "阶段": (
        "中国非遗保护大体经历了抢救记录、名录体系建设、法治化推进和活化传播四个阶段。"
        "早期重在普查与抢救，随后建立分级名录与传承人制度，"
        "2011年《非遗法》实施后进入制度化保护，近年更强调数字化传播与创新转化。"
    ),
}

REWRITE_SYSTEM_PROMPT = (
    "你是非遗导览官「黑塔」。基于参考信息润色重写回答。"
    "要求：紧扣参考信息的事实回答，不要自由发挥推荐参考信息之外的内容方向。"
    "事实准确、口语自然、100字以内、不用编号和Markdown、不提'参考信息'。"
    "直接输出回答，不要复述指令、不要自我纠正、不要暴露思考过程。"
    "你可以推荐平台的非遗内容文章、线下体验活动和社区讨论话题，但不要承诺纪录片、线下场馆参观、课程报名等平台不提供的功能。"
    "如果用户问本地活动或线下体验推荐，请积极告知可以在下方推荐卡片中查看附近的非遗体验活动，不要说'不在服务范围'。"
)

DIRECT_ANSWER_SYSTEM_PROMPT = (
    "你是非遗导览官「黑塔」，温润专业。只答非遗相关问题，超出范围礼貌引导。"
    "口语化中文，100字以内，不用编号和Markdown。严禁编造事实。"
    "直接输出回答，不要复述指令、不要自我纠正、不要暴露思考过程。"
    "你可以推荐平台的非遗内容文章、线下体验活动和社区讨论话题，但不要承诺纪录片、线下场馆参观、课程报名等平台不提供的功能。"
    "如果用户问本地活动或线下体验推荐，请积极告知可以在下方推荐卡片中查看附近的非遗体验活动，不要说'不在服务范围'。"
)


def _load_recent_history(db: Session, user_id: int, limit: int = 3) -> list[dict]:
    """从AIQALog加载最近N轮对话，组装为messages格式

    返回: [{"role": "user", "content": "问题"}, {"role": "assistant", "content": "回答"}, ...]
    每条截取前120字，避免token过长。跳过ASK选项点击（问题以ASK_ID:开头）。
    """
    if not user_id:
        return []
    logs = (
        db.query(AIQALog)
        .filter(AIQALog.user_id == user_id, AIQALog.answer.isnot(None), AIQALog.answer != "")
        .order_by(AIQALog.id.desc())
        .limit(limit * 2)
        .all()
    )
    if not logs:
        return []
    # 倒序→正序，取最近limit轮
    logs = list(reversed(logs[-(limit * 2):]))
    messages = []
    for log in logs:
        q = (log.question or "").strip()
        a = (log.answer or "").strip()
        if not q or not a:
            continue
        # 跳过ASK选项点击
        if q.startswith("ASK_"):
            continue
        messages.append({"role": "user", "content": q[:HISTORY_TRUNCATE_LEN]})
        messages.append({"role": "assistant", "content": a[:HISTORY_TRUNCATE_LEN]})
    return messages


# L4：追问意图检测 + 推荐卡片上下文构建

_FOLLOWUP_KEYWORDS = [
    "围绕", "继续", "下一步", "深入", "展开", "详细讲讲",
    "还能怎么", "还有什么", "顺着", "沿着", "延伸",
    "详细", "再说", "多说", "讲讲", "具体",
    "为什么", "怎么", "如何", "哪些", "什么区别",
    "还有", "其他", "呢", "吗",
]

_FOLLOWUP_TOPIC_TEMPLATES = [
    "你刚才推荐了关于「{topic}」的内容，请根据这些推荐给出下一步深入了解的建议",
    "基于刚才的{topic}推荐，帮我规划一个了解路径",
    "我看了你推荐的{topic}相关内容，接下来还值得了解什么",
]


def _detect_vague_followup(question: str, db: Session, user_id: int | None, last_log: AIQALog | None = None) -> dict:
    """检测短追问（无明确话题），从上一轮AI回答提取主题上下文

    当用户输入很短且不含明确话题时，从AIQALog提取上轮问答，
    让豆包知道"详细说说"的对象是什么。

    Args:
        last_log: 可选，外部已加载的最近一条AIQALog，避免重复查询

    Returns:
        {"is_vague": bool, "context_text": str}
    """
    if not user_id or not question:
        return {"is_vague": False, "context_text": ""}

    q = question.strip()

    if len(q) > VAGUE_FOLLOWUP_MAX_LEN:
        return {"is_vague": False, "context_text": ""}

    has_vague_kw = any(kw in q for kw in _FOLLOWUP_KEYWORDS)
    if not has_vague_kw:
        return {"is_vague": False, "context_text": ""}

    try:
        log = last_log if last_log is not None else (
            db.query(AIQALog)
            .filter(AIQALog.user_id == user_id)
            .order_by(AIQALog.id.desc())
            .first()
        )
        if not log:
            return {"is_vague": False, "context_text": ""}

        last_q = (log.question or "").strip()
        last_a = (log.answer or "").strip()
        if not last_q:
            return {"is_vague": False, "context_text": ""}

        context_text = (
            f"用户上一轮的问题是：「{last_q[:60]}」，你的回答是：「{last_a[:HISTORY_TRUNCATE_LEN]}」。\n"
            f"用户现在追问「{q}」，请基于上一轮的话题来回答，不要说'请告诉我具体项目'之类的话。"
        )
        return {"is_vague": True, "context_text": context_text}
    except Exception:
        return {"is_vague": False, "context_text": ""}


def _build_followup_context(question: str, context_cards: list[dict] | None) -> dict:
    """检测追问意图，构建推荐卡片上下文

    Returns:
        {
            "is_followup": bool,
            "topic": str,          # 上轮推荐的主题词，用于推荐查询
            "context_text": str,   # 注入豆包的上下文文本
        }
    """
    if not context_cards or not question:
        return {"is_followup": False, "topic": "", "context_text": ""}

    q = question.strip()

    # 检测追问意图
    is_followup = any(kw in q for kw in _FOLLOWUP_KEYWORDS)
    if not is_followup:
        return {"is_followup": False, "topic": "", "context_text": ""}

    # 从推荐卡片中提取主题信息
    topics = []
    card_summaries = []

    for card in (context_cards or [])[:3]:
        title = card.get("title", "").strip()
        summary = card.get("summary", "").strip()
        reason = card.get("reason", "").strip()
        card_type = card.get("type", "")

        if title:
            topics.append(title)

        # 组装每张卡片的摘要
        parts = [f"【{card_type}】{title}"]
        if summary:
            parts.append(summary[:80])
        if reason:
            parts.append(f"推荐理由：{reason[:60]}")
        card_summaries.append("，".join(parts))

    if not topics:
        return {"is_followup": False, "topic": "", "context_text": ""}

    # 主题：取第一张卡片标题
    topic = topics[0]

    # 构建给豆包的上下文
    context_lines = [
        "用户刚才收到了以下推荐内容，现在希望围绕这些推荐继续深入了解：",
        "",
    ]
    for i, summary in enumerate(card_summaries, 1):
        context_lines.append(f"{i}. {summary}")
    context_lines.append("")
    context_lines.append("请根据以上推荐内容，告诉用户接下来可以怎么深入了解相关非遗项目。")

    return {
        "is_followup": True,
        "topic": topic,
        "context_text": "\n".join(context_lines),
    }


def _build_crs_aware_prompt(
    crs_mode: str,
    rec_payload: dict | None,
    kb_result: dict | None,
) -> str:
    """根据CRS模式和用户画像生成动态system prompt

    - cold_start：简洁介绍，引发好奇
    - mixed：结合画像方向，适度引导
    - precision：结合用户偏好精准回答
    """
    profile = (rec_payload or {}).get("profile_summary") or {}
    heritage_terms = profile.get("heritage_terms") or []
    scene_terms = profile.get("scene_terms") or []
    top_heritage = ", ".join(heritage_terms[:3]) if heritage_terms else ""
    top_scene = ", ".join(scene_terms[:2]) if scene_terms else ""

    parts = ["你是非遗导览官「黑塔」，温润专业。只答非遗相关问题，超出范围礼貌引导。"]
    parts.append("口语化中文，100字以内，不用编号和Markdown。严禁编造事实。")
    parts.append("直接输出回答，不要复述指令、不要自我纠正、不要暴露思考过程。")
    parts.append("你可以推荐平台的非遗内容文章、线下体验活动和社区讨论话题，但不要承诺纪录片、线下场馆参观、课程报名等平台不提供的功能。")
    parts.append("如果用户问本地活动或线下体验推荐，请告知可以在下方推荐卡片中查看，不要拒绝。")

    if crs_mode == "cold_start":
        if top_heritage:
            parts.append(f"用户刚接触非遗，目前对{top_heritage}有初步兴趣，回答要浅显易懂、引发好奇心。")
        else:
            parts.append("用户刚开始了解非遗，回答要浅显易懂，多给正面鼓励。")
    elif crs_mode == "mixed":
        if top_heritage:
            parts.append(f"用户对{top_heritage}已有初步了解，可以适当深入，结合{top_scene or '知识阅读'}场景引导。")
        else:
            parts.append("用户正在探索非遗方向，回答兼顾知识性和趣味性。")
    elif crs_mode == "precision":
        if top_heritage:
            parts.append(f"用户偏好方向：{top_heritage}。围绕用户当前问题回答，不要主动推荐其他方向的内容。")
        else:
            parts.append("用户对非遗已有较深了解，回答可以更专业深入。")

    # KB命中的章节信息也注入，帮助模型知道当前讨论的话题分类
    kb_chapter = (kb_result or {}).get("chapter", "")
    if kb_chapter and kb_chapter not in ("", "其他"):
        parts.append(f"当前话题分类：{kb_chapter}。")

    return "\n".join(parts)


def _build_recommend_context_for_ai(
    recommend_cards: list[dict],
    strategy_payload: dict,
    user_question: str = "",
) -> str:
    """将推荐卡片信息翻译成豆包能理解的上下文，让AI文本和推荐卡片协同输出。

    核心改动：豆包从此知道系统已推荐了什么卡片，
    不再说"我没法推荐"，而是自然引出推荐内容。

    v2.1增强：识别追问场景，明确告知豆包用户在追问哪张卡片。
    """
    if not recommend_cards:
        return ""

    # 识别追问关键词
    is_followup = any(kw in user_question for kw in _FOLLOWUP_KEYWORDS)

    type_labels = {"content": "内容文章", "event": "线下活动", "topic": "社区讨论"}
    lines = ["[系统提示] 下方已展示以下推荐卡片，你可在回答中自然提及："]

    for i, card in enumerate(recommend_cards[:3], 1):
        card_type = type_labels.get(card.get("type", ""), card.get("type", ""))
        title = card.get("title", "")
        if is_followup and i == 1:
            line = f"  {i}. 【{card_type}】{title} ← 用户正在追问"
        else:
            line = f"  {i}. 【{card_type}】{title}"
        lines.append(line)

    strategy_name = strategy_payload.get("strategy", "")

    if is_followup:
        lines.append("请针对第1项展开介绍。")
    elif strategy_name == "intent_driven_rec":
        lines.append("用户主动求推荐，自然引出这些推荐。")
    elif strategy_name == "precision":
        lines.append("自然提及推荐即可。")
    elif strategy_name == "mixed":
        lines.append("适度提及推荐。")

    return "\n".join(lines)


def _extract_kg_entity(question: str, rec_payload: dict) -> str:
    q = (question or "").strip()
    for entity in KG_ENTITY_HINTS:
        if entity in q:
            return entity
    profile_summary = (rec_payload or {}).get("profile_summary") or {}
    for term in profile_summary.get("heritage_terms") or []:
        if term in KG_ENTITY_HINTS:
            return term
    return ""


def _inject_kg_reason(cards: list[dict], kg_similar: dict, kg_expand: dict) -> list[dict]:
    """将KG推理结果注入推荐卡片的 explain.kg_context（L4层）

    不再修改 reason 字符串，保持 L1 用户可读理由的纯粹性。
    KG信息统一归入 explain.kg_context 子字典。
    """
    if not cards:
        return cards
    similar_items = (kg_similar or {}).get("items") or []
    expand_items = (kg_expand or {}).get("items") or []

    similar_names = [item.get("entity", "") for item in similar_items[:3] if item.get("entity")]
    top_expand = expand_items[0] if expand_items else {}
    path = top_expand.get("path") or []
    kg_reason = top_expand.get("reason") or ""
    kg_score = top_expand.get("score") if isinstance(top_expand, dict) else None
    kg_path_text = " → ".join(path[:4]) if path else ""

    # 无KG数据则跳过
    if not similar_names and not kg_path_text:
        return cards

    # ── L4：KG推理上下文 ──
    kg_context = {
        "similar_entities": similar_names,
        "expand_path": kg_path_text,
        "kg_reason": kg_reason,
        "kg_score": kg_score if kg_score is not None else 0,
    }

    for card in cards:
        explain = (card or {}).get("explain") or {}
        if not explain:
            explain = {
                "match_score": round((card.get("id") or 0) % 10 / 10 + 0.6, 2),
                "novelty_score": 0.6,
                "diversity_penalty": 0.0,
                "final_score": round((card.get("id") or 0) % 10 / 10 + 1.2, 2),
            }
        # 注入L4 KG上下文
        explain["kg_context"] = kg_context
        # 兼容：保留顶层 kg_reason/kg_score/kg_path_text 供旧前端读取
        explain["kg_reason"] = kg_reason
        explain["kg_score"] = kg_score if kg_score is not None else 0
        explain["kg_path_text"] = kg_path_text
        card["explain"] = explain
        # 不再修改 reason 字符串（保持L1纯粹）

    return cards


def _normalize_answer_text(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"来源[：:]\s*豆包方舟模型生成[（(]仅供参考[）)]", "", text)
    cleaned = cleaned.replace("##", "")
    lines = []
    for line in cleaned.splitlines():
        l = line.strip()
        if not l:
            lines.append("")
            continue
        if re.search(r"(来源|仅供参考|豆包|方舟模型)", l):
            continue
        lines.append(l)
    cleaned = "\n".join(lines).strip()
    if len(cleaned) > 500:
        cleaned = cleaned[:500].rstrip("，,;；。.!！?？") + "。"
    return cleaned


def _build_recommend_fallback_answer(question: str, recommend_cards: list[dict]) -> str:
    """当生成式回答失败但已有推荐卡片时，转成可读回答。"""
    cards = [c for c in (recommend_cards or []) if c.get("title")]
    if not cards:
        return ""

    q = (question or "").strip()
    first = cards[0].get("title", "")
    second = cards[1].get("title", "") if len(cards) > 1 else ""

    if any(term in q for term in ["先看", "看什么", "先了解", "适合"]):
        if second:
            return f"如果你想从这个方向入门，建议先看《{first}》，再接着了解《{second}》。我也给你整理了相关活动和讨论，可以直接往下看。"
        return f"如果你想从这个方向入门，建议先看《{first}》。我也给你整理了相关活动和讨论，可以直接往下看。"

    if second:
        return f"这个问题我先用推荐内容带你进入主题：可以先看《{first}》，再补充了解《{second}》。下面还有相关活动和讨论可继续看。"
    return f"这个方向可以先从《{first}》开始看起。下面我也给你准备了相关活动和讨论。"


def _extract_json(raw: str, expect_array: bool = False) -> dict | list | None:
    """从豆包回复中提取JSON，兼容```json包裹和纯文本"""
    if not raw:
        return None
    json_str = raw.strip()
    if "```json" in json_str:
        json_str = json_str.split("```json", 1)[-1].split("```", 1)[0]
    elif "```" in json_str:
        json_str = json_str.split("```", 1)[-1].split("```", 1)[0]
    bracket = ("[", "]") if expect_array else ("{", "}")
    start = json_str.find(bracket[0])
    end = json_str.rfind(bracket[1]) + 1
    if start >= 0 and end > start:
        try:
            return json.loads(json_str[start:end])
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def _ask_doubao_with_fallback(
    question: str,
    history: list[dict] | None = None,
    context: str | None = None,
    system_prompt: str | None = None,
) -> str:
    """带兜底的豆包调用，异常时返回空字符串而不是抛错。"""
    if not settings.doubao_api_key:
        return ""
    try:
        return ask_doubao(
            question=question,
            history=history,
            context=context,
            system_prompt=system_prompt,
            max_tokens=120,
            temperature=0.5,
        )
    except Exception as e:
        logger.error("豆包调用失败: %s", e)
        return ""


def _ask_doubao_combined(
    question: str,
    history: list[dict] | None = None,
    context: str | None = None,
    system_prompt: str | None = None,
) -> dict:
    """一次豆包调用同时返回回答和追问建议，减少API调用次数"""

    combined_prompt = (system_prompt or DIRECT_ANSWER_SYSTEM_PROMPT)
    combined_prompt += (
        "\n\n[输出格式要求] 请严格按以下JSON格式输出，不要输出其他内容：\n"
        '{"answer": "你的回答（100字以内）", "followups": ["追问建议1", "追问建议2", "追问建议3"]}\n'
        "追问建议要求：每个不超过20字，与用户话题紧密相关，有深度，不重复已问内容。"
    )

    raw = ""
    if not settings.doubao_api_key:
        return {"answer": "", "followups": []}
    try:
        raw = ask_doubao(
            question=question,
            history=history,
            context=context,
            system_prompt=combined_prompt,
            max_tokens=250,
            temperature=0.5,
        )
    except Exception as e:
        logger.error("豆包合并调用失败: %s", e)
        return {"answer": "", "followups": []}

    if not raw:
        return {"answer": "", "followups": []}

    parsed = _extract_json(raw)
    if isinstance(parsed, dict):
        answer = parsed.get("answer", "")
        followups = parsed.get("followups", [])
        if isinstance(followups, list) and answer:
            return {"answer": answer, "followups": [str(f) for f in followups if f][:4]}

    return {"answer": raw, "followups": []}


def ai_recommend_with_context(
    candidates: list[dict],
    question: str,
    chat_history: list[dict] | None = None,
    strategy_name: str = "",
) -> list[dict]:
    """基于对话上下文从推荐候选集中挑选最相关的，生成自然推荐语

    本地排序策略：按标题与当前问题的关键词重叠度打分，
    避免二次豆包API调用（节省~4s响应时间）。
    """
    if not candidates:
        return []

    q_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,}', question))
    q_chars = set(question)
    scored = []
    for c in candidates:
        title = c.get("title", "")
        reason = c.get("reason", "")
        text = f"{title}{reason}"
        kw_hits = sum(1 for kw in q_keywords if kw in text)
        char_overlap = sum(1 for ch in text if ch in q_chars)
        scored.append((kw_hits * 10 + char_overlap, c))

    scored.sort(key=lambda x: -x[0])
    top = [c for _, c in scored[:3]]

    for c in top:
        if not c.get("reason") or len(c["reason"]) < 4:
            t = c.get("type", "")
            if t == "content":
                c["reason"] = "这篇内容很适合你"
            elif t == "event":
                c["reason"] = "有相关线下体验活动"
            elif t == "topic":
                c["reason"] = "社区里有相关讨论"
            else:
                c["reason"] = "推荐看看"

    return top


def _generate_answer(
    q: str,
    kb_result: dict,
    vague_followup: dict,
    followup_context: dict,
    rec_context_for_ai: str,
    chat_history: list[dict],
    dynamic_prompt: str,
    recommend_cards: list[dict],
) -> tuple[str, str, float, list[str]]:
    """五级回退策略生成回答

    L1: KB润色 → L2: 豆包参考KB → L3: 豆包直答 → L4: 联网+豆包 → L5: 兜底
    Returns: (answer, source, confidence, combined_followups)
    """
    answer = ""
    source = "doubao"
    confidence = 0.80
    combined_followups = []

    kb_matched = kb_result.get("matched", False)
    kb_confidence = kb_result.get("confidence", 0)
    kb_answer = kb_result.get("answer", "")

    if kb_matched and kb_confidence >= 0.8:
        logger.info("KB命中(conf=%.2f)，交由豆包润色", kb_confidence)
        raw_kb = kb_answer[:400]
        kb_context = f"参考回答：\n{raw_kb}"
        if vague_followup["is_vague"]:
            kb_context = vague_followup.get("context_text", "") + "\n\n参考知识库：\n" + raw_kb
        if rec_context_for_ai:
            kb_context = rec_context_for_ai + "\n\n" + kb_context
        answer = _ask_doubao_with_fallback(
            question=q, history=chat_history,
            context=kb_context, system_prompt=REWRITE_SYSTEM_PROMPT,
        )
        if answer:
            source = "kb_enhanced"
            confidence = 0.92
        else:
            answer = _normalize_answer_text(kb_answer)
            source = "local_kb"
            confidence = kb_confidence

    elif kb_matched and kb_confidence >= 0.45:
        logger.info("KB低置信度命中(conf=%.2f)，豆包参考回答", kb_confidence)
        raw_kb = kb_answer[:300]
        context_text = f"参考内容（可能不准确）：\n{raw_kb}" if raw_kb else None
        if vague_followup["is_vague"]:
            context_text = vague_followup.get("context_text", "")
        if rec_context_for_ai:
            context_text = (rec_context_for_ai + "\n\n" + (context_text or "")).strip()
        answer = _ask_doubao_with_fallback(
            question=q, history=chat_history,
            context=context_text, system_prompt=dynamic_prompt,
        )
        if answer:
            source = "doubao"
            confidence = 0.78
        else:
            answer = _normalize_answer_text(kb_answer)
            source = "local_kb"
            confidence = kb_confidence

    else:
        logger.info("KB未命中，豆包合并调用（回答+追问建议）")
        extra_context = None
        if followup_context["is_followup"]:
            extra_context = followup_context.get("context_text", "")
        elif vague_followup["is_vague"]:
            extra_context = vague_followup.get("context_text", "")
        if rec_context_for_ai:
            extra_context = (rec_context_for_ai + "\n\n" + (extra_context or "")).strip()
        combined = _ask_doubao_combined(
            question=q, history=chat_history,
            context=extra_context, system_prompt=dynamic_prompt,
        )
        answer = combined.get("answer", "")
        combined_followups = combined.get("followups", [])
        if answer:
            source = "doubao"
            confidence = 0.75
        else:
            logger.info("豆包失败，尝试联网搜索")
            web_brief = ""
            try:
                web_brief = search_web_brief(q)
            except Exception:
                web_brief = ""

            if web_brief:
                answer = _ask_doubao_with_fallback(
                    question=q, history=chat_history,
                    context=f"以下是网络搜索到的信息：\n{web_brief[:500]}",
                    system_prompt=dynamic_prompt,
                )
                if answer:
                    source = "web_enhanced"
                    confidence = 0.65
                else:
                    answer = _normalize_answer_text(f"我已为你联网补充信息：{web_brief}")
                    source = "web_search"
                    confidence = 0.52

            if not answer:
                fallback = FALLBACK_ANSWERS.get("阶段") if ("阶段" in q or "历程" in q) else ""
                if not fallback:
                    fallback = _build_recommend_fallback_answer(q, recommend_cards)
                if not fallback:
                    fallback = "抱歉，暂时无法回答这个问题，请换一种方式提问，或浏览推荐内容发现感兴趣的方向。"
                answer = _normalize_answer_text(fallback)
                source = "fallback"
                confidence = 0.25

    return answer, source, confidence, combined_followups


def ai_answer(db: Session, question: str, user_id: int | None = None, context_cards: list[dict] | None = None) -> dict:
    """AI问答主入口

    策略层级：
    L1: 五级回退（KB润色 → 豆包直答 → 联网+豆包 → 兜底）
    L2: CRS对话策略（ASK-REC状态机驱动）
    L3: KG图谱增强（实体识别→相似推荐→路径解释）
    L4: 追问感知（围绕推荐卡片生成下一步建议）
    """
    q = (question or "").strip()

    last_log = None
    if user_id:
        last_log = db.query(AIQALog).filter(AIQALog.user_id == user_id).order_by(AIQALog.id.desc()).first()

    vague_followup = _detect_vague_followup(q, db, user_id, last_log=last_log)
    followup_context = _build_followup_context(q, context_cards)
    rec_query = followup_context["topic"] if followup_context["is_followup"] else q
    kb_result = search_local_knowledge(db, rec_query)
    kb_matched = kb_result.get("matched", False)

    user = db.query(User).filter(User.id == user_id).first() if user_id else None
    if user and q:
        if _sync_question_to_preferences(user, q):
            logger.info("问题→偏好反哺画像: user=%s, question='%s'", user_id, q[:30])
        if kb_matched:
            kb_chapter = kb_result.get("chapter", "")
            if kb_chapter and _sync_kb_chapter_to_preference(user, kb_chapter):
                logger.info("KB章节反哺画像: user=%s, chapter=%s", user_id, kb_chapter)
            _auto_create_ask_log(db, user_id, q, kb_result)

    rec_payload = generate_recommendation_payload(db, user_id, context_text=rec_query, scene="ai")

    kg_entity = _extract_kg_entity(q, rec_payload)
    if user and kg_entity and _sync_kg_entity_to_preference(user, kg_entity):
        logger.info("KG实体→偏好自动更新: user=%s, entity=%s", user_id, kg_entity)

    crs_session = None
    confidence_result = {"confidence_score": 0, "mode": "cold_start", "dimensions": {}}
    if user_id:
        crs_session = _get_or_create_session(db, user_id)
        confidence_result = calc_confidence(db, user_id)
        _update_session_mode(db, crs_session, confidence_result["confidence_score"])

    strategy_payload = _crs_decide(q, confidence_result, crs_session, rec_payload, kb_result, is_followup=followup_context["is_followup"])
    prefer_hot_cards = strategy_payload.get("strategy") in ("cold_start_ask", "recovery_ask") or confidence_result.get("mode") == "cold_start"
    recommend_cards = generate_ai_recommend_cards(
        db, user_id, rec_query,
        rec_payload=rec_payload, prefer_hot=prefer_hot_cards,
    )

    chat_history = _load_recent_history(db, user_id, limit=3) if user_id else []

    kg_similar = {"entity": "", "items": []}
    kg_expand = {"entity": "", "depth": 2, "items": []}
    kg_path = {"from": "", "to": "", "distance": -1, "path": []}
    if kg_entity:
        kg_similar = kg_service.similar_entities(kg_entity, limit=3)
        kg_expand = kg_service.expand_recommendations(kg_entity, depth=2, limit=5)
        if kg_similar.get("items"):
            first_similar = kg_similar["items"][0].get("entity", "")
            if first_similar:
                kg_path = kg_service.shortest_path(kg_entity, first_similar)
        recommend_cards = _inject_kg_reason(recommend_cards, kg_similar, kg_expand)

    if recommend_cards and len(recommend_cards) > 1 and strategy_payload.get("strategy") in ("intent_driven_rec", "precision", "mixed"):
        try:
            recommend_cards = ai_recommend_with_context(
                candidates=recommend_cards, question=q,
                chat_history=chat_history, strategy_name=strategy_payload["strategy"],
            )
        except Exception as e:
            logger.warning("豆包推荐挑选失败，使用原始排序: %s", e)

    crs_mode = confidence_result.get("mode", "cold_start")
    dynamic_prompt = _build_crs_aware_prompt(crs_mode, rec_payload, kb_result)
    rec_context_for_ai = _build_recommend_context_for_ai(recommend_cards, strategy_payload, user_question=q)

    answer, source, confidence, _combined_followups = _generate_answer(
        q, kb_result, vague_followup, followup_context,
        rec_context_for_ai, chat_history, dynamic_prompt, recommend_cards,
    )

    answer = _normalize_answer_text(answer)

    strategy_name = strategy_payload["strategy"]
    max_cards = {
        "cold_start_ask": 2, "recovery_ask": 2, "mixed": 2,
        "intent_driven_rec": 3, "precision": 3,
    }.get(strategy_name, 2)
    if len(recommend_cards) > max_cards:
        recommend_cards = recommend_cards[:max_cards]

    result = {
        "source": source,
        "answer": answer,
        "confidence": confidence,
        "searching_web": source in ("web_search", "web_enhanced"),
        "rewrite_suggestions": _combined_followups if _combined_followups else (_rewrite_suggestions(q, answer[:80] if answer else "", chat_history)),
        "recommend_cards": recommend_cards,
        "recommend_payload": rec_payload,
    }

    strategy_display_map = {
        "cold_start_ask": "冷启动提问", "mixed": "推荐+追问",
        "precision": "精准推荐", "intent_driven_rec": "意图驱动推荐",
        "recovery_ask": "恢复提问",
    }
    result["strategy"] = strategy_name
    result["strategy_display"] = strategy_display_map.get(strategy_name, strategy_name)
    result["strategy_note"] = strategy_payload["strategy_note"]
    result["ask_prompt"] = strategy_payload["ask_prompt"]
    result["ask_options"] = strategy_payload["ask_options"]
    result["ask_id"] = strategy_payload["ask_id"]
    result["ask_attribute"] = strategy_payload["ask_attribute"]
    result["crs_mode"] = strategy_payload["mode"]
    confidence_result["dimensions"] = {
        "explicit": confidence_result.get("score_explicit", 0),
        "implicit": confidence_result.get("score_implicit", 0),
        "dialogue": confidence_result.get("score_dialogue", 0),
    }
    result["crs_confidence"] = confidence_result
    result["crs_session_id"] = crs_session.session_id if crs_session else ""
    result["kg_entity"] = kg_entity
    result["kg_similar"] = kg_similar
    result["kg_expand"] = kg_expand
    result["kg_path"] = kg_path

    kb_chapter = kb_result.get("chapter") if kb_matched else None
    prev_qs_for_exclude = [q] if q else []
    for h in (chat_history or []):
        if h.get("role") == "user" and h.get("content"):
            prev_qs_for_exclude.append(h["content"])
    recommended_questions = _generate_recommended_questions(
        strategy_name, confidence_result.get("mode", "cold_start"), q, answer,
        db=db, user_id=user_id, kb_chapter=kb_chapter,
        prev_questions=prev_qs_for_exclude,
    )
    if recommended_questions:
        result["recommended_questions"] = recommended_questions

    db.add(AIQALog(user_id=user_id, question=q, answer=result["answer"], source=result["source"], confidence=result["confidence"]))
    db.commit()
    return result

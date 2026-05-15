"""推荐系统核心引擎

职责：
1. 构建用户画像（偏好画像 + 浏览记录 + AI提问 + 报名行为 + 社区互动）
2. 内容/活动/话题三路推荐评分
3. 推荐理由生成 + 策略摘要
4. AI对话场景推荐卡片
"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.activity_registration import ActivityRegistration
from app.models.ai_qa_log import AIQALog
from app.models.content import Content
from app.models.discussion_comment import DiscussionComment
from app.models.discussion_extra import DiscussionFavorite, DiscussionTopicTag
from app.models.discussion_like import DiscussionLike
from app.models.discussion_topic import DiscussionTopic
from app.models.recommend_log import RecommendLog
from app.models.user import User

# ═══════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════

HERITAGE_KEYWORDS = [
    "戏曲", "工艺", "节俗", "传统音乐", "传统舞蹈",
    "传统美术", "传统技艺", "民俗", "昆曲", "古琴",
    "皮影", "云锦", "书法", "节气",
    "医药", "针灸", "中药", "茶艺", "饮食",
]

REGION_KEYWORDS = [
    "华南", "华东", "华北", "西南", "西北", "东北",
    "江苏", "浙江", "北京", "福建", "广东", "四川",
]

VALID_SCENES = {"home", "content", "activity", "discussion", "ai"}

# 行为权重：expose=被动曝光，click=主动点击，view=深度阅读
ACTION_WEIGHTS = {"expose": 0.35, "click": 1.2, "view": 1.6}

# 已看惩罚：不同目标类型扣不同分
SEEN_PENALTY = {"content": 12.0, "event": 10.0, "topic": 8.0}

# 场景加权：当推荐类型与场景匹配时加2.2，不匹配时减0.2
SCENE_BONUS_MAP = {
    "content":    {"content": 2.2, "event": -0.2, "topic": -0.2},
    "activity":   {"content": -0.2, "event": 2.2, "topic": -0.2},
    "discussion": {"content": -0.2, "event": -0.2, "topic": 2.2},
    "ai":         {"content": 0.6, "event": 0.6, "topic": 0.6},
}

# 新鲜度标签
FRESHNESS_LABELS = [
    (7, "近期上新"),
    (30, "最近值得看"),
    (9999, "持续热门"),
]

# 异常标题过滤
SKIP_TITLE_PATTERNS = [
    "测试", "test", "唐开", "兰有祥", "样例",
    "placeholder", "占位", "xxx", "undefined", "null",
]

# 明确实体词：用户问到这些词时，优先召回命中实体本身的候选
EXPLICIT_ENTITY_KEYWORDS = [
    "剪纸", "中国剪纸", "昆曲", "京剧", "苏绣", "湘绣", "蜀绣", "粤绣",
    "皮影", "皮影戏", "古琴", "云锦", "书法", "端午", "节气", "针灸",
    "太极", "陶瓷", "紫砂", "年画", "扎染", "蜡染",
]

# ═══════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════

def _safe_json_loads(value: str | None) -> list:
    """安全解析JSON字符串为列表"""
    if not value:
        return []
    try:
        return json.loads(value) or []
    except Exception:
        return []


def _concat_text(*parts) -> str:
    """拼接多个文本字段，空值跳过"""
    return " ".join(str(p or "") for p in parts)


def _keyword_hits(text: str, keywords: list[str]) -> list[str]:
    """从文本中命中的关键词列表"""
    return [kw for kw in keywords if kw and kw in (text or "")]


def _extract_explicit_entities(text: str) -> list[str]:
    """从当前问题中提取明确实体词，如剪纸/昆曲/苏绣"""
    source = text or ""
    return [kw for kw in EXPLICIT_ENTITY_KEYWORDS if kw in source]


def _entity_recall_bonus(text: str, explicit_entities: list[str], bonus: float = 18.0) -> tuple[float, list[str]]:
    """命中当前问题中的明确实体词时，给予强召回优先级"""
    if not explicit_entities:
        return 0.0, []
    hits = [entity for entity in explicit_entities if entity in (text or "")]
    return (bonus * len(hits), hits)



def _add_weights(bucket: dict, terms: list[str], weight: float) -> None:
    """对命中的关键词累加权重"""
    for term in terms:
        bucket[term] += weight

def _detect_scene_tags(text: str) -> list[str]:
    """从文本中识别场景标签"""
    tags = []
    if any(kw in text for kw in ["活动", "报名", "参加", "体验"]):
        tags.append("活动体验")
    if any(kw in text for kw in ["帖子", "讨论", "评论", "社区"]):
        tags.append("论坛交流")
    if any(kw in text for kw in ["专题", "内容", "文化", "阅读", "了解"]):
        tags.append("知识阅读")
    return tags


def _top_terms(profile: dict, key: str, limit: int = 2) -> list[str]:
    """取画像中权重最高的N个词条"""
    bucket = profile.get(key, {})
    return [k for k, _ in sorted(bucket.items(), key=lambda it: it[1], reverse=True)[:limit]]


def _scene_bonus(scene: str, kind: str) -> float:
    """场景加权：推荐类型与场景匹配时加分，否则减分"""
    bonus_map = SCENE_BONUS_MAP.get(scene, {})
    if bonus_map:
        return bonus_map.get(kind, 0.0)
    return 0.0


def _freshness_label(days: int) -> str:
    """根据天数返回新鲜度标签"""
    for threshold, label in FRESHNESS_LABELS:
        if days <= threshold:
            return label
    return "持续热门"


def _is_valid_title(title: str | None) -> bool:
    """过滤异常标题（测试残留、无意义标题等）"""
    if not title or not str(title).strip():
        return False
    text = str(title).strip()
    if any(p.lower() in text.lower() for p in SKIP_TITLE_PATTERNS):
        return False
    return len(text) > 3


# ═══════════════════════════════════════════════
# 用户画像构建
# ═══════════════════════════════════════════════

def build_user_profile(
    db: Session,
    user_id: int | None,
    context_text: str = "",
) -> dict:
    """构建用户画像

    整合5维信号源，生成 heritage/scene/region 三维权重向量 + 已看集合。

    Returns:
        {
            "user": User对象,
            "heritage": {"昆曲": 4.6, "工艺": 2.2, ...},
            "scene": {"知识阅读": 3.0, ...},
            "region": {"华东": 1.5, ...},
            "seen": {"content": {1,3,5}, "event": {2}, "topic": {4}},
            "sources": ["偏好画像", "浏览记录", ...]
        }
    """
    heritage = defaultdict(float)
    scene = defaultdict(float)
    region = defaultdict(float)
    seen = {"content": set(), "event": set(), "topic": set()}
    sources = []

    # ── 信号1：用户偏好画像 ──
    user = db.query(User).filter(User.id == user_id).first() if user_id else None
    if user:
        _add_weights(heritage, _safe_json_loads(user.preferred_heritage_types), 3.0)
        _add_weights(scene, _safe_json_loads(user.preferred_scene_types), 2.2)
        _add_weights(region, _safe_json_loads(user.preferred_regions), 2.0)
        if heritage or scene or region:
            sources.append("偏好画像")

    # 冷启动兜底：无偏好时默认推荐戏曲和工艺；有偏好时追加弱兜底防止偏好关键词无法命中任何内容
    if not heritage:
        _add_weights(heritage, ["戏曲", "工艺"], 1.6)
    else:
        _add_weights(heritage, ["戏曲", "工艺"], 1.0)

    # ── 信号2：当前问题上下文（权重高于历史画像，确保推荐与当前问题相关） ──
    if context_text:
        _add_weights(heritage, _keyword_hits(context_text, HERITAGE_KEYWORDS), 3.0)
        _add_weights(heritage, _extract_explicit_entities(context_text), 6.0)
        _add_weights(scene, _detect_scene_tags(context_text), 2.2)
        _add_weights(region, _keyword_hits(context_text, REGION_KEYWORDS), 2.0)
        sources.append("当前问题")

    if not user_id:
        return {
            "user": user,
            "heritage": dict(heritage),
            "scene": dict(scene),
            "region": dict(region),
            "seen": seen,
            "sources": sources,
        }

    # ── 信号3：浏览记录（RecommendLog） ──
    logs = (
        db.query(RecommendLog)
        .filter(RecommendLog.user_id == user_id)
        .order_by(RecommendLog.id.desc())
        .limit(60)
        .all()
    )
    if logs:
        _enrich_from_browse_logs(logs, db, heritage, scene, region, seen)
        sources.append("浏览记录")

    # ── 信号4：AI提问记录 ──
    qa_logs = (
        db.query(AIQALog)
        .filter(AIQALog.user_id == user_id)
        .order_by(AIQALog.id.desc())
        .limit(15)
        .all()
    )
    if qa_logs:
        for qa in qa_logs:
            question = qa.question or ""
            _add_weights(heritage, _keyword_hits(question, HERITAGE_KEYWORDS), 1.1)
            _add_weights(scene, _detect_scene_tags(question), 0.9)
            _add_weights(region, _keyword_hits(question, REGION_KEYWORDS), 0.7)
        sources.append("AI提问")

    # ── 信号5：活动报名 ──
    registrations = (
        db.query(ActivityRegistration, Activity)
        .join(Activity, Activity.id == ActivityRegistration.activity_id)
        .filter(ActivityRegistration.user_id == user_id)
        .all()
    )
    if registrations:
        for _, event in registrations:
            text = _concat_text(event.title, event.description, event.location)
            _add_weights(heritage, _keyword_hits(text, HERITAGE_KEYWORDS), 1.4)
            _add_weights(region, _keyword_hits(text, REGION_KEYWORDS), 1.0)
            _add_weights(scene, ["活动体验"], 1.5)
            seen["event"].add(event.id)
        sources.append("报名行为")

    # ── 信号6：社区互动（点赞/收藏/评论） ──
    engaged_topic_ids = _get_engaged_topic_ids(db, user_id)
    if engaged_topic_ids:
        _enrich_from_engagement(db, engaged_topic_ids, heritage, scene, seen)
        sources.append("社区互动")

    return {
        "user": user,
        "heritage": dict(heritage),
        "scene": dict(scene),
        "region": dict(region),
        "seen": seen,
        "sources": sources,
    }


# source_scene前缀 → 非浏览行为的假click，不应进入浏览画像
_NON_BROWSE_SCENES = {"topic_like", "topic_favorite", "topic_comment"}


def _is_browse_log(log) -> bool:
    """判断RecommendLog是否代表真实浏览行为

    过滤规则：
    - expose：被动曝光，不算浏览
    - source_scene以topic_开头的假click：点赞/收藏/评论冒充的click，由信号6独立统计
    """
    if log.action == "expose":
        return False
    scene = getattr(log, "source_scene", None) or ""
    if scene in _NON_BROWSE_SCENES:
        return False
    return True


def _enrich_from_browse_logs(
    logs, db, heritage, scene, region, seen
) -> None:
    """从浏览记录中提取画像权重

    仅处理真实浏览行为（click/view），排除：
    - expose（被动曝光不构成偏好信号）
    - 点赞/收藏/评论冒充的假click（由信号6社区互动独立统计）
    """
    # 过滤非浏览记录
    browse_logs = [log for log in logs if _is_browse_log(log)]

    # 批量查询关联内容，减少DB查询次数
    content_ids = {log.target_id for log in browse_logs if log.target_type == "content"}
    event_ids = {log.target_id for log in browse_logs if log.target_type == "event"}
    topic_ids = {log.target_id for log in browse_logs if log.target_type == "topic"}

    contents = {
        c.id: c
        for c in db.query(Content).filter(Content.id.in_(content_ids)).all()
    } if content_ids else {}

    events = {
        e.id: e
        for e in db.query(Activity).filter(Activity.id.in_(event_ids)).all()
    } if event_ids else {}

    topics = {
        t.id: t
        for t in db.query(DiscussionTopic).filter(DiscussionTopic.id.in_(topic_ids)).all()
    } if topic_ids else {}

    topic_tags = _load_topic_tags(db, topic_ids)

    for log in browse_logs:
        weight = ACTION_WEIGHTS.get(log.action, 0.5)
        seen[log.target_type].add(log.target_id)

        if log.target_type == "content" and log.target_id in contents:
            c = contents[log.target_id]
            text = _concat_text(c.title, c.summary, c.chapter, c.sub_chapter)
            _add_weights(heritage, _keyword_hits(text, HERITAGE_KEYWORDS), weight)
            _add_weights(scene, ["知识阅读"], weight * 0.5)

        elif log.target_type == "event" and log.target_id in events:
            e = events[log.target_id]
            text = _concat_text(e.title, e.description, e.location)
            _add_weights(heritage, _keyword_hits(text, HERITAGE_KEYWORDS), weight)
            _add_weights(region, _keyword_hits(text, REGION_KEYWORDS), weight * 0.8)
            _add_weights(scene, ["活动体验"], weight * 0.7)

        elif log.target_type == "topic" and log.target_id in topics:
            t = topics[log.target_id]
            text = _concat_text(t.title, t.content, " ".join(topic_tags.get(t.id, [])))
            _add_weights(heritage, _keyword_hits(text, HERITAGE_KEYWORDS), weight)
            _add_weights(scene, ["论坛交流"], weight * 0.7)


def _get_engaged_topic_ids(db: Session, user_id: int) -> set[int]:
    """获取用户参与互动（点赞/收藏/评论）的话题ID集合"""
    liked = {x.topic_id for x in db.query(DiscussionLike).filter(DiscussionLike.user_id == user_id).all()}
    favorited = {x.topic_id for x in db.query(DiscussionFavorite).filter(DiscussionFavorite.user_id == user_id).all()}
    commented = {x.topic_id for x in db.query(DiscussionComment).filter(DiscussionComment.user_id == user_id).all()}
    return liked | favorited | commented


def _enrich_from_engagement(db, topic_ids, heritage, scene, seen) -> None:
    """从社区互动中提取画像权重"""
    topics = {t.id: t for t in db.query(DiscussionTopic).filter(DiscussionTopic.id.in_(topic_ids)).all()}
    tags_map = _load_topic_tags(db, topic_ids)

    for t in topics.values():
        text = _concat_text(t.title, t.content, " ".join(tags_map.get(t.id, [])))
        _add_weights(heritage, _keyword_hits(text, HERITAGE_KEYWORDS), 1.2)
        _add_weights(scene, ["论坛交流"], 1.3)
        seen["topic"].add(t.id)


def _load_topic_tags(db, topic_ids: set[int]) -> dict[int, list[str]]:
    """批量加载话题标签"""
    if not topic_ids:
        return {}
    rows = db.query(DiscussionTopicTag).filter(DiscussionTopicTag.topic_id.in_(topic_ids)).all()
    tags_map = defaultdict(list)
    for row in rows:
        tags_map[row.topic_id].append(row.tag)
    return dict(tags_map)


# ═══════════════════════════════════════════════
# 评分函数
# ═══════════════════════════════════════════════

def _score_text(text: str, weights: dict) -> tuple[float, list[str]]:
    """关键词命中加权评分

    Args:
        text: 待评分文本
        weights: 关键词→权重映射

    Returns:
        (总分, 命中的前2个关键词)
    """
    total = 0.0
    hits = []
    for keyword, weight in weights.items():
        if keyword in text:
            total += weight
            hits.append(keyword)
    hits.sort(key=lambda kw: weights.get(kw, 0), reverse=True)
    return total, hits[:2]


def _build_explain(
    match_score: float,
    novelty_score: float,
    diversity_penalty: float,
    final_score: float,
    crs_mode: str = "",
    match_detail: dict | None = None,
    strategy_context: dict | None = None,
) -> dict:
    """构建推荐解释字典 — 4层结构

    层级：
    L1 用户可读理由 → 由 _generate_reason() 生成 reason 字段
    L2 系统依据    → match_score/novelty_score/penalty/final_score + match_detail子项
    L3 策略上下文  → crs_mode/sources/heritage_terms 等
    L4 KG推理     → 由 ai_service._inject_kg_reason() 注入 kg_context

    Args:
        match_detail: 匹配分子项分解，如 {"heritage": 3.2, "scene": 1.5, "quality": 4.4, ...}
        strategy_context: 策略上下文，如 {"sources": [...], "heritage_terms": [...]}
    """
    result = {
        # ── L2：系统依据（顶层分数） ──
        "match_score_text": f"{round(match_score, 1)}",
        "novelty_score_text": f"{round(novelty_score, 1)}",
        "diversity_penalty_text": f"{round(diversity_penalty, 1)}",
        "final_score_text": f"{round(final_score, 1)}",
        "match_score": round(match_score, 3),
        "novelty_score": round(novelty_score, 3),
        "diversity_penalty": round(diversity_penalty, 3),
        "final_score": round(final_score, 3),
    }

    # ── L2：系统依据（匹配分子项分解） ──
    if match_detail:
        result["match_detail"] = {k: round(v, 2) for k, v in match_detail.items() if v}

    # ── L3：策略上下文 ──
    if crs_mode:
        _CRS_MODE_LABELS = {
            "cold_start": "冷启动探索",
            "mixed": "混合推荐",
            "precision": "精准匹配",
        }
        result["crs_mode"] = crs_mode
        result["crs_mode_label"] = _CRS_MODE_LABELS.get(crs_mode, crs_mode)
    if strategy_context:
        result["strategy_context"] = strategy_context

    return result


# ═══════════════════════════════════════════════
# 推荐理由生成
# ═══════════════════════════════════════════════

_REASON_TEMPLATES = {
    "content": [
        "你最近在关注 {keywords}，这篇文章正好深入讲了核心要点",
        "根据你之前浏览过的 {keywords} 方向，这篇内容匹配度很高",
        "发现你似乎对 {keywords} 比较感兴趣，推荐从这篇开始深入了解",
    ],
    "event": [
        "你关注的方向和这场活动主题很接近（{keywords}）",
        "结合你最近的兴趣点 {keywords}，这场线下体验值得考虑",
        "如果你想在现实中感受 {keywords}，这场活动是个不错的切入点",
    ],
    "topic": [
        "社区里关于 {keywords} 的讨论热度不错，可以看看大家在聊什么",
        "你关注的 {keywords} 在论坛里有新动态，适合参与讨论",
        "{keywords} 相关的话题最近讨论比较活跃，值得一看",
    ],
}

# CRS模式感知的推荐理由模板
_REASON_TEMPLATES_CRS = {
    "cold_start": {
        "content": [
            "还不确定你的偏好方向，先从 {keywords} 这个热门方向开始探索",
            "平台里 {keywords} 方向的内容质量较高，适合从这里入门",
            "{keywords} 是很多用户的第一站，推荐先看看这篇",
        ],
        "event": [
            "{keywords} 相关的活动近期比较受欢迎，可以先试试",
            "还没有足够的偏好数据，先推荐 {keywords} 方向的热门活动",
        ],
        "topic": [
            "社区里 {keywords} 话题讨论比较多，适合先看大家聊什么",
            "不妨从 {keywords} 相关的讨论开始了解社区氛围",
        ],
    },
    "mixed": {
        "content": [
            "根据你初步关注的 {keywords}，这篇内容应该比较对口",
            "你似乎对 {keywords} 有了方向感，这篇正好延伸阅读",
        ],
        "event": [
            "结合你目前关注的 {keywords}，这场活动值得考虑",
            "你对 {keywords} 的兴趣正在形成，这场活动可以加深了解",
        ],
        "topic": [
            "你关注的 {keywords} 在论坛里有新动态，适合参与讨论",
            "社区里 {keywords} 相关话题和你的探索方向一致",
        ],
    },
    "precision": {
        "content": [
            "因为你喜欢 {keywords}，这篇内容和你偏好高度匹配",
            "基于你对 {keywords} 的深入了解需求，这篇是最佳选择",
            "精准匹配你的 {keywords} 偏好，这篇不容错过",
        ],
        "event": [
            "因为你偏好 {keywords}，这场活动最适合你参与",
            "精准匹配你的 {keywords} 兴趣，推荐优先报名",
        ],
        "topic": [
            "精准匹配你的 {keywords} 偏好，这个讨论和你最相关",
            "基于你对 {keywords} 的兴趣，这个话题值得参与",
        ],
    },
}


def _generate_reason(kind: str, profile: dict, hits: list[str], heat: int = 0, crs_mode: str = "") -> str:
    """生成推荐理由

    根据CRS模式差异化生成推荐解释：
    - cold_start：承认不确定性，引导用户探索
    - mixed：部分匹配，探索性推荐
    - precision：精确匹配，给出具体原因
    - 空字符串：使用原有模板（兼容旧逻辑）

    优先使用命中关键词模板，其次用偏好画像兜底，最后按类型补充通用理由。
    """
    top_pref = _top_terms(profile, "heritage", 2)
    top_scene = _top_terms(profile, "scene", 1)
    reasons = []

    # CRS模式感知：优先使用模式专属模板
    if crs_mode and crs_mode in _REASON_TEMPLATES_CRS and hits:
        keywords = "、".join(hits[:2])
        mode_templates = _REASON_TEMPLATES_CRS[crs_mode].get(kind, [])
        if mode_templates:
            reasons.append(random.choice(mode_templates).format(keywords=keywords))

    # 无CRS模式 或 无命中关键词 → 回退到原有模板
    if not reasons and hits:
        keywords = "、".join(hits[:2])
        templates = _REASON_TEMPLATES.get(kind, _REASON_TEMPLATES["content"])
        reasons.append(random.choice(templates).format(keywords=keywords))

    # 偏好画像兜底
    if not reasons and top_pref:
        prefs = "、".join(top_pref)
        if crs_mode == "precision":
            reasons.append(f"精准匹配你偏好的「{prefs}」方向")
        elif crs_mode == "cold_start":
            reasons.append(f"暂时还不了解你的偏好，先从「{prefs}」方向推荐")
        else:
            reasons.append(f"这条和你偏好的「{prefs}」方向比较契合")

    # 精准模式：补充画像来源增强可解释性
    if crs_mode == "precision":
        sources = profile.get("sources", [])
        source_labels = {
            "偏好画像": "你设置的偏好",
            "浏览记录": "你浏览过的内容",
            "AI提问": "你问过的问题",
            "报名行为": "你报名的活动",
            "社区互动": "你参与的讨论",
        }
        source_texts = [source_labels.get(s, s) for s in sources[:2] if s in source_labels]
        if source_texts and len(reasons) == 1:
            reasons.append("参考了" + "和".join(source_texts))

    # 冷启动模式：引导用户参与CRS对话
    if crs_mode == "cold_start" and not reasons:
        reasons.append("和黑塔聊聊，推荐会更准")

    # 按类型补充理由
    if kind == "content":
        if not any("阅读" in r or "了解" in r for r in reasons):
            reasons.append("适合作为下一篇继续阅读")

    elif kind == "event":
        if heat > 5:
            reasons.append(f"已有 {heat} 人报名，近期热度较高")
        elif heat > 0:
            reasons.append("目前还有名额，适合尽早锁定")
        elif "体验" in str(top_scene):
            reasons.append("符合你最近偏向线下参与的浏览习惯")
        else:
            reasons.append("适合从线上了解走到线下亲身体验")

    elif kind == "topic":
        if heat >= 6:
            reasons.append(f"已有 {heat} 次互动，讨论氛围活跃")
        elif heat > 0:
            reasons.append("有人已经在聊这个话题了")
        elif "论坛交流" in top_scene:
            reasons.append("也符合你在社区持续关注的领域")
        else:
            reasons.append("适合先看看大家正在讨论什么")

    if reasons:
        return "，".join(reasons[:2])

    # 兜底
    if crs_mode == "cold_start":
        return "和黑塔聊聊你的兴趣，推荐会更精准"
    if crs_mode == "precision":
        return "这项推荐精准匹配了你的偏好画像"
    if kind == "content":
        return "内容质量和你的兴趣方向比较匹配"
    return "这项推荐综合了你的使用轨迹和当前热度"


# ═══════════════════════════════════════════════
# 内容推荐
# ═══════════════════════════════════════════════

def recommend_contents(
    db: Session,
    profile: dict,
    limit: int = 5,
    scene: str = "home",
    crs_mode: str = "",
    context_text: str = "",
) -> list[dict]:
    """内容推荐：基于遗产类型匹配 + 场景匹配 + 质量分 + 新鲜度 + 流行度

    评分公式：
        final_score = match_score + novelty_score - diversity_penalty
        match_score = heritage_match * 1.4 + scene_match * 0.8 + quality * 2.2 + featured + popularity
        novelty_score = freshness + scene_bonus * 10
        diversity_penalty = 已看惩罚 (12分，只扣一次)
    """
    # 全局流行度（click+view次数）
    popularity_rows = (
        db.query(RecommendLog.target_id, func.count(RecommendLog.id))
        .filter(
            RecommendLog.target_type == "content",
            RecommendLog.action.in_(["click", "view"]),
        )
        .group_by(RecommendLog.target_id)
        .all()
    )
    popularity = {row[0]: int(row[1] or 0) for row in popularity_rows}

    # 候选内容 — SQL粗排：按quality_score+is_featured排序，取top50
    # 当context_text含明确实体词时，OR召回标题/摘要含该实体的内容
    explicit_from_q = _extract_explicit_entities(context_text) if context_text else []
    base_q = (
        db.query(Content)
        .filter(
            Content.status == "published",
            Content.review_status == "approved",
            Content.quality_score >= 0.8,
        )
    )
    if explicit_from_q:
        from sqlalchemy import or_
        entity_filters = or_(*[Content.title.ilike(f"%{e}%") for e in explicit_from_q])
        items = (
            base_q.filter(entity_filters)
            .order_by(Content.quality_score.desc(), Content.is_featured.desc())
            .limit(25)
            .all()
        )
        generic_items = (
            base_q.order_by(Content.quality_score.desc(), Content.is_featured.desc())
            .limit(25)
            .all()
        )
        seen_ids = {item.id for item in items}
        for item in generic_items:
            if item.id not in seen_ids:
                items.append(item)
                seen_ids.add(item.id)
    else:
        items = (
            base_q.order_by(Content.quality_score.desc(), Content.is_featured.desc())
            .limit(50)
            .all()
        )

    # P0#5: explicit_entities覆盖修复 — 合并画像关键词和当前问题实体
    explicit_entities = _top_terms(profile, "heritage", 3) + _extract_explicit_entities(context_text)
    rows = []

    for item in items:
        text = _concat_text(item.title, item.summary, item.chapter, item.sub_chapter, item.content_type)

        # 匹配分
        heritage_score, heritage_hits = _score_text(text, profile["heritage"])
        entity_bonus, entity_hits = _entity_recall_bonus(text, explicit_entities)
        scene_score, scene_hits = _score_text(text, profile["scene"])
        quality = float(item.quality_score or 0)
        featured_bonus = 1 if item.is_featured else 0
        pop_bonus = min(2.0, popularity.get(item.id, 0) * 0.2)
        match_score = heritage_score * 1.4 + entity_bonus + scene_score * 0.8 + quality * 2.2 + featured_bonus + pop_bonus

        # 新鲜度
        days = max(1, (datetime.now() - item.created_at).days) if item.created_at else 30
        freshness = max(0.0, 14.0 - min(14.0, days / 2))
        novelty_score = freshness + _scene_bonus(scene, "content") * 10

        # 已看惩罚（只扣一次）
        penalty = SEEN_PENALTY["content"] if item.id in profile["seen"]["content"] else 0.0
        final_score = match_score + novelty_score - penalty

        all_hits = entity_hits + heritage_hits + scene_hits
        match_detail = {
            "heritage": heritage_score,
            "entity_recall": entity_bonus,
            "scene": scene_score,
            "quality": quality,
            "featured": featured_bonus,
            "popularity": pop_bonus,
        }
        explain = _build_explain(match_score, novelty_score, penalty, final_score, crs_mode=crs_mode, match_detail=match_detail)
        rows.append((item, final_score, all_hits, days, explain))

    # 排序 + 章节多样性
    rows.sort(key=lambda x: (x[1], x[0].id or 0), reverse=True)
    results = []
    chapter_count = defaultdict(int)

    for item, _, hits, days, explain in rows:
        chapter = item.chapter or "综合"
        if chapter_count[chapter] >= 2:
            continue
        chapter_count[chapter] += 1
        results.append({
            "id": item.id,
            "title": item.title,
            "summary": item.summary,
            "content_type": item.content_type,
            "cover_url": item.cover_url,
            "reason": _generate_reason("content", profile, hits, crs_mode=crs_mode),
            "tags": hits[:2] or _top_terms(profile, "heritage", 2),
            "freshness_label": _freshness_label(days),
            "explain": explain,
        })
        if len(results) >= limit:
            break

    return results


# ═══════════════════════════════════════════════
# 活动推荐
# ═══════════════════════════════════════════════

def recommend_events(
    db: Session,
    profile: dict,
    limit: int = 5,
    scene: str = "home",
    crs_mode: str = "",
) -> list[dict]:
    """活动推荐：基于遗产匹配 + 地区匹配 + 场景权重 + 热度 + 即将程度

    评分公式：
        match_score = heritage*1.1 + region*1.1 + scene_weight*0.8 + heat*0.24 + featured
        novelty_score = urgency + scene_bonus*10
        diversity_penalty = 已看惩罚 (10分，只扣一次)
    """
    # 活动热度（报名人数）
    heat_rows = (
        db.query(ActivityRegistration.activity_id, func.count(ActivityRegistration.id))
        .filter(ActivityRegistration.status.in_(["registered", "checked_in", "completed"]))
        .group_by(ActivityRegistration.activity_id)
        .all()
    )
    heat_map = {row[0]: int(row[1] or 0) for row in heat_rows}

    # 候选活动：未来60天内
    now = datetime.now()
    end = now + timedelta(days=60)
    items = (
        db.query(Activity)
        .filter(Activity.status == "open", Activity.start_time >= now, Activity.start_time <= end)
        .all()
    )

    explicit_entities = _top_terms(profile, "heritage", 3)
    rows = []
    for item in items:
        text = _concat_text(item.title, item.description, item.location)

        # 匹配分
        heritage_score, heritage_hits = _score_text(text, profile["heritage"])
        entity_bonus, entity_hits = _entity_recall_bonus(text, explicit_entities, bonus=14.0)
        region_score, region_hits = _score_text(text, profile["region"])
        scene_weight = profile["scene"].get("活动体验", 0) * 0.8
        heat_bonus = min(3.2, heat_map.get(item.id, 0) * 0.24)
        featured_bonus = 1 if item.is_featured else 0
        match_score = heritage_score * 1.1 + entity_bonus + region_score * 1.1 + scene_weight + heat_bonus + featured_bonus

        # 即将程度
        days_ahead = max(0, (item.start_time - now).days) if item.start_time else 30
        urgency = max(0.0, 20.0 - min(20.0, days_ahead * 0.8))
        novelty_score = urgency + _scene_bonus(scene, "event") * 10

        # 已看惩罚（只扣一次）
        penalty = SEEN_PENALTY["event"] if item.id in profile["seen"]["event"] else 0.0
        final_score = match_score + novelty_score - penalty

        all_hits = entity_hits + heritage_hits + region_hits
        match_detail = {
            "heritage": heritage_score,
            "entity_recall": entity_bonus,
            "region": region_score,
            "scene_weight": scene_weight,
            "heat": heat_bonus,
            "featured": featured_bonus,
        }
        explain = _build_explain(match_score, novelty_score, penalty, final_score, crs_mode=crs_mode, match_detail=match_detail)
        rows.append((item, final_score, all_hits, heat_map.get(item.id, 0), days_ahead, explain))

    rows.sort(key=lambda x: (x[1], x[0].id or 0), reverse=True)

    return [
        {
            "id": item.id,
            "title": item.title,
            "location": item.location,
            "start_time": item.start_time,
            "status": item.status,
            "cover_url": item.cover_url,
            "heat": heat,
            "reason": _generate_reason("event", profile, hits, heat, crs_mode=crs_mode),
            "tags": hits[:2] or _top_terms(profile, "heritage", 2),
            "freshness_label": "即将开始" if days_ahead <= 7 else "近期可参与",
            "explain": explain,
        }
        for item, _, hits, heat, days_ahead, explain in rows[:limit]
    ]


# ═══════════════════════════════════════════════
# 话题推荐
# ═══════════════════════════════════════════════

def recommend_topics(
    db: Session,
    profile: dict,
    limit: int = 5,
    scene: str = "home",
    crs_mode: str = "",
) -> list[dict]:
    """话题推荐：基于遗产匹配 + 场景权重 + 互动热度

    评分公式：
        match_score = heritage*1.2 + scene_weight*0.9 + likes*1.3 + favs*1.5 + comments*1.1 + featured
        novelty_score = scene_bonus*10
        diversity_penalty = 已看惩罚 (8分，只扣一次)
    """
    items = db.query(DiscussionTopic).all()
    topic_ids = [t.id for t in items]
    tags_map = _load_topic_tags(db, set(topic_ids))

    explicit_entities = _top_terms(profile, "heritage", 3)
    rows = []
    for item in items:
        text = _concat_text(item.title, item.content, " ".join(tags_map.get(item.id, [])))

        # 匹配分
        heritage_score, heritage_hits = _score_text(text, profile["heritage"])
        entity_bonus, entity_hits = _entity_recall_bonus(text, explicit_entities, bonus=16.0)
        scene_weight = profile["scene"].get("论坛交流", 0) * 0.9
        interaction_heat = item.like_count + item.favorite_count + item.comment_count
        engagement_score = item.like_count * 0.45 + item.favorite_count * 0.55 + item.comment_count * 0.4
        if heritage_score + entity_bonus < 2.0:
            engagement_score *= 0.25
        featured_bonus = 1 if item.is_featured else 0
        match_score = heritage_score * 1.2 + entity_bonus + scene_weight + engagement_score + featured_bonus

        # 新鲜度（话题不做时间衰减，只做场景加权）
        novelty_score = _scene_bonus(scene, "topic") * 10

        # 已看惩罚（只扣一次）
        penalty = SEEN_PENALTY["topic"] if item.id in profile["seen"]["topic"] else 0.0
        final_score = match_score + novelty_score - penalty

        all_hits = entity_hits + heritage_hits + tags_map.get(item.id, [])[:1]
        match_detail = {
            "heritage": heritage_score,
            "entity_recall": entity_bonus,
            "scene_weight": scene_weight,
            "engagement": engagement_score,
            "featured": featured_bonus,
        }
        explain = _build_explain(match_score, novelty_score, penalty, final_score, crs_mode=crs_mode, match_detail=match_detail)
        rows.append((item, final_score, all_hits, interaction_heat, explain))

    rows.sort(key=lambda x: (x[1], x[0].id or 0), reverse=True)

    return [
        {
            "id": item.id,
            "title": item.title,
            "reason": _generate_reason("topic", profile, hits, heat, crs_mode=crs_mode),
            "tags": hits[:2] or tags_map.get(item.id, [])[:2],
            "freshness_label": "讨论升温中" if heat >= 6 else "值得参与",
            "explain": explain,
        }
        for item, _, hits, heat, explain in rows[:limit]
    ]


# ═══════════════════════════════════════════════
# 引导文案 & 策略摘要
# ═══════════════════════════════════════════════

def build_guide_text(profile: dict) -> str:
    """生成推荐引导文案"""
    top = _top_terms(profile, "heritage", 3)
    main = "、".join(top) if top else "非遗综合"
    sources = profile["sources"][:3]

    if "AI提问" in sources:
        return f"我结合你刚才的问题，再参考你的历史偏好，优先整理了 {main} 相关的内容、活动和讨论。"
    if sources:
        return f"我参考了你的{'、'.join(sources)}，优先给你挑了 {main} 方向更值得先看的内容。"
    return f"我先从平台里质量更高、也更适合入门的 {main} 方向开始为你推荐。"


def build_strategy_summary(profile: dict) -> dict:
    """生成策略摘要（画像来源、兴趣重点、场景、地区）"""
    heritage_terms = sorted(
        profile["heritage"].keys(),
        key=lambda k: profile["heritage"][k],
        reverse=True,
    )[:5]
    scene_terms = sorted(
        profile["scene"].keys(),
        key=lambda k: profile["scene"][k],
        reverse=True,
    )[:3]
    region_terms = sorted(
        profile["region"].keys(),
        key=lambda k: profile["region"][k],
        reverse=True,
    )[:3]
    source_terms = profile["sources"][:4]

    chips = []
    if source_terms:
        chips.append("画像来源：" + " / ".join(source_terms))
    if heritage_terms:
        chips.append("兴趣重点：" + " / ".join(heritage_terms[:2]))
    if scene_terms:
        chips.append("当前场景：" + " / ".join(scene_terms[:2]))
    if region_terms:
        chips.append("关注地区：" + " / ".join(region_terms[:2]))

    return {
        "sources": source_terms,
        "heritage_terms": heritage_terms,
        "scene_terms": scene_terms,
        "region_terms": region_terms,
        "summary_text": " · ".join(chips),
    }


# ═══════════════════════════════════════════════
# 总入口
# ═══════════════════════════════════════════════

def generate_recommendation_payload(
    db: Session,
    user_id: int | None,
    context_text: str = "",
    scene: str = "home",
) -> dict:
    """推荐系统总入口：构建画像 → 三路推荐 → 聚合返回"""
    scene = scene or "home"
    if scene not in VALID_SCENES:
        scene = "home"

    profile = build_user_profile(db, user_id, context_text=context_text)
    strategy_summary = build_strategy_summary(profile)

    # 获取CRS模式，用于推荐解释差异化
    crs_mode = ""
    if user_id:
        try:
            conf = calc_confidence(db, user_id, use_cache=True)
            crs_mode = conf.get("mode", "")
        except Exception:
            pass

    return {
        "scene": scene,
        "guide_text": build_guide_text(profile),
        "contents": recommend_contents(db, profile, scene=scene, crs_mode=crs_mode, context_text=context_text),
        "events": recommend_events(db, profile, scene=scene, crs_mode=crs_mode),
        "topics": recommend_topics(db, profile, scene=scene, crs_mode=crs_mode),
        "profile_summary": strategy_summary,
        "crs_mode": crs_mode,
    }


def generate_ai_recommend_cards(
    db: Session,
    user_id: int | None,
    question: str,
    rec_payload: dict | None = None,
    prefer_hot: bool = False,
) -> list[dict]:
    """AI聊天场景：从推荐结果中每种类型各取1条，最多3张卡片

    每张卡片的 explain 中注入 L3 策略上下文（来自 profile_summary），
    确保4层解释结构完整。

    v2.1: 新增 rec_payload 参数，允许复用已生成的推荐画像，避免重复计算。
    prefer_hot=True 时，在冷启动/低了解阶段优先选择热门候选作为兜底。
    """
    payload = rec_payload if rec_payload is not None else generate_recommendation_payload(db, user_id, context_text=question, scene="ai")
    cards = []

    # L3 策略上下文：从 profile_summary 提取关键字段注入单卡片
    profile_summary = payload.get("profile_summary") or {}
    strategy_context = {
        "sources": profile_summary.get("sources", []),
        "heritage_terms": profile_summary.get("heritage_terms", [])[:3],
        "scene_terms": profile_summary.get("scene_terms", [])[:2],
        "region_terms": profile_summary.get("region_terms", [])[:2],
    }

    def pick_item(pool: list[dict]) -> dict | None:
        valid = [x for x in pool if _is_valid_title(x.get("title"))]
        if not valid:
            return None
        if not prefer_hot:
            return valid[0]
        def hot_key(item: dict):
            explain = item.get("explain") or {}
            final_score = float(explain.get("final_score", 0) or 0)
            match_score = float(explain.get("match_score", 0) or 0)
            popularity = float(((explain.get("match_detail") or {}).get("popularity", 0)) or 0)
            novelty = float(explain.get("novelty_score", 0) or 0)
            return (popularity, novelty, final_score, match_score, item.get("id", 0))
        return sorted(valid, key=hot_key, reverse=True)[0]

    for pool, type_name in [
        (payload.get("contents") or [], "content"),
        (payload.get("events") or [], "event"),
        (payload.get("topics") or [], "topic"),
    ]:
        item = pick_item(pool)
        if not item:
            continue
        explain = item.get("explain", {})
        # 注入L3策略上下文（不覆盖已有的crs_mode等字段）
        if "strategy_context" not in explain:
            explain["strategy_context"] = strategy_context
        cards.append({
            "type": type_name,
            "id": item["id"],
            "title": item["title"],
            "reason": item["reason"],
            "summary": item.get("summary", ""),
            "cover_url": item.get("cover_url", ""),
            "explain": explain,
        })

    return cards[:3]


# ═══════════════════════════════════════════════
# CRS 置信度计算（v2.0 新增）
# ═══════════════════════════════════════════════

# CRS 置信度权重
CRS_WEIGHT_EXPLICIT = 0.40   # 显式偏好权重
CRS_WEIGHT_IMPLICIT = 0.35   # 隐式行为权重
CRS_WEIGHT_DIALOGUE = 0.25   # 对话语义权重

# CRS 模式阈值
CRS_THRESHOLD_COLD = 28      # C < 28 → cold_start
CRS_THRESHOLD_MIXED = 62     # 28 ≤ C < 62 → mixed; C ≥ 62 → precision


def calc_confidence(db: Session, user_id: int, use_cache: bool = False) -> dict:
    """计算CRS置信度（精简版3维）

    公式：C = 0.4 * S_explicit + 0.35 * S_implicit + 0.25 * S_dialogue
    各维度满分100，C满分100。

    Args:
        db: 数据库会话
        user_id: 用户ID
        use_cache: 是否优先使用User表缓存（true时跳过全量重算）

    Returns:
        {
            "confidence_score": float,     # 综合置信度 0-100
            "score_explicit": float,       # 显式偏好分 0-100
            "score_implicit": float,       # 隐式行为分 0-100
            "score_dialogue": float,       # 对话语义分 0-100
            "mode": str,                   # cold_start / mixed / precision
            "detail": dict                 # 各维度明细
        }
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return _empty_confidence()

    # 缓存模式：直接读User表的缓存值，不做全量计算
    if use_cache and user.confidence_score is not None:
        c = user.confidence_score
        return {
            "confidence_score": c,
            "confidence_score_raw": c,
            "stage_progress_percent": _stage_progress_percent(_determine_mode(c), c),
            "score_explicit": user.score_explicit or 0,
            "score_implicit": user.score_implicit or 0,
            "score_dialogue": user.score_dialogue or 0,
            "mode": _determine_mode(c),
            "detail": {},  # 缓存模式不返回明细
        }

    s_explicit = _calc_explicit_score(db, user)
    s_implicit = calc_implicit_score(db, user_id)
    s_dialogue = _calc_dialogue_score(db, user_id)

    c = (
        CRS_WEIGHT_EXPLICIT * s_explicit
        + CRS_WEIGHT_IMPLICIT * s_implicit
        + CRS_WEIGHT_DIALOGUE * s_dialogue
    )
    c = round(min(100.0, max(0.0, c)), 1)

    mode = _determine_mode(c)

    # 回写到User表
    user.confidence_score = c
    user.score_explicit = round(s_explicit, 1)
    user.score_implicit = round(s_implicit, 1)
    user.score_dialogue = round(s_dialogue, 1)
    db.commit()

    return {
        "confidence_score": c,
        "confidence_score_raw": c,
        "stage_progress_percent": _stage_progress_percent(mode, c),
        "score_explicit": round(s_explicit, 1),
        "score_implicit": round(s_implicit, 1),
        "score_dialogue": round(s_dialogue, 1),
        "mode": mode,
        "detail": {
            "explicit": {
                "has_heritage_types": len(_safe_json_loads(user.preferred_heritage_types)) > 0,
                "has_scene_types": len(_safe_json_loads(user.preferred_scene_types)) > 0,
                "has_regions": len(_safe_json_loads(user.preferred_regions)) > 0,
                "ask_answer_count": _count_ask_answers(db, user_id),
            },
            "implicit": {
                "browse_count": _count_browse_actions(db, user_id),
                "registration_count": _count_registrations(db, user_id),
                "engagement_count": len(_get_engaged_topic_ids(db, user_id)),
            },
            "dialogue": {
                "qa_count": _count_qa_logs(db, user_id),
                "ask_answered": _count_ask_answers(db, user_id),
            },
        },
    }


def _empty_confidence() -> dict:
    """空用户/未登录的默认置信度"""
    return {
        "confidence_score": 0.0,
        "confidence_score_raw": 0.0,
        "stage_progress_percent": 0,
        "score_explicit": 0.0,
        "score_implicit": 0.0,
        "score_dialogue": 0.0,
        "mode": "cold_start",
        "detail": {},
    }


def _stage_progress_percent(mode: str, confidence_score: float) -> int:
    """根据CRS阶段返回统一展示进度，避免前端自行猜测口径"""
    score = float(confidence_score or 0)
    if mode == "precision":
        normalized = max(0.0, min(1.0, (score - CRS_THRESHOLD_MIXED) / max(1.0, 100.0 - CRS_THRESHOLD_MIXED)))
        return max(82, min(100, round(82 + normalized * 18)))
    if mode == "mixed":
        normalized = max(0.0, min(1.0, (score - CRS_THRESHOLD_COLD) / max(1.0, CRS_THRESHOLD_MIXED - CRS_THRESHOLD_COLD)))
        return max(42, min(78, round(42 + normalized * 36)))
    if score <= 0:
        return 0
    return max(8, min(36, round(score)))


def _calc_explicit_score(db: Session, user: User) -> float:
    """显式偏好分 S_explicit

    基于用户主动设置的偏好字段：
    - preferred_heritage_types: 每个关键词 +30分，最多60
    - preferred_scene_types: 每个关键词 +20分，最多40
    - preferred_regions: 每个关键词 +20分，最多40
    - CRS ASK回答增量: 从CrsAskLog统计，每个有效回答 +10分，最多30

    满分映射到100
    """
    heritage = _safe_json_loads(user.preferred_heritage_types)
    scenes = _safe_json_loads(user.preferred_scene_types)
    regions = _safe_json_loads(user.preferred_regions)

    raw = 0.0
    raw += min(60.0, len(heritage) * 30.0) if heritage else 0.0
    raw += min(40.0, len(scenes) * 20.0) if scenes else 0.0
    raw += min(40.0, len(regions) * 20.0) if regions else 0.0

    # CRS ASK回答增量：每个有效（非跳过）回答 +10分，上限30
    ask_answer_count = _count_ask_answers(db, user.id)
    raw += min(30.0, ask_answer_count * 10.0)

    return min(100.0, raw)


def calc_implicit_score(db: Session, user_id: int) -> float:
    """隐式行为分 S_implicit

    基于用户行为数据：
    - 浏览记录：click/view 每条 +5分，最多40
    - 活动报名：每条 +15分，最多30
    - 社区互动（点赞/收藏/评论）：每条 +8分，最多30
    - CRS ASK回答激励：有回答时给基础分（"已开始探索"），每条+7，上限20
    - AI对话激励：每条AI对话+5分，上限20（v2.1.3提升，冷启动核心驱动力）

    满分映射到100
    """
    browse_count = _count_browse_actions(db, user_id)
    registration_count = _count_registrations(db, user_id)
    engagement_count = len(_get_engaged_topic_ids(db, user_id))

    raw = 0.0
    raw += min(40.0, browse_count * 5.0)
    raw += min(30.0, registration_count * 15.0)
    raw += min(30.0, engagement_count * 8.0)

    # CRS ASK回答激励：回答过ASK说明用户已开始主动探索，给基础implicit分
    # 解决冷启动阶段implicit=0导致收敛过慢的问题
    ask_answer_count = _count_ask_answers(db, user_id)
    if ask_answer_count > 0:
        raw += min(20.0, ask_answer_count * 7.0)

    # AI对话激励（v2.1.3提升）：每条AI对话+5分，上限20
    # 用户和黑塔对话 = 已开始探索，implicit不应为0
    qa_count = _count_qa_logs(db, user_id)
    if qa_count > 0:
        raw += min(20.0, qa_count * 5.0)

    return min(100.0, raw)


def _calc_dialogue_score(db: Session, user_id: int) -> float:
    """对话语义分 S_dialogue

    基于AI对话和CRS ASK回答：
    - AI提问记录：每条 +4分，最多40
    - CRS ASK回答：每条 +12分，最多60

    满分映射到100
    """
    qa_count = _count_qa_logs(db, user_id)
    ask_count = _count_ask_answers(db, user_id)

    raw = 0.0
    raw += min(40.0, qa_count * 4.0)
    raw += min(60.0, ask_count * 12.0)

    return min(100.0, raw)


def _count_browse_actions(db: Session, user_id: int) -> int:
    """统计用户浏览行为次数（click + view，排除点赞/收藏/评论的假click）"""
    from sqlalchemy import func as sql_func
    count = (
        db.query(sql_func.count(RecommendLog.id))
        .filter(
            RecommendLog.user_id == user_id,
            RecommendLog.action.in_(["click", "view"]),
            ~RecommendLog.source_scene.in_(["topic_like", "topic_favorite", "topic_comment"]),
        )
        .scalar()
    )
    return int(count or 0)


def _count_registrations(db: Session, user_id: int) -> int:
    """统计用户活动报名次数"""
    from sqlalchemy import func as sql_func
    count = (
        db.query(sql_func.count(ActivityRegistration.id))
        .filter(ActivityRegistration.user_id == user_id)
        .scalar()
    )
    return int(count or 0)


def _count_qa_logs(db: Session, user_id: int) -> int:
    """统计用户AI提问次数"""
    from sqlalchemy import func as sql_func
    count = (
        db.query(sql_func.count(AIQALog.id))
        .filter(AIQALog.user_id == user_id)
        .scalar()
    )
    return int(count or 0)


def _count_ask_answers(db: Session, user_id: int) -> int:
    """统计用户CRS ASK有效回答次数（排除跳过类回答）"""
    from sqlalchemy import func as sql_func
    from app.models.crs_ask_log import CrsAskLog
    count = (
        db.query(sql_func.count(CrsAskLog.id))
        .filter(
            CrsAskLog.user_id == user_id,
            CrsAskLog.is_skipped == False,
        )
        .scalar()
    )
    return int(count or 0)


def _determine_mode(confidence: float) -> str:
    """根据置信度决定CRS模式"""
    if confidence < CRS_THRESHOLD_COLD:
        return "cold_start"
    elif confidence < CRS_THRESHOLD_MIXED:
        return "mixed"
    else:
        return "precision"


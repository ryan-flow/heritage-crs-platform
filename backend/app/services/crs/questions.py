"""CRS 推荐问题生成

三阶段策略：cold_start(广撒网) → mixed(同类目深入) → precision(垂直追问)
优先从KB提取问题（100%命中率），兜底用预设问题池。
"""

import json
import logging
import random
from collections import defaultdict

from sqlalchemy.orm import Session

from app.services.recommendation_service import _safe_json_loads
from app.services.crs.constants import SPECIFIC_TERMS, CONTENT_CHAPTERS

logger = logging.getLogger(__name__)

# KB章节 → 兴趣关键词
_CHAPTER_TO_INTEREST = {
    "传统工艺": ["工艺", "手工", "绣", "瓷", "锦", "织", "染", "纸", "壶", "编", "技艺", "蜡染", "扎染", "刺绣"],
    "戏曲与表演艺术": ["戏曲", "昆曲", "京剧", "粤剧", "黄梅戏", "越剧", "皮影"],
    "传统音乐": ["音乐", "古琴", "古筝", "琵琶", "笛", "箫", "二胡", "南音"],
    "岁时节庆与民俗": ["民俗", "节庆", "端午", "春节", "中秋", "清明", "节气", "龙", "狮"],
    "传统医药": ["医药", "中医", "针灸", "中药", "藏医", "养生", "五行"],
    "传统美术": ["美术", "剪纸", "篆刻", "年画", "刺绣", "苏绣", "湘绣"],
    "传统体育": ["体育", "武术", "太极", "围棋", "龙舟", "少林"],
    "非遗基础认知": ["非遗", "类别", "名录", "保护", "传承人"],
    "传承实践": ["传承", "教育", "研学", "校园", "乡村振兴", "年轻人"],
    "数字化体验": ["数字化", "VR", "AI", "短视频", "体验", "博物馆"],
    "国际传播": ["国际", "联合国", "世界级", "传播", "海外"],
    "保护制度": ["法律", "制度", "政策", "法规", "保护"],
}

# 兴趣关键词 → KB章节（反向映射）
_INTEREST_TO_CHAPTERS: dict[str, list[str]] = {}
for _ch, _kws in _CHAPTER_TO_INTEREST.items():
    for _kw in _kws:
        _INTEREST_TO_CHAPTERS.setdefault(_kw, []).append(_ch)

_GENERIC_KWS = {
    "传承", "体验", "技艺", "非遗", "保护", "发展", "文化", "传统", "中国",
    "研学", "校园", "乡村", "旅游", "博物馆", "教育", "学生", "社区",
    "活动", "参加", "申报", "名录", "政策", "制度",
}

# 字符级反向索引，加速章节匹配
def _build_char_index() -> dict[str, list[tuple[str, list[str]]]]:
    char_index = defaultdict(list)
    for kw, chapters in _INTEREST_TO_CHAPTERS.items():
        if kw in _GENERIC_KWS:
            continue
        for c in kw:
            char_index[c].append((kw, chapters))
    return char_index

_CHAR_INDEX = _build_char_index()

def _match_chapters(combined_text: str) -> set[str]:
    matched_chapters = set()
    processed_kws = set()
    for c in combined_text:
        if c in _CHAR_INDEX:
            for kw, chapters in _CHAR_INDEX[c]:
                if kw not in processed_kws:
                    processed_kws.add(kw)
                    if kw in combined_text:
                        matched_chapters.update(chapters)
    return matched_chapters

# 章节语义近邻（同类目扩展用）
_SEMANTIC_ADJACENT = {
    "传统工艺": ["传统美术"],
    "传统美术": ["传统工艺"],
    "戏曲与表演艺术": ["传统音乐"],
    "传统音乐": ["戏曲与表演艺术"],
    "岁时节庆与民俗": ["传统体育"],
    "传统体育": ["岁时节庆与民俗"],
    "非遗基础认知": ["保护制度"],
    "保护制度": ["非遗基础认知"],
    "传承实践": ["数字化体验"],
    "数字化体验": ["传承实践"],
    "国际传播": ["非遗基础认知"],
    "传统医药": [],
}

# 属性 → 默认章节
_ATTR_CHAPTERS = {
    "category": ["传统工艺", "戏曲与表演艺术", "传统音乐", "传统美术"],
    "region": ["国际传播", "传统医药", "岁时节庆与民俗"],
    "scene": ["传承实践", "数字化体验"],
    "general": ["非遗基础认知", "保护制度"],
}

# 属性检测关键词
_ATTR_KEYWORDS = {
    "scene": ["活动", "体验", "参加", "研学", "线下", "现场"],
    "region": ["华东", "华南", "华北", "西南", "地区", "地方", "省", "国际", "海外"],
    "general": ["申报", "保护", "法律", "制度", "名录", "传承人", "政策"],
}

def _detect_attr(combined_text: str) -> str:
    for attr, keywords in _ATTR_KEYWORDS.items():
        for kw in keywords:
            if kw in combined_text:
                return attr
    return "category"

# 兜底问题池
_COLD_START_FALLBACK = {
    "category": [
        "苏绣有什么特点？", "昆曲适合新手从哪里入门？", "端午节有哪些习俗？",
        "传统医药类非遗为什么和日常生活也有关系？", "紫砂壶怎么鉴别真假？",
        "四大名绣各有什么特色？", "景泰蓝是怎么做出来的？", "剪纸有哪些代表性地域流派？",
        "皮影戏怎么制作的？", "中国结有哪些基本结型？", "年画有哪些产地风格？", "古琴有哪些名曲？",
    ],
    "region": [
        "粤剧为什么是中国戏曲国际传播中的代表项目？", "藏戏在中国非遗版图中有什么代表性？",
        "南音为什么常被称为很有古韵的音乐？", "蜀绣的代表特点是什么？",
        "苗族银饰有什么工艺特色？", "闽南文化有哪些典型非遗？",
        "傣族孔雀舞有什么文化含义？", "维吾尔族木卡姆是什么？",
    ],
    "scene": [
        "有哪些体验非遗的好方式？", "非遗与研学活动为什么容易结合？",
        "非遗短视频为什么在抖音等平台这么受欢迎？", "VR技术如何用于非遗保护？",
        "非遗文创产品有哪些成功案例？", "博物馆里怎么体验非遗项目？",
        "哪些城市的非遗体验活动做得好？", "年轻人学习非遗技艺有哪些途径？",
    ],
    "general": [
        "非遗有哪些类别？", "中国有多少项联合国非遗名录？",
        "什么是非遗传承人？", "年轻人怎么参与非遗保护？",
        "非遗和文化遗产有什么区别？", "非遗怎么申报的？",
        "非遗为什么适合进入校园教育？", "国家级非遗名录是如何评定的？",
    ],
}

_MIXED_FALLBACK = [
    "湘绣和苏绣有什么区别？", "京剧和昆曲有什么区别？", "古筝和古琴有什么区别？",
    "非遗数字化保护是什么意思？", "非遗如何向外国人介绍？", "非遗生产性保护是什么意思？",
    "太极拳的养生价值体现在哪里？", "传统技艺非遗怎么实现商业化？",
    "非遗传承为什么需要年轻人参与？", "哪些非遗项目正面临消失危险？",
    "非遗节庆活动如何吸引年轻人？", "景德镇陶瓷为什么享誉世界？",
    "传统武术和现代体育有什么关系？", "非遗保护中政府和民间各扮演什么角色？",
]

_PRECISION_FALLBACK = [
    "苏绣的针法有哪些流派？", "昆曲的折子戏和全本有什么区别？",
    "景泰蓝的制作工序有多少道？", "龙泉青瓷釉色如何形成？",
    "皮影的制作材料有哪些讲究？", "古琴曲谱的减字谱怎么读？",
    "端午节各地习俗有哪些差异？", "太极拳的内劲是什么意思？",
    "中医针灸取穴有哪些原则？", "雕版印刷和活字印刷有何本质区别？",
    "云锦为什么只能手工织造？", "剪纸的南北流派有哪些代表作品？",
]


def fetch_kb_questions(
    db, chapters: list[str], limit: int = 6,
    exclude: list[str] | None = None, randomize: bool = True,
    topic_keywords: list[str] | None = None,
) -> list[str]:
    """从KB中按章节提取问题，支持话题锚定排序"""
    from app.models.local_knowledge_base import LocalKnowledgeBase
    from sqlalchemy import func as sqlfunc

    exclude_set = set(exclude or [])
    order_clause = sqlfunc.random() if randomize else LocalKnowledgeBase.id

    records = (
        db.query(LocalKnowledgeBase.question)
        .filter(LocalKnowledgeBase.status == "active", LocalKnowledgeBase.chapter.in_(chapters))
        .order_by(order_clause)
        .all()
    )
    all_qs = [r[0] for r in records]
    filtered = [q for q in all_qs if q not in exclude_set]

    # 话题锚定：含关键词的问题优先
    if topic_keywords:
        anchored, remaining = [], []
        for q in filtered:
            (anchored if any(kw in q for kw in topic_keywords) else remaining).append(q)
        combined = anchored + remaining
        if len(combined) >= limit:
            return combined[:limit]
        return (combined + [q for q in all_qs if q in exclude_set])[:limit]

    if len(filtered) >= limit:
        return filtered[:limit]
    return (filtered + [q for q in all_qs if q in exclude_set])[:limit]


def generate_recommended_questions(
    strategy: str, crs_mode: str, question: str, answer: str,
    db=None, user_id: int = 0, kb_chapter: str = None,
    prev_questions: list[str] | None = None,
) -> list[str]:
    q = (question or "").strip()
    a = (answer or "").strip()
    exclude = list(prev_questions or []) + ([q] if q else [])

    pref_user = None
    if db and user_id:
        from app.models.user import User
        pref_user = db.query(User).filter(User.id == user_id).first()

    if crs_mode == "precision":
        return _gen_precision_questions(q, a, exclude, db, user_id, pref_user)
    return _gen_non_precision_questions(crs_mode, q, a, exclude, db, user_id, kb_chapter, pref_user)


def _gen_precision_questions(
    q: str, a: str, exclude: list[str], db, user_id: int, pref_user=None,
) -> list[str]:
    combined_text = q + " " + a
    precision_chapters: list[str] = []

    if pref_user:
        heritage = _safe_json_loads(pref_user.preferred_heritage_types)
        for h in (heritage or []):
            for kw, chs in _INTEREST_TO_CHAPTERS.items():
                if kw in h:
                    precision_chapters.extend(chs)

    topic_kws = [t for t in SPECIFIC_TERMS if t in combined_text]
    for kw, chs in _INTEREST_TO_CHAPTERS.items():
        if kw in combined_text and kw not in _GENERIC_KWS:
            for c in chs:
                if c not in precision_chapters:
                    precision_chapters.append(c)

    if not precision_chapters:
        precision_chapters = ["传统工艺", "戏曲与表演艺术", "传统美术", "传统音乐"]
    precision_chapters = list(dict.fromkeys(precision_chapters))[:4]

    if db:
        precision_qs = fetch_kb_questions(db, precision_chapters, limit=8, exclude=exclude, randomize=True, topic_keywords=topic_kws or None)
        if len(precision_qs) >= 2:
            return precision_qs[:4]

    pool = [x for x in _PRECISION_FALLBACK if x not in set(exclude)]
    random.shuffle(pool)
    return pool[:4] if pool else _PRECISION_FALLBACK[:4]


def _gen_non_precision_questions(
    crs_mode: str, q: str, a: str, exclude: list[str], db, user_id: int, kb_chapter: str, pref_user=None,
) -> list[str]:
    combined_text = q + " " + a
    matched_chapters = _match_chapters(combined_text)

    content_matched = matched_chapters & CONTENT_CHAPTERS
    if content_matched:
        matched_chapters = content_matched

    topic_kws = [term for term in SPECIFIC_TERMS if term in combined_text]
    effective_kb_chapter = kb_chapter if kb_chapter in CONTENT_CHAPTERS else None

    if effective_kb_chapter and db:
        kb_qs = fetch_kb_questions(db, [effective_kb_chapter], limit=8, exclude=exclude, randomize=True, topic_keywords=topic_kws or None)
        if len(kb_qs) >= 3:
            adjacent = _SEMANTIC_ADJACENT.get(effective_kb_chapter, [])
            if adjacent and len(kb_qs) < 4:
                extra_qs = fetch_kb_questions(db, adjacent, limit=4, exclude=exclude + kb_qs, randomize=True)
                combined = kb_qs[:3] + extra_qs[:1]
            else:
                combined = kb_qs[:4]
            if len(combined) >= 2:
                return combined[:4]

    if crs_mode == "cold_start":
        return _gen_cold_start_questions(combined_text, matched_chapters, exclude, db, user_id, pref_user)
    return _gen_mixed_questions(combined_text, matched_chapters, exclude, db, user_id, pref_user)


def _gen_cold_start_questions(
    combined_text: str, matched_chapters: set, exclude: list[str], db, user_id: int, pref_user=None,
) -> list[str]:
    if matched_chapters and db:
        kb_qs = fetch_kb_questions(db, list(matched_chapters), limit=6, exclude=exclude, randomize=True)
        if len(kb_qs) >= 3:
            return kb_qs[:4]

    attr = _detect_attr(combined_text)
    attr_chapters = {k: list(v) for k, v in _ATTR_CHAPTERS.items()}

    if pref_user:
        heritage = _safe_json_loads(pref_user.preferred_heritage_types)
        extra_chs = []
        for h in (heritage or []):
            for kw, chs in _INTEREST_TO_CHAPTERS.items():
                if kw in h:
                    extra_chs.extend(chs)
        if extra_chs:
            attr_chapters[attr] = list(dict.fromkeys(extra_chs + attr_chapters.get(attr, [])))

    if db:
        target_chapters = attr_chapters.get(attr, attr_chapters["category"])
        kb_qs = fetch_kb_questions(db, target_chapters, limit=8, exclude=exclude, randomize=True)
        if len(kb_qs) >= 2:
            return kb_qs[:4]

    fallback_pool = _COLD_START_FALLBACK.get(attr, _COLD_START_FALLBACK["general"])
    shuffled = [x for x in fallback_pool if x not in set(exclude)]
    random.shuffle(shuffled)
    return shuffled[:4] if shuffled else fallback_pool[:4]


def _gen_mixed_questions(
    combined_text: str, matched_chapters: set, exclude: list[str], db, user_id: int, pref_user=None,
) -> list[str]:
    mixed_chapters = list(matched_chapters) if matched_chapters else []

    if pref_user and not mixed_chapters:
        heritage = _safe_json_loads(pref_user.preferred_heritage_types)
        for h in (heritage or []):
            for kw, chs in _INTEREST_TO_CHAPTERS.items():
                if kw in h:
                    mixed_chapters.extend(chs)

    if not mixed_chapters:
        mixed_chapters = ["传统工艺", "戏曲与表演艺术", "传统美术", "传统音乐"]

    expanded = set(mixed_chapters)
    for ch in list(mixed_chapters):
        expanded.update(_SEMANTIC_ADJACENT.get(ch, []))

    if db:
        kb_qs = fetch_kb_questions(db, list(expanded), limit=10, exclude=exclude, randomize=True)
        if len(kb_qs) >= 2:
            return kb_qs[:4]

    shuffled_mixed = [x for x in _MIXED_FALLBACK if x not in set(exclude)]
    random.shuffle(shuffled_mixed)
    return shuffled_mixed[:4] if shuffled_mixed else _MIXED_FALLBACK[:4]


def rewrite_suggestions(question: str, last_answer: str = "", chat_history: list[dict] | None = None) -> list[str]:
    """调用豆包生成追问建议"""
    q = (question or "").strip()
    if not q:
        return []

    if "阶段" in q or "历程" in q:
        return [
            "非遗保护大致经历了哪几个阶段？",
            "2011年《非遗法》实施后，保护工作有哪些变化？",
            "非遗保护从抢救到活化传播的演进逻辑是什么？",
        ]

    topic_hint = f"（刚回答过：{last_answer[:80]}）" if last_answer else ""
    history_hint = ""
    if chat_history:
        last_q = chat_history[-1].get("content", "")
        if last_q:
            history_hint = f"用户此前的问题：{last_q}"

    from app.services.doubao_client import ask_doubao

    prompt = (
        "你是非遗文化AI助手。用户刚问了以下问题，请给出4个后续追问建议，"
        "每个建议不超过20字，必须与用户刚才的话题紧密相关、有深度，"
        "不要重复用户已问的内容。"
        f"用户问题：{q}{topic_hint}{history_hint}\n"
        "请严格按JSON数组格式回复，例如[\"问题1\",\"问题2\",\"问题3\",\"问题4\"]，不要加其他文字。"
    )

    try:
        result = ask_doubao(prompt)
        if result:
            cleaned = result.strip().strip("```").strip()
            if cleaned.startswith("["):
                return json.loads(cleaned)
    except Exception as e:
        logger.warning("豆包生成追问建议失败: %s", e)

    return []

"""偏好同步

用户偏好写入的统一入口，所有偏好变更都经过此模块。
"""

import json
import logging
import uuid

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.crs_session import CrsSession
from app.models.crs_ask_log import CrsAskLog
from app.services.recommendation_service import _safe_json_loads
from app.services.crs.mappings import (
    KG_ENTITY_TO_CATEGORY,
    KB_CHAPTER_TO_PREFERENCE,
    lookup_option_preference,
    lookup_kg_entity_category,
    lookup_kb_chapter_preference,
    lookup_question_preferences,
)
from app.services.crs.constants import AI_DIALOG_SCORE_DELTA

logger = logging.getLogger(__name__)


def append_preference(user: User, field_name: str, values: list[str]) -> bool:
    """向JSON列表字段追加值，自动去重"""
    if not values:
        return False
    current = _safe_json_loads(getattr(user, field_name))
    changed = False
    for v in values:
        if v not in current:
            current.append(v)
            changed = True
    if changed:
        setattr(user, field_name, json.dumps(current, ensure_ascii=False))
    return changed


def apply_answer_to_preference(user: User, answer: str) -> None:
    """ASK回答 → 偏好字段"""
    mapping = lookup_option_preference(answer)
    if not mapping:
        return
    field_name, value = mapping
    if field_name is None:
        return
    current = _safe_json_loads(getattr(user, field_name, None))
    if value not in current:
        current.append(value)
        setattr(user, field_name, json.dumps(current, ensure_ascii=False) if current else None)


def sync_kg_entity_to_preference(user: User, kg_entity: str) -> bool:
    """KG实体 → 偏好（CRS+KG联动）"""
    if not kg_entity or not user:
        return False
    category = lookup_kg_entity_category(kg_entity)
    if not category:
        return False
    return append_preference(user, "preferred_heritage_types", [category])


def sync_kb_chapter_to_preference(user: User, kb_chapter: str) -> bool:
    """KB章节 → 偏好（KB信号反哺画像）"""
    if not kb_chapter or not user:
        return False
    category = lookup_kb_chapter_preference(kb_chapter)
    if not category:
        return False
    result = append_preference(user, "preferred_heritage_types", [category])
    if result:
        logger.info("KB章节→偏好: chapter=%s, category=%s", kb_chapter, category)
    return result


def sync_question_to_preferences(user: User, question: str) -> bool:
    """问题文本 → 三类偏好（heritage / scene / region）"""
    if not question or not user:
        return False
    prefs = lookup_question_preferences(question)
    updated = False
    field_map = {
        "heritage": "preferred_heritage_types",
        "scene": "preferred_scene_types",
        "region": "preferred_regions",
    }
    for key, field in field_map.items():
        hits = prefs.get(key, set())
        if hits:
            updated |= append_preference(user, field, list(hits))
    if updated:
        logger.info("问题→偏好: user=%s, q='%s'", user.id, question[:30])
    return updated


def auto_create_ask_log(db: Session, user_id: int, question: str, kb_result: dict):
    """AI对话命中KB时，自动创建ASK记录（同一问题不重复创建）"""
    q = (question or "").strip()
    if not q:
        return

    if db.query(CrsAskLog).filter(CrsAskLog.user_id == user_id, CrsAskLog.question_text == q).first():
        return

    session = db.query(CrsSession).filter(
        CrsSession.user_id == user_id, CrsSession.is_active == 1,
    ).first()
    if not session:
        session = CrsSession(session_id=str(uuid.uuid4()), user_id=user_id, is_active=True)
        db.add(session)
        db.flush()

    # 属性推断：优先从KB章节，其次从问题文本
    attribute = _infer_attribute(q, kb_result)

    ask_log = CrsAskLog(
        ask_id=f"AI-{uuid.uuid4().hex[:6]}",
        session_id=session.session_id,
        user_id=user_id,
        attribute=attribute,
        question_text=q,
        answer=f"[AI对话] {q}",
        is_skipped=False,
        score_delta=AI_DIALOG_SCORE_DELTA,
    )
    db.add(ask_log)
    db.commit()
    logger.info("AI对话→ASK: user=%s, q='%s', attr=%s", user_id, q[:30], attribute)


def _infer_attribute(question: str, kb_result: dict) -> str:
    """从问题文本和KB结果推断ASK属性"""
    kb_chapter = kb_result.get("chapter", "") if kb_result else ""
    if kb_chapter:
        if any(kw in kb_chapter for kw in ["国际", "传播"]):
            return "region"
        if any(kw in kb_chapter for kw in ["传承", "数字化", "体验"]):
            return "scene"
    if any(kw in question for kw in ["体验", "研学", "博物馆", "工坊", "数字化", "VR", "AR"]):
        return "scene"
    if any(kw in question for kw in ["华东", "华南", "地区", "国际", "广东", "北京", "西藏", "联合国"]):
        return "region"
    return "category"

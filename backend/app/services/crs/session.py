"""CRS 会话管理"""

import logging
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.crs_session import CrsSession
from app.models.crs_ask_log import CrsAskLog
from app.models.user import User
from app.services.recommendation_service import calc_confidence, generate_ai_recommend_cards
from app.services.crs.ask_templates import ASK_TEMPLATES, SKIP_ANSWERS
from app.services.crs.decision import generate_ask_transition
from app.services.crs.preference import apply_answer_to_preference
from app.services.crs.constants import SESSION_TIMEOUT_MINUTES

logger = logging.getLogger(__name__)


def get_or_create_session(db: Session, user_id: int) -> CrsSession:
    """获取活跃会话，超时则关闭旧会话并创建新的"""
    session = (
        db.query(CrsSession)
        .filter(CrsSession.user_id == user_id, CrsSession.is_active == 1)
        .order_by(CrsSession.updated_at.desc())
        .first()
    )
    if session:
        last_active = session.updated_at or session.created_at
        if last_active and datetime.utcnow() - last_active > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            session.is_active = 0
            db.commit()
        else:
            return session

    session = CrsSession(user_id=user_id, session_id=str(uuid.uuid4()), mode="cold_start", turn_count=0, is_active=1)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def update_session_mode(db: Session, session: CrsSession, confidence: float) -> None:
    """根据置信度更新会话模式"""
    from app.services.recommendation_service import _determine_mode
    new_mode = _determine_mode(confidence)
    if session.mode != new_mode:
        session.mode = new_mode
    db.commit()


def process_ask_answer(db: Session, user_id: int, session_id: str, ask_id: str, answer: str) -> dict:
    """处理ASK回答：记录 → 更新偏好 → 重算置信度 → 刷新推荐"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return calc_confidence(db, user_id)

    template = ASK_TEMPLATES.get(ask_id)
    if not template:
        logger.warning("未知ASK模板: %s", ask_id)
        return calc_confidence(db, user_id)

    is_skip = answer in SKIP_ANSWERS

    # 记录回答
    db.add(CrsAskLog(
        user_id=user_id, session_id=session_id, ask_id=ask_id,
        attribute=template["attribute"], question_text=template["prompt"],
        answer=answer, is_skipped=is_skip,
        score_delta=0 if is_skip else template["score_delta"],
    ))

    # 更新偏好
    apply_answer_to_preference(user, answer)

    # 更新会话状态
    session = db.query(CrsSession).filter(CrsSession.session_id == session_id).first()
    if session:
        session.turn_count = (session.turn_count or 0) + 1
        session.last_ask_attribute = template["attribute"]
        session.last_ask_id = ask_id
        session.add_asked_attribute(template["attribute"])
        db.commit()

    # 重算置信度
    new_confidence = calc_confidence(db, user_id)
    new_confidence["transition_msg"] = generate_ask_transition(ask_id, answer, is_skip)

    # 即时刷新推荐
    if not is_skip:
        try:
            new_confidence["recommend_cards"] = generate_ai_recommend_cards(db, user_id, "")
        except Exception as e:
            logger.warning("ASK后刷新推荐失败: %s", e)

    return new_confidence

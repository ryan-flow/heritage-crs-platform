from fastapi import APIRouter, Depends
import json
import logging
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.responses import success
from app.models.recommend_log import RecommendLog
from app.models.user import User
from app.services.recommendation_service import generate_recommendation_payload, calc_confidence

logger = logging.getLogger(__name__)

router = APIRouter()


class TrackIn(BaseModel):
    user_id: int | None = None
    action: str
    target_type: str
    target_id: int
    source_scene: str | None = None
    explain: dict | None = None


@router.post("/track")
def track_recommend_action(payload: TrackIn, db: Session = Depends(get_db)):
    if payload.action not in {"expose", "click", "view", "feedback_like", "feedback_dislike"}:
        return success({"ok": False}, "action非法")
    if payload.target_type not in {"content", "event", "topic"}:
        return success({"ok": False}, "target_type非法")

    db.add(
        RecommendLog(
            user_id=payload.user_id,
            action=payload.action,
            target_type=payload.target_type,
            target_id=payload.target_id,
            source_scene=payload.source_scene,
            explain_json=json.dumps(payload.explain or {}, ensure_ascii=False),
        )
    )
    db.commit()

    # CRS v2.0.1：click/view/feedback行为自动更新隐式偏好缓存
    if payload.user_id and payload.action in ("click", "view", "feedback_like"):
        try:
            _refresh_implicit_cache(db, payload.user_id)
        except Exception as e:
            logger.warning("刷新隐式偏好缓存失败(user=%s): %s", payload.user_id, e)

    return success({"ok": True})


def _refresh_implicit_cache(db: Session, user_id: int) -> None:
    """用户产生click/view行为后，重新计算score_implicit并缓存到User表"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return

    # 只重算隐式维度（不需要全量重算）
    from app.services.recommendation_service import calc_implicit_score
    score_implicit = calc_implicit_score(db, user_id)
    user.score_implicit = score_implicit

    # 同步更新总置信度（用缓存的显式+对话分数）
    score_explicit = user.score_explicit or 0
    score_dialogue = user.score_dialogue or 0
    user.confidence_score = round(
        0.4 * score_explicit + 0.35 * score_implicit + 0.25 * score_dialogue, 1
    )
    db.commit()


@router.get("")
def get_recommendations(user_id: int | None = None, context: str = "", scene: str = "home", db: Session = Depends(get_db)):
    result = generate_recommendation_payload(db, user_id, context_text=context, scene=scene)

    # CRS v2.0.4：首页推荐集成CRS置信度
    if user_id:
        try:
            confidence_result = calc_confidence(db, user_id, use_cache=True)
            result["crs_state"] = {
                "mode": confidence_result.get("mode", "cold_start"),
                "confidence_score": confidence_result.get("confidence_score", 0),
                "confidence_score_raw": confidence_result.get("confidence_score_raw", confidence_result.get("confidence_score", 0)),
                "stage_progress_percent": confidence_result.get("stage_progress_percent", 0),
                "need_cold_start": confidence_result.get("mode") == "cold_start",
            }
        except Exception:
            pass

    return success(result)

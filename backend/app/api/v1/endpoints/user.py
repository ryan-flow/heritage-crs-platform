import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.responses import success
from app.models.activity import Activity
from app.models.activity_registration import ActivityRegistration
from app.models.ai_qa_log import AIQALog
from app.models.discussion_comment import DiscussionComment
from app.models.discussion_extra import DiscussionFavorite
from app.models.discussion_like import DiscussionLike
from app.models.discussion_topic import DiscussionTopic
from app.models.recommend_log import RecommendLog
from app.models.user import User
from app.services.recommendation_service import build_strategy_summary, build_user_profile


router = APIRouter()


class PreferenceIn(BaseModel):
    heritage_types: list[str] = Field(default_factory=list)
    scene_types: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)


class NicknameIn(BaseModel):
    nickname: str = Field(min_length=1, max_length=20)


PREFERENCE_CANONICAL_MAP = {
    "heritage": {
        "工艺": "工艺",
        "传统技艺": "工艺",
        "传统美术": "工艺",
        "戏曲": "戏曲",
        "传统音乐": "戏曲",
        "传统舞蹈": "戏曲",
        "民俗": "民俗",
        "民俗节俗": "民俗",
        "节俗": "民俗",
        "医药": "医药",
        "饮食医药": "医药",
    },
    "scene": {
        "知识阅读": "知识阅读",
        "阅读了解": "知识阅读",
        "活动体验": "活动体验",
        "线下体验": "活动体验",
        "论坛交流": "论坛交流",
        "社区交流": "论坛交流",
        "亲子研学": "活动体验",
        "深度考据": "知识阅读",
    },
    "region": {
        "华东": "华东",
        "华东地区": "华东",
        "华南": "华南",
        "华南地区": "华南",
        "西南": "西南",
        "西南地区": "西南",
        "华北": "华北",
        "华北地区": "华北",
        "西北": "西北",
        "西北地区": "西北",
        "东北": "东北",
        "东北地区": "东北",
    },
}


def _normalize_preferences(values: list[str], kind: str) -> list[str]:
    mapping = PREFERENCE_CANONICAL_MAP.get(kind, {})
    normalized = []
    for value in values or []:
        text = str(value or "").strip()
        if not text:
            continue
        normalized_value = mapping.get(text, text)
        if normalized_value not in normalized:
            normalized.append(normalized_value)
    return normalized


def _user_to_dict(user: User) -> dict:
    def _loads(v: str | None) -> list[str]:
        if not v:
            return []
        try:
            return json.loads(v)
        except Exception:
            return []

    return {
        "id": user.id,
        "openid": user.openid,
        "nickname": user.nickname,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "preferred_heritage_types": _loads(user.preferred_heritage_types),
        "preferred_scene_types": _loads(user.preferred_scene_types),
        "preferred_regions": _loads(user.preferred_regions),
        "created_at": user.created_at,
    }


@router.get("/me/{user_id}")
def get_me(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return success(_user_to_dict(user))


@router.put("/me/{user_id}")
def update_nickname(user_id: int, payload: NicknameIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.nickname = payload.nickname.strip()
    db.commit()
    db.refresh(user)
    return success(_user_to_dict(user), "昵称更新成功")


@router.put("/me/{user_id}/preferences")
def update_preferences(user_id: int, payload: PreferenceIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    normalized_heritage = _normalize_preferences(payload.heritage_types, "heritage")
    normalized_scene = _normalize_preferences(payload.scene_types, "scene")
    normalized_region = _normalize_preferences(payload.regions, "region")

    user.preferred_heritage_types = json.dumps(normalized_heritage, ensure_ascii=False)
    user.preferred_scene_types = json.dumps(normalized_scene, ensure_ascii=False)
    user.preferred_regions = json.dumps(normalized_region, ensure_ascii=False)
    db.commit()
    db.refresh(user)
    return success(_user_to_dict(user), "偏好更新成功")


@router.get("/{user_id}/recommend-profile")
def get_recommend_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    profile = build_user_profile(db, user_id)
    strategy_summary = build_strategy_summary(profile)

    # 4维偏好雷达图数据：从heritage字典聚合到4大类目
    heritage = profile.get("heritage", {})
    radar = _heritage_to_radar(heritage)

    action_rows = (
        db.query(RecommendLog.target_type, RecommendLog.action, func.count(RecommendLog.id))
        .filter(RecommendLog.user_id == user_id)
        .group_by(RecommendLog.target_type, RecommendLog.action)
        .all()
    )
    feedback = {"content": 0, "event": 0, "topic": 0}
    action_breakdown = {}
    for target_type, action, count in action_rows:
        feedback[target_type] = feedback.get(target_type, 0) + int(count or 0)
        action_breakdown[f"{target_type}_{action}"] = int(count or 0)

    topic_count = db.query(DiscussionTopic).filter(DiscussionTopic.user_id == user_id).count()
    comment_count = db.query(DiscussionComment).filter(DiscussionComment.user_id == user_id).count()
    favorite_count = db.query(DiscussionFavorite).filter(DiscussionFavorite.user_id == user_id).count()
    like_count = db.query(DiscussionLike).filter(DiscussionLike.user_id == user_id).count()
    registration_count = db.query(ActivityRegistration).filter(ActivityRegistration.user_id == user_id).count()
    qa_count = db.query(AIQALog).filter(AIQALog.user_id == user_id).count()

    return success(
        {
            "portrait": {
                "heritage_terms": sorted(profile["heritage"].keys(), key=lambda x: profile["heritage"][x], reverse=True)[:6],
                "scene_terms": sorted(profile["scene"].keys(), key=lambda x: profile["scene"][x], reverse=True)[:4],
                "region_terms": sorted(profile["region"].keys(), key=lambda x: profile["region"][x], reverse=True)[:4],
                "sources": profile["sources"],
                "summary_text": strategy_summary["summary_text"],
            },
            "radar": radar,
            "feedback": feedback,
            "action_breakdown": action_breakdown,
            "activity": {
                "qa_count": qa_count,
                "registration_count": registration_count,
                "topic_count": topic_count,
                "comment_count": comment_count,
                "favorite_count": favorite_count,
                "like_count": like_count,
            },
        }
    )


# 遗产类目→4维雷达映射
_RADAR_CATEGORY_MAP = {
    "工艺": "传统技艺",
    "传统技艺": "传统技艺",
    "传统美术": "传统技艺",
    "云锦": "传统技艺",
    "书法": "传统技艺",
    "戏曲": "戏曲艺术",
    "昆曲": "戏曲艺术",
    "皮影": "戏曲艺术",
    "传统音乐": "戏曲艺术",
    "古琴": "戏曲艺术",
    "传统舞蹈": "戏曲艺术",
    "民俗": "民俗节庆",
    "节俗": "民俗节庆",
    "节气": "民俗节庆",
    "端午": "民俗节庆",
}


def _heritage_to_radar(heritage: dict) -> dict:
    """将heritage关键词权重聚合为4维雷达数据"""
    categories = {"传统技艺": 0.0, "戏曲艺术": 0.0, "民俗节庆": 0.0, "传统医药": 0.0}
    for keyword, weight in heritage.items():
        cat = _RADAR_CATEGORY_MAP.get(keyword)
        if cat and cat in categories:
            categories[cat] += weight
        else:
            # 未映射的关键词归入"传统技艺"
            categories["传统技艺"] += weight * 0.3

    # 归一化到0-100
    max_val = max(categories.values()) if any(categories.values()) else 1.0
    return {
        "dimensions": [
            {"name": name, "value": round(min(score / max_val * 100, 100), 1)}
            for name, score in categories.items()
        ],
        "top_keywords": sorted(heritage.keys(), key=lambda x: heritage[x], reverse=True)[:3],
    }


@router.get("/{user_id}/registrations")
def get_my_registrations(user_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(ActivityRegistration, Activity)
        .join(Activity, Activity.id == ActivityRegistration.activity_id)
        .filter(ActivityRegistration.user_id == user_id)
        .order_by(ActivityRegistration.id.desc())
        .all()
    )
    items = []
    for registration, activity in rows:
        items.append(
            {
                "registration_id": registration.id,
                "activity_id": activity.id,
                "activity_title": activity.title,
                "status": registration.status,
                "remark": registration.remark,
                "created_at": registration.created_at,
            }
        )
    return success({"items": items, "total": len(items)})


@router.get("/{user_id}")
def fe_get_user(user_id: int, db: Session = Depends(get_db)):
    """Frontend compatible: GET /users/{id}"""
    from app.api.v1.endpoints.user import get_me
    return get_me(user_id, db)


@router.get("/{user_id}/history")
def fe_user_history(user_id: int, db: Session = Depends(get_db)):
    """Frontend compatible: GET /users/{id}/history"""
    from app.models.recommend_log import RecommendLog
    from app.models.content import Content
    rows = (
        db.query(RecommendLog, Content)
        .join(Content, Content.id == RecommendLog.target_id)
        .filter(
            RecommendLog.user_id == user_id,
            RecommendLog.target_type == "content",
            RecommendLog.action.in_(["view", "click"]),
        )
        .order_by(RecommendLog.id.desc())
        .limit(100)
        .all()
    )
    seen = set()
    items = []
    for log, content in rows:
        if content.id in seen:
            continue
        seen.add(content.id)
        from app.api.v1.endpoints.content import _content_to_dict
        d = _content_to_dict(content)
        d["viewed_at"] = str(log.created_at or "")
        items.append(d)
    return success({"contents": items})

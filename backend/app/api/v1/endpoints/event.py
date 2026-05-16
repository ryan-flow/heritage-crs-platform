from datetime import datetime
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.core.responses import success
from app.models.activity import Activity
from app.models.activity_registration import ActivityRegistration
from app.models.recommend_log import RecommendLog
from app.models.user import User
from app.services.display_enrichment import build_event_display

logger = logging.getLogger(__name__)

router = APIRouter()


def _sync_event_to_preference(db: Session, user_id: int, event: Activity) -> None:
    """活动报名后自动更新用户偏好（CRS联动）

    从活动标题和描述中提取非遗类目关键词，自动加入偏好列表。
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return

    text = f"{event.title or ''} {event.description or ''}"
    type_mapping = {
        "工艺": ["工艺", "手工", "制作", "织", "绣", "陶", "瓷", "雕", "剪"],
        "戏曲": ["戏曲", "剧", "曲艺", "音乐", "表演", "唱", "昆曲", "京剧"],
        "民俗": ["民俗", "节", "俗", "祭祀", "庆典", "庙会", "端午"],
        "医药": ["医药", "针灸", "中药", "养生", "中医"],
    }

    current = json.loads(user.preferred_heritage_types or "[]")
    updated = False
    for category, keywords in type_mapping.items():
        if category not in current and any(kw in text for kw in keywords):
            current.append(category)
            updated = True

    if updated:
        user.preferred_heritage_types = json.dumps(current, ensure_ascii=False)
        db.commit()
        logger.info("活动报名→偏好更新: user=%s, event=%s, types=%s", user_id, event.id, current)


class ActivityIn(BaseModel):
    title: str
    cover_url: str | None = None
    location: str | None = None
    organizer: str | None = None
    start_time: str
    end_time: str
    max_participants: int = 50
    description: str | None = None
    notes: str | None = None
    status: str = "open"


class RegisterIn(BaseModel):
    user_id: int
    remark: str | None = None


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", ""))


def _media_full_url(request: Request, url: str | None) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    base = str(request.base_url).rstrip("/")
    return f"{base}{raw if raw.startswith('/') else '/' + raw}"


@router.get("/")
def list_events(
    request: Request,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Activity)
    if status and status not in ("全部", ""):
        query = query.filter(Activity.status == status)
    items = query.order_by(Activity.is_featured.desc(), Activity.id.desc()).all()
    result = []
    for item in items:
        reg_count = db.query(ActivityRegistration).filter(ActivityRegistration.activity_id == item.id).count()
        data = {
            "id": item.id,
            "title": item.title,
            "cover_url": item.cover_url,
            "cover_full_url": _media_full_url(request, item.cover_url),
            "location": item.location,
            "organizer": item.organizer,
            "start_time": item.start_time.isoformat() if item.start_time else "",
            "end_time": item.end_time.isoformat() if item.end_time else "",
            "max_participants": item.max_participants,
            "current_participants": reg_count,
            "description": item.description,
            "notes": item.notes,
            "status": item.status,
            "is_featured": bool(getattr(item, "is_featured", False)),
            "created_at": str(item.created_at or ""),
        }
        result.append(data)
    return success(result)


@router.get("/registrations")
def get_my_event_registrations(
    user_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """Get current user's activity registrations.

    Filters by user_id query parameter (required).
    Returns list of {id, activity_id, activity_title, status, created_at}.
    """
    if not user_id:
        return success({"items": [], "total": 0}, "请提供 user_id 参数")

    rows = (
        db.query(ActivityRegistration, Activity)
        .join(Activity, Activity.id == ActivityRegistration.activity_id)
        .filter(ActivityRegistration.user_id == user_id)
        .order_by(ActivityRegistration.id.desc())
        .all()
    )

    items = []
    for registration, activity in rows:
        if status and registration.status != status:
            continue
        items.append({
            "id": registration.id,
            "activity_id": activity.id,
            "activity_title": activity.title,
            "cover_url": activity.cover_url or "",
            "location": activity.location or "",
            "start_time": activity.start_time.isoformat() if activity.start_time else "",
            "status": registration.status,
            "remark": registration.remark or "",
            "created_at": str(registration.created_at or ""),
        })

    return success({"items": items, "total": len(items)})


@router.get("/{event_id}")
def get_event(event_id: int, request: Request, user_id: int | None = None, db: Session = Depends(get_db)):
    item = db.query(Activity).filter(Activity.id == event_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="活动不存在")

    regs = db.query(ActivityRegistration).filter(ActivityRegistration.activity_id == event_id).all()
    registration_count = len(regs)

    my_status = "none"
    if user_id:
        my_reg = next((r for r in regs if r.user_id == user_id), None)
        if my_reg:
            my_status = my_reg.status

    return success(
        {
            "id": item.id,
            "title": item.title,
            "cover_url": item.cover_url,
            "cover_full_url": _media_full_url(request, item.cover_url),
            "location": item.location,
            "organizer": item.organizer,
            "start_time": item.start_time.isoformat() if item.start_time else "",
            "end_time": item.end_time.isoformat() if item.end_time else "",
            "max_participants": item.max_participants,
            "current_participants": registration_count,
            "description": item.description,
            "notes": item.notes,
            "status": item.status,
            "created_at": str(item.created_at or ""),
            "registration_count": registration_count,
            "registration_progress": round((registration_count / item.max_participants) * 100, 1) if item.max_participants else 0,
            "my_registration_status": my_status,
            "display_blocks": build_event_display(item.description, item.notes, item.location),
        }
    )


@router.post("/{event_id}/register")
def register_event(event_id: int, payload: RegisterIn, db: Session = Depends(get_db)):
    event = db.query(Activity).filter(Activity.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="活动不存在")

    current_count = (
        db.query(ActivityRegistration)
        .filter(ActivityRegistration.activity_id == event_id, ActivityRegistration.status.in_(["registered", "checked_in"]))
        .count()
    )
    if current_count >= event.max_participants:
        raise HTTPException(status_code=400, detail="活动报名人数已满")

    registration = ActivityRegistration(
        activity_id=event_id,
        user_id=payload.user_id,
        remark=payload.remark,
        status="registered",
    )
    db.add(registration)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="请勿重复报名")
    db.refresh(registration)
    db.add(RecommendLog(user_id=payload.user_id, action="click", target_type="event", target_id=event_id, source_scene="event_register"))
    db.commit()

    # CRS v2.0.4：活动报名自动更新用户偏好
    try:
        _sync_event_to_preference(db, payload.user_id, event)
    except Exception:
        pass  # 静默失败，不影响报名

    return success(registration, "报名成功")


@router.post("/{event_id}/cancel")
def cancel_registration(event_id: int, user_id: int, db: Session = Depends(get_db)):
    reg = (
        db.query(ActivityRegistration)
        .filter(ActivityRegistration.activity_id == event_id, ActivityRegistration.user_id == user_id)
        .first()
    )
    if not reg:
        raise HTTPException(status_code=404, detail="报名记录不存在")
    if reg.status == "checked_in":
        raise HTTPException(status_code=400, detail="已签到记录不可取消")
    reg.status = "cancelled"
    db.commit()
    db.refresh(reg)
    return success(reg, "已取消报名")


@router.post("/admin/{registration_id}/status", dependencies=[Depends(require_admin)])
def admin_update_registration_status(registration_id: int, status: str, db: Session = Depends(get_db)):
    if status not in {"registered", "checked_in", "completed", "cancelled"}:
        raise HTTPException(status_code=400, detail="状态值非法")
    reg = db.query(ActivityRegistration).filter(ActivityRegistration.id == registration_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="报名记录不存在")
    reg.status = status
    db.commit()
    db.refresh(reg)
    return success(reg, "状态更新成功")


@router.post("/admin", dependencies=[Depends(require_admin)])
def create_event(payload: ActivityIn, db: Session = Depends(get_db)):
    data = payload.model_dump()
    data["start_time"] = _parse_dt(payload.start_time)
    data["end_time"] = _parse_dt(payload.end_time)
    item = Activity(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return success(item, "创建成功")


@router.put("/admin/{event_id}", dependencies=[Depends(require_admin)])
def update_event(event_id: int, payload: ActivityIn, db: Session = Depends(get_db)):
    item = db.query(Activity).filter(Activity.id == event_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="活动不存在")
    data = payload.model_dump()
    data["start_time"] = _parse_dt(payload.start_time)
    data["end_time"] = _parse_dt(payload.end_time)
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return success(item, "更新成功")


@router.delete("/admin/{event_id}", dependencies=[Depends(require_admin)])
def delete_event(event_id: int, db: Session = Depends(get_db)):
    item = db.query(Activity).filter(Activity.id == event_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="活动不存在")
    db.delete(item)
    db.commit()
    return success({"id": event_id}, "删除成功")

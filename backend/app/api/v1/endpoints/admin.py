import csv, io, json, os, ssl, time, urllib.request
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.core.responses import success
from app.models.activity import Activity
from app.models.activity_registration import ActivityRegistration
from app.models.ai_qa_log import AIQALog
from app.models.content import Content
from app.models.discussion_comment import DiscussionComment
from app.models.discussion_extra import DiscussionFavorite, DiscussionTopicTag
from app.models.discussion_topic import DiscussionTopic
from app.models.discussion_like import DiscussionLike
from app.models.recommend_log import RecommendLog
from app.models.user import User
from app.models.local_knowledge_base import LocalKnowledgeBase
from app.services.content_governance import apply_whitelist, build_whitelist

router = APIRouter(dependencies=[Depends(require_admin)])


def _parse_dt(v: str | None):
    return datetime.fromisoformat(v.replace("Z", "")) if v else None


def _parse_date(v: str | None):
    if not v:
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", ""))
    except Exception:
        return None


class UserManageIn(BaseModel):
    nickname: str | None = None
    phone: str | None = None
    role: str = "user"
    is_active: bool = True


class ContentManageIn(BaseModel):
    title: str
    cover_url: str | None = None
    content_type: str
    source_site: str | None = None
    source_url: str | None = None
    chapter: str | None = None
    sub_chapter: str | None = None
    summary: str | None = None
    body: str | None = None
    quality_score: float = 0.0
    review_status: str = "pending"
    import_batch: str | None = None
    status: str = "draft"
    published_at: str | None = None
    created_by: int | None = None


class ActivityManageIn(BaseModel):
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
    is_featured: bool = False


class TopicManageIn(BaseModel):
    title: str
    content: str
    nickname: str | None = None
    cover_url: str | None = None
    like_count: int = 0
    favorite_count: int = 0
    comment_count: int = 0
    is_featured: bool = False


class ContentReviewIn(BaseModel):
    review_status: str | None = None
    status: str | None = None
    action: str | None = None  # frontend: "approve" | "reject" | "draft"


AUDIT_REPORT_PATH = Path(__file__).resolve().parents[4] / "storage" / "audit" / "content_audit_report.json"
UPLOAD_IMAGE_DIR = Path(__file__).resolve().parents[4] / "storage" / "uploads" / "images"


def _behavior_map(db: Session) -> dict[int, dict]:
    def rows(q):
        return {uid or 0: c for uid, c in q}

    qa = rows(db.query(AIQALog.user_id, func.count(AIQALog.id)).group_by(AIQALog.user_id).all())
    click = rows(db.query(RecommendLog.user_id, func.count(RecommendLog.id)).filter(RecommendLog.action == "click").group_by(RecommendLog.user_id).all())
    reg = rows(db.query(ActivityRegistration.user_id, func.count(ActivityRegistration.id)).group_by(ActivityRegistration.user_id).all())
    topic = rows(db.query(DiscussionTopic.user_id, func.count(DiscussionTopic.id)).group_by(DiscussionTopic.user_id).all())
    comment = rows(db.query(DiscussionComment.user_id, func.count(DiscussionComment.id)).group_by(DiscussionComment.user_id).all())
    all_ids = set(qa) | set(click) | set(reg) | set(topic) | set(comment)

    out: dict[int, dict] = {}
    for uid in all_ids:
        out[uid] = {
            "qa_count": qa.get(uid, 0),
            "recommend_click_count": click.get(uid, 0),
            "registration_count": reg.get(uid, 0),
            "topic_count": topic.get(uid, 0),
            "comment_count": comment.get(uid, 0),
        }
        out[uid]["total_actions"] = sum(out[uid].values())
    return out


@router.post("/upload/image")
async def admin_upload_image(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        raise HTTPException(status_code=400, detail="仅支持 jpg/jpeg/png/webp/gif")
    UPLOAD_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid4().hex}{ext}"
    target = UPLOAD_IMAGE_DIR / name
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件为空")
    target.write_bytes(content)
    return success({"url": f"/storage/uploads/images/{name}"}, "上传成功")


@router.get("/contents")
def admin_list_contents(
    keyword: str | None = None,
    search: str | None = None,
    status: str = "all",
    db: Session = Depends(get_db),
):
    q = db.query(Content)
    actual_keyword = keyword or search
    if actual_keyword:
        q = q.filter((Content.title.contains(actual_keyword)) | (Content.summary.contains(actual_keyword)))
    if status and status != "all":
        q = q.filter(Content.status == status)
    items = q.order_by(Content.id.desc()).all()
    from app.api.v1.endpoints.content import _content_to_dict
    return success([_content_to_dict(c) for c in items])


@router.post("/contents")
def admin_create_content(payload: ContentManageIn, db: Session = Depends(get_db)):
    data = payload.model_dump()
    data["published_at"] = _parse_dt(payload.published_at)
    item = Content(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return success(item, "创建成功")


# ── 全量内容接口（用于质量检查全览，优先级高于 {content_id} 参数路由）───
@router.get("/contents/all")
def admin_list_all_contents(db: Session = Depends(get_db)):
    """返回所有内容，质量分降序排列"""
    items = db.query(Content).order_by(Content.quality_score.desc().nullslast(), Content.id.desc()).all()
    rows = [{
        "id": item.id,
        "title": item.title,
        "summary": item.summary,
        "body": item.body,
        "status": item.status,
        "review_status": item.review_status,
        "quality_score": item.quality_score,
        "category_cn": item.chapter,
        "cover_url": item.cover_url,
        "import_batch": item.import_batch,
        "published_at": item.published_at,
    } for item in items]
    return success({"items": rows, "total": len(rows)})


@router.get("/contents/{content_id}")
def admin_get_content(content_id: int, db: Session = Depends(get_db)):
    item = db.query(Content).filter(Content.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="内容不存在")
    return success(item)


@router.put("/contents/{content_id}")
def admin_update_content(content_id: int, payload: ContentManageIn, db: Session = Depends(get_db)):
    item = db.query(Content).filter(Content.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="内容不存在")
    data = payload.model_dump(exclude_unset=True)
    if "published_at" in data:
        data["published_at"] = _parse_dt(payload.published_at)
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return success(item, "更新成功")


@router.put("/contents/{content_id}/status")
def admin_update_content_status(content_id: int, status: str, db: Session = Depends(get_db)):
    if status not in {"draft", "published", "archived"}:
        raise HTTPException(status_code=400, detail="状态值非法")
    item = db.query(Content).filter(Content.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="内容不存在")
    item.status = status
    if status == "published" and not item.published_at:
        item.published_at = datetime.now()
    db.commit()
    db.refresh(item)
    return success(item, "状态更新成功")


@router.put("/contents/{content_id}/review")
def admin_update_content_review(content_id: int, payload: ContentReviewIn, db: Session = Depends(get_db)):
    item = db.query(Content).filter(Content.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="内容不存在")

    # 前端 action 字段映射
    if payload.action:
        action_map = {
            "approve": ("approved", "published"),
            "reject": ("rejected", "draft"),
            "draft": ("pending", "draft"),
        }
        mapped = action_map.get(payload.action)
        if not mapped:
            raise HTTPException(status_code=400, detail="无效的操作")
        payload.review_status, payload.status = mapped

    if payload.review_status and payload.review_status not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="审核状态非法")

    if payload.review_status:
        item.review_status = payload.review_status
    if payload.status:
        item.status = payload.status
    elif payload.review_status == "approved" and item.status == "draft":
        item.status = "published"
        if not item.published_at:
            item.published_at = datetime.now()
    elif payload.review_status == "rejected":
        item.status = "draft"
    db.commit()
    db.refresh(item)
    from app.api.v1.endpoints.content import _content_to_dict
    return success(_content_to_dict(item), "审核状态更新成功")


@router.get("/contents/audit/report")
def admin_get_content_audit_report():
    if not AUDIT_REPORT_PATH.exists():
        return success({"exists": False, "items": [], "total": 0, "flagged": 0}, "暂无审计报告")
    payload = json.loads(AUDIT_REPORT_PATH.read_text(encoding="utf-8"))
    payload["exists"] = True
    return success(payload)


@router.get("/contents/audit/issues")
def admin_list_content_issues(db: Session = Depends(get_db)):
    items = db.query(Content).filter(
        (Content.review_status == "pending") |
        (Content.quality_score < 0.8)
    ).order_by(Content.quality_score.asc(), Content.id.desc()).all()
    rows = [{
        "id": item.id,
        "title": item.title,
        "status": item.status,
        "review_status": item.review_status,
        "quality_score": item.quality_score,
        "source_site": item.source_site,
        "import_batch": item.import_batch,
        "published_at": item.published_at,
    } for item in items]
    return success({"items": rows, "total": len(rows)})


@router.get("/contents/whitelist/candidates")
def admin_list_content_whitelist_candidates(db: Session = Depends(get_db)):
    items = build_whitelist(db.query(Content).all())
    rows = [{
        "id": item.id,
        "title": item.title,
        "summary": item.summary,
        "body": item.body,
        "status": item.status,
        "review_status": item.review_status,
        "quality_score": item.quality_score,
        "category_cn": item.chapter,
        "cover_url": item.cover_url,
        "import_batch": item.import_batch,
        "published_at": item.published_at,
    } for item in items]
    return success({"items": rows, "total": len(rows)})


@router.post("/contents/whitelist/promote")
def admin_promote_content_whitelist(db: Session = Depends(get_db)):
    items = db.query(Content).all()
    result = apply_whitelist(items)
    db.commit()
    return success({"total": len(items), **result}, "高质量内容白名单回补完成")


@router.delete("/contents/{content_id}")
def admin_delete_content(content_id: int, db: Session = Depends(get_db)):
    item = db.query(Content).filter(Content.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="内容不存在")
    db.delete(item)
    db.commit()
    return success({"id": content_id}, "删除成功")


@router.get("/activities")
def admin_list_activities(
    keyword: str | None = None,
    search: str | None = None,
    status: str = "all",
    db: Session = Depends(get_db),
):
    q = db.query(Activity)
    actual_keyword = keyword or search
    if actual_keyword:
        q = q.filter((Activity.title.contains(actual_keyword)) | (Activity.location.contains(actual_keyword)))
    if status and status != "all":
        q = q.filter(Activity.status == status)
    items = q.order_by(Activity.id.desc()).all()
    result = []
    for item in items:
        reg_count = db.query(ActivityRegistration).filter(ActivityRegistration.activity_id == item.id).count()
        result.append({
            "id": item.id,
            "title": item.title,
            "cover_url": item.cover_url or "",
            "location": item.location or "",
            "organizer": item.organizer or "",
            "start_time": str(item.start_time or ""),
            "end_time": str(item.end_time or ""),
            "max_participants": item.max_participants,
            "current_participants": reg_count,
            "description": item.description or "",
            "notes": item.notes or "",
            "status": item.status or "",
            "is_featured": bool(getattr(item, "is_featured", False)),
            "created_at": str(item.created_at or ""),
        })
    return success(result)


@router.get("/activities/{activity_id}")
def admin_get_activity(activity_id: int, db: Session = Depends(get_db)):
    item = db.query(Activity).filter(Activity.id == activity_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="活动不存在")
    return success(item)


@router.post("/activities")
def admin_create_activity(payload: ActivityManageIn, db: Session = Depends(get_db)):
    item = Activity(
        title=payload.title,
        cover_url=payload.cover_url,
        location=payload.location,
        organizer=payload.organizer,
        start_time=_parse_dt(payload.start_time),
        end_time=_parse_dt(payload.end_time),
        max_participants=payload.max_participants,
        description=payload.description,
        notes=payload.notes,
        status=payload.status,
        is_featured=payload.is_featured,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return success(item, "创建成功")


@router.put("/activities/{activity_id}")
def admin_update_activity(activity_id: int, payload: ActivityManageIn, db: Session = Depends(get_db)):
    item = db.query(Activity).filter(Activity.id == activity_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="活动不存在")
    data = payload.model_dump(exclude_unset=True)
    if "start_time" in data:
        item.start_time = _parse_dt(payload.start_time)
    if "end_time" in data:
        item.end_time = _parse_dt(payload.end_time)
    for k, v in data.items():
        if k in {"start_time", "end_time"}:
            continue
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return success(item, "更新成功")


@router.put("/activities/{activity_id}/status")
def admin_update_activity_status(activity_id: int, status: str, db: Session = Depends(get_db)):
    if status not in {"open", "closed"}:
        raise HTTPException(status_code=400, detail="状态值非法")
    item = db.query(Activity).filter(Activity.id == activity_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="活动不存在")
    item.status = status
    db.commit()
    db.refresh(item)
    return success(item, "状态更新成功")


@router.delete("/activities/{activity_id}")
def admin_delete_activity(activity_id: int, db: Session = Depends(get_db)):
    item = db.query(Activity).filter(Activity.id == activity_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="活动不存在")
    db.delete(item)
    db.commit()
    return success({"id": activity_id}, "删除成功")


@router.get("/activities/{activity_id}/registrations")
def admin_activity_registrations(activity_id: int, db: Session = Depends(get_db)):
    rows = db.query(ActivityRegistration, User).join(User, User.id == ActivityRegistration.user_id).filter(ActivityRegistration.activity_id == activity_id).order_by(ActivityRegistration.id.desc()).all()
    items = [{
        "registration_id": reg.id,
        "activity_id": reg.activity_id,
        "user_id": reg.user_id,
        "nickname": user.nickname,
        "status": reg.status,
        "remark": reg.remark,
        "created_at": reg.created_at,
        "updated_at": reg.updated_at,
    } for reg, user in rows]
    return success({"items": items, "total": len(items)})


@router.put("/activities/registrations/{registration_id}/status")
def admin_registration_status(registration_id: int, status: str, db: Session = Depends(get_db)):
    if status not in {"registered", "checked_in", "completed", "cancelled"}:
        raise HTTPException(status_code=400, detail="状态值非法")
    reg = db.query(ActivityRegistration).filter(ActivityRegistration.id == registration_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="报名记录不存在")
    reg.status = status
    db.commit()
    db.refresh(reg)
    return success(reg, "状态更新成功")


@router.put("/contents/{content_id}/feature")
def admin_set_content_feature(content_id: int, is_featured: bool, db: Session = Depends(get_db)):
    item = db.query(Content).filter(Content.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="内容不存在")
    item.is_featured = is_featured
    db.commit()
    db.refresh(item)
    return success(item, "加精状态已更新")


@router.put("/activities/{activity_id}/feature")
def admin_set_activity_feature(activity_id: int, is_featured: bool, db: Session = Depends(get_db)):
    item = db.query(Activity).filter(Activity.id == activity_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="活动不存在")
    item.is_featured = is_featured
    db.commit()
    db.refresh(item)
    return success(item, "加精状态已更新")


@router.get("/topics")
def admin_list_topics(keyword: str | None = None, search: str | None = None, db: Session = Depends(get_db)):
    q = db.query(DiscussionTopic)
    actual_keyword = keyword or search
    if actual_keyword:
        q = q.filter((DiscussionTopic.title.contains(actual_keyword)) | (DiscussionTopic.content.contains(actual_keyword)))
    items = q.order_by(DiscussionTopic.is_featured.desc(), DiscussionTopic.id.desc()).all()
    rows = []
    for t in items:
        heat = (t.like_count or 0) * 1.5 + (t.favorite_count or 0) * 1.8 + (t.comment_count or 0) * 1.2
        rows.append({
            "id": t.id,
            "title": t.title,
            "nickname": t.nickname,
            "like_count": t.like_count,
            "favorite_count": t.favorite_count,
            "comment_count": t.comment_count,
            "heat_score": round(heat, 2),
            "is_featured": bool(getattr(t, "is_featured", False)),
            "cover_url": getattr(t, "cover_url", None),
            "content": getattr(t, "content", ""),
            "created_at": t.created_at,
        })
    return success(rows)


@router.post("/topics")
def admin_create_topic(payload: TopicManageIn, db: Session = Depends(get_db)):
    item = DiscussionTopic(
        user_id=1,
        title=payload.title,
        content=payload.content,
        nickname=payload.nickname or "管理员",
        cover_url=payload.cover_url,
        like_count=payload.like_count,
        favorite_count=payload.favorite_count,
        comment_count=payload.comment_count,
        is_featured=payload.is_featured,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return success(item, "创建成功")


@router.put("/topics/{topic_id}")
def admin_update_topic(topic_id: int, payload: TopicManageIn, db: Session = Depends(get_db)):
    item = db.query(DiscussionTopic).filter(DiscussionTopic.id == topic_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="帖子不存在")
    item.title = payload.title
    item.content = payload.content
    item.nickname = payload.nickname
    item.cover_url = payload.cover_url
    item.like_count = payload.like_count
    item.favorite_count = payload.favorite_count
    item.comment_count = payload.comment_count
    item.is_featured = payload.is_featured
    db.commit()
    db.refresh(item)
    return success(item, "更新成功")


@router.put("/topics/{topic_id}/feature")
def admin_set_topic_feature(topic_id: int, is_featured: bool, db: Session = Depends(get_db)):
    item = db.query(DiscussionTopic).filter(DiscussionTopic.id == topic_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="帖子不存在")
    item.is_featured = is_featured
    db.commit()
    db.refresh(item)
    return success(item, "加精状态已更新")


@router.get("/topics/{topic_id}")
def admin_get_topic(topic_id: int, db: Session = Depends(get_db)):
    item = db.query(DiscussionTopic).filter(DiscussionTopic.id == topic_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return success({
        "id": item.id,
        "title": item.title or "",
        "content": item.content or "",
        "nickname": item.nickname or "",
        "cover_url": item.cover_url or "",
        "like_count": item.like_count or 0,
        "favorite_count": item.favorite_count or 0,
        "comment_count": item.comment_count or 0,
        "is_featured": bool(getattr(item, "is_featured", False)),
        "created_at": str(item.created_at or ""),
    })


@router.delete("/topics/{topic_id}")
def admin_delete_topic(topic_id: int, db: Session = Depends(get_db)):
    item = db.query(DiscussionTopic).filter(DiscussionTopic.id == topic_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="帖子不存在")
    db.query(DiscussionComment).filter(DiscussionComment.topic_id == topic_id).delete()
    db.query(DiscussionLike).filter(DiscussionLike.topic_id == topic_id).delete()
    db.query(DiscussionFavorite).filter(DiscussionFavorite.topic_id == topic_id).delete()
    db.query(DiscussionTopicTag).filter(DiscussionTopicTag.topic_id == topic_id).delete()
    db.delete(item)
    db.commit()
    return success(None, "帖子已删除")


@router.post("/curation/refresh-hot")
def admin_refresh_hot_curation(db: Session = Depends(get_db)):
    db.query(Content).update({Content.is_featured: False})
    db.query(Activity).update({Activity.is_featured: False})
    db.query(DiscussionTopic).update({DiscussionTopic.is_featured: False})
    db.commit()

    top_contents = db.query(Content).filter(
        Content.status == "published",
        Content.review_status == "approved",
        Content.quality_score >= 0.8,
    ).order_by(Content.id.desc()).limit(3).all()
    for c in top_contents:
        c.is_featured = True

    reg_rows = db.query(ActivityRegistration.activity_id, func.count(ActivityRegistration.id)).group_by(ActivityRegistration.activity_id).all()
    reg_map = {aid: cnt for aid, cnt in reg_rows}
    activities = db.query(Activity).filter(Activity.status == "open").all()
    top_activities = sorted(activities, key=lambda x: reg_map.get(x.id, 0), reverse=True)[:3]
    for a in top_activities:
        a.is_featured = True

    topics = db.query(DiscussionTopic).all()
    top_topics = sorted(
        topics,
        key=lambda x: (x.like_count or 0) * 1.5 + (x.favorite_count or 0) * 1.8 + (x.comment_count or 0) * 1.2,
        reverse=True,
    )[:5]
    for t in top_topics:
        t.is_featured = True

    db.commit()
    return success({
        "content_ids": [x.id for x in top_contents],
        "activity_ids": [x.id for x in top_activities],
        "topic_ids": [x.id for x in top_topics],
    }, "热门加精已刷新")


@router.get("/recommend/explain/logs")
def admin_recommend_explain_logs(
    limit: int = 80,
    action: str | None = None,
    target_type: str | None = None,
    source_scene: str | None = None,
    start_at: str | None = None,
    end_at: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(RecommendLog).filter(RecommendLog.explain_json.isnot(None))
    if action:
        q = q.filter(RecommendLog.action == action)
    if target_type:
        q = q.filter(RecommendLog.target_type == target_type)
    if source_scene:
        q = q.filter(RecommendLog.source_scene == source_scene)
    start_dt = _parse_date(start_at)
    end_dt = _parse_date(end_at)
    if start_dt:
        q = q.filter(RecommendLog.created_at >= start_dt)
    if end_dt:
        q = q.filter(RecommendLog.created_at <= end_dt)
    rows = q.order_by(RecommendLog.id.desc()).limit(min(max(limit, 1), 300)).all()
    items = []
    for row in rows:
        explain = {}
        try:
            explain = json.loads(row.explain_json or "{}")
        except Exception:
            explain = {}
        items.append({
            "id": row.id,
            "user_id": row.user_id,
            "action": row.action,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "source_scene": row.source_scene,
            "created_at": row.created_at,
            "explain": explain,
        })
    return success({"items": items, "total": len(items)})


@router.get("/recommend/explain/logs/export.csv")
def admin_recommend_explain_logs_export(
    action: str | None = None,
    target_type: str | None = None,
    source_scene: str | None = None,
    start_at: str | None = None,
    end_at: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(RecommendLog).filter(RecommendLog.explain_json.isnot(None))
    if action:
        q = q.filter(RecommendLog.action == action)
    if target_type:
        q = q.filter(RecommendLog.target_type == target_type)
    if source_scene:
        q = q.filter(RecommendLog.source_scene == source_scene)
    start_dt = _parse_date(start_at)
    end_dt = _parse_date(end_at)
    if start_dt:
        q = q.filter(RecommendLog.created_at >= start_dt)
    if end_dt:
        q = q.filter(RecommendLog.created_at <= end_dt)

    rows = q.order_by(RecommendLog.id.desc()).limit(2000).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "user_id", "action", "target_type", "target_id", "source_scene", "created_at", "final_score", "kg_score", "kg_reason", "kg_path_text"])
    for row in rows:
        explain = {}
        try:
            explain = json.loads(row.explain_json or "{}")
        except Exception:
            explain = {}
        writer.writerow([
            row.id,
            row.user_id,
            row.action,
            row.target_type,
            row.target_id,
            row.source_scene,
            row.created_at,
            explain.get("final_score", ""),
            explain.get("kg_score", ""),
            explain.get("kg_reason", ""),
            explain.get("kg_path_text", ""),
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=recommend_explain_logs.csv"},
    )


@router.get("/users")
def list_users(keyword: str | None = None, search: str | None = None, active: str = "all", db: Session = Depends(get_db)):
    q = db.query(User)
    actual_keyword = keyword or search
    if actual_keyword:
        q = q.filter((User.nickname.contains(actual_keyword)) | (User.openid.contains(actual_keyword)) | (User.phone.contains(actual_keyword)))
    if active == "true":
        q = q.filter(User.is_active.is_(True))
    elif active == "false":
        q = q.filter(User.is_active.is_(False))
    items = q.order_by(User.id.desc()).all()
    stat_map = _behavior_map(db)
    rows = []
    for u in items:
        s = stat_map.get(u.id, {"qa_count": 0, "recommend_click_count": 0, "registration_count": 0, "topic_count": 0, "comment_count": 0, "total_actions": 0})
        rows.append({"id": u.id, "username": u.username, "openid": u.openid, "nickname": u.nickname, "phone": u.phone, "role": u.role, "is_active": u.is_active, "preferred_heritage_types": u.preferred_heritage_types or "", "confidence_score": u.confidence_score, "created_at": u.created_at, **s})
    return success(rows)


@router.get("/users/{user_id}/behavior")
def user_behavior(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    qa_count = db.query(AIQALog).filter(AIQALog.user_id == user_id).count()
    expose = db.query(RecommendLog).filter(RecommendLog.user_id == user_id, RecommendLog.action == "expose").count()
    click = db.query(RecommendLog).filter(RecommendLog.user_id == user_id, RecommendLog.action == "click").count()
    reg = db.query(ActivityRegistration).filter(ActivityRegistration.user_id == user_id).count()
    topic = db.query(DiscussionTopic).filter(DiscussionTopic.user_id == user_id).count()
    comment = db.query(DiscussionComment).filter(DiscussionComment.user_id == user_id).count()
    return success({"user_id": user_id, "nickname": user.nickname, "qa_count": qa_count, "recommend_expose": expose, "recommend_click": click, "recommend_ctr": round((click / expose) * 100, 2) if expose else 0.0, "registration_count": reg, "topic_count": topic, "comment_count": comment})


@router.put("/users/{user_id}/active")
def set_user_active(user_id: int, is_active: bool, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return success(user, "状态更新成功")


class UserStatusIn(BaseModel):
    is_active: bool

class UserRoleIn(BaseModel):
    role: str

@router.put("/users/{user_id}/status")
def set_user_status(user_id: int, payload: UserStatusIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = payload.is_active
    db.commit()
    return success({"id": user_id, "is_active": payload.is_active}, "状态更新成功")


@router.put("/users/{user_id}/role")
def set_user_role(user_id: int, payload: UserRoleIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if payload.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="无效的角色值")
    user.role = payload.role
    db.commit()
    return success({"id": user_id, "role": payload.role}, "角色更新成功")


@router.put("/users/{user_id}")
def update_user(user_id: int, payload: UserManageIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return success(user, "更新成功")


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return success({"id": user_id}, "删除成功")


# ═══════════════════════════════════════════════
# 知识库管理
# ═══════════════════════════════════════════════

class KBItemIn(BaseModel):
    question: str
    answer: str
    qa_answer: str | None = None
    keywords: str | None = None
    chapter: str | None = None
    sub_chapter: str | None = None
    source: str | None = None
    status: str = "active"


class KBItemUpdate(BaseModel):
    question: str | None = None
    answer: str | None = None
    qa_answer: str | None = None
    keywords: str | None = None
    chapter: str | None = None
    sub_chapter: str | None = None
    source: str | None = None
    status: str | None = None


def _kb_to_dict(item: LocalKnowledgeBase) -> dict:
    return {
        "id": item.id,
        "question": item.question,
        "answer": item.answer[:200] if item.answer else "",
        "qa_answer": item.qa_answer[:200] if item.qa_answer else None,
        "keywords": item.keywords,
        "chapter": item.chapter,
        "sub_chapter": item.sub_chapter,
        "source": item.source,
        "status": item.status,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("/kb")
def list_kb(
    keyword: str = "",
    chapter: str = "",
    status: str = "",
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    q = db.query(LocalKnowledgeBase)
    if keyword:
        q = q.filter(
            (LocalKnowledgeBase.question.ilike(f"%{keyword}%"))
            | (LocalKnowledgeBase.keywords.ilike(f"%{keyword}%"))
        )
    if chapter:
        q = q.filter(LocalKnowledgeBase.chapter == chapter)
    if status:
        q = q.filter(LocalKnowledgeBase.status == status)
    total = q.count()
    items = q.order_by(LocalKnowledgeBase.id.desc()).offset((page - 1) * size).limit(size).all()
    return success({
        "items": [_kb_to_dict(i) for i in items],
        "total": total,
        "page": page,
        "size": size,
    })


@router.get("/kb/chapters")
def list_kb_chapters(db: Session = Depends(get_db)):
    rows = db.query(LocalKnowledgeBase.chapter).distinct().all()
    return success([r[0] for r in rows if r[0]])


@router.get("/kb/{item_id}")
def get_kb_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(LocalKnowledgeBase).filter(LocalKnowledgeBase.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")
    d = _kb_to_dict(item)
    d["answer"] = item.answer or ""
    d["qa_answer"] = item.qa_answer or ""
    return success(d)


@router.post("/kb")
def create_kb_item(payload: KBItemIn, db: Session = Depends(get_db)):
    item = LocalKnowledgeBase(
        question=payload.question,
        answer=payload.answer,
        qa_answer=payload.qa_answer,
        keywords=payload.keywords,
        chapter=payload.chapter,
        sub_chapter=payload.sub_chapter,
        source=payload.source,
        status=payload.status,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return success(_kb_to_dict(item), "创建成功")


@router.put("/kb/{item_id}")
def update_kb_item(item_id: int, payload: KBItemUpdate, db: Session = Depends(get_db)):
    item = db.query(LocalKnowledgeBase).filter(LocalKnowledgeBase.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return success(_kb_to_dict(item), "更新成功")


@router.put("/kb/{item_id}/status")
def toggle_kb_status(item_id: int, status: str = "inactive", db: Session = Depends(get_db)):
    item = db.query(LocalKnowledgeBase).filter(LocalKnowledgeBase.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")
    item.status = status
    db.commit()
    return success({"id": item_id, "status": status})


@router.delete("/kb/{item_id}")
def delete_kb_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(LocalKnowledgeBase).filter(LocalKnowledgeBase.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")
    db.delete(item)
    db.commit()
    return success({"id": item_id}, "删除成功")


PIXABAY_KEY = "55468384-6826bf941c33f15394e137805"
STORAGE_DIR = Path(__file__).resolve().parents[4] / "storage" / "covers"


@router.post("/fix-covers")
def admin_fix_covers(db: Session = Depends(get_db)):
    """Pixabay 搜图补封面：为没有合适封面的内容搜图，失败的删除。"""
    items = db.query(Content).filter(
        Content.cover_url.like("%_1.jpg"),
        Content.status == "published"
    ).order_by(Content.id).all()

    results = {"fixed": 0, "deleted": 0, "failed": []}
    ctx = ssl.create_default_context()

    for item in items:
        q = item.title.replace("'", "").replace('"', "")
        params = urllib.parse.urlencode({
            "key": PIXABAY_KEY, "q": q,
            "image_type": "photo", "orientation": "horizontal",
            "safesearch": "true", "per_page": 3,
        })
        try:
            req = urllib.request.Request(
                f"https://pixabay.com/api/?{params}",
                headers={"User-Agent": "HeritageCRS/1.0"}
            )
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                hits = json.loads(resp.read()).get("hits", [])
            if hits:
                img_url = hits[0]["webformatURL"]
                req2 = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req2, timeout=20, context=ctx) as resp2:
                    data = resp2.read()
                if len(data) > 5000:
                    filename = f"pixabay_{item.id}_{int(time.time())}.jpg"
                    (STORAGE_DIR / filename).write_bytes(data)
                    item.cover_url = f"/storage/covers/{filename}"
                    db.commit()
                    results["fixed"] += 1
                    continue
        except Exception:
            pass
        # No match → delete
        db.delete(item)
        db.commit()
        results["deleted"] += 1
        results["failed"].append(item.id)
        time.sleep(0.5)

    return success(results, f"修复完成：{results['fixed']} 已补图，{results['deleted']} 已删除")

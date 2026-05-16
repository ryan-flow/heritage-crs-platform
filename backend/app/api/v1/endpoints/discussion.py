from typing import Any
import json
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.responses import success
from app.core.config import settings
from app.models.discussion_comment import DiscussionComment
from app.models.discussion_like import DiscussionLike
from app.models.discussion_extra import DiscussionFavorite, DiscussionTopicTag
from app.models.discussion_topic import DiscussionTopic
from app.models.recommend_log import RecommendLog
from app.models.user import User
from app.services.display_enrichment import build_topic_display


router = APIRouter()

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
TAG_WHITELIST = {"戏曲", "工艺", "节俗", "求科普", "活动反馈", "传统音乐", "传统舞蹈", "传统美术", "传统技艺", "民俗"}


class TopicCreateIn(BaseModel):
    user_id: int
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    cover_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)


class CommentCreateIn(BaseModel):
    user_id: int
    content: str = Field(..., min_length=1)


def _media_full_url(request: Request | None, url: str | None) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    if not request:
        return raw
    base = str(request.base_url).rstrip("/")
    return f"{base}{raw if raw.startswith('/') else '/' + raw}"


def _topic_to_dict(topic: DiscussionTopic, liked: bool = False, favorited: bool = False, tags: list[str] | None = None, request: Request | None = None) -> dict[str, Any]:
    image_urls = []
    if topic.image_urls:
        try:
            image_urls = json.loads(topic.image_urls)
        except json.JSONDecodeError:
            image_urls = []
    return {
        "id": topic.id,
        "user_id": topic.user_id,
        "nickname": topic.nickname or "匿名用户",
        "title": topic.title,
        "content": topic.content,
        "cover_url": topic.cover_url,
        "cover_full_url": _media_full_url(request, topic.cover_url),
        "image_urls": image_urls,
        "tags": tags or [],
        "is_featured": bool(getattr(topic, "is_featured", False)),
        "like_count": topic.like_count,
        "favorite_count": topic.favorite_count,
        "comment_count": topic.comment_count,
        "heat_score": topic.like_count * 1.5 + topic.favorite_count * 1.8 + topic.comment_count * 1.2,
        "created_at": topic.created_at,
        "liked": liked,
        "favorited": favorited,
    }


def _get_tags(db: Session, topic_ids: list[int]) -> dict[int, list[str]]:
    if not topic_ids:
        return {}
    rows = db.query(DiscussionTopicTag).filter(DiscussionTopicTag.topic_id.in_(topic_ids)).all()
    result: dict[int, list[str]] = {}
    for r in rows:
        result.setdefault(r.topic_id, []).append(r.tag)
    return result


@router.post("/upload-cover")
async def upload_topic_cover(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXT:
        raise HTTPException(status_code=400, detail="仅支持 jpg/jpeg/png/webp 图片")

    content = await file.read()
    if len(content) > 4 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片不能超过4MB")

    save_dir = settings.backend_dir / "storage" / "discussion_covers"
    save_dir.mkdir(parents=True, exist_ok=True)
    filename = f"topic_{uuid.uuid4().hex}{suffix}"
    save_path = save_dir / filename
    save_path.write_bytes(content)

    return success({"url": f"/static/discussion_covers/{filename}"}, "上传成功")


@router.get("/topics")
def list_topics(
    request: Request,
    user_id: int | None = None,
    keyword: str | None = None,
    tag: str | None = None,
    sort: str = "hot",
    favorite_only: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(DiscussionTopic)
    if keyword:
        query = query.filter((DiscussionTopic.title.contains(keyword)) | (DiscussionTopic.content.contains(keyword)))

    topics = query.all()

    topic_ids = [t.id for t in topics]
    tag_map = _get_tags(db, topic_ids)

    if tag:
        topics = [t for t in topics if tag in tag_map.get(t.id, [])]

    liked_topic_ids: set[int] = set()
    favorited_topic_ids: set[int] = set()
    if user_id:
        liked_topic_ids = {row.topic_id for row in db.query(DiscussionLike).filter(DiscussionLike.user_id == user_id).all()}
        favorited_topic_ids = {row.topic_id for row in db.query(DiscussionFavorite).filter(DiscussionFavorite.user_id == user_id).all()}

    items = [
        _topic_to_dict(
            topic,
            topic.id in liked_topic_ids,
            topic.id in favorited_topic_ids,
            tag_map.get(topic.id, []),
            request,
        )
        for topic in topics
    ]

    featured_items = [it for it in items if any((t.id == it["id"] and bool(getattr(t, "is_featured", False))) for t in topics)]

    if favorite_only and user_id:
        items = [it for it in items if it["id"] in favorited_topic_ids]

    if sort == "new":
        items.sort(key=lambda x: x["id"], reverse=True)
    else:
        items.sort(key=lambda x: (x["heat_score"], x["id"]), reverse=True)

    featured_items.sort(key=lambda x: (x["heat_score"], x["id"]), reverse=True)
    return success({"items": items, "featured_items": featured_items[:5], "total": len(items)})


@router.post("/topics")
def create_topic(payload: TopicCreateIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    normalized_tags = [t.strip() for t in payload.tags if t and t.strip() in TAG_WHITELIST][:3]

    topic = DiscussionTopic(
        user_id=payload.user_id,
        nickname=user.nickname or f"用户{user.id}",
        title=payload.title.strip(),
        content=payload.content.strip(),
        cover_url=(payload.cover_url or "").strip() or None,
        image_urls=json.dumps(payload.image_urls, ensure_ascii=False),
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)

    for t in normalized_tags:
        db.add(DiscussionTopicTag(topic_id=topic.id, tag=t))
    db.commit()

    return success(_topic_to_dict(topic, tags=normalized_tags), "发布成功")


@router.get("/topics/{topic_id}")
def get_topic(topic_id: int, request: Request, user_id: int | None = None, db: Session = Depends(get_db)):
    topic = db.query(DiscussionTopic).filter(DiscussionTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")

    liked = False
    favorited = False
    if user_id:
        liked = db.query(DiscussionLike).filter(DiscussionLike.topic_id == topic_id, DiscussionLike.user_id == user_id).first() is not None
        favorited = db.query(DiscussionFavorite).filter(DiscussionFavorite.topic_id == topic_id, DiscussionFavorite.user_id == user_id).first() is not None

    comments = db.query(DiscussionComment).filter(DiscussionComment.topic_id == topic_id).order_by(DiscussionComment.id.asc()).all()
    tag_map = _get_tags(db, [topic_id])

    return success(
        {
            "topic": {
                **_topic_to_dict(topic, liked, favorited, tag_map.get(topic_id, []), request),
                "display_blocks": build_topic_display(topic.content),
            },
            "comments": [
                {
                    "id": item.id,
                    "topic_id": item.topic_id,
                    "user_id": item.user_id,
                    "nickname": item.nickname or "匿名用户",
                    "content": item.content,
                    "created_at": item.created_at,
                }
                for item in comments
            ],
        }
    )


@router.post("/topics/{topic_id}/comments")
def create_comment(topic_id: int, payload: CommentCreateIn, db: Session = Depends(get_db)):
    topic = db.query(DiscussionTopic).filter(DiscussionTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    comment = DiscussionComment(
        topic_id=topic_id,
        user_id=payload.user_id,
        nickname=user.nickname or f"用户{user.id}",
        content=payload.content.strip(),
    )
    db.add(comment)
    topic.comment_count += 1
    db.commit()
    db.refresh(comment)
    db.add(RecommendLog(user_id=payload.user_id, action="click", target_type="topic", target_id=topic_id, source_scene="topic_comment"))
    db.commit()
    return success(
        {
            "id": comment.id,
            "topic_id": comment.topic_id,
            "user_id": comment.user_id,
            "nickname": comment.nickname,
            "content": comment.content,
            "created_at": comment.created_at,
        },
        "评论成功",
    )


@router.post("/topics/{topic_id}/like")
def like_topic(topic_id: int, user_id: int, db: Session = Depends(get_db)):
    topic = db.query(DiscussionTopic).filter(DiscussionTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    record = DiscussionLike(topic_id=topic_id, user_id=user_id)
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="你已点赞该话题")
    topic.like_count += 1
    db.commit()
    db.refresh(topic)
    db.add(RecommendLog(user_id=user_id, action="click", target_type="topic", target_id=topic_id, source_scene="topic_like"))
    db.commit()
    return success({"topic_id": topic_id, "like_count": topic.like_count}, "点赞成功")


@router.delete("/topics/{topic_id}/like")
def unlike_topic(topic_id: int, user_id: int, db: Session = Depends(get_db)):
    topic = db.query(DiscussionTopic).filter(DiscussionTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    record = db.query(DiscussionLike).filter(DiscussionLike.topic_id == topic_id, DiscussionLike.user_id == user_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="点赞记录不存在")
    db.delete(record)
    if topic.like_count > 0:
        topic.like_count -= 1
    db.commit()
    db.refresh(topic)
    return success({"topic_id": topic_id, "like_count": topic.like_count}, "取消点赞成功")


@router.post("/topics/{topic_id}/favorite")
def favorite_topic(topic_id: int, user_id: int, db: Session = Depends(get_db)):
    topic = db.query(DiscussionTopic).filter(DiscussionTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    record = DiscussionFavorite(topic_id=topic_id, user_id=user_id)
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="已收藏")
    topic.favorite_count += 1
    db.commit()
    db.refresh(topic)
    db.add(RecommendLog(user_id=user_id, action="click", target_type="topic", target_id=topic_id, source_scene="topic_favorite"))
    db.commit()
    return success({"topic_id": topic_id, "favorite_count": topic.favorite_count}, "收藏成功")


@router.delete("/topics/{topic_id}/favorite")
def unfavorite_topic(topic_id: int, user_id: int, db: Session = Depends(get_db)):
    topic = db.query(DiscussionTopic).filter(DiscussionTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    record = db.query(DiscussionFavorite).filter(DiscussionFavorite.topic_id == topic_id, DiscussionFavorite.user_id == user_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="收藏记录不存在")
    db.delete(record)
    if topic.favorite_count > 0:
        topic.favorite_count -= 1
    db.commit()
    db.refresh(topic)
    return success({"topic_id": topic_id, "favorite_count": topic.favorite_count}, "取消收藏成功")


class LikeIn(BaseModel):
    topic_id: int
    user_id: int


class FavoriteIn(BaseModel):
    topic_id: int
    user_id: int


class CommentIn(BaseModel):
    topic_id: int
    user_id: int
    content: str = Field(..., min_length=1)


# ── 推荐 / 热门 / 模板 ──────────────────────────────────

TEMPLATES = [
    {
        "name": "体验分享",
        "title_template": "我在{地点}体验了{项目}",
        "content_template": "分享我的非遗体验...",
    },
    {
        "name": "求科普",
        "title_template": "请问{项目}有什么讲究？",
        "content_template": "想了解关于...",
    },
    {
        "name": "活动反馈",
        "title_template": "参加了{活动}后的感受",
        "content_template": "这次活动让我...",
    },
    {
        "name": "讨论交流",
        "title_template": "关于{话题}，大家怎么看？",
        "content_template": "我认为...",
    },
]


@router.get("/recommend/")
def get_recommend_topics(
    request: Request,
    user_id: int | None = None,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    """获取推荐话题

    基于用户偏好（如有 user_id）或按点赞数排序返回推荐话题。
    有 user_id 时使用推荐引擎的个人化推荐；
    无 user_id 时按 like_count 降序返回热门话题。
    """
    if user_id:
        # 有用户ID时使用推荐引擎
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        from app.services.recommendation_service import build_user_profile, recommend_topics
        profile = build_user_profile(db, user_id)
        items = recommend_topics(db, profile, limit=limit, scene="discussion")
        topic_ids = [t["id"] for t in items]
        topics = (
            db.query(DiscussionTopic)
            .filter(DiscussionTopic.id.in_(topic_ids))
            .all()
        ) if topic_ids else []
        topic_map = {t.id: t for t in topics}
        liked_ids: set[int] = set()
        favorited_ids: set[int] = set()
        if user_id:
            liked_ids = {
                r.topic_id
                for r in db.query(DiscussionLike).filter(DiscussionLike.user_id == user_id).all()
                if r.topic_id in topic_ids
            }
            favorited_ids = {
                r.topic_id
                for r in db.query(DiscussionFavorite).filter(DiscussionFavorite.user_id == user_id).all()
                if r.topic_id in topic_ids
            }
        tag_map = _get_tags(db, topic_ids)
        result = []
        for rec in items:
            topic = topic_map.get(rec["id"])
            if not topic:
                continue
            item = _topic_to_dict(
                topic,
                liked=rec["id"] in liked_ids,
                favorited=rec["id"] in favorited_ids,
                tags=tag_map.get(rec["id"], []),
                request=request,
            )
            item["reason"] = rec.get("reason", "")
            result.append(item)
        return success({"items": result, "total": len(result)})

    # 无 user_id 时按点赞数降序
    topics = (
        db.query(DiscussionTopic)
        .order_by(DiscussionTopic.like_count.desc(), DiscussionTopic.id.desc())
        .limit(limit)
        .all()
    )
    topic_ids = [t.id for t in topics]
    tag_map = _get_tags(db, topic_ids)
    items = [
        _topic_to_dict(t, tags=tag_map.get(t.id, []), request=request)
        for t in topics
    ]
    return success({"items": items, "total": len(items)})


@router.get("/hot/")
def get_hot_topics(
    request: Request,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """获取热门话题

    按热度公式排序：heat = like_count + comment_count * 2 + favorite_count * 1.5
    返回前 limit 条。
    """
    topics = db.query(DiscussionTopic).all()
    topic_ids = [t.id for t in topics]
    tag_map = _get_tags(db, topic_ids)

    # 计算综合热度并排序
    items_with_heat = []
    for t in topics:
        heat = t.like_count + t.comment_count * 2 + t.favorite_count * 1.5
        items_with_heat.append((t, heat))

    items_with_heat.sort(key=lambda x: (x[1], x[0].id), reverse=True)
    top_topics = items_with_heat[:limit]

    # 获取当前用户的点赞/收藏状态（如有 user_id 可扩展）
    items = [
        {
            **_topic_to_dict(t, tags=tag_map.get(t.id, []), request=request),
            "heat_score_raw": round(heat, 1),
        }
        for t, heat in top_topics
    ]
    return success({"items": items, "total": len(items)})


@router.get("/templates/")
def get_post_templates():
    """获取发帖模板列表

    返回预设的发帖模板，供前端在创建新话题时使用。
    """
    return success({"items": TEMPLATES, "total": len(TEMPLATES)})


# ── Frontend-compatible routes ──────────────────────────────


@router.get("/")
def fe_list_topics(request: Request, db: Session = Depends(get_db)):
    """Frontend: GET /discussion/ → list all topics as array"""
    from app.api.v1.endpoints.discussion import list_topics as _backend_list
    # call backend logic via query
    raw = _backend_list(request=request, db=db)
    items = raw.get("data", {}).get("items", [])
    return success(items)


@router.post("/like")
def fe_like_topic(payload: LikeIn, db: Session = Depends(get_db)):
    topic = db.query(DiscussionTopic).filter(DiscussionTopic.id == payload.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    record = DiscussionLike(topic_id=payload.topic_id, user_id=payload.user_id)
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="你已点赞该话题")
    topic.like_count += 1
    db.commit()
    db.refresh(topic)
    return success({"topic_id": payload.topic_id, "like_count": topic.like_count}, "点赞成功")


@router.post("/favorite")
def fe_favorite_topic(payload: FavoriteIn, db: Session = Depends(get_db)):
    topic = db.query(DiscussionTopic).filter(DiscussionTopic.id == payload.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    record = DiscussionFavorite(topic_id=payload.topic_id, user_id=payload.user_id)
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="已收藏")
    topic.favorite_count += 1
    db.commit()
    db.refresh(topic)
    db.add(RecommendLog(user_id=payload.user_id, action="click", target_type="topic", target_id=payload.topic_id, source_scene="topic_favorite"))
    db.commit()
    return success({"topic_id": payload.topic_id, "favorite_count": topic.favorite_count}, "收藏成功")


@router.post("/comment")
def fe_create_comment(payload: CommentIn, db: Session = Depends(get_db)):
    topic = db.query(DiscussionTopic).filter(DiscussionTopic.id == payload.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    comment = DiscussionComment(
        topic_id=payload.topic_id,
        user_id=payload.user_id,
        nickname=user.nickname or f"用户{user.id}",
        content=payload.content.strip(),
    )
    db.add(comment)
    topic.comment_count += 1
    db.commit()
    db.refresh(comment)
    return success({"id": comment.id}, "评论成功")


@router.get("/{topic_id}")
def fe_get_topic(topic_id: int, request: Request, user_id: int | None = None, db: Session = Depends(get_db)):
    """Frontend: GET /discussion/{id} → return topic dict with comments"""
    from app.api.v1.endpoints.discussion import get_topic as _backend_get
    raw = _backend_get(topic_id=topic_id, request=request, user_id=user_id, db=db)
    data = raw.get("data", {})
    topic_data = data.get("topic", {})
    topic_data["comments"] = data.get("comments", [])
    return success(topic_data)

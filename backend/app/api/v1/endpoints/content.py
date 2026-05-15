from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.core.responses import success
from app.models.content import Content
from app.services.display_enrichment import build_content_display


router = APIRouter()


class ContentIn(BaseModel):
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


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", ""))


_CONTENT_CATEGORY_TAGS = {
    "传统工艺": ["工艺", "传统技艺", "手工艺"],
    "戏曲音乐": ["戏曲", "音乐", "表演艺术"],
    "民俗节俗": ["民俗", "节庆", "习俗"],
    "饮食医药": ["饮食", "医药", "养生"],
    "民间文学": ["文学", "传说", "故事"],
    "传统美术": ["美术", "绘画", "雕塑"],
    "article": ["非遗", "文化"],
}


def _content_to_dict(c: Content) -> dict:
    """Content ORM → API dict (含前端兼容字段)"""
    tags = _CONTENT_CATEGORY_TAGS.get(c.content_type, _CONTENT_CATEGORY_TAGS.get("article", []))
    if c.chapter:
        tags = list(set(tags + [c.chapter]))
    return {
        "id": c.id,
        "title": c.title,
        "summary": c.summary or "",
        "content": c.body or "",
        "cover_url": c.cover_url or "",
        "category": c.content_type or "",
        "content_type": c.content_type or "",
        "region": "",
        "tags": tags,
        "chapter": c.chapter or "",
        "sub_chapter": c.sub_chapter or "",
        "source_site": c.source_site or "",
        "quality_score": c.quality_score or 0,
        "is_featured": 1 if c.is_featured else 0,
        "status": c.status or "",
        "view_count": 0,
        "like_count": 0,
        "favorite_count": 0,
        "created_at": str(c.created_at or ""),
    }


def _parse_params(
    category: str | None = None,
    search: str | None = None,
    keyword: str | None = None,
    content_type: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[str | None, str | None, int, int]:
    """统一处理前端/后端两套参数名"""
    actual_type = category or content_type
    if actual_type == "全部":
        actual_type = None
    actual_keyword = search or keyword
    actual_limit = page_size or limit
    actual_offset = ((page or 1) - 1) * actual_limit if page else offset
    return actual_type, actual_keyword, min(actual_limit, 50), actual_offset


@router.get("/")
def list_contents(
    # 前端参数
    category: str | None = None,
    search: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    # 后端参数
    keyword: str | None = None,
    content_type: str | None = None,
    chapter: str | None = None,
    status: str | None = "published",
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    actual_type, actual_keyword, actual_limit, actual_offset = _parse_params(
        category, search, keyword, content_type, page, page_size, limit, offset,
    )
    query = db.query(Content)
    if actual_keyword:
        query = query.filter(Content.title.contains(actual_keyword))
    if actual_type:
        query = query.filter(Content.content_type == actual_type)
    if chapter:
        query = query.filter(Content.chapter == chapter)
    if status:
        query = query.filter(Content.status == status)
        if status == "published":
            query = query.filter(Content.review_status == "approved", Content.quality_score >= 0.8)
    total = query.count()
    items = query.order_by(Content.is_featured.desc(), Content.id.desc()).offset(actual_offset).limit(actual_limit).all()
    return success([_content_to_dict(c) for c in items])


@router.get("/{content_id}")
def get_content(content_id: int, db: Session = Depends(get_db)):
    item = db.query(Content).filter(Content.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="内容不存在")
    data = _content_to_dict(item)
    data["display_blocks"] = build_content_display(item.summary, item.body)
    return success(data)


@router.get("/{content_id}/related")
def get_related_contents(content_id: int, limit: int = 4, db: Session = Depends(get_db)):
    """获取与指定内容相关的推荐内容（同类别 + 同章节优先）"""
    item = db.query(Content).filter(Content.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="内容不存在")

    # 第一优先级：同 content_type + 同 chapter
    related = []
    if item.content_type and item.chapter:
        related = (
            db.query(Content)
            .filter(
                Content.id != content_id,
                Content.content_type == item.content_type,
                Content.chapter == item.chapter,
                Content.status == "published",
                Content.review_status == "approved",
            )
            .order_by(Content.is_featured.desc(), Content.quality_score.desc())
            .limit(limit)
            .all()
        )

    # 第二优先级：同 content_type（补充不足的数量）
    if len(related) < limit and item.content_type:
        existing_ids = [r.id for r in related] + [content_id]
        more = (
            db.query(Content)
            .filter(
                Content.id.notin_(existing_ids),
                Content.content_type == item.content_type,
                Content.status == "published",
                Content.review_status == "approved",
            )
            .order_by(Content.is_featured.desc(), Content.quality_score.desc())
            .limit(limit - len(related))
            .all()
        )
        related.extend(more)

    # 第三优先级：已发布的精选内容（补充不足的数量）
    if len(related) < limit:
        existing_ids = [r.id for r in related] + [content_id]
        fallback = (
            db.query(Content)
            .filter(
                Content.id.notin_(existing_ids),
                Content.status == "published",
                Content.review_status == "approved",
            )
            .order_by(Content.is_featured.desc(), Content.quality_score.desc())
            .limit(limit - len(related))
            .all()
        )
        related.extend(fallback)

    result = []
    for r in related:
        result.append({
            "id": r.id,
            "title": r.title,
            "cover_url": r.cover_url,
            "content_type": r.content_type,
            "chapter": r.chapter,
            "sub_chapter": r.sub_chapter,
            "summary": (r.summary or "")[:80],
        })
    return success(result)


@router.post("/admin", dependencies=[Depends(require_admin)])
def create_content(payload: ContentIn, db: Session = Depends(get_db)):
    data = payload.model_dump()
    data["published_at"] = _parse_dt(payload.published_at)
    item = Content(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return success(item, "创建成功")


@router.put("/admin/{content_id}", dependencies=[Depends(require_admin)])
def update_content(content_id: int, payload: ContentIn, db: Session = Depends(get_db)):
    item = db.query(Content).filter(Content.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="内容不存在")
    data = payload.model_dump()
    data["published_at"] = _parse_dt(payload.published_at)
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return success(item, "更新成功")


@router.delete("/admin/{content_id}", dependencies=[Depends(require_admin)])
def delete_content(content_id: int, db: Session = Depends(get_db)):
    item = db.query(Content).filter(Content.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="内容不存在")
    db.delete(item)
    db.commit()
    return success({"id": content_id}, "删除成功")

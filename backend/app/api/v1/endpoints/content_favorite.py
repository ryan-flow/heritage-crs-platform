from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.content_favorite import ContentFavorite
from app.models.content import Content
from app.core.responses import success


router = APIRouter()


class FavoriteIn(BaseModel):
    content_id: int


@router.post("/")
def add_favorite(payload: FavoriteIn, user_id: int, db: Session = Depends(get_db)):
    """收藏内容（幂等）"""
    # 检查内容是否存在
    content = db.query(Content).filter(Content.id == payload.content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    # 检查是否已收藏
    existing = (
        db.query(ContentFavorite)
        .filter(ContentFavorite.user_id == user_id, ContentFavorite.content_id == payload.content_id)
        .first()
    )
    if existing:
        return success({"content_id": payload.content_id, "is_favorited": True}, "已收藏")
    fav = ContentFavorite(user_id=user_id, content_id=payload.content_id)
    db.add(fav)
    db.commit()
    return success({"content_id": payload.content_id, "is_favorited": True}, "收藏成功")


@router.delete("/")
def remove_favorite(content_id: int, user_id: int, db: Session = Depends(get_db)):
    """取消收藏"""
    fav = (
        db.query(ContentFavorite)
        .filter(ContentFavorite.user_id == user_id, ContentFavorite.content_id == content_id)
        .first()
    )
    if not fav:
        return success({"content_id": content_id, "is_favorited": False}, "未收藏")
    db.delete(fav)
    db.commit()
    return success({"content_id": content_id, "is_favorited": False}, "已取消收藏")


@router.get("/check")
def check_favorite(content_id: int, user_id: int, db: Session = Depends(get_db)):
    """检查是否已收藏"""
    fav = (
        db.query(ContentFavorite)
        .filter(ContentFavorite.user_id == user_id, ContentFavorite.content_id == content_id)
        .first()
    )
    return success({"content_id": content_id, "is_favorited": fav is not None})


@router.get("/list")
def list_favorites(user_id: int, limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    """获取用户收藏列表"""
    query = db.query(ContentFavorite).filter(ContentFavorite.user_id == user_id)
    total = query.count()
    items = query.order_by(ContentFavorite.created_at.desc()).offset(offset).limit(min(limit, 50)).all()
    content_ids = [item.content_id for item in items]
    contents = db.query(Content).filter(Content.id.in_(content_ids)).all() if content_ids else []
    content_map = {c.id: c for c in contents}
    result = []
    for fav in items:
        c = content_map.get(fav.content_id)
        if c:
            result.append({
                "id": c.id,
                "title": c.title,
                "cover_url": c.cover_url,
                "content_type": c.content_type,
                "chapter": c.chapter,
                "sub_chapter": c.sub_chapter,
                "summary": (c.summary or "")[:80],
                "favorited_at": str(fav.created_at) if fav.created_at else None,
            })
    return success({"items": result, "total": total})

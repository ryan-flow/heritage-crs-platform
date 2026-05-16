"""非遗地点（Places）相关端点

由于数据库中没有独立的 places 表，本模块从 contents 表的 chapter/sub_chapter
字段派生出"地点/流派/发源地"展示数据，按非遗类目分组。

返回结构：
- chapter: 非遗大类目（相当于"地区/流派"）
- sub_chapters: 子分类列表
- content_count: 该大类目下的内容数量
- representative_items: 代表性内容项（最多 6 条）
"""

import hashlib
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.responses import success
from app.models.content import Content

router = APIRouter()

# ── 类目→地点/发源地/地域 中文映射 ──
CHAPTER_LOCATION_MAP = {
    "传统医药": {
        "region": "华东/华南",
        "location_desc": "中医药文化核心发源地，遍布全国",
        "icon": "herb",
        "display_name": "传统医药源地",
        "description": "针灸、中药、茶艺等传统医药类非遗的发源与传承之地。",
    },
    "传统美术与工艺": {
        "region": "华东",
        "location_desc": "江南地区为核心，辐射全国",
        "icon": "brush",
        "display_name": "传统美术与工艺之乡",
        "description": "剪纸、年画、书法、陶瓷、丝织等传统美术与手工艺的核心传承区域。",
    },
    "传统音乐": {
        "region": "华东/华中",
        "location_desc": "长江流域为主线，多元分布",
        "icon": "music",
        "display_name": "传统音乐源流",
        "description": "古琴艺术等传统音乐类非遗的主要传承与活跃区域。",
    },
    "岁时节庆与民俗": {
        "region": "全国",
        "location_desc": "各地均有分布，节庆活动丰富",
        "icon": "calendar",
        "display_name": "岁时节庆与民俗",
        "description": "节气、节俗等民俗类非遗遍布全国，是最具群众基础的文化遗产。",
    },
    "戏曲与表演艺术": {
        "region": "华东/华南/西南",
        "location_desc": "昆曲（江苏）、粤剧（广东）、藏戏（西藏）等多地分布",
        "icon": "theater",
        "display_name": "戏曲与表演艺术舞台",
        "description": "昆曲、粤剧、藏戏等传统戏曲与表演艺术的发源和活跃区域。",
    },
}

_DEFAULT_PLACE: dict[str, str] = {
    "region": "全国",
    "location_desc": "多地分布",
    "icon": "map-pin",
    "display_name": "",
    "description": "",
}


def _chapter_to_id(chapter: str) -> int:
    """使用 MD5 生成稳定的正整数 ID"""
    h = hashlib.md5(chapter.encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def _get_chapter_by_id(place_id: int, db: Session) -> str | None:
    """根据 place_id 反查 chapter 名称"""
    chapters = (
        db.query(Content.chapter)
        .filter(
            Content.status == "published",
            Content.review_status == "approved",
            Content.chapter.isnot(None),
            Content.chapter != "",
        )
        .distinct()
        .all()
    )
    for (chapter,) in chapters:
        if _chapter_to_id(chapter) == place_id:
            return chapter
    return None


def _build_place(
    chapter: str,
    sub_chapters: list[dict[str, Any]],
    content_count: int,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    """将内容统计数据组装为地点展示数据结构"""
    meta = CHAPTER_LOCATION_MAP.get(chapter, dict(_DEFAULT_PLACE))
    if not meta.get("display_name"):
        meta["display_name"] = chapter
    return {
        "id": _chapter_to_id(chapter),
        "name": chapter,
        "display_name": meta.get("display_name", chapter),
        "region": meta.get("region", "全国"),
        "location_desc": meta.get("location_desc", ""),
        "icon": meta.get("icon", "map-pin"),
        "description": meta.get("description", ""),
        "content_count": content_count,
        "sub_chapters": sub_chapters,
        "representative_items": items,
    }


@router.get("/")
def list_places(
    request: Request,
    db: Session = Depends(get_db),
):
    """获取所有非遗地点/流派列表

    从 contents 表按 chapter 分组，返回各大类目及其子分类信息。
    """
    # 查询所有已发布且审核通过的内容
    rows = (
        db.query(Content.chapter, Content.sub_chapter, func.count(Content.id))
        .filter(
            Content.status == "published",
            Content.review_status == "approved",
            Content.chapter.isnot(None),
            Content.chapter != "",
        )
        .group_by(Content.chapter, Content.sub_chapter)
        .order_by(Content.chapter, func.count(Content.id).desc())
        .all()
    )

    # 按 chapter 聚合
    chapter_map: dict[str, dict[str, Any]] = {}
    for chapter, sub_chapter, cnt in rows:
        if chapter not in chapter_map:
            chapter_map[chapter] = {"total": 0, "sub_chapters": []}
        chapter_map[chapter]["total"] += cnt
        if sub_chapter:
            chapter_map[chapter]["sub_chapters"].append(
                {"name": sub_chapter, "content_count": cnt}
            )

    # 为每个 chapter 获取代表性内容
    result: list[dict[str, Any]] = []
    for chapter, agg in chapter_map.items():
        items = (
            db.query(Content)
            .filter(
                Content.chapter == chapter,
                Content.status == "published",
                Content.review_status == "approved",
            )
            .order_by(Content.is_featured.desc(), Content.quality_score.desc(), Content.id.desc())
            .limit(6)
            .all()
        )
        representative = [
            {
                "id": c.id,
                "title": c.title,
                "cover_url": c.cover_url or "",
                "content_type": c.content_type or "",
                "sub_chapter": c.sub_chapter or "",
                "summary": (c.summary or "")[:100],
            }
            for c in items
        ]

        place = _build_place(
            chapter=chapter,
            sub_chapters=agg["sub_chapters"],
            content_count=agg["total"],
            items=representative,
        )
        result.append(place)

    # 按 content_count 降序排列
    result.sort(key=lambda x: x["content_count"], reverse=True)

    return success({"items": result, "total": len(result)})


@router.get("/{place_id}")
def get_place(place_id: int, request: Request, db: Session = Depends(get_db)):
    """获取指定地点的详细信息及其下所有内容

    place_id 由 chapter 名称的 MD5 前 8 位十六进制生成，稳定不变。
    """
    chapter = _get_chapter_by_id(place_id, db)

    if not chapter:
        raise HTTPException(status_code=404, detail="地点不存在")

    # 查询该 chapter 下所有内容
    items = (
        db.query(Content)
        .filter(
            Content.chapter == chapter,
            Content.status == "published",
            Content.review_status == "approved",
        )
        .order_by(Content.is_featured.desc(), Content.quality_score.desc(), Content.id.desc())
        .all()
    )

    sub_chapter_set: dict[str, int] = {}
    content_list: list[dict[str, Any]] = []
    for c in items:
        content_list.append({
            "id": c.id,
            "title": c.title,
            "cover_url": c.cover_url or "",
            "content_type": c.content_type or "",
            "sub_chapter": c.sub_chapter or "",
            "summary": c.summary or "",
            "body": c.body or "",
            "quality_score": c.quality_score or 0,
            "is_featured": c.is_featured,
        })
        if c.sub_chapter:
            sub_chapter_set[c.sub_chapter] = sub_chapter_set.get(c.sub_chapter, 0) + 1

    sub_chapters = [
        {"name": name, "content_count": cnt}
        for name, cnt in sorted(sub_chapter_set.items(), key=lambda x: x[1], reverse=True)
    ]

    meta = CHAPTER_LOCATION_MAP.get(chapter, dict(_DEFAULT_PLACE))
    if not meta.get("display_name"):
        meta["display_name"] = chapter

    place_data: dict[str, Any] = {
        "id": place_id,
        "name": chapter,
        "display_name": meta.get("display_name", chapter),
        "region": meta.get("region", "全国"),
        "location_desc": meta.get("location_desc", ""),
        "icon": meta.get("icon", "map-pin"),
        "description": meta.get("description", ""),
        "content_count": len(items),
        "sub_chapters": sub_chapters,
        "contents": content_list,
    }

    return success(place_data)

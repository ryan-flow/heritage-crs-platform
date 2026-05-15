from __future__ import annotations

from app.models.content import Content
from crawler.quality import QualityScorer

MIN_QUALITY = 0.8
MIN_BODY_LEN = 280
FEATURE_LIMIT = 12
WHITELIST_BATCH = "whitelist_curated_v1"

quality = QualityScorer()


def _norm_text(value: str | None) -> str:
    return " ".join((value or "").split()).strip().lower()


def title_ok(title: str | None) -> bool:
    text = (title or "").strip()
    if len(text) < 6:
        return False
    if quality.has_bad_title(text):
        return False
    if quality.looks_garbled(text):
        return False
    return True


def build_whitelist(items: list[Content]) -> list[Content]:
    candidates = [
        item for item in items
        if (item.quality_score or 0) >= MIN_QUALITY
        and item.review_status == "approved"
        and len((item.body or "").strip()) >= MIN_BODY_LEN
        and title_ok(item.title)
        and not quality.looks_garbled(item.body or "")
    ]

    deduped: dict[str, Content] = {}
    for item in sorted(candidates, key=lambda x: ((x.quality_score or 0), x.id or 0), reverse=True):
        key = item.content_hash or _norm_text(item.title)
        if key and key not in deduped:
            deduped[key] = item
    return list(deduped.values())


def apply_whitelist(items: list[Content]) -> dict:
    whitelist = build_whitelist(items)
    whitelist_ids = {item.id for item in whitelist}

    featured_ids: list[int] = []
    for item in items:
        if item.id in whitelist_ids:
            item.status = "published"
            item.review_status = "approved"
            item.import_batch = WHITELIST_BATCH
        item.is_featured = False

    for item in sorted(whitelist, key=lambda x: ((x.quality_score or 0), x.id or 0), reverse=True)[:FEATURE_LIMIT]:
        item.is_featured = True
        featured_ids.append(item.id)

    return {
        "whitelist_count": len(whitelist),
        "featured_count": len(featured_ids),
        "featured_ids": featured_ids,
        "whitelist_ids": sorted(whitelist_ids),
        "batch": WHITELIST_BATCH,
    }

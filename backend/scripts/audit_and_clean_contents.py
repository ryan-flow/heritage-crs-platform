from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.database import SessionLocal
from app.models.content import Content
from crawler.cleaner import Cleaner
from crawler.models import CrawlArticle
from crawler.quality import QualityScorer
from crawler.utils import sha1_text

cleaner = Cleaner()
quality = QualityScorer()
REPORT_PATH = BASE_DIR / "storage" / "audit" / "content_audit_report.json"

BAD_KEYWORDS = ["版权所有", "ICP备", "广告", "赞助", "上一篇", "下一篇", "打印本页", "关闭窗口"]


def to_article(item: Content) -> CrawlArticle:
    return CrawlArticle(
        source_site=item.source_site or "manual",
        source_url=item.source_url or "",
        crawl_time="",
        title=item.title or "",
        summary=item.summary or "",
        content=item.body or "",
        cover_image=item.cover_url,
        image_urls=[],
        category=item.content_type or "article",
        region=None,
        tags=[],
        publish_time=item.published_at.strftime("%Y-%m-%d") if item.published_at else None,
        author=None,
        content_type=item.content_type or "article",
        quality_score=float(item.quality_score or 0),
    )


def inspect_content(item: Content) -> tuple[list[str], dict]:
    article = cleaner.normalize(to_article(item))
    score = quality.score(article)
    reasons: list[str] = []

    if len(article.title) < 6:
        reasons.append("title_too_short")
    if len(article.content) < 280:
        reasons.append("content_too_short")
    if quality.has_bad_title(article.title):
        reasons.append("meta_or_invalid_title")
    if quality.looks_garbled(article.title or ""):
        reasons.append("garbled_title")
    if quality.looks_garbled(article.content or ""):
        reasons.append("garbled_content")
    if any(word in (article.title + " " + article.content) for word in BAD_KEYWORDS):
        reasons.append("bad_keywords")
    if not quality.is_acceptable(article):
        reasons.append("quality_rejected")

    content_hash = sha1_text((article.title or "") + "\n" + (article.content or "")[:1000])
    normalized = {
        "title": article.title,
        "summary": article.summary,
        "body": article.content,
        "quality_score": score,
        "content_hash": content_hash,
        "review_status": "approved" if score >= 0.8 and not reasons else "pending",
    }
    return reasons, normalized


def audit_contents(apply: bool = False, set_draft: bool = False) -> dict:
    db = SessionLocal()
    try:
        items = db.query(Content).all()
        seen_hashes: dict[str, int] = {}
        duplicate_ids: set[int] = set()
        report_items = []

        for item in items:
            reasons, normalized = inspect_content(item)
            if normalized["content_hash"] in seen_hashes:
                reasons.append("duplicate_content")
                duplicate_ids.add(item.id)
            else:
                seen_hashes[normalized["content_hash"]] = item.id

            if reasons:
                report_items.append({
                    "id": item.id,
                    "title": item.title,
                    "reasons": sorted(set(reasons)),
                    "quality_score": normalized["quality_score"],
                })

            if apply:
                item.title = normalized["title"]
                item.summary = normalized["summary"]
                item.body = normalized["body"]
                item.quality_score = normalized["quality_score"]
                item.content_hash = normalized["content_hash"]
                item.review_status = normalized["review_status"]
                if item.review_status == "pending" and set_draft:
                    item.status = "draft"

        if apply:
            db.commit()

        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "total": len(items),
            "flagged": len(report_items),
            "duplicates": len(duplicate_ids),
            "applied": apply,
            "set_draft": set_draft,
            "items": report_items[:500],
        }
        REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
    finally:
        db.close()


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    set_draft = "--set-draft" in sys.argv
    result = audit_contents(apply=apply, set_draft=set_draft)
    print(json.dumps(result, ensure_ascii=False, indent=2))

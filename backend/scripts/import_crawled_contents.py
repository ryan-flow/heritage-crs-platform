from pathlib import Path
import sys
import json
from datetime import datetime

from sqlalchemy import select

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.database import SessionLocal
from app.models.content import Content
from crawler.cleaner import Cleaner
from crawler.quality import QualityScorer
from crawler.utils import sha1_text

RAW_JSONL = BASE_DIR / "storage" / "web_crawl" / "cleaned" / "contents.jsonl"
COVERS_DIR = BASE_DIR / "storage" / "covers"
COVERS_DIR.mkdir(parents=True, exist_ok=True)
DEMO_IMPORTER_ID = -199

PALETTES = {
    "专题研究": ("#1C2438", "#8C5A3C", "#F8E6C8"),
    "非遗资讯": ("#3A1816", "#A04D2B", "#FFE0B5"),
    "非遗采集": ("#20262B", "#6C5B45", "#F2DFC2"),
}

SVG_TEMPLATE = """<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='720' viewBox='0 0 1200 720'>
  <defs>
    <linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='{c1}'/>
      <stop offset='100%' stop-color='{c2}'/>
    </linearGradient>
  </defs>
  <rect width='1200' height='720' fill='url(#bg)' rx='36'/>
  <circle cx='1030' cy='120' r='180' fill='rgba(255,255,255,0.09)'/>
  <circle cx='1080' cy='580' r='220' fill='rgba(255,255,255,0.05)'/>
  <text x='78' y='110' fill='{accent}' font-size='28' font-family='Microsoft YaHei, sans-serif'>{chapter}</text>
  <text x='78' y='190' fill='#FFF8EF' font-size='66' font-weight='700' font-family='Microsoft YaHei, sans-serif'>{title1}</text>
  <text x='78' y='270' fill='#FFF8EF' font-size='66' font-weight='700' font-family='Microsoft YaHei, sans-serif'>{title2}</text>
  <text x='78' y='340' fill='rgba(255,248,239,0.92)' font-size='34' font-family='Microsoft YaHei, sans-serif'>{sub}</text>
  <text x='78' y='450' fill='rgba(255,243,232,0.9)' font-size='28' font-family='Microsoft YaHei, sans-serif'>{line1}</text>
  <text x='78' y='495' fill='rgba(255,243,232,0.9)' font-size='28' font-family='Microsoft YaHei, sans-serif'>{line2}</text>
</svg>"""

cleaner = Cleaner()
quality = QualityScorer()


def iter_jsonl(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def parse_published_at(value: str | None):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def source_bucket(item: dict) -> str:
    source = item.get("source_site") or ""
    if "天津大学" in source:
        return "tju"
    if "中国非物质文化遗产网" in source:
        return "ihchina"
    return "other"


def chapter_for(item: dict) -> str:
    bucket = source_bucket(item)
    if bucket == "tju":
        return "专题研究"
    if bucket == "ihchina":
        return "非遗资讯"

    category = item.get("category") or "采集内容"
    mapping = {
        "heritage_news": "非遗资讯",
        "traditional_art": "传统美术与工艺",
        "traditional_craft": "传统美术与工艺",
        "folk_custom": "岁时节庆与民俗",
    }
    return mapping.get(category, "非遗采集")


def sub_chapter_for(item: dict) -> str:
    bucket = source_bucket(item)
    title = item.get("title") or ""
    content = item.get("content") or ""
    merged = f"{title} {content}"

    if bucket == "tju":
        if any(word in merged for word in ["年画", "木版", "版画"]):
            return "木版年画专题"
        if any(word in merged for word in ["学科", "研究生", "硕士", "教材", "高校"]):
            return "高校研究视角"
        if any(word in merged for word in ["保护", "传承", "人才", "教育"]):
            return "非遗保护观察"
        return "专题深读"

    if bucket == "ihchina":
        if any(word in merged for word in ["春节", "元宵", "端午", "节", "年"]):
            return "节庆与民俗"
        if any(word in merged for word in ["通知", "名单", "评审", "政策", "保护"]):
            return "保护政策观察"
        if any(word in merged for word in ["活动", "展演", "启动", "开幕", "举办"]):
            return "地方活动精选"
        return "国家级动态"

    tags = item.get("tags") or []
    if tags:
        return tags[0][:100]
    region = item.get("region")
    if region:
        return f"{region}专题"
    return "网页采集"


def featured_for(item: dict) -> bool:
    score = item.get("quality_score") or 0
    bucket = source_bucket(item)
    title = item.get("title") or ""
    content = item.get("content") or ""
    merged = f"{title} {content}"

    if bucket == "tju" and score >= 0.95:
        return True
    if bucket == "ihchina" and any(word in merged for word in ["春节", "端午", "元宵", "保护", "名单", "活动"]):
        return True
    return score >= 0.96


def normalize_publish_key(value: str | None) -> str | None:
    if not value:
        return None
    return value[:10]


def sort_key(item: dict):
    bucket = source_bucket(item)
    bucket_rank = {"tju": 0, "ihchina": 1, "other": 2}.get(bucket, 9)
    featured_rank = 0 if featured_for(item) else 1
    publish = normalize_publish_key(item.get("publish_time")) or "0000-00-00"
    quality_score = -(item.get("quality_score") or 0)
    return (bucket_rank, featured_rank, quality_score, publish)


def svg_safe(text: str, limit: int) -> str:
    text = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&#39;").replace('"', '&quot;')
    return text[:limit]


def title_lines(title: str) -> tuple[str, str]:
    title = title.strip()
    if len(title) <= 16:
        return title, ""
    return title[:16], title[16:32]


def ensure_cover(item: dict, chapter: str, sub_chapter: str) -> str:
    existing = str(item.get("cover_image") or "").strip()
    if existing:
        return existing

    title = (item.get("title") or "未命名内容").strip()
    publish_key = normalize_publish_key(item.get("publish_time")) or "no-date"
    source = source_bucket(item)
    filename = f"crawler-{source}-{publish_key}-{abs(hash(title)) % 10**8}.svg"
    path = COVERS_DIR / filename

    if not path.exists():
        c1, c2, accent = PALETTES.get(chapter, PALETTES["非遗采集"])
        t1, t2 = title_lines(title)
        line1 = "来自网页采集的精选内容"
        line2 = "适合在小程序中做专题展示"
        svg = SVG_TEMPLATE.format(
            c1=c1,
            c2=c2,
            accent=accent,
            chapter=svg_safe(chapter, 12),
            title1=svg_safe(t1, 18),
            title2=svg_safe(t2, 18),
            sub=svg_safe(sub_chapter, 18),
            line1=svg_safe(line1, 22),
            line2=svg_safe(line2, 22),
        )
        path.write_text(svg, encoding="utf-8")

    return f"/static/covers/{filename}"


def sanitize_item(item: dict) -> dict | None:
    from crawler.models import CrawlArticle

    article = CrawlArticle(
        source_site=item.get("source_site") or "",
        source_url=item.get("source_url") or "",
        crawl_time=item.get("crawl_time") or "",
        title=item.get("title") or "",
        summary=item.get("summary") or "",
        content=item.get("content") or "",
        cover_image=item.get("cover_image"),
        image_urls=item.get("image_urls") or [],
        category=item.get("category") or "other",
        region=item.get("region"),
        tags=item.get("tags") or [],
        publish_time=item.get("publish_time"),
        author=item.get("author"),
        content_type=item.get("content_type") or "article",
        quality_score=float(item.get("quality_score") or 0),
    )
    article = cleaner.normalize(article)
    article.quality_score = quality.score(article)
    if not quality.is_acceptable(article):
        return None
    data = article.to_dict()
    data["content_hash"] = sha1_text((article.title or "") + "\n" + (article.content or "")[:1000])
    data["review_status"] = "approved" if article.quality_score >= 0.8 else "pending"
    data["import_batch"] = "crawler_import"
    return data


def upsert_item(db, existing_map: dict, item: dict) -> str:
    title = (item.get("title") or "未命名内容")[:200]
    publish_time = item.get("publish_time")
    normalized_publish = normalize_publish_key(publish_time)
    key = (title, normalized_publish)

    chapter = chapter_for(item)
    sub_chapter = sub_chapter_for(item)
    record = existing_map.get(key)
    payload = {
        "title": title,
        "cover_url": ensure_cover(item, chapter, sub_chapter),
        "content_type": item.get("content_type") or "article",
        "source_site": item.get("source_site"),
        "source_url": item.get("source_url"),
        "summary": item.get("summary"),
        "body": item.get("content"),
        "chapter": chapter,
        "sub_chapter": sub_chapter,
        "content_hash": item.get("content_hash"),
        "quality_score": float(item.get("quality_score") or 0),
        "review_status": item.get("review_status") or "approved",
        "import_batch": item.get("import_batch") or "crawler_import",
        "is_featured": featured_for(item),
        "status": "published",
        "published_at": parse_published_at(publish_time),
        "created_by": DEMO_IMPORTER_ID,
    }

    if record:
        for field, value in payload.items():
            setattr(record, field, value)
        return "updated"

    content = Content(**payload)
    db.add(content)
    existing_map[key] = content
    return "created"


def import_crawled_contents(limit: int | None = 30) -> tuple[int, int, int]:
    db = SessionLocal()
    created = 0
    updated = 0
    skipped = 0
    try:
        existing_rows = db.execute(select(Content)).scalars().all()
        existing_map = {
            (row.title, row.published_at.strftime("%Y-%m-%d") if row.published_at else None): row
            for row in existing_rows
        }

        raw_items = list(iter_jsonl(RAW_JSONL) or [])
        items = []
        for raw in raw_items:
            cleaned = sanitize_item(raw)
            if cleaned:
                items.append(cleaned)
            else:
                skipped += 1

        deduped = {}
        for item in items:
            title = (item.get("title") or "未命名内容")[:200]
            key = (title, normalize_publish_key(item.get("publish_time")))
            if key not in deduped or (item.get("quality_score") or 0) > (deduped[key].get("quality_score") or 0):
                deduped[key] = item

        curated = sorted(deduped.values(), key=sort_key)
        if limit is not None:
            curated = curated[:limit]

        for item in curated:
            result = upsert_item(db, existing_map, item)
            if result == "created":
                created += 1
            elif result == "updated":
                updated += 1
            else:
                skipped += 1

        db.commit()
        return created, updated, skipped
    finally:
        db.close()


def main() -> None:
    limit = 30
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            limit = 30

    created, updated, skipped = import_crawled_contents(limit=limit)
    print(json.dumps({
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "limit": limit,
        "source": RAW_JSONL.as_posix(),
        "importer_id": DEMO_IMPORTER_ID,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

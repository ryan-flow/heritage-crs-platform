from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class CrawlArticle:
    source_site: str
    source_url: str
    crawl_time: str
    title: str
    summary: str
    content: str
    cover_image: str | None = None
    image_urls: list[str] = field(default_factory=list)
    category: str = "other"
    region: str | None = None
    tags: list[str] = field(default_factory=list)
    publish_time: str | None = None
    author: str | None = None
    content_type: str = "article"
    quality_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CrawlResult:
    article: CrawlArticle
    raw_html_path: str
    cleaned_json_path: str


@dataclass(slots=True)
class SiteCandidate:
    name: str
    homepage: str
    sample_channel: str
    rationale: str
    strengths: list[str]
    risks: list[str]
    priority: int


@dataclass(slots=True)
class SiteDefinition:
    site_key: str
    site_name: str
    base_url: str
    start_urls: list[str]
    allowed_domains: list[str]
    category: str = "other"

    def now_iso(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

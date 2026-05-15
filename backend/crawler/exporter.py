from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from crawler.models import CrawlArticle
from crawler.storage import append_jsonl


class Exporter:
    def export_jsonl(self, path: Path, articles: list[CrawlArticle]) -> None:
        append_jsonl(path, [asdict(article) for article in articles])

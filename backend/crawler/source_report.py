from __future__ import annotations

from dataclasses import asdict

from crawler.registry import SITE_CANDIDATES


def build_source_report() -> list[dict]:
    return [asdict(item) for item in sorted(SITE_CANDIDATES, key=lambda item: item.priority)]

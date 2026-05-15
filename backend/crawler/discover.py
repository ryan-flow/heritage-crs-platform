from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from bs4 import BeautifulSoup

from crawler.utils import normalize_url


@dataclass(slots=True)
class DiscoveryResult:
    urls: list[str]


class URLDiscoverer:
    def discover(self, base_url: str, html: str, patterns: tuple[str, ...]) -> DiscoveryResult:
        soup = BeautifulSoup(html, "html.parser")
        links: list[str] = []
        for node in soup.select("a[href]"):
            href = node.get("href")
            if not href or href.startswith("javascript:") or href.startswith("#"):
                continue
            url = normalize_url(base_url, href)
            if any(part in url for part in patterns):
                links.append(url)
        unique = list(dict.fromkeys(links))
        return DiscoveryResult(urls=unique)

    def filter_new_urls(self, urls: Iterable[str], seen: set[str]) -> list[str]:
        fresh = [url for url in urls if url not in seen]
        seen.update(fresh)
        return fresh

from __future__ import annotations

from dataclasses import asdict
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from crawler.models import SiteCandidate
from crawler.utils import clean_text, extract_article_text, normalize_response_text


class SiteEvaluator:
    def __init__(self) -> None:
        self.client = httpx.Client(timeout=20, follow_redirects=True)

    def evaluate(self, candidate: SiteCandidate) -> dict:
        try:
            response = self.client.get(
                candidate.sample_channel,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
                },
            )
            response.raise_for_status()
            html = normalize_response_text(response)
            soup = BeautifulSoup(html, "html.parser")
            title = clean_text(soup.title.get_text(" ", strip=True) if soup.title else candidate.name)
            content = extract_article_text(html, candidate.sample_channel)
            image_count = len(soup.select("img"))
            domain = urlparse(candidate.homepage).netloc

            scores = {
                "theme_relevance": 1.0 if "非遗" in title or "遗产" in title or "文化" in title else 0.6,
                "content_depth": 1.0 if len(content) >= 500 else 0.6 if len(content) >= 200 else 0.2,
                "image_support": 1.0 if image_count >= 3 else 0.5 if image_count >= 1 else 0.0,
                "structure_stability": 0.9 if domain else 0.5,
                "recommendation_fit": 0.9 if len(content) >= 300 and image_count >= 1 else 0.5,
                "qa_fit": 0.9 if len(content) >= 500 else 0.4,
            }
            total = round(sum(scores.values()) / len(scores), 2)
            return {
                "candidate": asdict(candidate),
                "page_title": title,
                "content_length": len(content),
                "image_count": image_count,
                "scores": scores,
                "total_score": total,
                "accepted": total >= 0.75,
                "status": "ok",
            }
        except Exception as exc:
            return {
                "candidate": asdict(candidate),
                "page_title": candidate.name,
                "content_length": 0,
                "image_count": 0,
                "scores": {},
                "total_score": 0,
                "accepted": False,
                "status": "error",
                "error": str(exc),
            }

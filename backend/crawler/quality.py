from __future__ import annotations

import re

from crawler.models import CrawlArticle


META_TITLE_PATTERNS = [
    r"^\[general information\]$",
    r"^(general information|abstract|summary|contents|table of contents)$",
    r"^(目录|摘要|附录|参考文献|英文目录|作者简介)$",
]

BAD_KEYWORDS = ["版权所有", "ICP备", "广告", "赞助", "上一篇", "下一篇", "打印本页", "关闭窗口"]


class QualityScorer:
    def score(self, article: CrawlArticle) -> float:
        score = 0.0
        title_len = len(article.title or "")
        content_len = len(article.content or "")
        summary_len = len(article.summary or "")

        if 8 <= title_len <= 40:
            score += 0.2
        elif title_len >= 6:
            score += 0.1

        if content_len >= 300:
            score += 0.35
        if content_len >= 800:
            score += 0.15

        if 30 <= summary_len <= 120:
            score += 0.1
        if article.image_urls:
            score += 0.05
        if article.publish_time:
            score += 0.05
        if article.tags:
            score += 0.05
        if article.region:
            score += 0.05

        if self._looks_authoritative(article):
            score += 0.1
        if self._has_bad_signals(article):
            score -= 0.25
        if self.has_bad_title(article.title):
            score -= 0.2
        if self.looks_garbled(article.title or ""):
            score -= 0.2
        if self.looks_garbled(article.content or ""):
            score -= 0.15

        return round(max(0.0, min(score, 0.99)), 2)

    def is_acceptable(self, article: CrawlArticle) -> bool:
        title = (article.title or "").strip()
        content = (article.content or "").strip()
        summary = (article.summary or "").strip()

        if len(title) < 6 or len(content) < 280:
            return False
        if self.has_bad_title(title):
            return False
        if self.looks_garbled(title) or self.looks_garbled(content):
            return False
        if self._has_bad_signals(article):
            return False
        if self._repeated_ratio(content) > 0.45:
            return False
        if not summary and len(content) < 400:
            return False
        return True

    def has_bad_title(self, title: str | None) -> bool:
        text = (title or "").strip()
        if not text:
            return True
        lowered = text.lower()
        return any(re.fullmatch(pattern, lowered, flags=re.IGNORECASE) for pattern in META_TITLE_PATTERNS)

    def looks_garbled(self, text: str) -> bool:
        sample = (text or "").strip()
        if not sample:
            return True
        if "�" in sample:
            return True
        if sample.count("?") >= 4:
            return True
        weird = sample.count("□") + sample.count("■") + sample.count("◆") + sample.count("※")
        if weird >= 3:
            return True
        chunks = [seg for seg in re.split(r"[。！？；;,.、\s]", sample) if seg]
        short_chunks = sum(1 for seg in chunks[:20] if len(seg) <= 2)
        if len(chunks) >= 8 and short_chunks / max(len(chunks[:20]), 1) > 0.55:
            return True
        return False

    def _looks_authoritative(self, article: CrawlArticle) -> bool:
        source = article.source_site or ""
        return any(keyword in source for keyword in ["中国非物质文化遗产", "政府", "大学", "学院", "文旅", "文化馆"])

    def _has_bad_signals(self, article: CrawlArticle) -> bool:
        title = article.title or ""
        content = article.content or ""
        merged = f"{title} {content}"
        if any(word in merged for word in BAD_KEYWORDS):
            return True
        if re.search(r"(http|www\.)", content) and len(content) < 400:
            return True
        return False

    def _repeated_ratio(self, content: str) -> float:
        if not content:
            return 1.0
        chunks = [content[i:i + 20] for i in range(0, len(content), 20) if content[i:i + 20].strip()]
        if not chunks:
            return 1.0
        unique = len(set(chunks))
        return 1 - unique / len(chunks)

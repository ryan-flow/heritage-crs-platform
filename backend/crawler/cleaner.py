from __future__ import annotations

import re

from crawler.models import CrawlArticle
from crawler.utils import clean_text, extract_summary


BAD_TITLE_PATTERNS = [
    r"^(首页|正文|详情|更多|点击查看|阅读全文|相关阅读)$",
    r"^(目录|摘要|附录|参考文献|英文目录|作者简介)$",
    r"^(general information|abstract|summary|contents|table of contents)$",
    r"(版权所有|ICP备|网站地图|返回顶部)",
]

BAD_CONTENT_PATTERNS = [
    r"版权所有",
    r"ICP备",
    r"上一篇",
    r"下一篇",
    r"责任编辑",
    r"打印本页",
    r"关闭窗口",
    r"扫码",
]


class Cleaner:
    def normalize(self, article: CrawlArticle) -> CrawlArticle:
        article.title = self._clean_title(article.title)
        article.summary = self._clean_summary(article.summary)
        article.content = self._clean_content(article.content)
        article.tags = self._clean_tags(article.tags)
        article.image_urls = self._clean_image_urls(article.image_urls)
        article.cover_image = article.cover_image.strip() if article.cover_image else None

        if not article.summary and article.content:
            article.summary = extract_summary(article.content, max_chars=110)
        return article

    def _clean_title(self, value: str) -> str:
        text = clean_text(value)
        text = re.split(r"来源[:：]|作者[:：]|发布时间[:：]|责任编辑[:：]", text)[0].strip(" -|_")
        for pattern in BAD_TITLE_PATTERNS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        text = text.replace("[General Information]", "")
        return clean_text(text)

    def _clean_summary(self, value: str) -> str:
        text = clean_text(value)
        for pattern in BAD_CONTENT_PATTERNS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        return clean_text(text)[:140]

    def _clean_content(self, value: str) -> str:
        text = value or ""
        text = text.replace("\u3000", " ")
        text = re.sub(r"\s+", " ", text)
        for pattern in BAD_CONTENT_PATTERNS:
            text = re.sub(pattern + r".*?($|。|！|!|\.)", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"(来源[:：].*?)($|。|！|!|\.)", " ", text)
        text = re.sub(r"(作者[:：].*?)($|。|！|!|\.)", " ", text)
        text = re.sub(r"(责任编辑[:：].*?)($|。|！|!|\.)", " ", text)
        text = re.sub(r"\[(General Information|Abstract|Contents)\]", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"(英文目录|参考文献|附录)(\s|$)", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"([。！？；;])\1+", r"\1", text)
        return clean_text(text)

    def _clean_tags(self, tags: list[str]) -> list[str]:
        cleaned: list[str] = []
        for tag in tags:
            text = clean_text(tag)
            if not text or len(text) > 20:
                continue
            if text in cleaned:
                continue
            cleaned.append(text)
        return cleaned[:8]

    def _clean_image_urls(self, urls: list[str]) -> list[str]:
        cleaned: list[str] = []
        for url in urls:
            text = url.strip()
            if not text or text in cleaned:
                continue
            cleaned.append(text)
        return cleaned[:6]

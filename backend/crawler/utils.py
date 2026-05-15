from __future__ import annotations

import hashlib
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

import trafilatura
from bs4 import BeautifulSoup


def sha1_text(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def normalize_url(base_url: str, url: str) -> str:
    return urljoin(base_url, url)


def domain_of(url: str) -> str:
    return urlparse(url).netloc.lower()


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def extract_summary(content: str, max_chars: int = 120) -> str:
    return clean_text(content)[:max_chars]


def normalize_response_text(response) -> str:
    encoding = getattr(response, "encoding", None) or getattr(response, "charset_encoding", None) or "utf-8"
    text = response.text
    lowered = encoding.lower()
    if "gb" in lowered and "锟" in text:
        text = response.content.decode("utf-8", errors="ignore")
    return text


def extract_article_text(html: str, url: str) -> str:
    extracted = trafilatura.extract(html, url=url, include_comments=False, include_tables=False)
    if extracted:
        return clean_text(extracted)

    soup = BeautifulSoup(html, "html.parser")
    blocks = [clean_text(node.get_text(" ", strip=True)) for node in soup.select("article, .article, .content, .detail, .post, p")]
    blocks = [block for block in blocks if len(block) >= 20]
    return clean_text("\n".join(blocks))


def parse_publish_time(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"(20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2})", text)
    if not match:
        return None
    return match.group(1).replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-").replace(".", "-")


def is_probably_content_image(image_url: str) -> bool:
    lowered = image_url.lower()
    noise_keywords = [
        "/public/static/",
        "/themes/",
        "logo",
        "icon",
        "banner",
        "nav",
        "thumb",
        "temp/",
        "placeholder",
        "share",
    ]
    return not any(keyword in lowered for keyword in noise_keywords)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from crawler.cleaner import Cleaner
from crawler.discover import URLDiscoverer
from crawler.images import ImageDownloader
from crawler.models import CrawlArticle, CrawlResult, SiteDefinition
from crawler.paths import CLEANED_ROOT, IMAGE_ROOT, RAW_ROOT, STATE_ROOT
from crawler.quality import QualityScorer
from crawler.storage import append_jsonl, read_json, write_json
from crawler.utils import (
    clean_text,
    extract_article_text,
    extract_summary,
    is_probably_content_image,
    normalize_response_text,
    normalize_url,
    now_iso,
    parse_publish_time,
    sha1_text,
)


class BaseSpider:
    detail_patterns: tuple[str, ...] = tuple()

    def __init__(self, site: SiteDefinition) -> None:
        self.site = site
        self.client = httpx.Client(
            timeout=20,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
            },
        )
        self.discoverer = URLDiscoverer()
        self.image_downloader = ImageDownloader(IMAGE_ROOT)
        self.cleaner = Cleaner()
        self.quality = QualityScorer()
        self.content_hashes_path = STATE_ROOT / f"{site.site_key}_content_hashes.json"

        self.site_raw_root = RAW_ROOT / site.site_key
        self.site_pages_root = self.site_raw_root / "pages"
        self.site_html_root = self.site_raw_root / "html"
        self.site_json_root = self.site_raw_root / "json"
        self.state_path = STATE_ROOT / f"{site.site_key}_seen.json"
        for path in [self.site_raw_root, self.site_pages_root, self.site_html_root, self.site_json_root]:
            path.mkdir(parents=True, exist_ok=True)

    def fetch(self, url: str) -> str:
        response = self.client.get(url)
        response.raise_for_status()
        return normalize_response_text(response)

    def discover_urls(self, max_pages: int = 5) -> list[str]:
        seen = set(read_json(self.state_path, {"seen_urls": []}).get("seen_urls", []))
        matched: list[str] = []
        for url in self.site.start_urls[:max_pages]:
            html = self.fetch(url)
            file_key = sha1_text(url)
            (self.site_pages_root / f"{file_key}.html").write_text(html, encoding="utf-8")
            result = self.discoverer.discover(url, html, self.detail_patterns)
            matched.extend(result.urls)
            self.discoverer.filter_new_urls(result.urls, seen)

        matched = list(dict.fromkeys(matched))
        write_json(self.state_path, {"seen_urls": sorted(seen)})
        write_json(self.site_json_root / "seed_urls.json", {"site": self.site.site_key, "urls": matched})
        return matched

    def iter_articles(self, max_items: int) -> list[CrawlResult]:
        urls = self.discover_urls()
        if not urls:
            urls = read_json(self.site_json_root / "seed_urls.json", {"urls": []}).get("urls", [])

        results: list[CrawlResult] = []
        for url in urls[:max_items]:
            html = self.fetch(url)
            result = self.parse_detail(url, html)
            if result:
                results.append(result)
        return results

    def crawl(self, max_items: int = 20) -> list[CrawlResult]:
        seen_hashes = set(read_json(self.content_hashes_path, {"hashes": []}).get("hashes", []))
        results: list[CrawlResult] = []
        for result in self.iter_articles(max_items=max_items):
            article = self.cleaner.normalize(result.article)
            content_hash = sha1_text(article.title + "\n" + article.content[:1000])
            if content_hash in seen_hashes:
                append_jsonl(CLEANED_ROOT / "rejected.jsonl", [{**article.to_dict(), "reject_reason": "duplicate_content"}])
                continue
            article.quality_score = self.quality.score(article)
            if not self.quality.is_acceptable(article):
                append_jsonl(CLEANED_ROOT / "rejected.jsonl", [{**article.to_dict(), "reject_reason": "low_quality"}])
                continue
            seen_hashes.add(content_hash)
            result.article = article
            append_jsonl(CLEANED_ROOT / "contents.jsonl", [article.to_dict()])
            append_jsonl(self.site_json_root / "articles.jsonl", [article.to_dict()])
            results.append(result)

        write_json(self.content_hashes_path, {"hashes": sorted(seen_hashes)})
        return results

    def parse_detail(self, url: str, html: str) -> CrawlResult | None:
        soup = BeautifulSoup(html, "html.parser")
        title = self.extract_title(soup)
        content = extract_article_text(html, url)
        if not title or not content:
            return None

        summary = extract_summary(content)
        publish_time = self.extract_publish_time(soup)
        author = self.extract_author(soup)
        image_urls = self.extract_image_urls(soup, url)
        local_images = [
            img for img in (self.image_downloader.download(self.site.site_key, img) for img in image_urls[:5]) if img
        ]
        article = CrawlArticle(
            source_site=self.site.site_name,
            source_url=url,
            crawl_time=now_iso(),
            title=title,
            summary=summary,
            content=content,
            cover_image=local_images[0] if local_images else None,
            image_urls=local_images,
            category=self.site.category,
            region=self.extract_region(soup, content),
            tags=self.extract_tags(soup, content),
            publish_time=publish_time,
            author=author,
            content_type="article",
        )

        file_key = sha1_text(url)
        raw_html_path = self.site_html_root / f"{file_key}.html"
        raw_html_path.write_text(html, encoding="utf-8")
        cleaned_json_path = self.site_json_root / f"{file_key}.json"
        write_json(cleaned_json_path, article.to_dict())
        return CrawlResult(
            article=article,
            raw_html_path=raw_html_path.as_posix(),
            cleaned_json_path=cleaned_json_path.as_posix(),
        )

    def extract_title(self, soup: BeautifulSoup) -> str:
        selectors = [".article-title", "h1", ".detail-title", ".title"]
        for selector in selectors:
            node = soup.select_one(selector)
            if not node:
                continue
            text = clean_text(node.get_text(" ", strip=True))
            text = re.split(r"来源[:：]|作者[:：]|发布时间[:：]", text)[0].strip(" -|")
            if len(text) >= 6 and text != "相关阅读":
                return text
        title = soup.title.string if soup.title and soup.title.string else ""
        title = clean_text(title)
        return title.replace(" - 中国非物质文化遗产网中国非物质文化遗产数字博物馆", "").strip()

    def extract_publish_time(self, soup: BeautifulSoup) -> str | None:
        selectors = [".time", ".date", ".article-info", ".info", "meta[name='publishdate']"]
        for selector in selectors:
            node = soup.select_one(selector)
            if not node:
                continue
            text = node.get("content") if node.name == "meta" else node.get_text(" ", strip=True)
            parsed = parse_publish_time(text)
            if parsed:
                return parsed
        page_text = clean_text(soup.get_text(" ", strip=True))
        return parse_publish_time(page_text)

    def extract_author(self, soup: BeautifulSoup) -> str | None:
        page_text = clean_text(soup.get_text(" ", strip=True))
        match = re.search(r"来源[:：]\s*([^\s|]+)", page_text)
        return match.group(1) if match else self.site.site_name

    def extract_image_urls(self, soup: BeautifulSoup, page_url: str) -> list[str]:
        urls: list[str] = []
        for node in soup.select("article img, .article img, .content img, .detail img, .article-content img, img"):
            src = node.get("src") or node.get("data-src") or node.get("original")
            if not src or src.startswith("data:"):
                continue
            full_url = normalize_url(page_url, src)
            if is_probably_content_image(full_url):
                urls.append(full_url)
        return list(dict.fromkeys(urls))

    def extract_region(self, soup: BeautifulSoup, content: str) -> str | None:
        region_keywords = [
            "北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江", "上海", "江苏", "浙江", "安徽", "福建", "江西",
            "山东", "河南", "湖北", "湖南", "广东", "广西", "海南", "重庆", "四川", "贵州", "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆",
        ]
        page_text = clean_text(soup.get_text(" ", strip=True)) + " " + content
        for region in region_keywords:
            if region in page_text:
                return region
        return None

    def extract_tags(self, soup: BeautifulSoup, content: str) -> list[str]:
        tags: list[str] = []
        for node in soup.select("meta[name='keywords'], .tags a, .tag a"):
            value = node.get("content") if node.name == "meta" else node.get_text(" ", strip=True)
            if not value:
                continue
            if node.name == "meta":
                tags.extend([clean_text(part) for part in re.split(r"[,，]", value) if clean_text(part)])
            else:
                tags.append(clean_text(value))
        if not tags:
            title = self.extract_title(soup)
            tags.extend([clean_text(item) for item in [title[:8], self.site.site_name, self.site.category] if clean_text(item)])
        return list(dict.fromkeys(tags))[:8]

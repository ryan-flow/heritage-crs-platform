from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.base import BaseSpider
from crawler.models import CrawlArticle, CrawlResult, SiteCandidate, SiteDefinition
from crawler.storage import write_json
from crawler.utils import clean_text, extract_summary, now_iso, sha1_text


SITE_CANDIDATES: list[SiteCandidate] = [
    SiteCandidate(
        name="中国非物质文化遗产网",
        homepage="https://www.ihchina.cn/",
        sample_channel="https://www.ihchina.cn/news",
        rationale="国家级非遗主题门户，栏目清晰，资讯、项目、传承人内容齐全，适合作为知识库主干来源。",
        strengths=["官方权威", "详情页较稳定", "图文内容适合 AI 问答与推荐演示"],
        risks=["部分页面编码与模板较老", "栏目较多，需要控制详情页匹配规则"],
        priority=1,
    ),
    SiteCandidate(
        name="天津大学冯骥才文学艺术研究院中国木版年画研究中心",
        homepage="http://ich.tju.edu.cn/",
        sample_channel="http://ich.tju.edu.cn/index.htm",
        rationale="高校非遗专题站，聚焦木版年画等传统美术与非遗研究内容，适合补充专题深度内容。",
        strengths=["专题聚焦明确", "高校研究背景较权威", "适合补充传统美术类语料"],
        risks=["站点结构较老，但已确认可直接走后端 API", "部分图片链接为相对路径"],
        priority=2,
    ),
    SiteCandidate(
        name="中国非遗馆",
        homepage="https://www.chnim.cn/",
        sample_channel="https://www.chnim.cn/contents/12/",
        rationale="国家级展示平台，适合补充专题展览、馆藏故事与高质量封面素材。",
        strengths=["视觉素材质量较高", "专题内容适合前端展示"],
        risks=["部分页面可能动态渲染", "需要现场抽样验证结构稳定性"],
        priority=3,
    ),
    SiteCandidate(
        name="中国文化报非遗专题",
        homepage="https://www.ccdy.cn/",
        sample_channel="https://www.ccdy.cn/whzh/feiyi/",
        rationale="权威文化媒体，可快速扩充数量并提供新闻语料与事件型内容。",
        strengths=["更新频率高", "适合相关推荐与动态内容"],
        risks=["新闻稿模板较杂", "需严格筛正文质量"],
        priority=4,
    ),
]


class IhchinaSpider(BaseSpider):
    detail_patterns = (
        "/news_details/",
        "/news_1_details/",
        "/news_2_details/",
        "/news2_details/",
        "/luntan_details/",
    )


class TjuIchSpider(BaseSpider):
    API_GROUPS = {
        "news": "/prod-api/information/news/list",
        "conference": "/prod-api/information/conference/list",
        "lecture": "/prod-api/information/lecture/list",
    }

    def discover_urls(self, max_pages: int = 5) -> list[str]:
        urls: list[str] = []
        for group, api_path in self.API_GROUPS.items():
            api_url = urljoin(self.site.base_url, api_path)
            response = self.client.get(api_url, params={"pageNum": 1, "pageSize": max_pages * 10})
            response.raise_for_status()
            payload = response.json()
            rows = payload.get("rows", [])
            for row in rows:
                ich_id = row.get("ichId")
                if ich_id is None:
                    continue
                urls.append(f"api://{group}/{ich_id}")
            file_key = sha1_text(api_url)
            (self.site_pages_root / f"{file_key}.json").write_text(response.text, encoding="utf-8")

        urls = list(dict.fromkeys(urls))
        write_json(self.site_json_root / "seed_urls.json", {"site": self.site.site_key, "urls": urls})
        return urls

    def iter_articles(self, max_items: int) -> list[CrawlResult]:
        urls = self.discover_urls(max_pages=max_items)
        results: list[CrawlResult] = []
        for url in urls[:max_items]:
            parts = url.replace("api://", "").split("/")
            group, item_id = parts[0], parts[1]
            api_url = urljoin(self.site.base_url, f"/prod-api/information/{group}/{item_id}")
            response = self.client.get(api_url)
            response.raise_for_status()
            payload = response.json()
            result = self.parse_api_detail(group, payload)
            if result:
                results.append(result)
        return results

    def parse_api_detail(self, group: str, payload: dict) -> CrawlResult | None:
        data = payload.get("data") or payload
        title = clean_text(data.get("ichTitle") or "")
        content_html = data.get("ichContent") or ""
        soup = BeautifulSoup(content_html, "html.parser")
        content = clean_text(soup.get_text(" ", strip=True))
        if not title or not content:
            return None

        image_urls = []
        for node in soup.select("img"):
            src = node.get("src")
            if src:
                image_urls.append(urljoin(self.site.base_url, src))
        if data.get("ichIdximg") and str(data.get("ichIdximg")).strip():
            image_urls.insert(0, urljoin(self.site.base_url, data["ichIdximg"]))
        image_urls = list(dict.fromkeys(image_urls))
        local_images = [img for img in (self.image_downloader.download(self.site.site_key, img) for img in image_urls[:5]) if img]

        article = CrawlArticle(
            source_site=self.site.site_name,
            source_url=urljoin(self.site.base_url, f"/academicInformation/{group}/{data.get('ichId') or ''}"),
            crawl_time=now_iso(),
            title=title,
            summary=extract_summary(content),
            content=content,
            cover_image=local_images[0] if local_images else None,
            image_urls=local_images,
            category=self.site.category,
            region="天津" if "天津" in content or "天津" in title else None,
            tags=[group, self.site.category, self.site.site_name],
            publish_time=data.get("ichTime"),
            author=clean_text(data.get("ichSource") or self.site.site_name),
            content_type="article",
        )

        file_key = sha1_text(article.source_url)
        raw_html_path = self.site_html_root / f"{file_key}.json"
        raw_html_path.write_text(str(payload), encoding="utf-8")
        cleaned_json_path = self.site_json_root / f"{file_key}.json"
        write_json(cleaned_json_path, article.to_dict())
        return CrawlResult(article=article, raw_html_path=raw_html_path.as_posix(), cleaned_json_path=cleaned_json_path.as_posix())


SITE_REGISTRY: dict[str, tuple[SiteDefinition, type[BaseSpider]]] = {
    "ihchina": (
        SiteDefinition(
            site_key="ihchina",
            site_name="中国非物质文化遗产网",
            base_url="https://www.ihchina.cn/",
            start_urls=[
                "https://www.ihchina.cn/",
                "https://www.ihchina.cn/news",
                "https://www.ihchina.cn/news_1.html",
                "https://www.ihchina.cn/news_2",
                "https://www.ihchina.cn/luntan.html",
            ],
            allowed_domains=["www.ihchina.cn", "ihchina.cn"],
            category="heritage_news",
        ),
        IhchinaSpider,
    ),
    "tju_ich": (
        SiteDefinition(
            site_key="tju_ich",
            site_name="天津大学冯骥才文学艺术研究院中国木版年画研究中心",
            base_url="http://ich.tju.edu.cn/",
            start_urls=[
                "http://ich.tju.edu.cn/",
                "http://ich.tju.edu.cn/index.htm",
            ],
            allowed_domains=["ich.tju.edu.cn"],
            category="traditional_art",
        ),
        TjuIchSpider,
    ),
}


def create_spider(site_key: str) -> BaseSpider:
    site, spider_cls = SITE_REGISTRY[site_key]
    return spider_cls(site)

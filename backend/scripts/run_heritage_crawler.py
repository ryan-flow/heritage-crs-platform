from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from crawler.evaluator import SiteEvaluator
from crawler.paths import CLEANED_ROOT, STATE_ROOT
from crawler.registry import SITE_CANDIDATES, create_spider
from crawler.source_report import build_source_report
from crawler.storage import write_json


def cmd_sources(output: Path | None) -> None:
    report = build_source_report()
    if output:
        write_json(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def cmd_evaluate() -> None:
    evaluator = SiteEvaluator()
    results = [evaluator.evaluate(candidate) for candidate in SITE_CANDIDATES]
    print(json.dumps(results, ensure_ascii=False, indent=2))


def cmd_discover(site_key: str, max_pages: int) -> None:
    spider = create_spider(site_key)
    urls = spider.discover_urls(max_pages=max_pages)
    print(json.dumps({"site": site_key, "count": len(urls), "urls": urls[:50]}, ensure_ascii=False, indent=2))


def cmd_crawl(site_key: str, max_items: int, force: bool) -> None:
    if force:
        for path in [STATE_ROOT / f"{site_key}_seen.json", STATE_ROOT / f"{site_key}_content_hashes.json"]:
            if path.exists():
                path.unlink()
    spider = create_spider(site_key)
    results = spider.crawl(max_items=max_items)
    payload = {
        "site": site_key,
        "count": len(results),
        "jsonl": (CLEANED_ROOT / "contents.jsonl").as_posix(),
        "items": [result.article.to_dict() for result in results[:10]],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heritage web crawler toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sources = subparsers.add_parser("sources", help="输出候选站点清单")
    sources.add_argument("--output", type=Path, default=None)

    subparsers.add_parser("evaluate", help="评估候选站点")

    discover = subparsers.add_parser("discover", help="发现详情页链接")
    discover.add_argument("site_key")
    discover.add_argument("--max-pages", type=int, default=5)

    crawl = subparsers.add_parser("crawl", help="抓取详情页并导出 JSONL")
    crawl.add_argument("site_key")
    crawl.add_argument("--max-items", type=int, default=20)
    crawl.add_argument("--force", action="store_true")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "sources":
        cmd_sources(args.output)
    elif args.command == "evaluate":
        cmd_evaluate()
    elif args.command == "discover":
        cmd_discover(args.site_key, args.max_pages)
    elif args.command == "crawl":
        cmd_crawl(args.site_key, args.max_items, args.force)


if __name__ == "__main__":
    main()

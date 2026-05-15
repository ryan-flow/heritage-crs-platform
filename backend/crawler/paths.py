from __future__ import annotations

from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
CRAWL_ROOT = BACKEND_DIR / "storage" / "web_crawl"
RAW_ROOT = CRAWL_ROOT / "raw"
ASSET_ROOT = CRAWL_ROOT / "assets"
IMAGE_ROOT = ASSET_ROOT / "images"
CLEANED_ROOT = CRAWL_ROOT / "cleaned"
LOG_ROOT = CRAWL_ROOT / "logs"
STATE_ROOT = CRAWL_ROOT / "state"


for path in [CRAWL_ROOT, RAW_ROOT, ASSET_ROOT, IMAGE_ROOT, CLEANED_ROOT, LOG_ROOT, STATE_ROOT]:
    path.mkdir(parents=True, exist_ok=True)

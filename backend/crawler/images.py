from __future__ import annotations

from pathlib import Path

import httpx

from crawler.storage import slugify


class ImageDownloader:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def download(self, site_key: str, image_url: str) -> str | None:
        try:
            response = httpx.get(
                image_url,
                timeout=20,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
                },
            )
            response.raise_for_status()
        except Exception:
            return None

        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            return None

        suffix = Path(image_url.split("?")[0]).suffix or ".jpg"
        file_name = f"{slugify(site_key)}-{slugify(Path(image_url).stem or 'image')}{suffix}"
        file_path = self.root / file_name
        file_path.write_bytes(response.content)
        return file_path.as_posix()

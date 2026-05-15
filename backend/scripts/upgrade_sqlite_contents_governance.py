from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings
from app.core.database import engine


def upgrade_sqlite_contents_governance() -> dict:
    if not settings.sqlite_url.startswith("sqlite:///"):
        return {"ok": False, "message": "当前不是 sqlite，无需执行该脚本"}

    columns = {
        "chapter": "TEXT",
        "sub_chapter": "TEXT",
        "is_featured": "INTEGER NOT NULL DEFAULT 0",
        "source_site": "TEXT",
        "source_url": "TEXT",
        "content_hash": "TEXT",
        "quality_score": "REAL NOT NULL DEFAULT 0",
        "review_status": "TEXT NOT NULL DEFAULT 'pending'",
        "import_batch": "TEXT",
    }

    added: list[str] = []
    with engine.begin() as conn:
        existing = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info('contents')").fetchall()}
        for col_name, col_type in columns.items():
            if col_name not in existing:
                conn.exec_driver_sql(f"ALTER TABLE contents ADD COLUMN {col_name} {col_type}")
                added.append(col_name)

    return {"ok": True, "added": added, "table": "contents"}


if __name__ == "__main__":
    import json

    result = upgrade_sqlite_contents_governance()
    print(json.dumps(result, ensure_ascii=False, indent=2))

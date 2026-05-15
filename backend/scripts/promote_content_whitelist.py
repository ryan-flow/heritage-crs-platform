from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.database import SessionLocal
from app.models.content import Content
from app.services.content_governance import apply_whitelist


def promote_whitelist() -> dict:
    db = SessionLocal()
    try:
        items = db.query(Content).all()
        result = apply_whitelist(items)
        db.commit()
        return {"total": len(items), **result}
    finally:
        db.close()


if __name__ == "__main__":
    import json

    result = promote_whitelist()
    print(json.dumps(result, ensure_ascii=False, indent=2))

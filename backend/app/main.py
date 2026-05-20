from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.models  # noqa: F401  # type: ignore[reportUnusedImport]
from app.api.v1.endpoints import kg  # noqa: F401
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    # No-op: SQLite migration adapter removed (PostgreSQL only)
    _ensure_seed_data()
    yield


def _ensure_seed_data() -> None:
    """首次部署时自动播种种子数据"""
    from app.core.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return
    except Exception:
        return
    finally:
        db.close()

    # 播种基础数据
    import subprocess, sys
    from pathlib import Path

    backend_dir = Path(__file__).resolve().parent.parent
    scripts = [
        "scripts/reset_and_seed_national_heritage_demo.py",
        "scripts/seed_recommendation_content_pack.py",
    ]
    for script in scripts:
        sp = backend_dir / script
        if sp.exists():
            subprocess.run([sys.executable, str(sp)], cwd=str(backend_dir), capture_output=True)


app = FastAPI(title=settings.app_name, debug=settings.app_debug, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(kg.router, prefix="/api/kg", tags=["kg-compat"])
static_dir = settings.backend_dir / "storage"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.mount("/storage", StaticFiles(directory=str(static_dir)), name="storage")


def _ensure_sqlite_columns() -> None:
    return  # Dead code: PostgreSQL only

    table_columns = {
        "contents": {
            "chapter": "TEXT",
            "sub_chapter": "TEXT",
            "is_featured": "INTEGER NOT NULL DEFAULT 0",
            "source_site": "TEXT",
            "source_url": "TEXT",
            "content_hash": "TEXT",
            "quality_score": "REAL NOT NULL DEFAULT 0",
            "review_status": "TEXT NOT NULL DEFAULT 'pending'",
            "import_batch": "TEXT",
        },
        "activities": {
            "cover_url": "TEXT",
            "organizer": "TEXT",
            "notes": "TEXT",
            "is_featured": "INTEGER NOT NULL DEFAULT 0",
        },
        "local_knowledge_base": {
            "chapter": "TEXT",
            "sub_chapter": "TEXT",
            "qa_answer": "TEXT",
        },
        "discussion_topics": {
            "nickname": "TEXT",
            "cover_url": "TEXT",
            "image_urls": "TEXT",
            "is_featured": "INTEGER NOT NULL DEFAULT 0",
            "like_count": "INTEGER NOT NULL DEFAULT 0",
            "favorite_count": "INTEGER NOT NULL DEFAULT 0",
            "comment_count": "INTEGER NOT NULL DEFAULT 0",
        },
        "discussion_comments": {
            "nickname": "TEXT",
        },
        "activity_registrations": {
            "updated_at": "DATETIME",
        },
        "discussion_topic_tags": {
            "topic_id": "INTEGER",
            "tag": "TEXT",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        },
        "discussion_favorites": {
            "topic_id": "INTEGER",
            "user_id": "INTEGER",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        },
        "recommend_logs": {
            "user_id": "INTEGER",
            "action": "TEXT",
            "target_type": "TEXT",
            "target_id": "INTEGER",
            "source_scene": "TEXT",
            "explain_json": "TEXT",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        },
        "users": {
            "preferred_heritage_types": "TEXT",
            "preferred_scene_types": "TEXT",
            "preferred_regions": "TEXT",
            "confidence_score": "REAL NOT NULL DEFAULT 0",
            "score_explicit": "REAL NOT NULL DEFAULT 0",
            "score_implicit": "REAL NOT NULL DEFAULT 0",
            "score_dialogue": "REAL NOT NULL DEFAULT 0",
        },
        "crs_sessions": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_id": "INTEGER NOT NULL",
            "session_id": "TEXT NOT NULL UNIQUE",
            "mode": "TEXT NOT NULL DEFAULT 'cold_start'",
            "turn_count": "INTEGER NOT NULL DEFAULT 0",
            "last_ask_attribute": "TEXT",
            "last_ask_id": "TEXT",
            "context_summary": "TEXT",
            "is_active": "INTEGER NOT NULL DEFAULT 1",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        },
        "crs_ask_logs": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_id": "INTEGER NOT NULL",
            "session_id": "TEXT NOT NULL",
            "ask_id": "TEXT NOT NULL",
            "attribute": "TEXT NOT NULL",
            "question_text": "TEXT NOT NULL",
            "answer": "TEXT",
            "score_delta": "INTEGER NOT NULL DEFAULT 0",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        },
    }

    with engine.begin() as conn:
        for table, columns in table_columns.items():
            existing = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info('{table}')").fetchall()}
            for col_name, col_type in columns.items():
                if col_name not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(_, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": str(exc.detail), "data": None},
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request, exc: RequestValidationError):
    errors = exc.errors()
    print(f"[422] {request.url.path} -> {errors}")
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": "请求参数校验失败", "data": errors},
    )


@app.get("/")
def root() -> dict:
    return {"message": "China Intangible Cultural Heritage Platform API running"}


@app.get("/admin-web")
def admin_web() -> FileResponse:
    web_file = Path(__file__).resolve().parent / "web" / "admin.html"
    return FileResponse(str(web_file))

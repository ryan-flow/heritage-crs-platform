from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings


engine = create_engine(
    settings.sqlite_url,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _auto_migrate():
    """自动迁移：检测并添加缺失的列（SQLite专用）"""
    from sqlalchemy import text as sa_text

    with engine.connect() as conn:
        inspector = inspect(engine)
        # crs_ask_logs.is_skipped
        if "crs_ask_logs" in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns("crs_ask_logs")]
            if "is_skipped" not in cols:
                conn.execute(sa_text("ALTER TABLE crs_ask_logs ADD COLUMN is_skipped BOOLEAN DEFAULT 0 NOT NULL"))
                conn.commit()

        # users.username / users.password (web frontend login)
        if "users" in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns("users")]
            if "username" not in cols:
                conn.execute(sa_text("ALTER TABLE users ADD COLUMN username VARCHAR(64)"))
                conn.commit()
            if "password" not in cols:
                conn.execute(sa_text("ALTER TABLE users ADD COLUMN password VARCHAR(128)"))
                conn.commit()


_auto_migrate()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

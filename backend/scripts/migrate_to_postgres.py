"""
Migration: SQLite → PostgreSQL
Usage:
    # Local Docker PostgreSQL
    python scripts/migrate_to_postgres.py --target postgresql://heritage:heritage123@localhost:5432/heritage

    # Supabase (production)
    python scripts/migrate_to_postgres.py --target postgresql://user:pass@host:6543/postgres
"""
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DATABASE_URL", "")


def get_sqlite_engine():
    from app.core.config import settings
    return create_engine(settings.sqlite_url, connect_args={"check_same_thread": False})


def get_pg_engine(url: str):
    return create_engine(url, pool_pre_ping=True)


def migrate():
    import argparse
    parser = argparse.ArgumentParser(description="SQLite → PostgreSQL migration")
    parser.add_argument("--target", required=True, help="PostgreSQL connection URL")
    args = parser.parse_args()

    print("🔌 Connecting to SQLite...")
    sqlite = get_sqlite_engine()
    sqlite_session = sessionmaker(bind=sqlite)()

    print("🔌 Connecting to PostgreSQL...")
    pg = get_pg_engine(args.target)
    pg_session = sessionmaker(bind=pg)()

    # Import all models to register them with SQLAlchemy metadata
    from app.models import Base

    # Create all tables in PostgreSQL
    print("🏗️  Creating PostgreSQL tables...")
    Base.metadata.create_all(bind=pg)

    # Get all table names from SQLAlchemy metadata
    tables = Base.metadata.sorted_tables

    total_rows = 0
    for table in tables:
        table_name = table.name
        print(f"📋 Migrating {table_name}...", end=" ")

        # Read from SQLite
        rows = sqlite_session.execute(text(f"SELECT * FROM {table_name}")).fetchall()
        if not rows:
            print("0 rows (skip)")
            continue

        # Get column names
        col_names = [col.name for col in table.columns]

        # Insert into PostgreSQL
        for row in rows:
            data = dict(zip(col_names, row))
            stmt = table.insert().values(**{k: v for k, v in data.items() if k in col_names})
            pg_session.execute(stmt)

        pg_session.commit()
        print(f"{len(rows)} rows ✅")
        total_rows += len(rows)

    sqlite_session.close()
    pg_session.close()
    print(f"\n🎉 Migration complete: {total_rows} rows across {len(tables)} tables")


if __name__ == "__main__":
    import os
    migrate()

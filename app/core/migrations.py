import os
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session


MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")


def run_migrations(db: Session):
    # Ensure migrations table exists
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            applied_at DATETIME NOT NULL
        )
    """))
    db.commit()

    applied = {
        row[0]
        for row in db.execute(text("SELECT version FROM schema_migrations")).fetchall()
    }

    files = sorted(f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql"))

    for filename in files:
        version = filename.split("_")[0]
        if version in applied:
            continue

        print(f"[MIGRATION] Applying {filename}")
        path = os.path.join(MIGRATIONS_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            sql = f.read()

        # 🔧 SQLite requires executescript for multi-statement SQL
        conn = db.connection().connection
        conn.executescript(sql)

        db.execute(
            text("""
                INSERT INTO schema_migrations (version, name, applied_at)
                VALUES (:v, :n, :t)
            """),
            {
                "v": version,
                "n": filename,
                "t": datetime.utcnow(),
            },
        )
        db.commit()

        print(f"[MIGRATION] Applied {filename}")

    if not files or len(applied) == len(files):
        print("[MIGRATION] Database schema up to date")

"""Apply SQL migrations in db/migrations in name order, once each."""
import os
import pathlib

import psycopg

MIGRATIONS = pathlib.Path(__file__).parent / "migrations"


def main() -> None:
    url = os.environ.get("DATABASE_URL", "postgresql://cleartab:cleartab@localhost:5432/cleartab")
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        done = {r[0] for r in conn.execute("SELECT name FROM schema_migrations")}
        for path in sorted(MIGRATIONS.glob("*.sql")):
            if path.name in done:
                continue
            with conn.transaction():
                conn.execute(path.read_text())
                conn.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (path.name,))
            print(f"applied {path.name}")


if __name__ == "__main__":
    main()

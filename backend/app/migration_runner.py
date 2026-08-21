"""Migration execution engine.

Applies SQL files under migrations/ in filename order, tracking applied
versions in the schema_migrations table. Uses a simple sequential-SQL
approach instead of Alembic or similar tools.
"""

import logging
from pathlib import Path

from sqlalchemy import Engine, text

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def run_migrations(engine: Engine) -> None:
    """Apply SQL files in the migrations/ directory in order."""
    logger.info("Starting migrations")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )

        applied = {row[0] for row in conn.execute(text("SELECT version FROM schema_migrations"))}
        logger.info("Applied migrations count: %d", len(applied))

        applied_count = 0
        for migration_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = migration_file.stem
            if version in applied:
                logger.debug("Skipping: %s (already applied)", version)
                continue

            logger.info("Applying: %s", version)
            try:
                sql_content = migration_file.read_text(encoding="utf-8")
                for stmt in sql_content.split(";"):
                    stmt = stmt.strip()
                    if stmt:
                        conn.execute(text(stmt))

                conn.execute(
                    text("INSERT INTO schema_migrations (version) VALUES (:v)"),
                    {"v": version},
                )
                applied_count += 1
            except Exception:
                logger.exception("Migration failed: %s", version)
                raise

    if applied_count == 0:
        logger.info("Migrations: all already applied (nothing new)")
    else:
        logger.info("Migrations complete: %d applied", applied_count)

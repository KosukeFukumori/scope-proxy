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


def _run_migration_script(engine: Engine, sql_content: str) -> None:
    """Execute a full migration file as a single script.

    Splitting SQL on ";" breaks as soon as a migration contains a semicolon
    that isn't a statement terminator (a string literal, a comment, or a
    compound statement such as ``CREATE TRIGGER ... BEGIN ...; ...; END``).
    ``sqlite3``'s ``executescript`` tokenizes the script properly and runs
    every statement in it, so it is used instead of a naive split.

    Only the sqlite dialect is supported, matching the rest of the codebase
    (see connect_args handling in app.db), so a raw DBAPI connection is
    pulled out of the engine and executescript() is called directly.
    """
    if engine.dialect.name != "sqlite":
        raise NotImplementedError(
            f"Migration execution only supports sqlite, got dialect: {engine.dialect.name}"
        )

    raw_conn = engine.raw_connection()
    try:
        raw_conn.executescript(sql_content)
    finally:
        raw_conn.close()


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
            # executescript() implicitly commits, so it can't share a
            # transaction with the schema_migrations bookkeeping below.
            _run_migration_script(engine, sql_content)

            with engine.begin() as conn:
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

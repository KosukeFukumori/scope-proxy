"""マイグレーション実行エンジン。

migrations/ 配下の SQL ファイルをファイル名順に適用し、適用済みバージョンを
schema_migrations テーブルで管理する。Alembic 等は使わず、素朴な連番SQL方式にしている。
"""

import logging
from pathlib import Path

from sqlalchemy import Engine, text

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def run_migrations(engine: Engine) -> None:
    """migrations/ ディレクトリ内の SQL ファイルを順番に適用する。"""
    logger.info("マイグレーション開始")

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
        logger.info("適用済みマイグレーション数: %d", len(applied))

        applied_count = 0
        for migration_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = migration_file.stem
            if version in applied:
                logger.debug("スキップ: %s (適用済み)", version)
                continue

            logger.info("適用中: %s", version)
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
                logger.exception("マイグレーション失敗: %s", version)
                raise

    if applied_count == 0:
        logger.info("マイグレーション: すべて適用済み（新規なし）")
    else:
        logger.info("マイグレーション完了: %d 件適用", applied_count)

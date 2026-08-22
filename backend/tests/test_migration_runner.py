"""Tests for app.migration_runner.

Verifies that migrations containing semicolons inside string literals,
comments, and multi-statement triggers are applied correctly now that
migration files are executed as a single script instead of being split
on ";".
"""

from collections.abc import Generator
from pathlib import Path
from typing import cast

import pytest
from sqlalchemy import Engine, create_engine, text

from app import migration_runner
from app.migration_runner import run_migrations


@pytest.fixture
def engine(tmp_path: Path) -> Generator[Engine]:
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    yield engine
    engine.dispose()


def _write_migration(migrations_dir: Path, name: str, sql: str) -> None:
    (migrations_dir / name).write_text(sql, encoding="utf-8")


def test_migration_with_semicolon_in_string_literal(engine: Engine, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    monkeypatch.setattr(migration_runner, "MIGRATIONS_DIR", migrations_dir)

    _write_migration(
        migrations_dir,
        "0001_initial.sql",
        """
        -- comment containing a ; semicolon should not break parsing
        CREATE TABLE widgets (
            id INTEGER PRIMARY KEY,
            label TEXT NOT NULL DEFAULT 'a;b'
        );
        INSERT INTO widgets (label) VALUES ('x;y');
        INSERT INTO widgets DEFAULT VALUES;
        """,
    )

    run_migrations(engine)

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT label FROM widgets ORDER BY id")).all()
        versions = {row[0] for row in conn.execute(text("SELECT version FROM schema_migrations"))}

    assert rows == [("x;y",), ("a;b",)]
    assert versions == {"0001_initial"}


def test_migration_with_trigger_compound_statement(engine: Engine, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    monkeypatch.setattr(migration_runner, "MIGRATIONS_DIR", migrations_dir)

    _write_migration(
        migrations_dir,
        "0001_initial.sql",
        """
        CREATE TABLE items (
            id INTEGER PRIMARY KEY,
            updated_at TEXT
        );

        CREATE TRIGGER items_set_updated_at
        AFTER UPDATE ON items
        BEGIN
            UPDATE items SET updated_at = datetime('now') WHERE id = NEW.id;
        END;
        """,
    )

    run_migrations(engine)

    with engine.begin() as conn:
        conn.execute(text("INSERT INTO items (id) VALUES (1)"))
        conn.execute(text("UPDATE items SET id = 1 WHERE id = 1"))
        updated_at = conn.execute(text("SELECT updated_at FROM items WHERE id = 1")).scalar_one()

    assert updated_at is not None


def test_migrations_applied_across_multiple_files_and_are_idempotent(
    engine: Engine, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    monkeypatch.setattr(migration_runner, "MIGRATIONS_DIR", migrations_dir)

    _write_migration(
        migrations_dir,
        "0001_initial.sql",
        "CREATE TABLE foo (id INTEGER PRIMARY KEY);",
    )

    run_migrations(engine)

    _write_migration(
        migrations_dir,
        "0002_add_bar.sql",
        "CREATE TABLE IF NOT EXISTS bar (id INTEGER PRIMARY KEY);",
    )

    # Running again must skip 0001 (already applied) and only apply 0002.
    run_migrations(engine)

    with engine.connect() as conn:
        versions = {row[0] for row in conn.execute(text("SELECT version FROM schema_migrations"))}
        table_names = {
            row[0]
            for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type = 'table'"))
        }

    assert versions == {"0001_initial", "0002_add_bar"}
    assert {"foo", "bar"} <= table_names


def test_non_sqlite_dialect_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    monkeypatch.setattr(migration_runner, "MIGRATIONS_DIR", migrations_dir)
    _write_migration(migrations_dir, "0001_initial.sql", "CREATE TABLE foo (id INTEGER PRIMARY KEY);")

    class FakeDialect:
        name = "postgresql"

    class FakeEngine:
        dialect = FakeDialect()

        def begin(self):
            raise AssertionError("begin() should not be reached before the dialect check")

    with pytest.raises(NotImplementedError):
        migration_runner._run_migration_script(
            cast(Engine, FakeEngine()), "CREATE TABLE foo (id INTEGER PRIMARY KEY);"
        )

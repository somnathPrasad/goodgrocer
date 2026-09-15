"""Exercise the actual Alembic revision in an isolated schema, including rollback."""

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.core.config import get_settings


def test_migration_upgrade_downgrade_and_metadata_match():
    url = make_url(os.environ.get("TEST_DATABASE_URL", str(get_settings().database_url)))
    engine = create_engine(url)
    schema = "migration_test_" + uuid4().hex
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    isolated_url = url.update_query_dict({"options": "-csearch_path=" + schema})
    env = {**os.environ, "DATABASE_URL": isolated_url.render_as_string(hide_password=False)}
    try:
        for args in [("upgrade", "head"), ("check",), ("downgrade", "base"), ("upgrade", "head")]:
            result = subprocess.run(
                [sys.executable, "-m", "alembic", *args],
                cwd=Path(__file__).resolve().parents[1],
                env=env,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, result.stderr
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()

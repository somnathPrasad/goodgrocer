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
        steps = [
            ("upgrade", "d8a21e9c4b70"),
            ("upgrade", "head"),
            ("check",),
            ("downgrade", "d8a21e9c4b70"),
            ("upgrade", "head"),
            ("downgrade", "base"),
            ("upgrade", "head"),
        ]
        for step, args in enumerate(steps):
            result = subprocess.run(
                [sys.executable, "-m", "alembic", *args],
                cwd=Path(__file__).resolve().parents[1],
                env=env,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, result.stderr
            if step == 0:
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            f'INSERT INTO "{schema}".customers '
                            "(google_subject, created_at, updated_at) "
                            "VALUES ('existing-google-customer', now(), now())"
                        )
                    )
            elif step == 1:
                with engine.connect() as connection:
                    row = connection.execute(
                        text(
                            f'SELECT google_subject, address_onboarding_seen FROM "{schema}".customers'
                        )
                    ).one()
                    assert row == ("existing-google-customer", False)
            elif step == 3:
                with engine.begin() as connection:
                    subject = connection.execute(
                        text(f'SELECT google_subject FROM "{schema}".customers')
                    ).scalar_one()
                    assert subject == "existing-google-customer"
                    # Older phone-login revisions cannot represent a Google-only
                    # Customer. Remove this fixture before cycling the full history.
                    connection.execute(text(f'DELETE FROM "{schema}".customers'))
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()

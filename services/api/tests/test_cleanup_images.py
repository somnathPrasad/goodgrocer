import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app import cleanup_images as cleanup
from app.core.config import Settings

NOW = datetime(2026, 10, 10, tzinfo=UTC)
BASE = "https://example.supabase.co"
PUBLIC = BASE + "/storage/v1/object/public/catalogue-images/"


@pytest.fixture()
def image_db():
    # Only image columns are queried; SQLite can verify the reference query offline.
    engine = create_engine("sqlite://")
    with Session(engine) as db:
        db.execute(
            text("CREATE TABLE products (image_url TEXT, active BOOLEAN, available BOOLEAN)")
        )
        db.execute(text("CREATE TABLE categories (image_url TEXT, active BOOLEAN)"))
        yield db
    engine.dispose()


@pytest.fixture()
def isolated_search_path(db):
    # Raw PostgreSQL LOCK statements must use the fixture's isolated schema too.
    schema = db.get_bind().get_execution_options()["schema_translate_map"][None]
    db.execute(text("SELECT set_config('search_path', :schema, false)"), {"schema": schema})


@pytest.fixture()
def settings():
    return Settings(
        image_storage_provider="supabase",
        supabase_url=BASE,
        supabase_secret_key="sb_secret_test",
    )


def image(name, timestamp="2026-10-08T00:00:00Z", **changes):
    return {
        "id": name,
        "name": name,
        "created_at": timestamp,
        "updated_at": timestamp,
        "metadata": {"size": 1024},
        **changes,
    }


def test_dry_run_preserves_all_references_and_recent_uploads(image_db, settings):
    image_db.execute(
        text("INSERT INTO products VALUES (:url, false, false)"),
        {"url": PUBLIC + "catalogue/product%20photo.jpg?download=1"},
    )
    image_db.execute(
        text("INSERT INTO categories VALUES (:url, false)"),
        {"url": PUBLIC + "catalogue/category.jpg"},
    )
    image_db.commit()
    rows = [
        image("product photo.jpg"),
        image("category.jpg"),
        image("orphan.jpg"),
        image("recent.jpg", "2026-10-09T23:00:00Z"),
        image("replaced.jpg", updated_at="2026-10-09T23:00:00Z"),
        image("unknown.jpg", created_at=None),
        image("notes.txt"),
    ]

    def storage(request):
        assert request.method == "POST"
        assert json.loads(request.content)["prefix"] == "catalogue"
        return httpx.Response(200, json=rows)

    with httpx.Client(transport=httpx.MockTransport(storage)) as client:
        report = cleanup.cleanup_images(image_db, client, settings, now=NOW)

    assert report["paths"] == ["catalogue/orphan.jpg"]
    assert report["referenced_images"] == 2
    assert report["skipped_recent_or_unknown_age"] == 3
    assert report["known_candidate_bytes"] == 1024


def test_reference_matching_checks_project_bucket_and_decodes_paths(image_db, settings):
    image_db.execute(
        text("INSERT INTO products VALUES (:url, true, true)"),
        {"url": PUBLIC + "catalogue/shared.jpg"},
    )
    image_db.execute(
        text("INSERT INTO categories VALUES (:url, true)"),
        [
            {
                "url": BASE + "/storage/v1/render/image/public/catalogue-images/"
                "catalogue/nested/a%20b.jpg?width=50"
            },
            {"url": PUBLIC.replace("example.supabase.co", "other.supabase.co") + "other.jpg"},
        ],
    )
    image_db.commit()
    assert cleanup.referenced_paths(image_db, settings) == {
        "catalogue/shared.jpg",
        "catalogue/nested/a b.jpg",
    }
    image_db.execute(
        text("UPDATE products SET image_url = :url"),
        {"url": BASE + "/storage/v1/object/public/other/catalogue/shared.jpg"},
    )
    image_db.commit()
    assert "catalogue/shared.jpg" not in cleanup.referenced_paths(image_db, settings)


def test_pagination_recursion_and_deletion_batches(db, isolated_search_path, settings, monkeypatch):
    monkeypatch.setattr(cleanup, "PAGE_SIZE", 2)
    monkeypatch.setattr(cleanup, "DELETE_BATCH_SIZE", 2)
    requests = []

    def storage(request):
        body = json.loads(request.content)
        requests.append((request.method, body))
        if request.method == "POST":
            if body["prefix"] == "catalogue/nested":
                return httpx.Response(200, json=[image("c.jpg")])
            if body["offset"] == 0:
                return httpx.Response(200, json=[image("a.jpg"), image("nested", id=None)])
            return httpx.Response(200, json=[image("b.jpg")])
        assert request.url.path == "/storage/v1/object/catalogue-images"
        # Deletion holds both catalogue locks until this session ends.
        locks = db.scalars(text("SELECT mode FROM pg_locks WHERE pid = pg_backend_pid()")).all()
        assert locks.count("ShareRowExclusiveLock") == 2
        return httpx.Response(200, json=[{"name": path} for path in body["prefixes"]])

    with httpx.Client(transport=httpx.MockTransport(storage)) as client:
        report = cleanup.cleanup_images(db, client, settings, delete=True, now=NOW)

    assert report["deleted_count"] == 3
    assert report["paths"] == ["catalogue/a.jpg", "catalogue/b.jpg", "catalogue/nested/c.jpg"]
    assert [method for method, _ in requests] == ["POST", "POST", "POST", "DELETE", "DELETE"]
    assert requests[-1][1] == {"prefixes": ["catalogue/nested/c.jpg"]}


@pytest.mark.parametrize("failure", [401, 500, "invalid", "invalid-entry"])
def test_listing_failure_never_deletes(settings, failure):
    def storage(request):
        assert request.method == "POST"
        if isinstance(failure, int):
            return httpx.Response(failure)
        return httpx.Response(200, json={} if failure == "invalid" else [{"name": "a.jpg"}])

    with (
        httpx.Client(transport=httpx.MockTransport(storage)) as client,
        pytest.raises((httpx.HTTPStatusError, ValueError)),
    ):
        cleanup.cleanup_images(None, client, settings, delete=True, now=NOW)


def test_failed_delete_stops_remaining_batches(db, isolated_search_path, settings, monkeypatch):
    monkeypatch.setattr(cleanup, "DELETE_BATCH_SIZE", 1)
    deletes = []

    def storage(request):
        if request.method == "POST":
            return httpx.Response(200, json=[image("a.jpg"), image("b.jpg")])
        deletes.append(json.loads(request.content)["prefixes"])
        return httpx.Response(500)

    with (
        httpx.Client(transport=httpx.MockTransport(storage)) as client,
        pytest.raises(httpx.HTTPStatusError),
    ):
        cleanup.cleanup_images(db, client, settings, delete=True, now=NOW)
    assert deletes == [["catalogue/a.jpg"]]


def test_unconfirmed_deletion_is_not_reported_as_success(db, isolated_search_path, settings):
    def storage(request):
        return httpx.Response(200, json=[image("a.jpg")] if request.method == "POST" else [])

    with (
        httpx.Client(transport=httpx.MockTransport(storage)) as client,
        pytest.raises(ValueError, match="did not confirm"),
    ):
        cleanup.cleanup_images(db, client, settings, delete=True, now=NOW)


@pytest.mark.parametrize("hours", [-1, float("nan"), float("inf")])
def test_invalid_grace_period_never_contacts_storage(settings, hours):
    def storage(request):
        pytest.fail("Invalid grace period must fail before accessing Storage")

    with (
        httpx.Client(transport=httpx.MockTransport(storage)) as client,
        pytest.raises(ValueError, match="Minimum age"),
    ):
        cleanup.cleanup_images(None, client, settings, min_age_hours=hours)


def test_local_provider_is_rejected():
    with httpx.Client() as client, pytest.raises(ValueError, match="requires"):
        cleanup.cleanup_images(None, client, Settings())


def test_listing_traverses_all_pages_and_folders(settings, monkeypatch):
    monkeypatch.setattr(cleanup, "PAGE_SIZE", 2)
    requests = []

    def storage(request):
        body = json.loads(request.content)
        requests.append((body["prefix"], body["offset"]))
        pages = {
            ("catalogue", 0): [image("a.jpg"), image("nested", id=None)],
            ("catalogue", 2): [image("b.jpg")],
            ("catalogue/nested", 0): [image("c.jpg"), image("notes.txt")],
            ("catalogue/nested", 2): [],
        }
        return httpx.Response(200, json=pages[requests[-1]])

    with httpx.Client(transport=httpx.MockTransport(storage)) as client:
        images = cleanup.list_images(client, settings)
    assert [entry["path"] for entry in images] == [
        "catalogue/a.jpg",
        "catalogue/b.jpg",
        "catalogue/nested/c.jpg",
    ]
    assert requests == [
        ("catalogue", 0),
        ("catalogue", 2),
        ("catalogue/nested", 0),
        ("catalogue/nested", 2),
    ]


@pytest.mark.parametrize(
    ("changes", "eligible"),
    [
        ({}, True),
        ({"created_at": None}, False),
        ({"updated_at": "bad"}, False),
        ({"updated_at": "2026-10-08T00:00:00"}, False),
        ({"updated_at": "2026-10-10T00:00:00Z"}, False),
    ],
)
def test_age_requires_valid_old_creation_and_modification(changes, eligible):
    assert cleanup.old_enough(image("test.jpg", **changes), NOW - timedelta(hours=24)) is eligible

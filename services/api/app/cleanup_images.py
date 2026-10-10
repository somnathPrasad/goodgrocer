"""Operator cleanup of unreferenced catalogue images in Supabase Storage."""

import argparse
import json
from datetime import UTC, datetime, timedelta
from math import isfinite
from pathlib import PurePosixPath
from urllib.parse import quote, unquote, urlsplit

import httpx
from sqlalchemy import select, text, union_all
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.domain import Category, Product

PAGE_SIZE = 100
DELETE_BATCH_SIZE = 100
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def referenced_paths(db: Session, settings: Settings) -> set[str]:
    """Include inactive/unavailable rows and shared product/category images."""
    project = urlsplit(str(settings.supabase_url))
    prefixes = (
        "/storage/v1/object/public/",
        "/storage/v1/object/sign/",
        "/storage/v1/object/authenticated/",
        "/storage/v1/render/image/public/",
        "/storage/v1/render/image/sign/",
        "/storage/v1/render/image/authenticated/",
    )
    paths = set()
    urls = db.scalars(union_all(select(Product.image_url), select(Category.image_url)))
    for url in urls:
        if not url:
            continue
        parsed = urlsplit(url)
        if (parsed.scheme, parsed.netloc) != (project.scheme, project.netloc):
            continue
        path = unquote(parsed.path)
        for prefix in prefixes:
            bucket_prefix = prefix + settings.supabase_storage_bucket + "/"
            if path.startswith(bucket_prefix):
                paths.add(path.removeprefix(bucket_prefix))
                break
    return paths


def list_images(client: httpx.Client, settings: Settings) -> list[dict]:
    """Finish paginated traversal before deleting, so offsets cannot shift."""
    endpoint = (
        f"{str(settings.supabase_url).rstrip('/')}/storage/v1/object/list/"
        f"{quote(settings.supabase_storage_bucket, safe='')}"
    )
    folders = ["catalogue"]
    images = {}
    while folders:
        prefix = folders.pop()
        offset = 0
        seen_names = set()
        while True:
            response = client.post(
                endpoint,
                json={
                    "prefix": prefix,
                    "limit": PAGE_SIZE,
                    "offset": offset,
                    "sortBy": {"column": "name", "order": "asc"},
                },
            )
            response.raise_for_status()
            page = response.json()
            if not isinstance(page, list):
                raise ValueError("Invalid Storage listing; cleanup aborted")
            for entry in page:
                name = entry.get("name") if isinstance(entry, dict) else None
                if (
                    not isinstance(name, str)
                    or not name
                    or "/" in name
                    or name in {".", ".."}
                    or name in seen_names
                    or "id" not in entry
                ):
                    raise ValueError("Invalid or changing Storage listing; cleanup aborted")
                seen_names.add(name)
                path = f"{prefix}/{name}"
                if entry["id"] is None:
                    folders.append(path)
                elif PurePosixPath(name).suffix.lower() in IMAGE_SUFFIXES:
                    images[path] = {**entry, "path": path}
            if len(page) < PAGE_SIZE:
                break
            offset += len(page)
    return sorted(images.values(), key=lambda image: image["path"])


def old_enough(image: dict, cutoff: datetime) -> bool:
    # Missing or ambiguous timestamps are never grounds for deleting an image.
    try:
        timestamps = [
            datetime.fromisoformat(image[field].replace("Z", "+00:00"))
            for field in ("created_at", "updated_at")
        ]
        return all(stamp.tzinfo is not None and stamp <= cutoff for stamp in timestamps)
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def cleanup_images(
    db: Session,
    client: httpx.Client,
    settings: Settings,
    *,
    delete: bool = False,
    min_age_hours: float = 24,
    now: datetime | None = None,
) -> dict:
    if settings.image_storage_provider != "supabase":
        raise ValueError("Cleanup requires IMAGE_STORAGE_PROVIDER=supabase")
    if not isfinite(min_age_hours) or min_age_hours < 0:
        raise ValueError("Minimum age must be a finite, nonnegative number of hours")
    cutoff = (now or datetime.now(UTC)) - timedelta(hours=min_age_hours)
    images = list_images(client, settings)
    if delete:
        # Serialize cleaners and prevent references changing during deletion.
        # Session close/rollback releases these locks; storage deletes cannot roll back.
        db.execute(text("SET LOCAL lock_timeout = '5s'"))
        db.execute(text("LOCK TABLE products, categories IN SHARE ROW EXCLUSIVE MODE"))
    used = referenced_paths(db, settings)
    candidates = [
        image for image in images if image["path"] not in used and old_enough(image, cutoff)
    ]
    sizes = [(image.get("metadata") or {}).get("size") for image in candidates]
    report = {
        "mode": "delete" if delete else "dry-run",
        "bucket": settings.supabase_storage_bucket,
        "prefix": "catalogue/",
        "scanned_images": len(images),
        "referenced_images": sum(image["path"] in used for image in images),
        "skipped_recent_or_unknown_age": sum(
            image["path"] not in used and not old_enough(image, cutoff) for image in images
        ),
        "candidate_count": len(candidates),
        "known_candidate_bytes": sum(size for size in sizes if isinstance(size, int) and size >= 0),
        "candidates_with_unknown_size": sum(
            not isinstance(size, int) or size < 0 for size in sizes
        ),
        "paths": [image["path"] for image in candidates],
    }
    print(json.dumps(report, indent=2), flush=True)
    if delete:
        endpoint = (
            f"{str(settings.supabase_url).rstrip('/')}/storage/v1/object/"
            f"{quote(settings.supabase_storage_bucket, safe='')}"
        )
        deleted = 0
        for start in range(0, len(candidates), DELETE_BATCH_SIZE):
            paths = report["paths"][start : start + DELETE_BATCH_SIZE]
            response = client.request("DELETE", endpoint, json={"prefixes": paths})
            response.raise_for_status()
            result = response.json()
            if not isinstance(result, list) or {
                entry.get("name") for entry in result if isinstance(entry, dict)
            } != set(paths):
                raise ValueError("Storage did not confirm all deletions; inspect storage and rerun")
            deleted += len(paths)
            print(f"Confirmed deleted: {deleted} image(s).", flush=True)
        report["deleted_count"] = deleted
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delete", action="store_true", help="Permanently delete unused images")
    parser.add_argument(
        "--min-age-hours", type=float, default=24, help="Grace period for uploads (default: 24)"
    )
    args = parser.parse_args()
    try:
        settings = get_settings()
        if settings.image_storage_provider != "supabase":
            raise ValueError("Cleanup requires IMAGE_STORAGE_PROVIDER=supabase")
        from app.db.session import SessionLocal

        with (
            SessionLocal() as db,
            httpx.Client(
                timeout=30,
                headers={"apikey": settings.supabase_secret_key.get_secret_value()},
            ) as client,
        ):
            cleanup_images(
                db, client, settings, delete=args.delete, min_age_hours=args.min_age_hours
            )
    except Exception:
        # Upstream exceptions may contain credentials/connection strings.
        raise SystemExit(
            "Cleanup stopped. Check configuration, database access and Storage permissions. "
            "Earlier confirmed Storage deletions cannot be rolled back; inspect storage "
            "before rerunning."
        ) from None


if __name__ == "__main__":
    main()

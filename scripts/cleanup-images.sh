#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
uv run --directory services/api python -m app.cleanup_images "$@"

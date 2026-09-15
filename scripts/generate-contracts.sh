#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
uv run --directory services/api python -m app.cli export-openapi
npm run contracts --prefix apps/admin-web
npm run format --prefix apps/admin-web

# Goodgrocer

Goodgrocer is a grocery ordering product for a single physical Kirana store. The
primary customer experience will be a native Android application, supported by
a backend API and, later, a web portal for store administration.

This repository is in its foundation phase. It contains the initial FastAPI
backend and local PostgreSQL development environment. Product, customer,
order, authentication, payment, and administration functionality remain
unimplemented.

## Repository layout

```text
apps/
  android/        Native Android customer application
  admin-web/      Store-owner administration portal
services/
  api/            Backend API
packages/
  api-contracts/  Reserved for shared API contract artifacts
infra/            Reserved for infrastructure definitions
docs/             Product and technical documentation
scripts/          Reserved for repository automation
```

## Documentation

- [Product](docs/PRODUCT.md) describes the product direction and current scope.
- [Architecture](docs/ARCHITECTURE.md) records only the architecture decisions
  made so far.
- [Decisions](docs/DECISIONS.md) is the repository's lightweight architecture
  decision log.

## Backend development

Prerequisites: Docker, Docker Compose, and
[uv](https://docs.astral.sh/uv/) are installed.

From the repository root, create the local environment file and install the
Python 3.12 environment and dependencies:

```shell
cp .env.example .env
uv sync --directory services/api --dev
```

Start PostgreSQL:

```shell
docker compose up -d
```

Alembic is configured but there are no schema revisions yet. To apply all
available migrations now or in the future:

```shell
uv run --directory services/api alembic upgrade head
```

Start FastAPI from the repository root:

```shell
uv run --directory services/api uvicorn app.main:app --reload
```

In another terminal, verify the service:

```shell
curl http://127.0.0.1:8000/health
```

The response is:

```json
{"status":"ok"}
```

Run the API tests:

```shell
uv run --directory services/api pytest
```

Stop PostgreSQL without deleting its data:

```shell
docker compose down
```

To also delete the local PostgreSQL volume, use `docker compose down -v`.

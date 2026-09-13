# Architecture

This document contains only architecture decisions that have been made. The
current repository is a foundation; application and infrastructure architecture
will be added only as decisions are accepted.

## System boundaries

- Goodgrocer initially supports one physical Kirana store.
- The native Android customer application is the primary customer client.
- A web administration portal will serve the store owner.
- Customer and administration clients access business data through the backend
  API and do not access PostgreSQL directly.
- The backend API service owns access to PostgreSQL.

## Chosen technologies

- Android: Kotlin, Jetpack Compose, and Material 3.
- Backend API: Python and FastAPI.
- Persistence: PostgreSQL through SQLAlchemy, with Alembic for migrations.
- Backend runtime and dependency management: Python 3.12 and uv.
- PostgreSQL access uses SQLAlchemy 2's synchronous API with psycopg 3.
- A future iOS application will be native Swift and SwiftUI, but it is outside
  the current repository scope.
- The administration portal technology stack has not been selected.

## Monorepo layout

```text
apps/
  android/
  admin-web/
services/
  api/
packages/
  api-contracts/
infra/
docs/
scripts/
```

`packages/api-contracts/` is reserved for shared API contract artifacts. The
contract format, ownership workflow, client generation strategy, and packaging
have not been decided.

The backend currently has only thin configuration, database, schema, and API
route modules. `GET /health` is a process-liveness check and deliberately does
not query PostgreSQL. Database configuration is supplied through environment
variables, and migrations are run explicitly rather than during application
startup.

No deployment topology, infrastructure provider, service decomposition,
database model, or product API design has been selected.

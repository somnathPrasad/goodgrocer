# Architecture decision log

Record architectural decisions here as they are made. Give each decision the
next sequential ID and append it to this file. Do not rewrite an accepted
decision to hide history; mark it `Superseded` or `Deprecated` and link the
replacement decision when appropriate.

## Decision template

## ADR-NNN: Decision title

- Date: YYYY-MM-DD
- Status: Accepted | Superseded | Deprecated

### Context

What forces or constraints require a decision?

### Decision

What was decided?

### Consequences

What becomes easier, harder, required, or intentionally deferred?

## ADR-001: Use a purpose-based monorepo

- Date: 2026-09-13
- Status: Accepted

### Context

Goodgrocer will contain a customer application, an administration portal, a
backend API, shared API contract artifacts, infrastructure definitions,
documentation, and repository automation.

### Decision

Use one repository organized into `apps/`, `services/`, `packages/`, `infra/`,
`docs/`, and `scripts/`. Place Android and administration clients under
`apps/`, the backend API under `services/`, and the reserved API contract area
under `packages/`.

### Consequences

Related product components and documentation can evolve together. This
decision establishes locations, but does not select build orchestration,
dependency management, release processes, or shared-contract tooling.

## ADR-002: Select the initial client and backend technologies

- Date: 2026-09-13
- Status: Accepted

### Context

The initial customer platform and backend persistence stack need clear
technology boundaries before application bootstrapping begins.

### Decision

Build the primary customer application as native Android using Kotlin, Jetpack
Compose, and Material 3. Build the backend API using Python and FastAPI. Use
PostgreSQL for persistence, SQLAlchemy for database access, and Alembic for
schema migrations. Clients access business data through the backend API; the
API service owns database access.

### Consequences

Android and backend implementation work has an agreed technology direction.
Android SDK and Gradle configuration, Python version and packaging, internal
application architectures, API design, and deployment remain undecided.

## ADR-003: Bootstrap the backend runtime and local database

- Date: 2026-09-13
- Status: Accepted

### Context

The initial backend needs a reproducible local development path before product
models or APIs are introduced.

### Decision

Run the backend on Python 3.12 and manage its dependencies with uv. Use the
synchronous SQLAlchemy 2 API with psycopg 3. Configure PostgreSQL through a
repository-root environment file and provide PostgreSQL 17 Alpine through
Docker Compose for local development. Keep `GET /health` as a process-liveness
check that does not query the database, and run Alembic migrations explicitly.

### Consequences

Developers can start PostgreSQL, run the API, and verify its liveness with a
small repeatable command sequence. Database readiness, schema revisions, and
all product-domain models and endpoints remain deferred.

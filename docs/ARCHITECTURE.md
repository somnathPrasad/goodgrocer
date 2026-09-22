# Architecture

## Boundaries and technology

Goodgrocer serves one physical Kirana store. Both clients access business data
only through the backend; FastAPI alone owns PostgreSQL access.

- Android: Kotlin, Jetpack Compose/Material 3, ViewModel, StateFlow/coroutines,
  Retrofit/OkHttp, Moshi and Coil. Navigation Compose organizes the screens.
- Admin Android: Kotlin, Jetpack Compose/Material 3, ViewModel, Retrofit/Moshi.
- Retained admin web: Next.js App Router, TypeScript/React, semantic controls and custom CSS.
- Backend: Python 3.12/uv, FastAPI/Pydantic v2, synchronous SQLAlchemy 2,
  psycopg 3, PostgreSQL 17 and explicit Alembic migrations.
- Local infrastructure: Docker Compose for PostgreSQL only.

## Backend

One modular monolith. `app/models` owns normalized tables; `schemas` owns
validated contracts; `services` owns catalogue, authentication and order rules;
`api` exposes `/api/v1` and authorization dependencies. `GET /health` remains a
process-liveness check without a database query. Startup never seeds or migrates.

Products link to many flat categories and have flexible variants. Prices are
Numeric(12,2), never floating point. Public catalogue queries paginate and load
related categories/brands/variants in batches. Inactive products/variants are
hidden; active unavailable products remain visible. Search uses PostgreSQL ILIKE.

Customer and admin sessions are opaque random tokens, stored as hashes with
expiry and explicit logout. Admin credentials use Argon2 and a prompted bootstrap
command. Android obtains a Google ID token through Credential Manager; FastAPI
verifies its signature, issuer, audience and expiry using Google's auth library
and keys customers by the stable `sub` claim. The backend rate limits exchanges.
Contact phone numbers belong to delivery addresses or pickup orders. No Redis,
roles or service decomposition.

Checkout produces a signed, expiring quote. Order creation revalidates it while
locking involved product/variant rows, serializes submissions per customer and
uses a unique idempotency key. Orders snapshot prices, names and addresses.
Order transitions lock the order and enforce the exact product vocabulary;
payment state is independent. Pickup supports direct ACCEPTED → DELIVERED.
Paid online cancellation awaits a refund integration.
The first release rejects new pickup and non-COD checkout requests in the API;
existing orders retain their recorded workflows.

## Clients

The Next.js server proxies `/api/v1/admin` to FastAPI; an HttpOnly SameSite=Strict
cookie stays in the browser, and FastAPI checks Origin for writes. No browser
cross-origin access is required. The portal polls orders every 30 seconds.

The admin Android app calls FastAPI directly. Its dedicated password login returns
an opaque 12-hour admin session token, which it sends as a bearer token. The
token is AES-GCM encrypted with an Android Keystore key in private preferences;
backups are disabled. The browser login continues to use its cookie and Origin
check. The admin Android app polls dashboard and orders every 30 seconds.

Android uses UI → ViewModel → Repository → API/local storage. The customer app
opens at a Google sign-in entry screen when no session is stored, then gives
access to catalogue and basket. The basket persists in private preferences across
sessions. Session material is
AES-GCM encrypted using Android Keystore; backups are disabled. Checkout keys
persist for retry safety. Money uses BigDecimal. Order details refresh every
15 seconds while visible. Images use Coil caching and fixed-size placeholders.

OpenAPI is exported to `packages/api-contracts`; admin web consumes generated
TypeScript types. Both Android apps use explicit Moshi DTOs, verified by builds.

## External services

Protocols isolate payment attempts and image storage. Development
providers run only outside production. Local development and tests re-encode
media and store it on disk, with `/media` references in the database. Production
uses an explicitly selected Supabase Storage adapter while preserving the same
validation and re-encoding boundary. Local seed media is not promoted or migrated
to production. No production payment provider or hosting provider has been
selected; see `PRODUCTION.md`.

## Future considerations

Native Swift/SwiftUI iOS and multi-store remain future work. There are no tenant
columns, organizations or merchant onboarding. PostgreSQL and a single API
serve the customer app and both owner apps for the expected 500-product catalogue.

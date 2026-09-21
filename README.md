# Goodgrocer

A single-store grocery ordering app: native Android shopping, a Next.js owner
portal, and one FastAPI/PostgreSQL backend. Browse anonymously, keep a local
basket, sign in with Google, save addresses/favourites, order for delivery or
pickup, track orders and reorder. The owner manages catalogue/images/availability
and incoming orders. No customer web storefront or inventory quantity tracking.

## Repository

```text
apps/android/             Kotlin, Compose, Material 3, ViewModel, Retrofit/Moshi
apps/admin-web/           Next.js, React, TypeScript, custom CSS
services/api/
  app/api/               Versioned customer/admin routes and authorization
  app/core/              Settings and errors
  app/db/                SQLAlchemy session/base
  app/models/            PostgreSQL domain tables
  app/schemas/           Pydantic contracts and input validation
  app/services/          Catalogue, auth, checkout, orders, provider boundaries
  app/cli.py             Explicit development seed and admin bootstrap
  migrations/            Alembic schema revisions
  tests/                 PostgreSQL business/API tests
packages/api-contracts/   Exported OpenAPI source of truth
scripts/                 Contract generation and local checks
infra/                   Reserved; local PostgreSQL uses root compose.yaml
docs/                    Product, architecture, decisions, production notes
```

## Prerequisites

- Docker Desktop (running) with Docker Compose.
- [uv](https://docs.astral.sh/uv/) (installs the pinned Python 3.12 runtime).
- Node.js 22.15+ and npm.
- Android Studio, JDK 17, Android SDK Platform 36, an API 26+ emulator/device.
  Gradle 9.4.1 is included through the wrapper. Android uses AGP 9.2.1 with its
  built-in Kotlin support; do not add a second Android Kotlin plugin.

## Start locally

Run these from the repository root:

```sh
cp .env.example .env
uv sync --directory services/api --dev
docker compose up -d --wait
uv run --directory services/api alembic upgrade head
uv run --directory services/api python -m app.cli seed
uv run --directory services/api python -m app.cli bootstrap-admin
npm ci --prefix apps/admin-web
cp apps/admin-web/.env.example apps/admin-web/.env.local
```

Bootstrap prompts for a username and a confirmed password of at least 12
characters. It stores only an Argon2 hash; no default admin credentials exist.
Seed inserts 16 development products, three brands and five categories, including
multi-category products, flexible variants, discounts and unavailable examples.
It skips existing products, fills missing photos only for the matching demo produce,
and refuses production mode. Two public-domain produce photos are included; see
`services/api/seed-assets/README.md` for attribution. Upload further images from
the admin portal; missing images have placeholders.
Neither seeding nor migrations run automatically at application startup.

Start the API in one terminal:

```sh
uv run --directory services/api uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Start the portal in another:

```sh
npm run dev --prefix apps/admin-web
```

Open **http://localhost:3000** and sign in with your bootstrapped account.
Use `localhost` (not `127.0.0.1`) in the browser to match `ADMIN_ORIGIN`.
API docs: **http://localhost:8000/docs**. Liveness:

```sh
curl http://localhost:8000/health
curl 'http://localhost:8000/api/v1/products?page=1'
```

### Android

Open `apps/android` in Android Studio, let Gradle sync, select an emulator and
run `app`. Android Studio creates ignored `local.properties` with the SDK path.
Alternatively set `ANDROID_HOME` to your SDK installation and run:

```sh
# macOS default; on Linux commonly "$HOME/Android/Sdk"
export ANDROID_HOME="$HOME/Library/Android/sdk"
./apps/android/gradlew -p apps/android :app:assembleDebug :app:installDebug \
  -PGOOGLE_WEB_CLIENT_ID=your-web-oauth-client.apps.googleusercontent.com
```

The default emulator API URL is `http://10.0.2.2:8000/` (the host computer).
For a USB device, use `adb reverse` and a different build URL:

```sh
adb reverse tcp:8000 tcp:8000
./apps/android/gradlew -p apps/android :app:installDebug \
  -PAPI_URL=http://127.0.0.1:8000/ \
  -PGOOGLE_WEB_CLIENT_ID=your-web-oauth-client.apps.googleusercontent.com
```

API URLs require a trailing slash. Cleartext HTTP is permitted only in debug
builds. Release builds require an HTTPS endpoint and your own signing setup:

```sh
./apps/android/gradlew -p apps/android :app:assembleRelease \
  -PAPI_URL=https://api.example.com/ \
  -PGOOGLE_WEB_CLIENT_ID=your-web-oauth-client.apps.googleusercontent.com
```

### Google sign-in and development payments

Browse and fill the basket without signing in. For customer accounts, configure a
Google OAuth web client ID in `GOOGLE_WEB_CLIENT_ID` for the API and pass the same
ID to the Android build with `-PGOOGLE_WEB_CLIENT_ID=...`. Configure an Android
OAuth client for `com.goodgrocer.app` and the signing certificate fingerprints.
The Android app obtains an ID token through Credential Manager; the API verifies
it and issues the app session. Enter a contact phone in the delivery address or
at pickup checkout. Production requires the web client ID.

COD and UPI on delivery/collection work without payment credentials. The owner
marks payment received independently of delivery status. Online UPI is clearly
labelled as a development test; the order details screen can simulate PAID or
FAILED, with no money transfer. An unpaid online order cannot be accepted.
Production online UPI is disabled until a real integration is implemented.

## Environment

Root `.env` is read independently of the current working directory:

| Variable | Local value / purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy `postgresql+psycopg://…` connection |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Docker PostgreSQL credentials; sample values are local only |
| `ENVIRONMENT` | `development`, `test` or `production` |
| `SECRET_KEY` | Signs checkout quotes; replace with a random secret for production |
| `GOOGLE_WEB_CLIENT_ID` | Google OAuth web client ID used as the API token audience; required in production |
| `PAYMENT_PROVIDER` | `development` or `disabled`; production adapter not yet selected |
| `IMAGE_STORAGE_PROVIDER` | `local` for development/tests; production requires `supabase` |
| `SUPABASE_URL` | Supabase project HTTPS URL; required for Supabase image storage |
| `SUPABASE_SECRET_KEY` | Server-only `sb_secret_...` API key; never expose it to either client |
| `SUPABASE_STORAGE_BUCKET` | Public catalogue-image bucket; defaults to `catalogue-images` |
| `ADMIN_ORIGIN` | `http://localhost:3000`; exact trusted browser origin |
| `PUBLIC_API_URL` | `http://localhost:8000`; HTTPS required in production |
| `MEDIA_DIR` | Optional absolute path; defaults to `services/api/media` |
| `DELIVERY_FEE` | Decimal rupees, default `0.00`; pickup is free |
| `SESSION_HOURS` | Customer expiry, default 168; admin expiry is 12 hours |

The admin's `.env.local` uses `API_URL=http://127.0.0.1:8000`. Its Next.js server
proxies `/api/v1/admin` and `/media` to FastAPI. Browser requests are same-origin;
there is intentionally no cross-origin CORS allowlist. FastAPI checks Origin on
admin writes. Customer bearer sessions cannot authorize admin endpoints.

Uploads accept JPEG/PNG/WebP up to 5 MB and 20 megapixels, decode/re-encode to
JPEG to strip metadata, and store immutable random filenames outside PostgreSQL.
Local development stores them under `MEDIA_DIR`. Production uploads them under
`catalogue/` in the configured public Supabase Storage bucket and persists the
public HTTPS URL. The bucket must already exist; application startup does not
provision it. Local seed media is intentionally not migrated to production.

## Tests, formatting and builds

Backend tests use unique temporary schemas in PostgreSQL; they do not truncate
or drop your catalogue. The database user must have CREATE SCHEMA permission.
Set `TEST_DATABASE_URL` to use a separate PostgreSQL database if desired.

```sh
uv run --directory services/api pytest
uv run --directory services/api ruff check app tests migrations
uv run --directory services/api ruff format --check app tests migrations
uv run --directory services/api alembic check
npm run test --prefix apps/admin-web
npm run typecheck --prefix apps/admin-web
npm run format:check --prefix apps/admin-web
npm run build --prefix apps/admin-web
./apps/android/gradlew -p apps/android :app:testDebugUnitTest :app:lintDebug :app:ktlintCheck :app:assembleDebug
```

Format changes with `ruff format`, `npm run format --prefix apps/admin-web`,
and `./apps/android/gradlew -p apps/android :app:ktlintFormat`.
To run the built portal: `npm run start --prefix apps/admin-web`.

## API and contract workflow

Important routes (prefix `/api/v1`):

- `GET /config`, `/categories`, `/brands`, `/products`, `/products/{id}`
- `POST /auth/google`, `/auth/logout`
- `GET/POST /addresses`, `PUT/DELETE /addresses/{id}`
- `GET /favourites`, `PUT/DELETE /favourites/{product_id}`
- `POST /checkout/quote`, `POST /orders`, `GET /orders`, `/orders/{id}`
- `POST /orders/{id}/reorder`, `/orders/{id}/development-payment?outcome=PAID|FAILED`
- `POST /admin/auth/login`, `/admin/auth/logout`; `GET /admin/me`, `/admin/dashboard`
- Admin list/create/edit brands, categories, products and nested product variants
- `POST /admin/images`, `/admin/orders/{id}/status`, `/admin/orders/{id}/mark-paid`

Lists use pages, with products returning `items`, `total`, `page`, `page_size`.
Order pages contain 20 entries. Monetary JSON values are decimal strings.
Errors use `{"error":{"code":"…","message":"…"}}`. Quote tokens expire after
10 minutes. Order submission requires the quote plus an idempotency key;
retries return the original order, and changed requests cannot reuse that key.

After changing Pydantic contracts, regenerate and commit both artifacts:

```sh
./scripts/generate-contracts.sh
```

OpenAPI is the source of truth; admin types are generated with
`openapi-typescript`. Android keeps small explicit Moshi DTOs in `data/Models.kt`
and endpoint declarations in `data/Api.kt`; update them alongside contract
changes and run the Android tests/build. No internal publishing system is needed.

Verification results and tested limits: [docs/VERIFICATION.md](docs/VERIFICATION.md).

## Production boundaries

See [production configuration](docs/PRODUCTION.md). Online
UPI requires a selected provider and credentials **plus adapter implementation**.
The shipped development providers cannot run in production. Before public use,
configure TLS, a random secret, database credentials, Supabase Storage/backups,
release signing and store-specific delivery fee/pickup instructions. This repo
does not provision hosting, signing keys or a notification system.

[Product](docs/PRODUCT.md) · [Architecture](docs/ARCHITECTURE.md) ·
[Decision log](docs/DECISIONS.md)

Stop PostgreSQL without deleting data: `docker compose down`.

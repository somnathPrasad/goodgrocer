# V1 verification — 2026-09-15 (historical, before Google sign-in change)

## Automated checks

- PostgreSQL API/business suite: 28 passing tests.
- Actual Alembic revision: isolated-schema upgrade → metadata check → downgrade
  → upgrade passes (one additional test). Total backend tests: 29.
- `ruff check app tests migrations` and `ruff format --check`: pass.
- `alembic check`: no schema drift.
- Admin proxy tests: 3 pass (path restrictions, session forwarding, outage errors).
- Admin TypeScript check, Prettier check and Next.js production build: pass.
- Android `assembleDebug`, six unit tests, `ktlintCheck` and `lintDebug`: pass.
  Android lint has 16 non-fatal warnings: newer SDK/library/tool versions,
  SharedPreferences KTX suggestions and a redundant resource qualifier. No lint
  rules or compiler errors were suppressed to obtain the build.
- `git diff --check`: pass.

## Live local verification

PostgreSQL 17 container, FastAPI on port 8000, Next.js on port 3000, and the
API 36 Android emulator were used. The APK installed and opened without a crash.

Verified on Android:

1. Real seeded catalogue and product detail response.
2. Selecting the 1 kg tomato variant changes the price to ₹45.00.
3. Adding to the anonymous basket; checkout prompts for phone login.
4. Development OTP request, incorrect-code error and successful verification.
5. Pickup checkout displays the server-validated ₹45.00 total.
6. Order `GG-8126B83BCF8B` is created and shown on the success/tracking screen.
7. A temporary test admin logs in through the real Next.js proxy, sees that same
   order, accepts it, marks it collected and records payment received.
8. Android refresh displays collected and PAID.
9. Reorder restores the 1 kg variant at the current ₹45.00 price.
10. The final `com.goodgrocer.app` APK retains a basket after force-stop and cold
    start. The earlier development package was removed from the emulator.

The temporary admin and its sessions were removed. The development customer and
order remain as sample data on this machine. They are not seeded on new machines.

Admin browser interaction/visual testing and physical-device testing were not
performed. The admin's live authentication/proxy/order workflow was exercised
through HTTP, and its forms were production-built and type-checked. Delivery
transitions, addresses, favourites, stale checkout, availability, ownership and
payment boundaries are covered by PostgreSQL tests. Real SMS and online payment
providers remain unselected, so no real message or money transfer was tested.

## Google sign-in change — 2026-09-21

- API suite and isolated Alembic upgrade/check/downgrade: 41 passed.
- Python Ruff lint and format checks: passed.
- Android debug Kotlin compilation, unit tests and ktlint: passed.
- Admin TypeScript check and generated OpenAPI types: passed.
- A live Google account exchange was not tested because OAuth client IDs and
  Android signing fingerprints have not been configured for this environment.

## Customer deletion and public website — 2026-09-23

- PostgreSQL API/business suite and isolated Alembic migration cycle: 49 passed.
- Python Ruff lint and format checks: passed.
- Customer Android `ktlintCheck`, six unit tests, `lintDebug` and `assembleDebug`:
  passed.
- Public website Prettier check, TypeScript check and Next.js production build:
  passed. The home, privacy and account-deletion pages returned HTTP 200 locally;
  malformed deletion input returned HTTP 422.
- Admin web TypeScript check, Prettier check, three proxy tests and production
  build: passed.
- Admin Android debug compilation, lint and assembly: passed.
- `git diff --check`: passed.

A live Google deletion was not performed because production OAuth clients and
origins are not configured in this environment. Production still requires the
public website deployment, Android public-site URL, Play Store URL and a daily
schedule for `erase-expired-customer-data`.

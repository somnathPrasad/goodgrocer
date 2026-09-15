# V1 verification — 2026-09-15

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

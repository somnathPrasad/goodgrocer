# Production configuration and external integrations

## External blockers

### Public website

Publish the public website privacy policy under the operator name Somnath Prasad
with `somnathprasad559@gmail.com` as the privacy contact. Configure its Google web
client for the production origin and supply the Play Store URL when the listing
is available. Deploy it separately from the owner portal with server-only
`API_URL`, public `NEXT_PUBLIC_GOOGLE_WEB_CLIENT_ID`, and optional
`NEXT_PUBLIC_PLAY_STORE_URL`.

### Google sign-in

Create Google OAuth clients for the Android package and release signing
certificate, plus a web client for the backend audience. Set the same web client
ID as Android's `-PGOOGLE_WEB_CLIENT_ID=...` Gradle property and the API's
`GOOGLE_WEB_CLIENT_ID` environment variable. The backend verifies Google ID
tokens before issuing its own sessions. Production startup requires the web
client ID. Test on an Android device with Google Play services and the release
signing certificate before opening login. Contact phones are collected for
fulfilment and are not treated as verified identity.

### Online UPI

Choose a provider and extend `PaymentProvider` with its order/payment creation
and verification operations. The existing `PaymentAttempt` keeps provider,
reference, amount and independent status. Production needs credentials, checkout
handoff on Android, signed webhook verification, unique event/idempotent handling,
amount/currency/order matching, reconciliation and refunds. Never mark PAID from
an unverified customer callback. Permit cancellation of paid orders only after
implementing and testing refund behavior. Provider calls should not hold database
locks during slow network operations; persist an attempt before handoff.

The first release accepts delivery and COD only, regardless of payment provider
configuration. `PAYMENT_PROVIDER=disabled` also keeps online UPI unavailable when
that release restriction is eventually lifted. The development outcome endpoint is authenticated, owner-scoped,
terminal-state checked and guarded by the provider factory. It cannot run in
production. A failed test payment leaves a visible FAILED order, which the owner
can cancel; the customer may reorder. No money is transferred.

## Deployment checklist

- Set `ENVIRONMENT=production`, disable development payment provider, set a random
  `SECRET_KEY` (for example generate locally with `openssl rand -hex 32`),
  and use HTTPS for `PUBLIC_API_URL` and exact `ADMIN_ORIGIN`.
- Use unique database credentials and private database networking. The Compose
  credentials are only for local development. Run migrations as a release step.
- Deploy Next.js with server-side `API_URL` pointing to FastAPI; expose only the
  intended application surfaces. No wildcard CORS is configured or needed.
- Terminate TLS at a trusted proxy, enforce upload/request limits and timeouts,
  and configure trusted proxy addresses explicitly. Do not trust arbitrary
  forwarded client-IP headers. Admin rate limits currently see the Next.js
  server IP (an intentional conservative aggregate limit for the single owner).
- Create a public Supabase Storage bucket (default `catalogue-images`) restricted
  to JPEG objects and a 5 MB maximum. Set `IMAGE_STORAGE_PROVIDER=supabase`, the
  project `SUPABASE_URL`, a server-only `SUPABASE_SECRET_KEY`, and optionally
  `SUPABASE_STORAGE_BUCKET`. Never expose the secret to Next.js browser code or
  Android. FastAPI validates and re-encodes uploads before storing immutable
  `catalogue/*.jpg` objects. The app does not create the bucket at startup.
- Local seed media is not migrated to production. Replaced production objects are
  retained; add an operator cleanup process after deciding retention, never delete
  historical references indiscriminately.
- Schedule database/media backups and practice restore. Establish log rotation
  and retention, session/rate-limit/legacy-OTP cleanup and operational alerts.
  Request logs contain method/path/status/duration/request ID, not auth bodies.
- Run `uv run --directory services/api python -m app.cli erase-expired-customer-data`
  at least daily so active orders cannot retain deleted-customer delivery details
  beyond their 30-day limit.
- Configure the Android HTTPS API URL, release signing and store distribution.
  Test on physical devices, TalkBack, larger text and unreliable networks.
- Confirm store contact information and delivery fee.
  Fees default to zero. Addresses are manually assessed, without serviceability
  APIs. The owner must record received cash payments explicitly.

Infrastructure provisioning, release signing, a full penetration test, production
load testing and real payment certification are not delivered by a local V1.
No order notification provider is implemented or required.

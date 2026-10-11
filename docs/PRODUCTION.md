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

### WhatsApp webhook

The callback path is `/api/v1/webhooks/whatsapp` (no trailing slash). It captures
incoming events and delivery statuses; it does not send OTPs or change customer
login yet.

1. Set backend-only `WHATSAPP_WEBHOOK_VERIFY_TOKEN` to a random value (generate
   locally with `openssl rand -hex 32`). Set `WHATSAPP_APP_SECRET` to the **App
   secret** from Meta App Dashboard > App settings > Basic. This is not a WhatsApp
   access token, the webhook Verify token, or the Goodgrocer `SECRET_KEY`.
   Store both values in the deployment's secret environment settings; do not put
   them in Android, browser code, Git, logs or screenshots.
2. Run `uv run --directory services/api alembic upgrade head` as a release step
   and deploy/restart the API with those environment variables.
3. Ensure GET and POST reach the API through a public HTTPS URL with a valid
   trusted certificate. Preserve the raw POST body and `X-Hub-Signature-256`
   header. Set proxy request limits to allow up to 4 MiB; the API rejects larger
   payloads with 413. Do not log webhook bodies, signature headers or GET query
   strings (the latter contain the Verify token). The API's own request logger
   logs the path only. If enabling Meta's optional mTLS, configure certificate
   validation at the TLS proxy; application HMAC checks still apply.
4. In Meta's WhatsApp Configuration (or Use cases > Customize > Configuration),
   enter Callback URL `https://YOUR_API_HOST/api/v1/webhooks/whatsapp` and the
   exact `WHATSAPP_WEBHOOK_VERIFY_TOKEN` value in Verify token. Select Verify and
   save, then subscribe to `messages` for incoming messages and outbound message
   statuses. Ensure the app is also subscribed to the intended WABA.
5. Send a Meta test webhook and confirm a 200 response and a stored row in
   `whatsapp_webhook_deliveries`. Confirm real delivery after the sender/WABA
   subscription is configured. No live Meta verification is performed by local
   backend tests.

GET verification returns the challenge as unquoted plain text only for
`hub.mode=subscribe` and the matching token. POST rejects missing/incorrect
HMAC-SHA256 signatures before parsing or storage. It accepts a WhatsApp Business
Account envelope with an `entry` array, preserving every entry/update in the raw
batch without depending on specific subscribed fields. Unconfigured secrets
return 503. Invalid requests return 4xx; capture/commit failures return non-200
so Meta can retry. Exact-byte retries return 200 without adding another row;
different batches containing the same events are captured separately. Nothing
marks an OTP verified from a delivery/read status or incoming message.

Raw payloads include personal data. Restrict database/backup access and schedule
`uv run --directory services/api python -m app.cli erase-expired-whatsapp-webhooks`
at least daily to erase records aged 30 days or more. Align backup retention and
the published privacy policy with this diagnostic storage before enabling real
customer events. Cleanup is not scheduled automatically and payloads cannot be
recovered from Meta after deletion.

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
  retained until the operator runs the unused-image cleanup described below.
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

## Clean up unused catalogue images

Run from the repository root with the API's existing environment configuration:
`DATABASE_URL` must point to the database using the configured Supabase project
and bucket. The script reads product and category image references directly through
the backend, including inactive and unavailable rows. It scans JPEG, PNG and WebP
images under `catalogue/` in `SUPABASE_STORAGE_BUCKET`; other files and folders
outside that prefix are untouched. Orders do not store image references.

```sh
# Preview paths, counts and known reclaimable bytes; no deletion.
sh scripts/cleanup-images.sh

# Permanently delete unreferenced images that are at least 24 hours old.
sh scripts/cleanup-images.sh --delete

# Optional longer grace period for unfinished catalogue edits.
sh scripts/cleanup-images.sh --delete --min-age-hours 72
```

The default 24-hour grace period covers both creation and last modification.
Images with missing or invalid timestamps are skipped. Choose a longer grace
period if owner edits can remain unfinished longer; avoid running deletion while
an owner has an unsaved edit referencing an older unused image. `--min-age-hours 0`
disables the grace period. Verify the dry run and database/project pairing before
using `--delete`.

Listing completes before any deletion. Delete mode then locks product and category
tables, reads current references again, and holds the locks through deletion to
prevent concurrent catalogue writes and cleanup runs from changing the decision.
Customer reads continue, but owner catalogue saves may wait; run during a quiet
period. A five-second database lock timeout aborts a busy run. Storage requests
have a 30-second timeout and deletion uses batches of 100 through the Storage API,
as required by [Supabase's deletion guidance](https://supabase.com/docs/guides/storage/management/delete-objects).
The server-only secret needs Storage list/delete access. No new credentials or
dependencies are required.

The script exits nonzero on failure and reports each confirmed deletion batch.
Storage deletions are permanent and cannot roll back if a later batch fails;
inspect storage and rerun the preview after a failed run. Cleanup is manual unless
the operator schedules this command.

Infrastructure provisioning, release signing, a full penetration test, production
load testing and real payment certification are not delivered by a local V1.
No order notification provider is implemented or required.

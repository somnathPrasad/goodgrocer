# Repository guidance

Goodgrocer is initially a single-store Kirana/grocery ordering product. Keep
changes consistent with the product boundaries in `docs/PRODUCT.md` and the
confirmed technical choices in `docs/ARCHITECTURE.md`.

## Repository ownership

- `apps/android/` contains the native Android customer application.
- `apps/admin-web/` contains the store-owner web portal.
- `services/api/` contains the backend API and owns access to PostgreSQL.
- `packages/api-contracts/` is reserved for shared API contract artifacts.
- `infra/` is reserved for infrastructure definitions.
- `docs/` contains product and architecture documentation.
- `scripts/` is reserved for repository automation.

## Change discipline

- Do not introduce speculative frameworks, infrastructure, service boundaries,
  or abstractions.
- Do not implement roadmap functionality unless it is explicitly in the scope
  of the task.
- Keep clients behind the backend API boundary; clients must not access the
  database directly.
- Record new architectural decisions in `docs/DECISIONS.md` and update
  `docs/ARCHITECTURE.md` when the accepted architecture changes.
- Add build, test, formatting, and run instructions only when the associated
  tooling exists in the repository.
- Preserve the exact order status vocabulary documented in `docs/PRODUCT.md`
  unless a later accepted decision changes it.

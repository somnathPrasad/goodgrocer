# Goodgrocer

Goodgrocer is a grocery ordering product for a single physical Kirana store. The
primary customer experience will be a native Android application, supported by
a backend API and, later, a web portal for store administration.

This repository is currently in its foundation phase. It contains the agreed
monorepo structure and project documentation, but no application, service,
infrastructure, authentication, payment, ordering, or administration
implementation.

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

Build, test, and run instructions will be added when the corresponding
applications and services are bootstrapped.

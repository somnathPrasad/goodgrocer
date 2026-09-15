# API contracts

`openapi.json` is exported from FastAPI, not edited by hand. Run
`./scripts/generate-contracts.sh` from the repository root after contract edits.
Commit the JSON and generated `apps/admin-web/lib/api.generated.ts` together.
Android uses explicit DTOs in `data/Models.kt`; update them with the same change.
Decimal response values are strings. Request bodies reject unknown properties.

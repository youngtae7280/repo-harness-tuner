# Validation Guide

Use the cheapest check that gives meaningful evidence.

- Focused type check: `npm run typecheck`.
- Focused tests: `npm test`.
- Broad build check: `npm run build`.

Run broad validation for shared contracts, release-facing changes, or broad refactors. Record skipped validation with a reason when tools are unavailable.

# Changelog

## 2026-11-11 — Deployment and local-development repair

- Aligned the Render backend service reference with `freightpilot-backend`, matching the previously reported Render hostname.
- Changed the Render readiness probe to `/health/ready` so a running process is not marked healthy when PostgreSQL or required Redis is unavailable.
- Resolved the production storage conflict by configuring Render for PostgreSQL-backed document bytes, matching backend production validation.
- Standardized Node.js on 24.13.0 / Node 24 across `.node-version`, `.nvmrc`, frontend engine requirements, and CI.
- Added explicit frontend type-check and dependency-audit scripts and CI steps.
- Added local runbook, provider credential matrix, and security verification guidance.
- Archived conflicting historical handover and deployment notes so they are not mistaken for current instructions.
- Added backend readiness and local CORS regression tests.

## Verification

- Backend pytest suite: 51 passed.
- Python bytecode compilation: passed.
- Render YAML cross-reference/storage validation: passed.
- Frontend npm install/build and online dependency audit remain unverified in this environment because npm registry installation timed out; run them under Node 24.13.0 with registry access before release.
- Live Google, Apple, Firebase, and PayPal provider flows require the user's provider credentials and external accounts; they are not claimed as live-tested.

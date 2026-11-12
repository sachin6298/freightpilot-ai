> Historical project note archived during the November 2026 configuration repair. This file may describe an earlier state and is not authoritative for current setup. Use the root `README.md` and `docs/DEPLOYMENT.md` for current instructions.

# FINAL MASTER PROMPT FOR CLAUDE CODE — FREIGHT PROJECT FULL INTEGRATION

**Purpose:** finish the existing application locally by integrating the user's current redesigned React/Vite frontend with the existing FastAPI backend, fixing verified defects, testing all feasible workflows, and preparing a clean Render/Git-ready project.

**The current UI is approved and frozen. This is a functional engineering task, not a design task.** Claude must not redesign, restyle, rearrange, replace, simplify, or “improve” the existing UI. If functionality cannot be added without a visible design change, preserve the UI and report the blocker for user approval.

## Read this before starting

- The user will run this prompt against their local project folder in Claude Code, with local terminal/file permissions enabled. Complete the work locally; do not merely provide a plan.
- Use the actual working repository that contains the user's intended `.git` directory. Do not assume the extracted ZIP is the active repository, and do not overwrite an existing working tree with the ZIP.
- Read `AGENT_RULES.md` and all repository-specific instructions before editing. Follow them unless they conflict with this prompt's stricter UI lock or local-only boundary; in that case, this prompt wins.
- The user has explicitly asked to preserve the current UI. The landing page, authentication screens, dashboard, navbar, header, account dropdown, assets, typography, colors, spacing, animations, responsive behavior, and component composition must remain visually identical.
- The task includes integration of all existing supported features, not fabrication of features that the backend/provider does not support.
- Do not stop after the audit or a proposed plan. Audit, implement, test, document, and prepare the local working tree. If a blocker prevents one feature, continue with the remaining work and report the blocker precisely.

## Highest-priority rules (override any conflicting instruction)

1. **ZERO intentional visual redesign.** Existing screens must look the same before and after.
2. **No destructive Git actions.** Never run `git reset --hard`, `git clean`, `git checkout -- .`, `git restore .`, force-push, rebase, or commands that discard user work.
3. **No remote actions.** Do not push/pull/fetch, commit, deploy, create cloud resources, change remote settings, or call production provider APIs. Local Git inspection and local tests are allowed.
4. **No secrets exposure.** Never print or copy secret values. Do not place private credentials in frontend `VITE_*` variables or client bundles.
5. **No fake functionality.** No mock success, fabricated shipment/payment/analytics data, pretend provider calls, or dead buttons presented as working.
6. **No unnecessary rewrites.** Reuse the existing FastAPI services, schemas, database models, migrations, API client, and historical business logic where valid. Make the smallest safe changes.
7. **Evidence-based completion.** Report exact commands and results. Mark unavailable tests as blocked/not run; never claim they passed.

---

# Claude Code Master Task — Full Frontend/Backend Integration (STRICT UI LOCK)

> **Read this entire instruction before editing anything.** You are working on the existing local repository supplied by the user. The user has authorized local file edits, terminal commands, dependency installation, tests, and builds (including Claude Code's dangerous/full-permission mode). That permission is **not** permission to redesign the interface, expose secrets, push to Git, or deploy remotely.

## 0. Mission and priority order

Complete the existing application by connecting the user's **already-redesigned frontend** to the existing FastAPI backend, fixing verified defects, testing all feasible user journeys, and preparing the local repository for a later Git push and Render deployment of both frontend and backend.

Priority order:

1. **Preserve the current UI exactly.** This is a hard requirement and overrides any implementation preference.
2. Integrate the current frontend with the existing backend and database.
3. Make every existing visible control perform its intended action; do not leave fake-success or dead buttons.
4. Fix verified errors and add/update tests.
5. Prepare a clean, documented, Git-push-ready local working tree and Render configuration.

This is **not** a UI redesign, visual refresh, component-library migration, or backend rewrite.

---

## 1. ABSOLUTE UI FREEZE — NON-NEGOTIABLE

The user has explicitly said: **do not change the UI they have already made.** Treat the current frontend design as approved and frozen.

### 1.1 What must remain visually unchanged

Do not change, replace, simplify, restyle, rearrange, or regenerate any of the following in the existing pages:

- Landing page composition, hero section, hero video, poster image, public images, or media assets.
- Typography, font families, font weights, font sizes, line heights, text casing, or copywriting.
- Color palette, gradients, backgrounds, borders, shadows, radii, visual effects, or design tokens.
- Layout, page width, section order, component order, grid/flex structure, spacing, padding, margins, alignment, or dashboard density.
- Navbar, header, account dropdown, sidebar, active navigation appearance, dashboard cards, tables, charts, or responsive/mobile layout.
- Authentication page composition, auth artwork, social-login button appearance, form styling, or layout.
- Existing animations, transitions, hover/focus effects, icon choices, and visual behavior.
- Existing CSS class names, CSS selectors, CSS variables, Tailwind classes, inline style values, or component markup hierarchy.

Do not install a new UI kit or replace the current implementation with shadcn defaults, a dashboard template, a generic admin panel, or any historical version from Git.

### 1.2 UI files are protected

Treat these as protected design files. Do not edit their styling or layout:

- `frontend/src/App.css`
- `frontend/src/index.css`
- `frontend/src/components/Contact5.css`
- `frontend/src/components/auth/Auth7.css`
- `frontend/src/components/dashboard/freight-dashboard.css`
- Any other existing `.css`/`.scss`/style file used by the current landing, auth, navbar/header, or dashboard screens.

Treat the visual markup and component hierarchy in these as protected too:

- `frontend/src/App.tsx`
- `frontend/src/components/Contact5.tsx`
- `frontend/src/components/auth/Auth7.tsx`
- `frontend/src/components/dashboard/FreightDashboard.tsx`
- `frontend/src/components/Navbar.tsx` and `Header.tsx`, if active.

These TSX files may be edited **only to add the minimum required functional wiring**: props, API calls through separate hooks/services, event handlers, authenticated user data, route callbacks, and data values. Keep their existing JSX structure, DOM hierarchy, CSS classes, text, icons, and visible element order unchanged. Prefer adding logic in new hooks, API service modules, route controllers, and context providers rather than rewriting presentational components.

### 1.3 Allowed UI-related changes (strictly limited)

Allowed only when necessary to make an existing control work:

- Connect existing form/button callbacks to real handlers.
- Supply real authenticated user identity and API data to existing display slots.
- Add loading/disabled behavior to an existing button without changing its appearance when idle.
- Reuse an existing message/status slot for success or error feedback.
- Add route wiring while retaining the current appearance and existing navigation labels.
- Add a **new minimal functional page** only for a destination that currently has no page. Use the current typography, colors, spacing, and component patterns. Do not alter the existing Overview/dashboard layout to fit it.

Do not add large cards, new overview sections, new promotional content, new onboarding, or decorative UI. Do not add a visible component merely because it would be convenient for development.

If a feature cannot be completed without changing an approved visual element, **do not make that visual change**. Implement its backend/service logic where useful, document the blocker, and ask the user before altering the design.

### 1.4 Mandatory UI-preservation procedure

Before editing:

1. Inspect `git status --short --branch` and `git diff`.
2. Record the current versions of the protected files and create a local safety patch/copy outside the repository. Never include `.env` contents in that backup.
3. Start the frontend, if dependencies permit, and capture baseline screenshots at minimum desktop (1440×900) and mobile (390×844) for the landing, login, registration, and dashboard. Use the same test viewport after changes. Do not fabricate screenshots or claim visual comparison if browser tooling is unavailable.
4. Record the current route appearance and existing CSS classes/component hierarchy.

After implementation:

1. Capture the same pages at the same viewports if browser tooling is available.
2. Compare screenshots and inspect protected-file diffs.
3. There must be **no intentional visual differences** in existing screens. If an unintended difference appears, revert the specific visual/layout change and solve the issue in non-presentational integration code.
4. Confirm protected CSS files are unchanged. If any protected CSS modification seems unavoidable, stop and report the exact reason instead of making it without user approval.

A functional test passing does not waive the UI-freeze requirement.

---

## 2. Local-only and Git safety boundaries

The user allows dangerous/full-permission mode for **local work**. Follow these boundaries even in that mode:

- Work only in the supplied local repository. First locate the actual project root and confirm it contains the intended `.git` directory. Do not assume the current working directory is correct.
- Do not copy the ZIP over another working tree. Do not overwrite the user's current local files with the archive.
- Never run `git push`, `git pull`, `git fetch`, deploy commands, Render/GitHub/Firebase/Google/Apple/PayPal/Gemini/Resend/S3 production actions, or any remote mutation.
- Do not create cloud resources or change remote environment variables, DNS, OAuth configuration, webhook settings, or provider dashboards.
- Do not commit unless the user explicitly authorizes a commit later. Leave the user in control of review, commit, push, and deployment.
- Do not run destructive commands: `git reset --hard`, `git clean -fd`, `git checkout -- .`, `git restore .`, force operations, rebase, or commands that discard user work.
- Never overwrite or delete user changes simply to make the worktree clean.
- Do not print, paste into logs, summarize, or copy secret values. Refer to secret variable names only.
- Keep `.env`, private keys, service-account JSON, database files, local backups, virtual environments, `node_modules`, `dist`, and generated archives out of Git.

Before editing, preserve existing tracked changes and untracked files with a safety copy/patch outside the repository. Inspect whether any `.env` is tracked. If a real credential was included in the supplied archive, warn the user to rotate it; do not expose it in the terminal output or final report.

If the active folder has no `.git`, do not run `git init` and do not invent a remote. Finish local integration if safe, but report that Git push readiness cannot be confirmed from that folder.

---

## 3. Existing project context and starting audit findings

Re-check each item in the live repository before relying on it. The supplied archive was previously inspected and showed this architecture/state:

### Stack and architecture

- Frontend: React 19, TypeScript, Vite, React Router dependency, Firebase client SDK, Lucide icons, Tailwind v4 tooling.
- Backend: Python FastAPI, SQLAlchemy, Pydantic, JWT authentication, PostgreSQL for deployment, SQLite-supported local bootstrap, Alembic migrations.
- Payments: existing PayPal Sandbox-oriented backend integration.
- AI: backend Gemini/Copilot service with deterministic fallback when AI credentials are absent.
- Phone verification: Firebase Phone Authentication intended on the client, with Firebase Admin token verification on the backend.
- Deployment target: Render for backend and frontend, with PostgreSQL and Redis/Key Value as configured.
- No Supabase migration or integration is wanted. Use the existing PostgreSQL/SQLAlchemy architecture.

### Active frontend findings

The following were observed in the supplied snapshot; verify they are still true before changing code:

- `frontend/src/main.tsx` renders `App.tsx`.
- Active `App.tsx` handles only a small set of paths (`/`, `/login`, `/register`, `/dashboard`) through pathname checks. Unknown paths may fall back to the landing page.
- Login form and Google/Apple actions displayed placeholder messages rather than invoking the backend/provider authentication flow.
- `Auth7` exposes registration/provider/phone callback props, but not all were passed by the active app.
- `FreightDashboard.tsx` uses hard-coded shipment/payment/weekly-volume sample data and does not load real API data.
- Dashboard navigation exposes destinations including `/shipments`, `/marketplace`, `/quotes`, `/payments`, `/documents`, `/analytics`, and `/settings`; verify each route is implemented and refresh-safe.
- `frontend/src/api.ts` contains an existing API client, but it must be audited against actual FastAPI routes and schemas. Its presence does not mean that API integration is complete.
- Firebase initialization files exist in both JS and TS variants. Check for duplicate/stale imports. Missing optional Firebase configuration must not crash the whole app at import time; show an honest unavailable/config-required state using existing messaging patterns.
- There are current/legacy files in Git history that may contain reusable business logic, including historical PayPal checkout, shipment modal, quote comparison, and shipment detail implementations. Inspect history read-only (`git show`) and reuse logic only where suitable. **Never restore their old UI over the current redesign.**

### Backend capabilities to audit

Inspect `backend/app/main.py`, `backend/app/routes/`, `backend/app/schemas.py`, `backend/app/db/models.py`, `backend/app/services/`, and auth/authorization dependencies. Backend route groups previously found include:

- Authentication and identity/profile.
- Shipment create/list/detail/update/cancel and tracking.
- Quote generation/comparison, carrier quote refresh, and risk assessment.
- Marketplace, seller offers, and counteroffers.
- Calculator.
- PayPal order creation/capture/webhook and payments/settlements.
- Gemini-backed Copilot/AI assistance and fallback.
- Analytics.
- Notifications.
- Documents upload/download/delete.
- Seller verification.
- Admin/audit functions.

Do not assume every route is production-ready just because it exists. Validate implementation, response schemas, auth dependency, role requirements, ownership checks, and tests.

### Previous test/build audit

The earlier inspection reported:

- Backend pytest: 48 passed.
- `python -m compileall -q backend/app`: passed.
- Local SQLite bootstrap: passed.
- PostgreSQL-specific Alembic migration SQL failed when run against SQLite at migration `0002`; this is not proof of a PostgreSQL failure. PostgreSQL migrations must be validated against PostgreSQL.
- Frontend `npm ci` timed out during the earlier audit, so the frontend build was **not verified**. A failed/incomplete install must not be reported as a code build failure or as a passing build.
- CI was using Node 20 while locked Firebase packages required Node `>=24.12.0`. Confirm current lockfile engine requirements and use one compatible, tested Node 24.x LTS patch consistently.
- Existing `render.yaml` defined backend/database/Redis resources but not the frontend static site. Confirm and add the frontend static service if still absent.
- The supplied ZIP included unwanted local artifacts such as environment files, virtual environment, SQLite database files, build output, backup material, and nested archive content. Audit exact current paths; do not blindly delete a user's local backups.

---

## 4. First action: produce a factual repository map

Before implementation, inspect and record:

- Repository root, branch, remote names (read-only), and status.
- Tracked, modified, deleted, and untracked files.
- Frontend entry point, route mechanism, active components, CSS, assets, API client, auth modules, package scripts, lockfile, and TypeScript configuration.
- Backend routers, schemas, services, models, database configuration, migrations, settings, CORS, auth dependencies, tests, requirements, and startup command.
- Existing Render Blueprint and CI configuration.
- `.gitignore`, all `.env.example` files, and whether any secret-bearing files are tracked.

Then produce a short implementation checklist based on actual files. Continue into the work; do not stop after a plan.

---

## 5. Backend/API contract audit — backend is the source of truth

For every frontend workflow, map:

`screen/action → HTTP method + path → request schema → auth/role requirement → response schema → service/database effect → frontend state update`.

Use the actual FastAPI routes and Pydantic schemas as the authoritative API contract. Do not guess endpoint names or payload shapes from old TypeScript interfaces.

- Fix the existing typed API client or replace only the broken portions while preserving stable callers.
- Use a single configured API base URL. In development, support a local backend URL; in Render, use the HTTPS backend URL via a public `VITE_API_BASE_URL` build-time variable.
- Centralize bearer-token attachment, refresh/session behavior if supported, JSON parsing, multipart handling, timeout/abort behavior, and normalized API errors.
- Do not set `Content-Type: application/json` for `FormData` uploads; allow the browser to set the multipart boundary.
- Never place secrets or provider private keys in `VITE_*` variables.
- Implement protected routes and role-aware navigation without relying on client-side checks as security. Backend authorization must remain authoritative.
- Ensure logout clears client session state and cannot leave protected cached data visible.
- Ensure refresh/deep-link behavior works for every route.
- Avoid duplicate API clients, duplicate Firebase initialization, duplicate auth contexts, or competing sources of truth.

### Feature workflows to integrate

Implement only the features supported by actual backend services. Where backend support is missing or incomplete, add the smallest safe backend implementation only when it fits the existing architecture and add tests. Otherwise document the missing provider/dependency accurately.

1. **Authentication and account:** email/password registration, login, logout, current-user/session restoration, buyer/seller role, Google OAuth, Apple OAuth where backend provider support exists, and Firebase phone verification. Include validation and honest error handling.
2. **Dashboard/overview:** replace hard-coded business sample values with authenticated API data. Keep the same dashboard layout and components. Empty states should be accurate and must not invent shipments, payments, analytics, or activity.
3. **Shipments:** list, create, detail, edit/update, cancel, filter/search, shipment status, tracking timeline, and ownership protection.
4. **Quotes/risk:** quote calculation/request, carrier/quote comparison, refresh where supported, risk score and explanation. Never invent live carrier quotes.
5. **Marketplace:** browse listings/loads, seller actions, quote submission, buyer comparison, counteroffers, accept/reject/withdraw lifecycle according to backend state machine.
6. **Payments:** PayPal Sandbox order creation/approval/capture and payment history/status. Backend calculates amounts and confirms captures. Frontend must not mark payment completed on redirect or approval alone.
7. **AI/Copilot:** call backend endpoints only. Gemini credentials stay on the backend. Display deterministic fallback clearly when the Gemini key/provider is unavailable; never claim the AI provider responded if fallback content was used.
8. **Documents:** upload/list/download/delete with authenticated ownership checks, allowed file type/size validation, and safe error handling.
9. **Notifications:** retrieve/read/mark-read and provider delivery status where supported. Do not claim an email/SMS was delivered if the provider is unconfigured or delivery failed.
10. **Seller verification:** profile/KYC/document submission and status, following existing backend restrictions. Do not expose sensitive verification documents to other users.
11. **Analytics:** real backend metrics only. Empty state when no data exists; do not fill charts with fabricated sample values.
12. **Calculator:** connect to backend calculation logic and validate inputs/units.
13. **Settings/profile:** load and update current-user profile and account settings using authorized routes.
14. **Admin:** show only to ADMIN role and connect real admin routes. Enforce authorization on the backend; hiding menu items is not sufficient.

For existing buttons that have no backend capability, do not leave a fake action. Either implement a correct supported action, disable it with an honest explanation using the existing UI pattern, or document it as unavailable pending provider/configuration.

---

## 6. Authentication and provider-specific requirements

### Email/password

- Use existing backend password hashing, JWT/session behavior, schemas, rate limits, and error responses.
- Validate required fields client-side for usability and backend-side for security.
- Persist tokens/session only using the repository's existing secure pattern. Do not invent localStorage security guarantees; inspect how the backend issues/refreshes tokens and document the chosen approach.
- Load current-user identity and role after login and on refresh.

### Google and Apple

- Reuse existing backend OAuth verification. Verify issuer, audience, signature, expiry, nonce/state, and provider-specific claims as applicable.
- Do not accept arbitrary client-submitted email/profile data as proof of identity.
- If OAuth configuration is absent, keep the existing buttons' visual appearance but return an honest configuration-required state; do not display a success state.
- Do not invent client IDs, redirect URLs, private keys, or provider settings.

### Firebase phone OTP

- Reuse Firebase Client SDK Phone Auth, then send the Firebase ID token to the backend's existing Firebase verification/link endpoint.
- Verify the backend validates the Firebase project/audience, token signature/expiry, and phone claim.
- A backend route that is a no-op for `SMS_PROVIDER=firebase` must not be presented as if it sent a text message.
- Handle reCAPTCHA/confirmation flow and provider errors correctly.
- Optional Firebase configuration must not crash the landing page or email/password auth at module import time.

---

## 7. PayPal Sandbox requirements

- Keep `PAYPAL_ENV=sandbox` for this task. Do not enable Live mode.
- Reuse the existing backend order/capture service and webhook verification.
- Amount, currency, shipment/order association, and final status must be checked server-side.
- Verify capture against PayPal Sandbox before displaying a completed payment.
- Handle cancellation, approval failure, capture failure, duplicate callbacks, webhook idempotency, and pending states.
- Never trust browser redirect parameters, client-side state, a mock response, or a user-editable amount.
- Keep `PAYPAL_CLIENT_SECRET` and webhook secrets on the backend only. A Sandbox client ID may be public if required by the SDK.
- Without provider credentials, finish code and tests that do not require external access and label real provider execution `CREDENTIALS_REQUIRED`.

---

## 8. Gemini / AI requirements

- Frontend calls the existing FastAPI Copilot endpoint only.
- Gemini API key and provider configuration remain server-side.
- Preserve the current deterministic fallback. Clearly distinguish provider-generated results from fallback results in API metadata and UI status if supported.
- Add robust timeouts, safe errors, request validation, and rate/usage limits as appropriate.
- Do not hardcode AI outputs, pretend a provider call succeeded, or expose the key in logs/client bundles.

---

## 9. Database, security, and backend quality

- Preserve PostgreSQL/SQLAlchemy/Alembic as the deployed architecture; SQLite may remain for local tests/bootstrap where already supported.
- Do not add Supabase or migrate to Firebase database services.
- Preserve existing role separation (`BUYER`, `SELLER`, `ADMIN`), JWT security, password hashing, audit logging, CORS allowlist, rate limiting, ownership helpers, and validation.
- Audit IDOR on shipments, quotes, payments, documents, verification records, and admin resources.
- Audit mass assignment, unsafe serialization, upload/download authorization, path traversal, file type/size validation, content type, and storage path isolation.
- Audit payment state transitions, amount/currency consistency, idempotency, webhook signature verification, and duplicate captures.
- Audit OAuth and Firebase token verification.
- Do not weaken production configuration to make local tests pass.
- Add or update tests for each meaningful change.
- Do not run production migrations. Validate migrations only against a fresh disposable PostgreSQL database.
- If local Docker/PostgreSQL is unavailable, do not claim the Alembic PostgreSQL chain passed. Use CI configuration if possible and report the unresolved local validation clearly.

---

## 10. Build, Node, CI, and dependency handling

1. Inspect the actual lockfile and engines declared by all packages.
2. Choose a compatible Node 24.x patch version satisfying every locked package requirement (the earlier audit found Firebase packages requiring at least 24.12.0). Pin one tested version consistently in `.node-version`, `frontend/package.json` engines, GitHub Actions, and Render setup where applicable.
3. Do not blindly upgrade packages or regenerate the lockfile. Change dependencies only when required to fix a verified incompatibility; document why.
4. Run a clean frontend install with `npm ci`, then `npm run build`. If install times out due to network, record it as an infrastructure/install blocker, retry only when reasonable, and do not report it as a source-code failure or a successful build.
5. Fix TypeScript, unused import, missing module, asset path, Vite, and type errors without weakening `tsconfig` or adding broad `any` types.
6. Update GitHub Actions to use the same tested Node version and retain backend tests. Add PostgreSQL service/migration validation if it is missing and can be configured safely.
7. Do not update a package solely because a newer version exists.

---

## 11. Render deployment readiness — frontend AND backend

Inspect the current `render.yaml` and current Render Blueprint schema before editing. Do not deploy or change remote resources.

### Backend Web Service

Keep the existing backend service if correctly defined. Verify:

- Root directory: `backend` (or current correct root).
- Build command installs `requirements.txt`.
- Start command uses `uvicorn app.main:app --host 0.0.0.0 --port $PORT` or the repository's verified equivalent.
- Health check points to the actual health endpoint (previously `/health`; verify).
- PostgreSQL and Redis/Key Value references are valid and do not accidentally create duplicates.
- Production settings require strong secrets, HTTPS origins, auth, and disabled demo mode.
- Pre-deploy migration command is included only if supported by the selected Render service/plan and correct for the actual build environment. Never run it remotely.

### Frontend Static Site

If missing, add a Render static-site service:

- Root directory: `frontend`.
- Build command: `npm ci && npm run build`.
- Publish directory: `dist`.
- SPA rewrite: all app paths must serve `/index.html` using supported Render rewrite syntax.
- Configure `VITE_API_BASE_URL` as a public build-time variable pointing to the deployed backend HTTPS origin.
- Only public Firebase configuration, public OAuth client IDs, and PayPal Sandbox client ID may be placed in public frontend variables if genuinely required.
- Never add private keys, API secrets, service-account JSON, PayPal secret, Gemini key, email key, database credentials, or storage secrets to frontend environment variables.

### CORS and provider configuration

Document exact names and where each belongs. Verify the backend reads these names before documenting them. Expected categories may include:

- `APP_ENV`, `DEMO_MODE`, `AUTO_CREATE_DB`, `AUTH_REQUIRED`.
- `DATABASE_URL`, strong `JWT_SECRET_KEY`, `REDIS_URL`.
- `FRONTEND_ORIGIN`, `CORS_ALLOWED_ORIGINS`, `API_PUBLIC_URL`.
- `PAYPAL_ENV=sandbox`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, webhook ID if used.
- Google OAuth and Apple Sign-In values only if implemented.
- Gemini `AI_API_KEY` and model name.
- Resend/email provider credentials and verified sender only if supported.
- Firebase public client configuration and backend Firebase Admin credentials.
- Object-storage and malware-scan settings only if implemented and required.
- Frontend `VITE_API_BASE_URL` and required public provider identifiers.

Do not assume every variable is required. Confirm against config classes and validators. Provide placeholder names, never real credentials. Explain that Render Static Site `VITE_*` changes require a frontend rebuild/redeploy.

---

## 12. Git hygiene and source archive readiness

- Inspect `.gitignore` at root and in subprojects. Ensure secrets and generated files are ignored.
- Preserve safe `.env.example` files with placeholder values only.
- Ensure `.env`, `.env.*` (except explicitly safe examples), `*.local`, service-account credentials, private keys, DB files, venvs, `.venv`, `node_modules`, `dist`, `build`, caches, logs, TypeScript build info, backup directories, and generated ZIPs are not staged.
- Inspect `git ls-files` for any already-tracked secret/artifact. If found, do not just delete blindly: remove it from version control safely in the local working copy and report any credential rotation required.
- Do not remove local backup directories without explicit permission; exclude them from Git/release output.
- Run `git diff --check` and inspect the complete final `git status` and diff summary.
- Prepare commands for the user to commit/push later, but do not execute them.
- Generate a clean source ZIP only if safe and useful. Exclude `.git`, `.env*` real values, DBs, venvs, caches, `node_modules`, `dist`, nested ZIPs, local backups, and generated artifacts. Include source, assets, lockfiles, migrations, tests, and docs.

---

## 13. Required documentation updates

Update root/backend/frontend README files so they accurately describe:

- Local startup of backend and frontend.
- Environment setup using `.env.example` files.
- API base URL and authentication flow.
- Buyer/seller/admin roles.
- Shipment, quote, marketplace, payments, documents, analytics, notifications, and AI functionality.
- Firebase phone authentication, Google/Apple OAuth requirements, PayPal Sandbox, Gemini fallback.
- Test commands and migration validation.
- Render deployment for both services.

Create or repair referenced docs such as:

- `docs/DEPLOYMENT.md`
- `docs/SECURITY.md`
- `docs/PROVIDER_CREDENTIALS.md`

Ensure all README links point to real files. Correct stale delivery/status documents so they do not claim incomplete features are complete.

---

## 14. Verification — execute, do not merely describe

### Backend

From `backend`:

```bash
python -m compileall -q app
pytest -q
```

Validate the Alembic chain against a **fresh disposable PostgreSQL database**. Do not test PostgreSQL-specific migrations against SQLite and then claim PostgreSQL success. Never point migration tests at the user's real database.

### Frontend

From `frontend`, using the selected pinned Node version:

```bash
npm ci
npm run build
```

### Repository/deployment

From repository root:

```bash
git diff --check
git status --short --branch
git diff --stat
```

Also:

- Validate YAML syntax in `render.yaml` and CI workflow.
- Validate Render Blueprint fields and frontend rewrite.
- Verify every visible navigation destination resolves and supports direct refresh.
- Verify every frontend API request uses the configured backend base URL.
- Search production frontend bundles for secret-like values and ensure private credentials are not present.
- Verify no secret files or local artifacts are staged.
- Confirm no protected UI CSS changed and compare screenshots if browser automation is available.

### Minimum user journey tests

Test as far as local setup and credentials permit:

- Landing page and existing navigation.
- Login, registration, logout, session restoration, protected route, and refresh.
- Buyer and seller role separation.
- Shipment create/list/detail/edit/cancel/tracking.
- Quote calculation/comparison/risk result.
- Marketplace offer and counteroffer lifecycle.
- PayPal Sandbox order/approval/capture/payment history.
- Gemini-backed Copilot and deterministic fallback without AI credentials.
- Notifications.
- Document upload/list/download/delete and access isolation.
- Seller verification.
- Admin-only functions.
- Analytics, calculator, and profile/settings.
- Deep-link refresh on every implemented app route.

If external credentials or a provider account are unavailable, mark the specific test `NOT RUN — CREDENTIALS REQUIRED`. Do not simulate a successful provider call.

---

## 15. Definition of done

The work is complete only when all of the following have been addressed and honestly reported:

- Existing landing, auth, navbar/header, account dropdown, and dashboard design are visually unchanged.
- No protected CSS/design token/layout file has been changed without user approval.
- Existing auth screens are wired to real authentication flows where configuration exists.
- Dashboard figures come from authenticated backend data; no fake sample data is presented as real.
- Every existing navigation item works or has an accurately documented unavailable state.
- Supported shipment, quote, marketplace, payment, AI, document, notification, analytics, settings, and admin workflows are connected.
- All authorization and ownership rules are enforced by the backend.
- PayPal Sandbox payment state is verified server-side.
- Gemini requests go through the backend and fallback behavior is truthful.
- Firebase phone OTP is genuinely sent/confirmed through the client SDK; no no-op backend path is reported as delivery.
- Backend tests and frontend install/build are run and results are recorded.
- PostgreSQL migration success is claimed only if tested against PostgreSQL.
- Render Blueprint defines both backend and frontend with correct environment wiring and SPA routing.
- Documentation and `.gitignore` are correct.
- Local Git tree is reviewed and ready for the user to inspect. **No commit, push, or deployment has occurred.**

If one item cannot be completed due to missing credentials, provider configuration, network failure, unavailable browser, or unsupported Render plan feature, complete all other local work and state the exact limitation and next manual action. Do not stop early with just a plan.

---

## 16. Final report format

At the end, give the user a concise but complete report with:

1. **UI preservation:** confirm which protected files remained unchanged; list any unavoidable functional TSX modifications separately. State whether screenshot comparison was performed.
2. **Completed integrations:** list each feature that is truly connected and tested.
3. **Files changed:** path and reason, grouped by frontend/backend/deployment/docs.
4. **Verification:** exact commands and actual pass/fail results. Separate code failures from network/credential/environment blockers.
5. **Known remaining issues:** root cause and exact next step for each.
6. **Manual credentials/configuration:** variable names and the service where each must be entered. Never show secret values.
7. **Local startup commands:** exact PowerShell commands for backend and frontend based on the final repository structure.
8. **Git readiness:** branch, status, confirmation that no secrets or generated artifacts are staged, and proposed `git add`, `git commit`, and `git push` commands for the user to execute later.
9. **Render deployment steps:** service names, root directories, build/start commands, environment variables, health check, CORS, and SPA rewrite.

### Final absolute instruction

**Do not change the user's existing UI. Do not redesign it. Do not replace it. Do not “improve” it. Do not restore the old UI.** Connect the current interface to the backend with the smallest possible functional code changes. If you believe a visual change is necessary, stop before making it and explain why approval is needed.


---

# FINAL EXECUTION ADDENDUM — APPLY THESE RULES THROUGHOUT THE TASK

## A. Explicit UI freeze enforcement

Before changing code, create a protected-file manifest and capture the current state of the active UI. At minimum, identify the actual files used by the live app for:

- landing page and hero/video assets;
- login, registration, and phone/social-auth presentation;
- dashboard overview and dashboard styling;
- navbar, header, account dropdown, sidebar, and navigation;
- global styles, fonts, icons, theme variables, responsive breakpoints, and animations.

Do not assume the filenames in this prompt are exhaustive. Discover the actual active import graph from `frontend/src/main.tsx`.

**Hard rule:** do not edit CSS, SCSS, Tailwind theme/configuration, design tokens, global styles, asset files, font files, or visual markup/layout to make integration easier. Do not run formatters over protected UI files if they may rewrite markup or classes. Do not replace the current dashboard with a historical dashboard or a downloaded template.

Functional-only edits to an existing TSX component are allowed only when required to attach an event handler, receive real data, show an existing status message, or call an existing callback. Preserve its JSX element order, nesting, class names, visible text, icons, dimensions, and idle appearance. Prefer new hooks, contexts, API adapters, route guards, and service modules over editing presentational components.

If a new route is required, reuse an existing visual shell and current design tokens/components. Do not modify the overview dashboard to accommodate it. Do not add a new dashboard card or section unless it already exists in the approved design.

At the end, report a list of every protected file and whether it changed. A protected file change must have a specific functional reason and must not create a visual difference. If you cannot demonstrate that, revert only your own change safely; never revert pre-existing user edits.

## B. Preserve user work before making changes

1. Run `git status --short --branch`, `git diff --stat`, and inspect staged/unstaged diffs.
2. Identify changes that existed before your work. Record them separately.
3. Make a local safety copy/patch of the starting state outside the repository, excluding all secrets and environment-file contents.
4. Do not stage, commit, stash, reset, or overwrite the user's pre-existing changes.
5. Keep a clear change log of files changed by you.

If multiple project folders exist, compare their `.git` roots and status. Ask no unnecessary questions: choose the repository matching the supplied project and latest active UI, but if two candidates are ambiguous or contain materially different uncommitted work, stop before editing and report the paths and differences.

## C. Feature acceptance criteria

For each workflow, record the exact backend endpoint, HTTP method, schema, auth/role requirement, response, and frontend component using it. Verify the end-to-end behavior rather than merely confirming an API function exists.

- Authentication: registration, login, session restore, logout, role assignment, protected route, and error handling.
- Buyer/seller: correct role-specific actions and backend-enforced authorization.
- Dashboard: real data from the authenticated account; accurate zero-data state; no sample data represented as live.
- Shipments: create, list, detail, edit, cancel, status/tracking, and ownership isolation.
- Quotes: quote calculation/request, comparison, refresh only if supported, risk output, and validation.
- Marketplace: listing discovery, seller actions, offers, counteroffers, and accepted/rejected/withdrawn state transitions.
- PayPal: sandbox order, approval, server-side capture verification, history, failure/cancel/pending state, and idempotency. Never enable Live mode.
- Gemini: frontend calls FastAPI only; API key stays server-side; distinguish Gemini response from deterministic fallback.
- Documents: upload, list, download, delete, allowed file/size checks, and per-user access isolation.
- Notifications: list/read/mark-read and actual provider delivery state only where supported.
- Seller verification: submission/status and strict privacy for verification documents.
- Analytics: server-derived metrics only; never fabricate chart values.
- Calculator: real calculation logic and input/unit validation.
- Settings/profile: authenticated read/update.
- Admin: ADMIN-only route and backend authorization; UI hiding alone is not security.

A feature is “implemented” only if its UI action is wired, request/response contract matches the backend, state updates correctly, errors are handled, and meaningful tests exist. If provider credentials are absent, finish safe code paths and tests that do not need credentials, then mark live-provider verification `NOT RUN — CREDENTIALS REQUIRED`.

## D. Provider and integration boundaries

- Keep PostgreSQL/SQLAlchemy/Alembic as the production data architecture. Do not add Supabase.
- Keep PayPal in Sandbox. Do not make a Live-mode change or test real charges.
- Gemini credentials, PayPal secrets, JWT secrets, Firebase Admin credentials, email credentials, database credentials, and storage secrets must remain backend-only.
- Google/Apple OAuth must use actual server-side token verification and validated issuer/audience/state/nonce as appropriate. If provider setup is absent, preserve the current button and show an honest configuration-required state using an existing feedback mechanism.
- Firebase phone OTP must use the actual client SDK confirmation flow and backend ID-token verification. Do not describe a no-op SMS route as a delivered OTP.
- Email/SMS must not be reported as sent/delivered unless a configured provider confirms the result.
- Do not invent API routes, provider credentials, redirect URLs, webhook IDs, or production configuration. Derive them from code and document missing items.

## E. Deployment and environment correctness

Inspect actual settings and startup code before writing deployment instructions. Validate the Render Blueprint against current supported syntax and ensure it defines both the FastAPI backend and frontend static site, if both are intended to deploy on Render. Ensure the frontend's `VITE_API_BASE_URL` points to the backend public HTTPS origin and backend CORS includes the exact frontend origin. Confirm SPA fallback for every client-side route.

Check the actual Node engine constraints in `package-lock.json` and package metadata. The prior archive audit found Firebase dependencies requiring Node `>=24.12.0` while CI used Node 20; verify current constraints and choose a compatible tested Node 24.x release consistently. Do not blindly change dependency versions or regenerate the lockfile.

PostgreSQL-specific Alembic migrations must be validated against a disposable PostgreSQL database, not SQLite. Never run migrations against production or a user database. If PostgreSQL is unavailable locally, report that limitation and do not claim migration validation passed.

## F. Security and data integrity gates

Audit authentication and authorization server-side, including IDOR/ownership checks for shipments, quotes, payments, documents, seller verification, and admin resources. Check mass assignment, input validation, file upload limits/type validation, path traversal, safe download headers, secrets in logs, CORS, rate limiting, OAuth/Firebase token verification, payment amount/currency verification, webhook signature verification, duplicate webhook handling, and legal state transitions.

Do not weaken auth, validation, TLS/CORS, production settings, or tests merely to make a workflow pass. Add regression tests for each security fix. Do not use real customer data or production credentials in test fixtures.

## G. Required final handoff

The final response must include:

1. A clear statement that the UI was preserved, with a protected-file change report and screenshot comparison status.
2. Completed feature integrations and the evidence/tests for each.
3. Features still blocked by missing credentials/provider setup, with exact environment-variable NAMES (never values) and the manual setup action.
4. Backend test results, frontend install/build results, lint/typecheck results if scripts exist, and PostgreSQL migration validation status.
5. Deployment configuration changes for Render frontend and backend, including service root directories, build/start commands, health check, SPA rewrite, API URL, and CORS origin.
6. Security findings and fixes, plus any remaining high-risk issues.
7. Exact local PowerShell commands to start backend and frontend using the actual final project structure.
8. Git status, diff summary, confirmation that no commit/push/deploy occurred, and proposed commands for the user to review and execute later.
9. The exact path to the final clean source archive if one is created and verified. Do not include `.env`, local DBs, virtual environments, `node_modules`, build output, caches, backups, or nested archives.

**Do not mark the project “production ready” merely because builds pass.** Use one of these precise statuses: `READY FOR USER REVIEW`, `READY FOR SANDBOX TESTING`, `DEPLOYMENT CONFIGURED — MANUAL CREDENTIALS REQUIRED`, or `BLOCKED`, and explain why.

## Final instruction

The user is satisfied with the current visual design. Your job is to make that exact interface work with the existing application. The correct outcome is the same UI, backed by real data and working functionality—not a different or “better-looking” UI.

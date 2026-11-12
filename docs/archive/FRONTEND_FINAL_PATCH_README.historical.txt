> Historical project note archived during the November 2026 configuration repair. This file may describe an earlier state and is not authoritative for current setup. Use the root `README.md` and `docs/DEPLOYMENT.md` for current instructions.

FreightPilot frontend UI fixes

Files changed:
- src/App.tsx
  * Real Google SVG, Apple SVG and smartphone SVG in provider buttons.
  * Top-right Register action is labelled Create account and opens the existing register mode.
  * Modal uses accessible dialog semantics and only closes on backdrop clicks.
- src/components/workspace/freightpilot-refinement.css
  * Keeps public landing navigation visible with top-right Workspace / Sign in / Create account / theme actions.
  * Rebuilds auth dialog sizing and responsive breakpoint to avoid image slivers and form clipping.
  * Fixes input icon vs placeholder collisions, line-height and spacing.
  * Light teal palette; no orange/coral interaction colors.

Existing App.tsx API and OAuth handlers are retained. Auth7.tsx is not mounted by App.tsx; the live auth flow is AuthModal in App.tsx, so it was intentionally not substituted with the standalone sample that contains placeholder handlers.

Apply by extracting this package over frontend/, then run npm run build on Windows and npm run dev.

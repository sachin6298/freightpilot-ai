FRONTEND UI RESTORATION — 10 NOVEMBER

WHAT THIS PATCH DOES
1. Keeps the existing full App.tsx application and its freight operations handlers.
2. Uses the supplied yacht-motion.mp4 as a full-bleed, muted, looping landing-page hero video.
3. Uses the supplied cargo-ship photo on the RIGHT side of sign-in and registration.
4. Keeps the overall application in a light theme for now.
5. Preserves existing authentication, shipments, quotes, payments, PayPal checkout, tracking, and Gemini-backed Copilot API calls.
6. Locks the theme to light temporarily; dark mode can be re-enabled after visual approval.

FILES THAT WERE UPDATED
- src/components/workspace/freightpilot-refinement.css (hero, auth, light visual system)
- src/components/workspace/ThemeProvider.tsx (light theme lock)
- index.html (Google Identity script id used by the existing OAuth initializer)
- public/images/freightpilot-auth-ship.png (exact supplied cargo ship photograph)
- public/videos/yacht-motion.mp4 (exact supplied yacht footage)

The package also includes the complete existing frontend source tree and assets so imports remain resolvable. The main App.tsx and index.css are included unchanged because the active app already contains the API-backed page logic and landing/auth structure; the visual adjustments are applied via the workspace refinement stylesheet and supplied assets.

SAFE APPLICATION
- Extract this ZIP OVER the existing frontend folder. Do not delete the folder first.
- No backend files are included.
- No .env, .env.local, .env.production, node_modules, or dist folders are included. Existing local environment files and dependencies remain untouched when extracting over the folder.

VALIDATION
- TypeScript project check (tsc -b): passed.
- CSS syntax parsing: passed.
- Vite bundle step could not be run in the Linux validation container because its node_modules came from a Windows installation and the Rolldown native binding is platform-specific. Run npm run build on Windows with the Windows node_modules already installed.

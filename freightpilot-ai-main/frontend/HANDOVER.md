# Frontend handover

This is the complete replacement `frontend/` source folder.

- `node_modules/`, `dist/`, and local `.env*` secrets are intentionally excluded.
- Run `npm ci`, `npm run build`, then `npm run dev` from this folder.
- Copy your existing local `.env` / `.env.local` into the new folder after replacement. Do not paste private provider secrets into `VITE_*` variables.
- The public Client IDs for Google/Apple/PayPal can be supplied as documented in `.env.example`; provider secrets and the Gemini API key must stay on the backend.
- The Tallie dashboard ZIP is used as a visual/layout reference. The demo's unrelated Three-Way Match data and fake transaction feed are not copied. The workspace shell and operational dashboard are adapted to actual freight API records.
- The supplied `yacht-motion.mp4` is included as uploaded; it depicts a yacht, not a container ship.

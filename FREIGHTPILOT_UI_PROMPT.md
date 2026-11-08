# FreightPilot AI — Frontend Visual Overhaul (Token-Efficient)

**Scope:** `frontend/` only. Backend is READ-ONLY. No new features, no new dependencies, no project regeneration. Keep every API call, auth flow, PayPal flow and route working.

## 0. Token-saving rules (follow strictly)

- `src/App.tsx` (~960 lines, 93 KB) and `src/index.css` (~1,200 lines, 88 KB) are large. **Never `cat` them whole.** Use `grep -n` to locate, then `sed -n 'A,Bp'` to read only the needed range.
- Edit with targeted replacements. Do not rewrite App.tsx or index.css.
- Put new work in **new small files**: `src/components/HeroScene.tsx`, `src/components/Breadcrumbs.tsx`, `src/ui.css` (imported in `main.tsx` after `index.css`, overrides via same-specificity-later). Keep each under ~250 lines.
- No UI libraries, no animation libraries, no images generated. Use SVG + CSS keyframes (+ one small `<canvas>` or SVG-path animation for waves).
- Plan in ≤10 lines, then implement. Do not narrate. Do not re-read files you already edited.
- Build and screenshot **once per phase**, not after every edit. Final report ≤15 lines.

## 1. Fixed design tokens (ONLY these 3 base colours)

| Token | Hex | Use |
|---|---|---|
| `--navy` | `#14213D` | Backgrounds, surfaces (deepen with `color-mix` toward black, never a new hue) |
| `--cream` | `#F4EDE0` | Text, light cards, highlights |
| `--coral` | `#FF6B5B` | CTAs, active states, accents, key data series |

- Derive all shades with opacity or `color-mix()` from these three. **No other hues** (remove the existing blue/cyan/purple/green/amber accents).
- Status badges: distinguish by **label + icon + coral intensity** (e.g. High = solid coral, Medium = coral outline, Low = cream outline), not new colours.
- Dark-navy canvas, cream text, coral accent. Liquid-glass = `rgba(244,237,224,.06–.10)` fill, `backdrop-filter: blur(18px) saturate(140%)`, 1px `rgba(244,237,224,.14)` border, soft inner top highlight.
- Font: one clean sans (Inter, already usable via system stack fallback). Scale: 12/14/16/20/28/56. Headlines weight 700, tight tracking.

## 2. Landing page (`Page = 'landing'`) — highest priority

Layout: 2-column hero, `min-height: 100svh`, headline + CTAs left, maritime scene right (bleeds to the edge, behind a navy→transparent gradient on its left side). Ship fully visible above the fold on 1366×768 and 1920×1080; on mobile it stacks, scene below text at ≥40svh.

`HeroScene.tsx` — pure SVG/CSS, no static photo:

1. **Sky:** navy-to-deep-navy gradient + coral/cream sunset glow near the horizon, slow drifting cloud shapes (CSS `translateX` loop, 60–90 s).
2. **Ship (large, ~60% of scene width):** inline SVG hull (navy, coral waterline stripe), cream bridge with lit windows, stacked containers in coral/cream/navy tones, mast light that gently pulses. Animate: slow bob (`translateY ±6px`), pitch (`rotate ±1.2deg`, `transform-origin` at hull center), 5–7 s ease-in-out infinite; a slight forward drift.
3. **Waves (must genuinely move):** 3–4 layered SVG wave paths, each in a `200%`-wide strip translating horizontally in a seamless loop at different speeds (parallax, front layer fastest, 8–20 s). Front layer overlaps the hull bottom so the ship sits *in* the water. Add a bow-wake foam shape that pulses, and a coral/cream shimmering reflection strip under the ship (opacity animation).
4. Optional: 20–30 tiny CSS stars/spray particles. Skip if it hurts performance.
5. Animate only `transform`/`opacity` (GPU-friendly). Add `will-change: transform` on moving layers. Respect the existing `prefers-reduced-motion` block (stop motion, keep static scene).

Rest of landing: sticky glass navbar (logo, links, Sign In ghost, Get Started coral); headline "Navigate Freight. *Move Smarter.*" (second line coral); 4 glass feature cards (AI Copilot, Risk Management, Secure Payments, Real-time Tracking) with hover lift; stats row (10K+, 500+, 99.9%, 150+ — keep existing labelling rules: mark as demo if the project rules require it). Remove dead space between sections. Reuse the existing `AuthModal` (restyle only) — sign-in card = centered glass panel with Google / Apple / Phone buttons and email/password.

## 3. App shell + dashboard (all pages share it)

- **Sidebar:** 240 px glass, logo top, grouped nav with line icons (reuse existing `Icon`), active item = coral left bar + coral-tint fill + cream text; hover = cream 6% fill + 2px slide; collapsible with width transition; user card at bottom.
- **Top bar:** glass, search field, notification bell with coral dot, avatar dropdown (animated: fade + scale-from-origin 160 ms).
- **Page header:** title + subtitle left, primary action right, `Breadcrumbs` above (Home › Section › Item) using the existing hash navigation (`navigate`/`pushState` near `App.tsx` lines ~366–380). Add a working **Back** button on detail views/modals that returns to the previous page via `history.back()` with a fallback to `overview`.
- **KPI cards (4):** icon chip, big number, delta chip in coral/cream, hover lift + soft coral glow border; subtle count-up on mount (≤600 ms).
- **Charts:** hand-built SVG (area chart with coral line + gradient fill, donut for mode split, bar chart for spend). Gridlines cream 8%. Tooltips on hover. No chart libs.
- **Tables:** sticky header, 48 px rows, zebra via cream 3%, row hover highlight, status badges per §1, compact mono IDs, right-aligned numbers.
- **AI Copilot page:** chat bubbles (user = coral tint, AI = glass), pinned input with send button, answer card for route recommendations.
- **Risk page:** gauge (SVG arc, coral), breakdown legend, alerts table.
- Spacing: 8-pt grid, 24 px page padding, 16–20 px card gaps, 16–20 px card radius. Remove empty/placeholder blocks; every card must carry real data or an `EmptyState`.

## 4. Interactions (implement all)

- Buttons: hover lift 1–2 px + brightness, active press scale .98, visible `:focus-visible` coral ring. Primary = coral, secondary = glass.
- Cards: hover `translateY(-3px)` + border brighten, 180 ms ease.
- Sidebar active indicator slides/fades; page transition = 200 ms fade+8px rise keyed on `page` state.
- Modals (`NewShipmentModal`, `QuoteDetailModal`, `AuthModal`): backdrop blur fade-in + panel scale .96→1; Esc and backdrop click close; close animation before unmount.
- Dropdowns: same animation as above, click-outside closes.
- Keep transitions 150–250 ms; use one shared easing `cubic-bezier(.2,.8,.2,1)`.

## 5. Consistency pass

Apply §1 tokens to **every** page: overview, shipments, quotes, risk, copilot, payments, analytics, settings, all modals. Delete orphaned/duplicated CSS for removed colours only where you touched it (do not mass-refactor). Same header, card, table, button, badge styles everywhere.

## 6. Verification (do it, report real output)

Run once per phase; keep output short (`| tail -20`).

```bash
cd frontend && npm install && npm run build 2>&1 | tail -20   # must pass: tsc + vite build
npm run dev -- --port 5173 &                                    # then:
npx playwright install chromium >/dev/null 2>&1
```

Playwright script (single file, throwaway, delete after) must:

1. Open `/` at 1440×900 → screenshot `landing.png`. Assert the ship SVG element's bounding box lies fully inside the viewport (no scroll).
2. **Prove motion:** read the ship's `getBoundingClientRect().y` and a wave layer's `transform` at t=0 and t=1.5 s; they must differ.
3. Open `/#overview`, `#shipments`, `#quotes`, `#risk`, `#copilot`, `#payments`, `#analytics`, `#settings` → screenshot each at 1440×900 (view only 2–3 images yourself: landing, overview, one more).
4. Click sidebar items; confirm active indicator changes, breadcrumb text updates, Back returns to previous page.
5. Open and close one modal and one dropdown.
6. Check mobile 390×844 landing once.
7. Confirm no console errors and that the backend directory has no diff: `git status --short -- ../backend` (or compare to the original) is empty.

Fix whatever fails, rebuild once, then stop.

## 7. Definition of done

- Cargo ship visible above the fold, bobbing; waves visibly scrolling at several speeds.
- Only navy / cream / coral (+ opacity tints) appear in the UI.
- Dashboard and all pages look like one commercial SaaS product (glass sidebar, topbar, KPIs, charts, tables).
- Breadcrumbs, Back, hover/active states, modal/dropdown animations work.
- `npm run build` passes. No backend, `.env`, or dependency changes.
- Final message: files changed, commands run with pass/fail, what the screenshots confirmed. No claims that weren't tested.

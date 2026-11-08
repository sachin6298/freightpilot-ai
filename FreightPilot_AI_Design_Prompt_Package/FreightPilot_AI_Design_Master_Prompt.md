# FreightPilot AI — Final UI/UX Redesign Master Prompt

> **How to use:** Open the FreightPilot AI project in Claude Code. Keep this Markdown file and the entire `design-references` folder together. Paste the complete prompt from the section **MASTER PROMPT FOR CLAUDE CODE** into Claude Code. The relative image links below are included so the design references remain visible in Markdown viewers that support local images.

## 1. Visual references

### A. Consolidated visual-direction board supplied by the user

This board shows the intended combination of a cinematic cargo-ship landing page, a dark glass-style workspace, liquid-glass surfaces, and refined editorial colour/typography. Study this board first and use it as a high-level visual target. The individual reference images below provide more focused detail.

![User-supplied visual direction overview](design-references/visual-direction-overview.png)

These are the actual reference images to follow. Use them as visual guidance, not as assets to copy blindly. The ocean/yacht reference establishes the public landing-page direction; the palette reference establishes the brand colours; the UI-styles reference identifies relevant design languages. The current-interface screenshot is an **anti-reference**: fix its problems rather than reproducing them.

### A. Ocean, yacht and cinematic maritime landing-page direction

![Ocean and yacht website reference](design-references/ocean-yacht-website-reference.png)

### B. Brand palette reference — navy, cream and coral

![Navy cream coral palette reference](design-references/navy-cream-coral-palette-reference.png)

### C. UI-style reference — liquid glass, bento grid and related visual languages

![UI styles reference](design-references/ui-styles-liquid-glass-bento-reference.png)

### D. Current FreightPilot AI screen — problems to correct, not imitate

![Current FreightPilot UI before redesign](design-references/current-freightpilot-ui-before-redesign.png)

### E. Contact sheet of additional screenshots supplied during the work

![Additional reference uploads contact sheet](design-references/reference-uploads-contact-sheet.png)

### F. Supplementary UI reference document

[Open supplementary UI reference PDF](design-references/supplementary-ui-reference.pdf)

Use this PDF only as supplementary inspiration where relevant. The FreightPilot-specific references and requirements in this document take priority.

---

# MASTER PROMPT FOR CLAUDE CODE

Act as a principal product designer, senior React/TypeScript architect and frontend engineer. Redesign the existing **FreightPilot AI** product into a premium, polished, enterprise-grade maritime logistics and freight procurement SaaS platform.

This is a complete visual and frontend-architecture refinement. Do not merely recolour the existing UI, add decorative cards, or generate another generic SaaS dashboard.

## 0. Mandatory reference-first workflow

Before editing anything:

1. Inspect the existing project structure, route/page architecture, components, styles, assets, API clients and current environment-variable usage.
2. Open and study every image in `design-references/`.
3. Treat `ocean-yacht-website-reference.png` as the primary public landing-page visual reference.
4. Treat `navy-cream-coral-palette-reference.png` as the primary brand-colour reference.
5. Treat `ui-styles-liquid-glass-bento-reference.png` as a reference for design-language choices. Use liquid glass and bento layouts selectively and coherently.
6. Inspect `current-freightpilot-ui-before-redesign.png` to identify what must be corrected. Do not reproduce its broken composition.
7. Map each reference to the appropriate FreightPilot page before implementation.

Do not claim visual matching unless you have actually inspected the files and compared the rendered pages with them. If any reference cannot be opened, report that limitation and continue with the available references.

## 1. Design objective

Create one coherent visual identity combining:

- A cinematic ocean-and-cargo-ship public landing page.
- Minimalist bento-grid composition.
- Premium liquid-glass surfaces and restrained glassmorphism.
- Strong typography, deliberate spacing and editorial hierarchy.
- A practical, data-dense enterprise workspace that remains readable and efficient.

The result must feel like a carefully art-directed maritime intelligence product—not a template, toy UI, gaming dashboard or collection of unrelated screens.

## 2. Brand palette — use these exact core colours

The supplied palette reference is authoritative. Start with:

| Token | Hex | Intended use |
|---|---|---|
| Deep Navy | `#14213D` | Main brand background, navigation and dark hero surfaces |
| Warm Cream | `#F4EDE0` | Main light surfaces and warm contrast |
| Coral | `#FF6B5B` | Primary actions, active highlights and key emphasis |

Build a restrained supporting palette around those colours:

- Darker navy for depth: `#0B1427`.
- Navy surface: `#1B2C4A`.
- Soft cream: `#FBF8F1`.
- Muted warm border: `rgba(20, 33, 61, 0.12)`.
- Secondary slate text: a desaturated blue-grey with sufficient contrast.
- Positive, warning and destructive semantic colours only where status meaning requires them.

Do not introduce multiple competing accent colours. Coral is the main accent. Do not replace the supplied navy/cream/coral identity with a random gold, purple, neon or rainbow palette. Any metallic or oceanic secondary accent must remain extremely restrained and subordinate.

Define reusable CSS variables/design tokens and use them consistently across every page.

## 3. Liquid Glass UI — high quality, restrained implementation

Implement a refined liquid-glass language with:

- Translucent surfaces with carefully controlled opacity.
- `backdrop-filter: blur(...) saturate(...)` and the WebKit fallback.
- Fine low-opacity borders and subtle inner highlights.
- Gentle directional reflections and layered depth.
- Natural, short hover/focus transitions.
- Correct contrast against the background behind each glass surface.

Use liquid glass selectively for floating navigation, hero overlays, compact floating panels, contextual controls, dropdowns and dialogs. Do not make every card transparent. Do not apply heavy blur to dense tables, forms, charts or long text. Use solid, readable surfaces for operational data.

Provide solid-color fallbacks for browsers without `backdrop-filter`. Respect `prefers-reduced-motion`. Avoid excessive glow, glossy gradients, thick borders, strong drop shadows and fake 3D bevels.

## 4. Fix the application architecture before visual polish

The current screenshot shows the public landing page rendered inside the dashboard workspace/sidebar. This is a structural defect.

Separate the application into two independent shells:

### Public website

- Public landing page.
- Product/feature sections as appropriate to the existing product.
- Sign-in and registration entry points.

### Authenticated application

- Workspace shell.
- Sidebar and top navigation.
- Buyer, seller and admin views.
- Operational pages.

The public landing page must never appear inside the authenticated dashboard shell. Eliminate nested shells, duplicate branding/navigation, nested scrollbars, redundant page headings, excessive blank regions and invalid layout nesting. Preserve existing route semantics and authentication flow.

Do not add a new router or major dependency unless the current architecture genuinely requires it. First understand the routing that already exists.

## 5. Public landing page — cinematic maritime experience

Follow the supplied ocean/yacht reference closely in composition and atmosphere, adapting it to FreightPilot AI:

- High-quality ocean/water visual as the hero background.
- A cargo ship or container vessel that visibly moves across the scene, with gentle natural bobbing.
- Subtle moving water/wave layers to create depth. Motion must look calm and believable, not like a cartoon.
- A legible navy/cream/coral brand treatment.
- Refined, compact navigation with clear hierarchy.
- A strong headline, concise product value proposition and no clutter.
- One clear primary call to action and at most one appropriate secondary action.
- A minimalist bento feature section for the actual product capabilities.
- A clean footer and consistent responsive behaviour.

The ship and water must not obstruct text, controls or accessibility. Use available project assets first. If suitable ship/ocean assets are missing, identify suitable assets or implement the motion with existing available techniques; do not substitute childish illustrations or generic emoji.

Keep performance in mind: use efficient CSS transforms, restrained animation, optimized image sizes and reduced-motion fallbacks. Do not build a massive animated canvas unless it is genuinely necessary.

## 6. Bento grid and content composition

Use a minimalist bento-grid system where it improves content hierarchy:

- A small number of purposeful, asymmetrical content panels.
- Consistent grid gaps and alignment.
- Clear distinction between primary and secondary information.
- Generous but controlled whitespace.
- Mixed panel sizes only when content importance justifies them.

Do not turn every section into a card. Avoid repetitive three-card rows, excessive rounded rectangles, meaningless metrics, decorative badges, redundant CTA buttons and empty placeholders.

## 7. Authenticated workspace — premium but operationally useful

Build a compact, highly readable workspace with:

### Navigation

- Overview
- Shipments
- Freight Quotes
- Risk Manager
- AI Copilot
- Payments
- Analytics
- Settings

Use a clear hierarchy, consistent icons, a restrained active state and responsive sidebar behaviour. Keep the sidebar width sensible and avoid its own unnecessary scrollbar.

### Overview

Present useful operational indicators such as active shipments, total shipments, pending quotes, payments and risk alerts—only where backed by real existing data. Organize them with clear hierarchy and avoid oversized empty cards.

### Shipments

Support the existing functionality for shipment creation, search/filtering, origin/destination, shipment status, milestones and tracking details. Use a clean table/list or split-view appropriate to the data.

### Freight quotes

Present existing carrier/quote data in an easy-to-compare format: carrier, price, transit estimate, quote status and risk indicators. Make the selected quote and next action obvious.

### Risk Manager

Use clear risk scores, severity levels and explainable risk factors. Avoid decorative gauges that obscure the meaning of the data.

### AI Copilot

Create a focused AI workspace with readable conversation content, a usable input composer, loading/error states and contextual data where supported by the existing backend.

### Payments

Create a trustworthy payment experience showing quote total, payment summary, status, transaction history and PayPal Sandbox checkout. Keep the real checkout control prominent and fully usable. Never replace payment integration with a visual mockup.

### Analytics and Settings

Keep charts legible and forms consistent. Use existing real data and API integrations; do not fabricate metrics.

## 8. Shared component quality

Standardize buttons, inputs, selects, tables, cards, dialogs, status indicators, badges, tabs, empty states, loading states and error states.

Requirements:

- Clear primary/secondary/tertiary button hierarchy.
- Consistent control heights and spacing.
- Sensible corner radii; avoid excessive pill shapes.
- Visible focus, hover, disabled and loading states.
- Accessible contrast and keyboard navigation.
- Typography appropriate to each content level.
- No dead buttons or decorative controls pretending to work.

Do not add more buttons just to make the interface look interactive. Every button must map to a real action already supported or explicitly required.

## 9. Motion and interaction

Use motion to communicate state and bring the maritime setting to life, not as decoration everywhere:

- Gentle ship movement and subtle water motion on the public hero.
- Brief hover/focus feedback.
- Smooth, short menu/dialog transitions.
- Subtle page transitions only if compatible with current routing.
- Respect `prefers-reduced-motion`.

Avoid continuous movement inside data-heavy pages, excessive parallax, particle effects, long entrance animations and any motion that harms readability or performance.

## 10. Preserve all existing product functionality

This is a frontend redesign, not a feature-removal exercise. Preserve existing integrations and workflows:

- Buyer registration and authentication.
- Seller registration, onboarding and verification.
- Admin functions.
- Shipment creation and tracking.
- Freight quote workflows.
- Risk scoring and Risk Manager.
- AI Copilot.
- PayPal Sandbox order creation, checkout and capture.
- Payment history and status.
- Analytics and settings.
- Existing backend endpoints, database operations and role-based behaviour.

Do not replace API calls with static mock data. Do not silently remove controls, routes or fields. Do not rewrite backend business logic just to simplify the UI. If an existing function is incomplete or fails, preserve it as safely as possible and report the exact issue.

## 11. Environment variables and security

- Preserve the existing environment variable names and loading mechanisms.
- Never put PayPal Client Secret, Gemini API key, database credentials, JWT secrets or other provider secrets in `VITE_*` variables or frontend bundles.
- The frontend may use only the browser-safe PayPal Client ID where the existing integration expects it.
- Do not overwrite populated `.env` or `.env.local` files.
- Do not print secrets in logs or final reports.

## 12. Code and responsive requirements

- Use the existing React + TypeScript + Vite stack.
- Inspect before modifying; reuse sound existing components and services.
- Keep components modular and CSS maintainable.
- Avoid one enormous `App.tsx`, duplicated style rules and brittle inline-style patches.
- Do not install unnecessary packages.
- Do not make destructive file operations.
- Test desktop, laptop, tablet and mobile layouts (approximately 1440px, 1366px, 768px and 390px widths).
- Prevent horizontal overflow and broken tables/forms.
- Ensure sidebar behaviour and navigation work on small screens.
- Use semantic elements, accessible labels, keyboard support and visible focus indicators.

## 13. Required execution and verification

Implement the work directly in the current project. Do not stop after writing a design plan.

After implementation:

1. Run the frontend production build (`npm run build`) from the frontend directory.
2. Run the backend test suite from the project root using the project's documented command and environment.
3. Fix errors introduced by the redesign.
4. Verify the landing page is independent from the authenticated workspace.
5. Inspect each major page in the browser if browser preview is available.
6. Compare actual screenshots against the supplied reference images.
7. Verify responsive layouts and no nested/duplicate scrollbars.
8. Verify that PayPal Sandbox environment-variable usage and checkout controls remain intact.
9. Report any tests or interactions that could not be verified. Never claim success without evidence.

Do not push to GitHub, deploy, or modify remote services as part of this task.

## 14. Definition of done

The task is complete only when:

- The public landing page is visually close to the supplied maritime/yacht reference.
- The brand palette visibly follows navy `#14213D`, cream `#F4EDE0` and coral `#FF6B5B`.
- Liquid-glass surfaces are restrained, polished and legible.
- Bento layouts are purposeful rather than repetitive.
- The landing page and authenticated workspace are architecturally separate.
- Every existing major page uses one consistent design system.
- Existing product workflows and backend connections are preserved.
- The frontend build passes and backend test results are reported accurately.
- No fake data, dead controls or unverified claims are introduced.

**Final priority:** reference fidelity, visual quality, correct application architecture, usability and preservation of working functionality—in that order. Implement the complete redesign, inspect the rendered result, correct visible defects, and finish with a factual summary of files changed, validation results and remaining limitations.

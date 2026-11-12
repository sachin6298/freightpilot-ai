> Historical project note archived during the November 2026 configuration repair. This file may describe an earlier state and is not authoritative for current setup. Use the root `README.md` and `docs/DEPLOYMENT.md` for current instructions.

# Landing hero video integration

The landing hero now uses the supplied `public/videos/yacht-motion.mp4` as its primary right-side visual, with `public/images/yacht-poster.png` as the poster/fallback. The old SVG cargo-vessel `HeroScene` component has been removed from the active source and its unused component file deleted.

The video is muted, autoplaying, looping, and inline so browsers can start it without an audio gesture. The duplicate lower-page video showcase was removed so the moving yacht appears in the first screen as requested.

If autoplay is blocked by the browser or device power-saving settings, the supplied yacht poster remains visible.

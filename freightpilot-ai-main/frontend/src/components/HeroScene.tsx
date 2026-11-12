import React from 'react';

/**
 * HeroScene — Pure SVG/CSS cinematic maritime hero scene.
 * Navy (#14213D), Cream (#F4EDE0), and Coral (#FF6B5B) palette.
 * Features an animated detailed cargo vessel sitting in parallax scrolling ocean waves.
 */
export default function HeroScene(): React.ReactElement {
  return (
    <div className="hero-scene" aria-label="Cinematic maritime cargo ship sailing on animated ocean">
      {/* Atmospheric Sky with Sunset Glow & Drifting Clouds */}
      <div className="hero-sky" aria-hidden="true">
        <div className="hero-sunset-glow" />
        <div className="hero-clouds">
          <svg viewBox="0 0 1200 80" preserveAspectRatio="none" className="hero-cloud-strip hero-cloud-strip-1">
            <path
              d="M0,45 Q150,20 300,45 T600,45 T900,45 T1200,45 V80 H0 Z"
              fill="rgba(244, 237, 224, 0.06)"
            />
          </svg>
          <svg viewBox="0 0 1200 80" preserveAspectRatio="none" className="hero-cloud-strip hero-cloud-strip-2">
            <path
              d="M-50,35 Q180,15 400,35 T800,35 T1200,35 V80 H0 Z"
              fill="rgba(255, 107, 91, 0.05)"
            />
          </svg>
        </div>
      </div>

      {/* Ocean Base & Parallax Waves */}
      <div className="hero-ocean" aria-hidden="true">
        {/* Distant Wave Layer 3 (Slowest - Horizon Swell) */}
        <div className="hero-wave-layer hero-wave-layer-3">
          <svg viewBox="0 0 1200 60" preserveAspectRatio="none" className="hero-wave-svg">
            <path
              d="M0,28 C150,15 300,40 450,28 C600,16 750,40 900,28 C1050,16 1150,38 1200,28 V60 H0 Z"
              fill="#101C35"
              opacity="0.8"
            />
          </svg>
          <svg viewBox="0 0 1200 60" preserveAspectRatio="none" className="hero-wave-svg">
            <path
              d="M0,28 C150,15 300,40 450,28 C600,16 750,40 900,28 C1050,16 1150,38 1200,28 V60 H0 Z"
              fill="#101C35"
              opacity="0.8"
            />
          </svg>
        </div>

        {/* Shimmering Water Reflection below Vessel */}
        <div className="hero-water-reflection" />

        {/* Midground Wave Layer 2 (Moderate Speed) */}
        <div className="hero-wave-layer hero-wave-layer-2">
          <svg viewBox="0 0 1200 70" preserveAspectRatio="none" className="hero-wave-svg">
            <path
              d="M0,32 C200,18 400,46 600,32 C800,18 1000,46 1200,32 V70 H0 Z"
              fill="#14213D"
              opacity="0.75"
            />
          </svg>
          <svg viewBox="0 0 1200 70" preserveAspectRatio="none" className="hero-wave-svg">
            <path
              d="M0,32 C200,18 400,46 600,32 C800,18 1000,46 1200,32 V70 H0 Z"
              fill="#14213D"
              opacity="0.75"
            />
          </svg>
        </div>

        {/* Large Detailed Cargo Vessel (Inline SVG) */}
        <div className="hero-ship-stage">
          <svg
            viewBox="0 0 680 240"
            className="hero-ship-svg hero-ship"
            role="img"
            aria-label="Large container cargo vessel sailing on the ocean"
          >
            <defs>
              <linearGradient id="hullNavyGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#14213D" />
                <stop offset="60%" stopColor="#0B1323" />
                <stop offset="100%" stopColor="#070C18" />
              </linearGradient>
              <linearGradient id="superstructureCream" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#FAF6F0" />
                <stop offset="100%" stopColor="#F4EDE0" />
              </linearGradient>
              <linearGradient id="coralWaterlineGrad" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#FF6B5B" />
                <stop offset="70%" stopColor="#FF7A6C" />
                <stop offset="100%" stopColor="#FF6B5B" />
              </linearGradient>
            </defs>

            {/* Stern Propeller Wash Foam */}
            <path
              d="M 60,185 C 40,188 20,180 5,188 C 15,195 45,194 65,190 Z"
              fill="rgba(244, 237, 224, 0.45)"
            />

            {/* Vessel Hull */}
            {/* Main Freeboard Hull Block */}
            <path
              d="M 75,120 L 520,120 L 595,145 L 615,178 L 590,186 L 85,186 L 70,165 Z"
              fill="url(#hullNavyGrad)"
              stroke="rgba(244, 237, 224, 0.15)"
              strokeWidth="1.2"
            />

            {/* Bulbous Bow & Stem Contour */}
            <path
              d="M 590,186 C 615,186 630,180 622,172 C 612,162 590,145 520,120 Z"
              fill="#0B1323"
            />

            {/* Coral Waterline Stripe */}
            <path
              d="M 80,180 L 590,180 L 610,188 L 84,188 Z"
              fill="url(#coralWaterlineGrad)"
            />

            {/* Hawsehole & Anchor Pocket */}
            <ellipse cx="570" cy="140" rx="5" ry="3.5" fill="#070C18" stroke="#FF6B5B" strokeWidth="0.8" />
            <path d="M 570,142 L 575,152" stroke="#F4EDE0" strokeWidth="0.8" opacity="0.6" />

            {/* Draft Marks on Stem */}
            <line x1="595" y1="162" x2="598" y2="162" stroke="#F4EDE0" strokeWidth="1" opacity="0.7" />
            <line x1="598" y1="168" x2="602" y2="168" stroke="#F4EDE0" strokeWidth="1" opacity="0.7" />
            <line x1="602" y1="174" x2="607" y2="174" stroke="#F4EDE0" strokeWidth="1" opacity="0.7" />

            {/* Deck Coamings and Railings */}
            <line x1="75" y1="119" x2="520" y2="119" stroke="#F4EDE0" strokeWidth="1.5" opacity="0.4" />

            {/* STACKED CONTAINER BAYS (Coral, Cream, Navy) */}
            <g className="hero-containers">
              {/* Bay 1 (Aft Deck) */}
              <rect x="95" y="98" width="36" height="20" rx="1.5" fill="#FF6B5B" />
              <rect x="95" y="76" width="36" height="20" rx="1.5" fill="#14213D" stroke="rgba(244, 237, 224, 0.2)" strokeWidth="0.8" />
              <rect x="95" y="54" width="36" height="20" rx="1.5" fill="#F4EDE0" />

              {/* Bay 2 */}
              <rect x="135" y="98" width="36" height="20" rx="1.5" fill="#F4EDE0" />
              <rect x="135" y="76" width="36" height="20" rx="1.5" fill="#FF6B5B" />
              <rect x="135" y="54" width="36" height="20" rx="1.5" fill="#14213D" stroke="rgba(244, 237, 224, 0.2)" strokeWidth="0.8" />
              <rect x="135" y="32" width="36" height="20" rx="1.5" fill="#FF6B5B" />

              {/* Bay 3 */}
              <rect x="175" y="98" width="38" height="20" rx="1.5" fill="#14213D" stroke="rgba(244, 237, 224, 0.2)" strokeWidth="0.8" />
              <rect x="175" y="76" width="38" height="20" rx="1.5" fill="#F4EDE0" />
              <rect x="175" y="54" width="38" height="20" rx="1.5" fill="#FF6B5B" />

              {/* Bay 4 (Midships 40ft Bay) */}
              <rect x="217" y="98" width="46" height="20" rx="1.5" fill="#FF6B5B" />
              <rect x="217" y="76" width="46" height="20" rx="1.5" fill="#14213D" stroke="rgba(244, 237, 224, 0.2)" strokeWidth="0.8" />
              <rect x="217" y="54" width="46" height="20" rx="1.5" fill="#F4EDE0" />
              <rect x="217" y="32" width="46" height="20" rx="1.5" fill="#FF6B5B" />

              {/* Bay 5 */}
              <rect x="267" y="98" width="46" height="20" rx="1.5" fill="#F4EDE0" />
              <rect x="267" y="76" width="46" height="20" rx="1.5" fill="#FF6B5B" />
              <rect x="267" y="54" width="46" height="20" rx="1.5" fill="#14213D" stroke="rgba(244, 237, 224, 0.2)" strokeWidth="0.8" />

              {/* Bay 6 */}
              <rect x="317" y="98" width="44" height="20" rx="1.5" fill="#14213D" stroke="rgba(244, 237, 224, 0.2)" strokeWidth="0.8" />
              <rect x="317" y="76" width="44" height="20" rx="1.5" fill="#F4EDE0" />
              <rect x="317" y="54" width="44" height="20" rx="1.5" fill="#FF6B5B" />
              <rect x="317" y="32" width="44" height="20" rx="1.5" fill="#F4EDE0" />

              {/* Bay 7 (Forward of Bridge) */}
              <rect x="428" y="98" width="42" height="20" rx="1.5" fill="#FF6B5B" />
              <rect x="428" y="76" width="42" height="20" rx="1.5" fill="#14213D" stroke="rgba(244, 237, 224, 0.2)" strokeWidth="0.8" />
              <rect x="428" y="54" width="42" height="20" rx="1.5" fill="#F4EDE0" />

              {/* Bay 8 (Bow Section) */}
              <rect x="474" y="102" width="38" height="18" rx="1.5" fill="#F4EDE0" />
              <rect x="474" y="82" width="38" height="18" rx="1.5" fill="#FF6B5B" />
            </g>

            {/* SUPERSTRUCTURE & NAVIGATION BRIDGE (Cream #F4EDE0) */}
            <g className="hero-superstructure">
              {/* Lower Deckhouse */}
              <rect x="367" y="78" width="54" height="42" fill="url(#superstructureCream)" />
              <line x1="367" y1="92" x2="421" y2="92" stroke="#14213D" strokeWidth="0.8" opacity="0.3" />
              <line x1="367" y1="106" x2="421" y2="106" stroke="#14213D" strokeWidth="0.8" opacity="0.3" />

              {/* Upper Deckhouse & Bridge Deck */}
              <rect x="364" y="46" width="60" height="32" fill="url(#superstructureCream)" />

              {/* Extended Bridge Wings */}
              <rect x="358" y="44" width="72" height="11" rx="1" fill="#F4EDE0" stroke="rgba(20, 33, 61, 0.25)" strokeWidth="0.8" />

              {/* Illuminated Wheelhouse Windows (Warm Glow) */}
              <rect x="366" y="47" width="7" height="5" rx="0.8" fill="#FF6B5B" opacity="0.95" />
              <rect x="375" y="47" width="7" height="5" rx="0.8" fill="#F4EDE0" opacity="0.95" />
              <rect x="384" y="47" width="7" height="5" rx="0.8" fill="#FF6B5B" opacity="0.95" />
              <rect x="393" y="47" width="7" height="5" rx="0.8" fill="#F4EDE0" opacity="0.95" />
              <rect x="402" y="47" width="7" height="5" rx="0.8" fill="#FF6B5B" opacity="0.95" />
              <rect x="411" y="47" width="7" height="5" rx="0.8" fill="#F4EDE0" opacity="0.95" />

              {/* Funnel / Exhaust Stack */}
              <rect x="372" y="24" width="16" height="22" rx="1" fill="#14213D" />
              <rect x="372" y="30" width="16" height="6" fill="#FF6B5B" />

              {/* Radar Mast & Scanner */}
              <line x1="400" y1="44" x2="400" y2="14" stroke="#F4EDE0" strokeWidth="2.2" strokeLinecap="round" />
              <line x1="392" y1="22" x2="408" y2="22" stroke="#F4EDE0" strokeWidth="1.5" />
              <line x1="395" y1="16" x2="405" y2="16" stroke="#FF6B5B" strokeWidth="2" strokeLinecap="round" />
              <ellipse cx="400" cy="12" rx="3" ry="1.5" fill="#F4EDE0" />

              {/* Aft Pulsing Mast Beacon Light */}
              <circle cx="400" cy="11" r="3.5" fill="#FF6B5B" className="hero-mast-light">
                <animate attributeName="opacity" values="0.4;1;0.4" dur="2s" repeatCount="indefinite" />
              </circle>
            </g>

            {/* Forecastle & Forward Mast */}
            <line x1="540" y1="120" x2="540" y2="78" stroke="#F4EDE0" strokeWidth="1.8" strokeLinecap="round" />
            <line x1="535" y1="88" x2="545" y2="88" stroke="#F4EDE0" strokeWidth="1.2" />
            <circle cx="540" cy="76" r="2.8" fill="#FF6B5B" className="hero-mast-light">
              <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite" />
            </circle>

            {/* Bow Wake & Dynamic Wave Foam (Pulsing) */}
            <path
              d="M 605,182 Q 625,186 642,192 Q 622,190 600,188 Z"
              fill="rgba(244, 237, 224, 0.75)"
              className="hero-bow-wake"
            />
            <circle cx="616" cy="186" r="4.5" fill="rgba(244, 237, 224, 0.6)" className="hero-bow-spray" />
            <circle cx="628" cy="190" r="3" fill="rgba(244, 237, 224, 0.45)" className="hero-bow-spray" />
          </svg>
        </div>

        {/* Foreground Wave Layer 1 (Translates Fastest & Overlaps Hull Waterline) */}
        <div className="hero-wave-layer hero-wave-layer-1">
          <svg viewBox="0 0 1200 80" preserveAspectRatio="none" className="hero-wave-svg">
            <path
              d="M0,38 C180,18 360,54 540,36 C720,18 900,54 1080,36 C1140,30 1180,44 1200,38 V80 H0 Z"
              fill="#14213D"
            />
            {/* Wave Crest Highlight */}
            <path
              d="M0,38 C180,18 360,54 540,36 C720,18 900,54 1080,36 C1140,30 1180,44 1200,38"
              fill="none"
              stroke="rgba(244, 237, 224, 0.35)"
              strokeWidth="1.8"
            />
          </svg>
          <svg viewBox="0 0 1200 80" preserveAspectRatio="none" className="hero-wave-svg">
            <path
              d="M0,38 C180,18 360,54 540,36 C720,18 900,54 1080,36 C1140,30 1180,44 1200,38 V80 H0 Z"
              fill="#14213D"
            />
            <path
              d="M0,38 C180,18 360,54 540,36 C720,18 900,54 1080,36 C1140,30 1180,44 1200,38"
              fill="none"
              stroke="rgba(244, 237, 224, 0.35)"
              strokeWidth="1.8"
            />
          </svg>
        </div>

        {/* Bottom Baseline Seal */}
        <div className="hero-bottom-seal" />
      </div>
    </div>
  );
}
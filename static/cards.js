/** Distinctive Major Arcana faces — local SVG, gold / indigo, unique per card. */
const CARD_SVG = (() => {
  const gold = "#e4c46a";
  const goldSoft = "#c9a24a";
  const ink = "#f4ecff";
  const dusk = "#6d4cae";

  function card(id, art) {
    return `<svg class="card-art" viewBox="0 0 120 158" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <linearGradient id="bg${id}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#3a1d6e"/>
          <stop offset="55%" stop-color="#140b28"/>
          <stop offset="100%" stop-color="#07050f"/>
        </linearGradient>
        <radialGradient id="glow${id}" cx="50%" cy="32%" r="55%">
          <stop offset="0%" stop-color="#8b5cf6" stop-opacity="0.45"/>
          <stop offset="100%" stop-color="#8b5cf6" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <rect width="120" height="158" rx="8" fill="url(#bg${id})"/>
      <rect x="4" y="4" width="112" height="150" rx="6" fill="none" stroke="${gold}" stroke-opacity="0.7" stroke-width="1.4"/>
      <rect x="8" y="8" width="104" height="142" rx="4" fill="none" stroke="${gold}" stroke-opacity="0.28"/>
      <rect width="120" height="158" rx="8" fill="url(#glow${id})"/>
      ${art}
    </svg>`;
  }

  const arts = {
    0: `<circle cx="88" cy="28" r="10" fill="${gold}" opacity="0.85"/>
      <path d="M22 128 L50 78 L70 98 L98 52" fill="none" stroke="${dusk}" stroke-width="3"/>
      <circle cx="42" cy="92" r="11" fill="${ink}" opacity="0.9"/>
      <path d="M42 103 L42 128 M34 112 L50 112" stroke="${gold}" stroke-width="2.2"/>
      <path d="M52 86 L68 70" stroke="${goldSoft}" stroke-width="2"/>
      <circle cx="70" cy="68" r="3" fill="${gold}"/>`,
    1: `<path d="M60 24 L60 44" stroke="${gold}" stroke-width="2"/>
      <circle cx="60" cy="22" r="7" fill="none" stroke="${gold}" stroke-width="2"/>
      <rect x="28" y="108" width="64" height="10" rx="2" fill="${goldSoft}"/>
      <circle cx="38" cy="104" r="5" fill="${dusk}"/>
      <rect x="54" y="96" width="10" height="12" fill="${gold}"/>
      <path d="M78 104 L86 92 L90 104" fill="${ink}"/>
      <path d="M40 70 L80 70 L60 48 Z" fill="${ink}" opacity="0.85"/>
      <circle cx="60" cy="62" r="6" fill="#241445"/>`,
    2: `<rect x="22" y="36" width="12" height="92" fill="${dusk}"/>
      <rect x="86" y="36" width="12" height="92" fill="${dusk}"/>
      <path d="M40 128 Q60 48 80 128" fill="${ink}" opacity="0.88"/>
      <circle cx="60" cy="70" r="10" fill="#1a1236"/>
      <path d="M48 28 Q60 16 72 28" fill="none" stroke="${gold}" stroke-width="2"/>
      <circle cx="60" cy="22" r="5" fill="${gold}"/>`,
    3: `<circle cx="60" cy="58" r="16" fill="${ink}"/>
      <path d="M36 78 Q60 130 84 78" fill="${goldSoft}" opacity="0.9"/>
      <path d="M24 118 L36 100 L48 118 L60 96 L72 118 L84 100 L96 118" fill="none" stroke="${gold}" stroke-width="2"/>
      <circle cx="60" cy="88" r="5" fill="#7c3aed"/>`,
    4: `<rect x="30" y="70" width="60" height="50" rx="3" fill="${dusk}"/>
      <rect x="42" y="46" width="36" height="28" fill="${goldSoft}"/>
      <path d="M42 46 L60 28 L78 46" fill="${gold}"/>
      <circle cx="60" cy="92" r="8" fill="${ink}"/>
      <path d="M24 128 H96" stroke="${gold}" stroke-width="3"/>`,
    5: `<path d="M40 40 L60 22 L80 40 V70 H40 Z" fill="${gold}"/>
      <circle cx="60" cy="86" r="14" fill="${ink}"/>
      <path d="M36 128 V100 H84 V128" fill="none" stroke="${dusk}" stroke-width="6"/>
      <circle cx="48" cy="118" r="5" fill="${goldSoft}"/>
      <circle cx="72" cy="118" r="5" fill="${goldSoft}"/>`,
    6: `<circle cx="60" cy="30" r="12" fill="${gold}"/>
      <circle cx="40" cy="88" r="14" fill="${ink}"/>
      <circle cx="80" cy="88" r="14" fill="${ink}"/>
      <path d="M40 102 Q60 122 80 102" fill="none" stroke="${gold}" stroke-width="2.4"/>
      <path d="M60 42 L60 72" stroke="${goldSoft}" stroke-width="2"/>`,
    7: `<rect x="34" y="70" width="52" height="28" rx="4" fill="${goldSoft}"/>
      <circle cx="44" cy="112" r="12" fill="none" stroke="${gold}" stroke-width="3"/>
      <circle cx="76" cy="112" r="12" fill="none" stroke="${gold}" stroke-width="3"/>
      <path d="M48 70 L60 38 L72 70" fill="${ink}"/>
      <path d="M28 70 H92" stroke="${dusk}" stroke-width="3"/>`,
    8: `<ellipse cx="62" cy="100" rx="28" ry="18" fill="${dusk}"/>
      <circle cx="78" cy="86" r="14" fill="${goldSoft}"/>
      <circle cx="42" cy="72" r="12" fill="${ink}"/>
      <path d="M42 84 Q58 70 74 86" fill="none" stroke="${gold}" stroke-width="2.5"/>
      <path d="M36 28 Q48 18 42 34 Q54 24 48 40" fill="none" stroke="${gold}" stroke-width="2"/>`,
    9: `<path d="M48 128 L48 70 Q48 48 60 40 Q72 48 72 70 L72 128" fill="#1c1238"/>
      <circle cx="60" cy="56" r="10" fill="${ink}"/>
      <path d="M60 66 L60 92" stroke="${gold}" stroke-width="2"/>
      <circle cx="60" cy="38" r="8" fill="${gold}" opacity="0.9"/>
      <circle cx="60" cy="38" r="3" fill="#1a1236"/>`,
    10: `<circle cx="60" cy="84" r="36" fill="none" stroke="${gold}" stroke-width="3"/>
      <circle cx="60" cy="84" r="18" fill="none" stroke="${dusk}" stroke-width="2"/>
      <path d="M60 48 L60 120 M24 84 H96" stroke="${goldSoft}" stroke-width="1.6"/>
      <circle cx="60" cy="48" r="5" fill="${ink}"/>
      <circle cx="96" cy="84" r="5" fill="${gold}"/>
      <circle cx="60" cy="120" r="5" fill="${ink}"/>
      <circle cx="24" cy="84" r="5" fill="${gold}"/>`,
    11: `<path d="M60 28 L60 70" stroke="${gold}" stroke-width="3"/>
      <path d="M60 28 L52 70 H68 Z" fill="${goldSoft}"/>
      <rect x="28" y="70" width="24" height="8" fill="${ink}"/>
      <rect x="68" y="70" width="24" height="8" fill="${ink}"/>
      <path d="M40 78 L40 100 M80 78 L80 100" stroke="${gold}" stroke-width="2"/>
      <path d="M36 128 H84 L60 108 Z" fill="${dusk}"/>`,
    12: `<path d="M36 36 H84" stroke="${gold}" stroke-width="4"/>
      <path d="M60 36 L60 58" stroke="${goldSoft}" stroke-width="2"/>
      <circle cx="60" cy="88" r="12" fill="${ink}"/>
      <path d="M60 76 L48 54 M60 76 L72 54" stroke="${dusk}" stroke-width="3"/>
      <path d="M60 100 L52 128 M60 100 L68 128" stroke="${gold}" stroke-width="2.4"/>`,
    13: `<path d="M22 128 Q40 70 60 86 Q80 104 98 48" fill="none" stroke="${dusk}" stroke-width="5"/>
      <circle cx="78" cy="58" r="10" fill="${ink}"/>
      <path d="M48 40 Q60 22 72 40 Q60 34 48 40" fill="#c45c7a"/>
      <path d="M30 118 L90 118" stroke="${gold}" stroke-width="2" opacity="0.5"/>`,
    14: `<circle cx="40" cy="58" r="12" fill="none" stroke="${gold}" stroke-width="2.5"/>
      <circle cx="80" cy="108" r="12" fill="none" stroke="${gold}" stroke-width="2.5"/>
      <path d="M44 66 Q60 88 76 100" stroke="${ink}" stroke-width="3" fill="none"/>
      <circle cx="60" cy="84" r="8" fill="${dusk}"/>
      <path d="M28 128 H92" stroke="${goldSoft}" stroke-width="2"/>`,
    15: `<path d="M40 128 L40 80 L60 48 L80 80 L80 128" fill="#2a1030"/>
      <circle cx="60" cy="70" r="14" fill="${ink}" opacity="0.85"/>
      <path d="M48 66 L44 58 M72 66 L76 58" stroke="${gold}" stroke-width="2"/>
      <path d="M36 100 H84" stroke="${goldSoft}" stroke-width="2"/>
      <circle cx="36" cy="100" r="4" fill="${gold}"/>
      <circle cx="84" cy="100" r="4" fill="${gold}"/>`,
    16: `<path d="M44 128 V62 L60 38 L76 62 V128" fill="${dusk}"/>
      <path d="M28 40 L70 70" stroke="${gold}" stroke-width="3"/>
      <path d="M70 70 L92 52" stroke="${gold}" stroke-width="2"/>
      <circle cx="50" cy="92" r="4" fill="${ink}"/>
      <circle cx="70" cy="108" r="4" fill="${ink}"/>
      <path d="M36 128 H84" stroke="${goldSoft}" stroke-width="3"/>`,
    17: `<polygon points="60,24 66,48 92,48 70,64 78,90 60,74 42,90 50,64 28,48 54,48" fill="${gold}"/>
      <path d="M24 128 Q60 96 96 128" fill="#3d2a7a"/>
      <circle cx="40" cy="118" r="3" fill="${ink}"/>
      <circle cx="80" cy="114" r="3" fill="${ink}"/>`,
    18: `<circle cx="60" cy="52" r="22" fill="${goldSoft}" opacity="0.35"/>
      <circle cx="60" cy="52" r="16" fill="${ink}" opacity="0.9"/>
      <circle cx="68" cy="46" r="12" fill="#140b28"/>
      <path d="M60 78 Q48 100 40 128 M60 78 Q72 100 80 128" fill="none" stroke="${gold}" stroke-width="2"/>
      <circle cx="36" cy="100" r="5" fill="${dusk}"/>
      <circle cx="84" cy="108" r="5" fill="${dusk}"/>`,
    19: `<circle cx="60" cy="58" r="22" fill="${gold}"/>
      <g stroke="${goldSoft}" stroke-width="2">
        <path d="M60 22 L60 14 M90 58 L98 58 M60 94 L60 102 M30 58 L22 58"/>
        <path d="M82 36 L88 30 M82 80 L88 86 M38 36 L32 30 M38 80 L32 86"/>
      </g>
      <circle cx="48" cy="118" r="8" fill="${ink}"/>
      <circle cx="72" cy="122" r="6" fill="${ink}" opacity="0.8"/>`,
    20: `<path d="M40 48 L80 32 L76 44 L92 48 L76 54 L80 66 L40 50 Z" fill="${gold}"/>
      <circle cx="40" cy="110" r="10" fill="${ink}"/>
      <circle cx="80" cy="110" r="10" fill="${ink}"/>
      <path d="M28 128 H92" stroke="${dusk}" stroke-width="4"/>
      <path d="M60 70 L60 96" stroke="${goldSoft}" stroke-width="2"/>`,
    21: `<ellipse cx="60" cy="84" rx="38" ry="48" fill="none" stroke="${gold}" stroke-width="3"/>
      <circle cx="60" cy="84" r="16" fill="${ink}"/>
      <path d="M60 68 L66 84 L60 100 L54 84 Z" fill="${goldSoft}"/>
      <circle cx="60" cy="36" r="4" fill="${gold}"/>
      <circle cx="98" cy="84" r="4" fill="${gold}"/>
      <circle cx="60" cy="132" r="4" fill="${gold}"/>
      <circle cx="22" cy="84" r="4" fill="${gold}"/>`,
  };

  const out = {};
  for (let i = 0; i < 22; i += 1) out[i] = card(i, arts[i]);
  return out;
})();

"""Stylized SVG portraits for demo seekers — local files, no CDN."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from app.db import UPLOADS

PORTRAITS_DIR = UPLOADS / "portraits"

SKINS = [
    "#f6e0c8",
    "#f0d0b0",
    "#e8c09a",
    "#d4a574",
    "#c68642",
    "#a56a3a",
    "#8d5524",
    "#6b3d1f",
    "#4a2c14",
    "#e2b896",
    "#c9a07a",
    "#9c6b45",
]

HAIR = [
    "#1a120c",
    "#2c1810",
    "#3b2214",
    "#5a3318",
    "#6b3a22",
    "#8b4a28",
    "#a65b32",
    "#c4a35a",
    "#d8c48a",
    "#8b3a3a",
    "#4a2a3a",
    "#2a2438",
    "#c8c2b4",
    "#111111",
    "#3d2a1c",
]

EYES = ["#2a1a12", "#3d2914", "#1c3a2e", "#24344a", "#4a3020", "#1a1a1a", "#3a4a2a"]

CLOTHES = [
    "#2a4a6b",
    "#6b2d3c",
    "#2d5a45",
    "#3d2a5c",
    "#8a5a2b",
    "#1c1c22",
    "#c4b8a0",
    "#4a6b8a",
    "#7a3e2e",
    "#2a3d4a",
    "#5c3d6b",
    "#3a5a58",
    "#6b4a2a",
    "#2c3a5c",
]

BACKGROUNDS = [
    ("#3a1d6e", "#140b28"),
    ("#1d3a6e", "#0b1428"),
    ("#6e1d3a", "#280b14"),
    ("#1d6e4a", "#0b2818"),
    ("#6e4a1d", "#28180b"),
    ("#2a1d4a", "#0e081c"),
    ("#4a1d3a", "#1a0814"),
    ("#1d4a4a", "#081818"),
    ("#3a2a1d", "#140e08"),
    ("#2d1d6e", "#100b28"),
    ("#1d2a3a", "#080e14"),
    ("#4a2d1d", "#1c1008"),
]

HAIR_WOMAN = ["bob", "long", "bun", "pony", "afro", "curly", "braids", "pixie", "locs", "waves"]
HAIR_MAN = ["short", "side", "shaved", "undercut", "curly", "afro", "locs", "long", "pixie"]
HAIR_NB = ["bob", "short", "undercut", "curly", "bun", "afro", "pixie", "waves", "locs", "side"]


def _slug(email: str) -> str:
    local = email.split("@")[0].lower()
    return re.sub(r"[^a-z0-9]+", "-", local).strip("-") or "seeker"


def _rng(seed: str):
    n = int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16)

    def nxt(mod: int) -> int:
        nonlocal n
        n = (n * 6364136223846793005 + 1) & ((1 << 64) - 1)
        return n % mod

    return nxt


def _pick(rnd, seq):
    return seq[rnd(len(seq))]


def _darken(hex_color: str, amount: float = 0.22) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = max(0, int(r * (1 - amount)))
    g = max(0, int(g * (1 - amount)))
    b = max(0, int(b * (1 - amount)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _lighten(hex_color: str, amount: float = 0.18) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return f"#{r:02x}{g:02x}{b:02x}"


def _hair_behind(style: str, hair: str, rx: int, ry: int) -> str:
    dark = _darken(hair, 0.12)
    if style == "afro":
        return (
            f'<ellipse cx="128" cy="100" rx="{rx + 38}" ry="{ry + 28}" fill="{hair}"/>'
            f'<ellipse cx="78" cy="118" rx="34" ry="38" fill="{hair}"/>'
            f'<ellipse cx="178" cy="118" rx="34" ry="38" fill="{hair}"/>'
            f'<ellipse cx="128" cy="62" rx="42" ry="28" fill="{dark}"/>'
        )
    if style == "curly":
        curls = []
        for cx, cy, r in (
            (92, 78, 22),
            (116, 62, 20),
            (142, 60, 22),
            (166, 78, 20),
            (80, 108, 18),
            (176, 108, 18),
            (100, 58, 16),
            (156, 56, 16),
        ):
            curls.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{hair}"/>')
        return "".join(curls)
    if style == "locs":
        locs = [f'<ellipse cx="128" cy="88" rx="{rx + 16}" ry="{ry - 8}" fill="{hair}"/>']
        for i, x in enumerate((78, 92, 108, 148, 164, 178)):
            h = 70 + (i % 3) * 14
            locs.append(
                f'<rect x="{x - 6}" y="110" width="12" height="{h}" rx="6" fill="{hair if i % 2 == 0 else dark}"/>'
            )
        return "".join(locs)
    if style == "braids":
        return (
            f'<ellipse cx="128" cy="92" rx="{rx + 10}" ry="{ry - 6}" fill="{hair}"/>'
            f'<path d="M78 120 C70 160 74 200 68 232" stroke="{hair}" stroke-width="14" fill="none" stroke-linecap="round"/>'
            f'<path d="M90 122 C86 164 90 204 84 236" stroke="{dark}" stroke-width="12" fill="none" stroke-linecap="round"/>'
            f'<path d="M178 120 C186 160 182 200 188 232" stroke="{hair}" stroke-width="14" fill="none" stroke-linecap="round"/>'
            f'<path d="M166 122 C170 164 166 204 172 236" stroke="{dark}" stroke-width="12" fill="none" stroke-linecap="round"/>'
        )
    if style in ("long", "waves", "pony", "bun"):
        wave = (
            f'<path d="M70 110 C58 150 62 190 54 236 L100 236 C104 190 96 150 86 118 Z" fill="{hair}"/>'
            f'<path d="M186 110 C198 150 194 190 202 236 L156 236 C152 190 160 150 170 118 Z" fill="{hair}"/>'
        )
        if style == "waves":
            wave += (
                f'<path d="M64 150 C50 170 78 180 60 200 C48 214 72 224 58 236" '
                f'stroke="{dark}" stroke-width="8" fill="none"/>'
                f'<path d="M192 150 C206 170 178 180 196 200 C208 214 184 224 198 236" '
                f'stroke="{dark}" stroke-width="8" fill="none"/>'
            )
        return f'<ellipse cx="128" cy="92" rx="{rx + 12}" ry="{ry - 4}" fill="{hair}"/>' + wave
    if style == "bob":
        return (
            f'<path d="M70 100 C66 70 90 42 128 40 C166 42 190 70 186 100 '
            f'C190 150 176 168 168 172 L88 172 C80 168 66 150 70 100 Z" fill="{hair}"/>'
        )
    if style == "undercut":
        return f'<path d="M88 92 C92 52 112 40 128 40 C148 40 168 56 166 92 C150 70 128 66 108 78 Z" fill="{hair}"/>'
    if style == "side":
        return (
            f'<path d="M78 108 C80 58 110 38 132 42 C158 46 176 70 174 108 '
            f'C168 88 150 72 128 74 C104 76 86 92 78 108 Z" fill="{hair}"/>'
        )
    if style == "short":
        return f'<path d="M76 108 C78 60 104 40 128 40 C154 40 180 62 180 108 C164 78 140 70 128 70 C110 70 90 82 76 108 Z" fill="{hair}"/>'
    if style == "pixie":
        return f'<path d="M84 112 C86 68 108 48 128 48 C150 48 172 68 172 112 C160 84 140 76 128 76 C112 76 96 88 84 112 Z" fill="{hair}"/>'
    # shaved
    return f'<path d="M90 100 C96 64 112 52 128 52 C146 52 162 66 166 100 C150 78 128 74 108 86 Z" fill="{hair}" opacity="0.55"/>'


def _hair_front(style: str, hair: str, rx: int) -> str:
    dark = _darken(hair, 0.08)
    if style in ("bun",):
        return (
            f'<ellipse cx="128" cy="46" rx="28" ry="22" fill="{hair}"/>'
            f'<ellipse cx="128" cy="46" rx="18" ry="14" fill="{dark}"/>'
            f'<path d="M88 88 C104 72 120 78 128 80 C140 78 154 70 168 88" '
            f'stroke="{hair}" stroke-width="16" fill="none" stroke-linecap="round"/>'
        )
    if style == "pony":
        return (
            f'<path d="M88 90 C108 70 128 74 148 70 C166 88 160 96 150 92" fill="{hair}"/>'
            f'<ellipse cx="168" cy="58" rx="16" ry="22" fill="{hair}"/>'
            f'<path d="M168 70 C186 90 178 140 172 168" stroke="{hair}" stroke-width="16" fill="none" stroke-linecap="round"/>'
        )
    if style in ("long", "waves", "bob"):
        bangs = [
            f'<path d="M78 92 C96 70 112 86 128 78 C146 70 160 86 178 94 C160 78 140 68 128 70 C112 68 94 80 78 92 Z" fill="{hair}"/>'
        ]
        if style == "bob":
            bangs.append(
                f'<path d="M96 78 C110 92 118 88 128 86 C140 88 148 94 162 80" fill="{dark}"/>'
            )
        return "".join(bangs)
    if style == "side":
        return f'<path d="M118 72 C130 88 148 86 168 78 C150 70 132 66 118 72 Z" fill="{hair}"/>'
    if style == "undercut":
        return f'<path d="M100 78 C118 92 140 86 158 74 C140 68 120 66 100 78 Z" fill="{hair}"/>'
    if style in ("pixie", "short"):
        return f'<path d="M92 86 C110 74 128 82 148 76 C136 70 118 68 92 86 Z" fill="{hair}"/>'
    if style == "curly":
        return (
            f'<circle cx="104" cy="80" r="14" fill="{hair}"/>'
            f'<circle cx="128" cy="74" r="13" fill="{dark}"/>'
            f'<circle cx="152" cy="80" r="14" fill="{hair}"/>'
        )
    return ""


def _clothes(kind: str, color: str, skin: str) -> str:
    dark = _darken(color, 0.2)
    light = _lighten(color, 0.12)
    neck = f'<path d="M108 168 L148 168 L158 214 L98 214 Z" fill="{skin}"/>'
    if kind == "turtleneck":
        body = (
            f'<path d="M40 236 L68 188 L98 210 L158 210 L188 188 L216 236 Z" fill="{color}"/>'
            f'<rect x="108" y="168" width="40" height="46" rx="10" fill="{dark}"/>'
        )
    elif kind == "vneck":
        body = (
            f'<path d="M36 240 L70 186 Q128 210 186 186 L220 240 Z" fill="{color}"/>'
            f'<path d="M108 176 L128 214 L148 176" fill="{skin}"/>'
        )
    elif kind == "collar":
        body = (
            f'<path d="M38 240 L72 188 L184 188 L218 240 Z" fill="{color}"/>'
            f'<path d="M108 176 L128 168 L148 176 L140 198 L116 198 Z" fill="{light}"/>'
            f'<path d="M100 176 L128 196 L92 210 Z" fill="{dark}"/>'
            f'<path d="M156 176 L128 196 L164 210 Z" fill="{dark}"/>'
        )
    elif kind == "jacket":
        body = (
            f'<path d="M32 240 L66 184 L190 184 L224 240 Z" fill="{color}"/>'
            f'<path d="M96 188 L128 236 L160 188 L150 184 L106 184 Z" fill="{dark}"/>'
            f'<path d="M108 176 L148 176 L144 198 L112 198 Z" fill="{_darken(skin, 0.08)}"/>'
        )
    elif kind == "hoodie":
        body = (
            f'<path d="M40 240 L74 190 L182 190 L216 240 Z" fill="{color}"/>'
            f'<path d="M86 176 Q128 210 170 176 Q168 168 128 168 Q88 168 86 176 Z" fill="{dark}"/>'
            f'<rect x="122" y="198" width="12" height="36" rx="3" fill="{light}"/>'
        )
    elif kind == "tank":
        body = (
            f'<path d="M70 240 L88 198 L168 198 L186 240 Z" fill="{color}"/>'
            f'<path d="M88 176 L100 198 L88 210 Z" fill="{skin}"/>'
            f'<path d="M168 176 L156 198 L168 210 Z" fill="{skin}"/>'
        )
    else:  # crew
        body = (
            f'<path d="M38 240 L72 188 Q128 204 184 188 L218 240 Z" fill="{color}"/>'
            f'<path d="M108 172 Q128 186 148 172 Q146 198 128 202 Q110 198 108 172 Z" fill="{skin}"/>'
        )
    return neck + body


def _beard(kind: str, hair: str, skin: str) -> str:
    if kind == "none":
        return ""
    shade = _darken(hair, 0.05)
    if kind == "stubble":
        return (
            f'<ellipse cx="128" cy="158" rx="36" ry="22" fill="{shade}" opacity="0.28"/>'
            f'<ellipse cx="100" cy="148" rx="10" ry="16" fill="{shade}" opacity="0.22"/>'
            f'<ellipse cx="156" cy="148" rx="10" ry="16" fill="{shade}" opacity="0.22"/>'
        )
    if kind == "mustache":
        return (
            f'<path d="M108 150 Q128 160 148 150 Q140 156 128 154 Q116 156 108 150 Z" fill="{shade}"/>'
        )
    # full beard
    return (
        f'<path d="M92 140 C88 168 104 186 128 188 C152 186 168 168 164 140 '
        f'C150 152 140 148 128 150 C116 148 106 152 92 140 Z" fill="{shade}"/>'
        f'<ellipse cx="128" cy="168" rx="22" ry="14" fill="{_darken(shade, 0.15)}"/>'
    )


def _glasses(kind: str) -> str:
    if kind == "none":
        return ""
    if kind == "round":
        return (
            '<circle cx="104" cy="114" r="16" fill="none" stroke="#1a1420" stroke-width="3" opacity="0.85"/>'
            '<circle cx="152" cy="114" r="16" fill="none" stroke="#1a1420" stroke-width="3" opacity="0.85"/>'
            '<path d="M120 114 H136" stroke="#1a1420" stroke-width="3"/>'
            '<path d="M88 112 H78" stroke="#1a1420" stroke-width="3"/>'
            '<path d="M168 112 H178" stroke="#1a1420" stroke-width="3"/>'
            '<circle cx="104" cy="114" r="14" fill="#9ec9e8" opacity="0.12"/>'
            '<circle cx="152" cy="114" r="14" fill="#9ec9e8" opacity="0.12"/>'
        )
    return (
        '<rect x="86" y="102" width="36" height="26" rx="6" fill="none" stroke="#241820" stroke-width="3"/>'
        '<rect x="134" y="102" width="36" height="26" rx="6" fill="none" stroke="#241820" stroke-width="3"/>'
        '<path d="M122 114 H134" stroke="#241820" stroke-width="3"/>'
        '<rect x="88" y="104" width="32" height="22" rx="5" fill="#9ec9e8" opacity="0.1"/>'
        '<rect x="136" y="104" width="32" height="22" rx="5" fill="#9ec9e8" opacity="0.1"/>'
    )


def _earrings(kind: str, metal: str) -> str:
    if kind == "none":
        return ""
    if kind == "hoops":
        return (
            f'<circle cx="70" cy="138" r="8" fill="none" stroke="{metal}" stroke-width="3"/>'
            f'<circle cx="186" cy="138" r="8" fill="none" stroke="{metal}" stroke-width="3"/>'
        )
    return (
        f'<circle cx="70" cy="138" r="3.5" fill="{metal}"/>'
        f'<circle cx="186" cy="138" r="3.5" fill="{metal}"/>'
    )


def portrait_svg(email: str, name: str, gender: str) -> str:
    rnd = _rng(email + "|" + name)
    skin = _pick(rnd, SKINS)
    hair = _pick(rnd, HAIR)
    eye_color = _pick(rnd, EYES)
    cloth = _pick(rnd, CLOTHES)
    bg_a, bg_b = _pick(rnd, BACKGROUNDS)
    uid = _slug(email)

    if gender == "woman":
        style = _pick(rnd, HAIR_WOMAN)
        beard = "none" if rnd(10) else "none"
        ears_acc = _pick(rnd, ["hoops", "studs", "studs", "none", "hoops"])
        glasses = _pick(rnd, ["none", "none", "none", "round", "rect"])
        top = _pick(rnd, ["crew", "vneck", "turtleneck", "tank", "jacket", "hoodie"])
    elif gender == "man":
        style = _pick(rnd, HAIR_MAN)
        beard = _pick(rnd, ["none", "none", "stubble", "stubble", "beard", "mustache"])
        ears_acc = _pick(rnd, ["none", "none", "none", "studs"])
        glasses = _pick(rnd, ["none", "none", "rect", "none", "round"])
        top = _pick(rnd, ["crew", "collar", "jacket", "hoodie", "turtleneck", "vneck"])
    else:
        style = _pick(rnd, HAIR_NB)
        beard = _pick(rnd, ["none", "none", "none", "stubble"])
        ears_acc = _pick(rnd, ["none", "hoops", "studs", "none"])
        glasses = _pick(rnd, ["none", "round", "none", "rect"])
        top = _pick(rnd, ["crew", "jacket", "hoodie", "turtleneck", "collar", "tank"])

    rx = 50 + rnd(10)
    ry = 62 + rnd(10)
    eye_y = 112 + rnd(4)
    eye_dx = 22 + rnd(5)
    mouth_y = 154 + rnd(4)
    smile = rnd(4)
    brow_lift = rnd(6) - 2
    blush = rnd(3) == 0
    lip = _darken(skin, 0.22) if gender != "woman" else _pick(rnd, ["#b56a6a", "#a85a62", "#c47a78", _darken(skin, 0.18)])
    metal = _pick(rnd, ["#e4c46a", "#d8d0c4", "#c0a060"])
    blush_c = _lighten("#c47a78", 0.1)

    iris_r = 5 + rnd(2)
    mouth = (
        f'<path d="M114 {mouth_y} Q128 {mouth_y + 6 + smile} 142 {mouth_y}" '
        f'fill="none" stroke="{lip}" stroke-width="3" stroke-linecap="round"/>'
        if smile < 3
        else f'<path d="M114 {mouth_y} Q128 {mouth_y - 4} 142 {mouth_y}" fill="none" stroke="{lip}" stroke-width="3" stroke-linecap="round"/>'
    )
    if smile == 1:
        mouth = (
            f'<path d="M112 {mouth_y} Q128 {mouth_y + 10} 144 {mouth_y}" fill="{lip}"/>'
            f'<path d="M118 {mouth_y + 1} Q128 {mouth_y + 6} 138 {mouth_y + 1}" fill="#f4e6e0" opacity="0.55"/>'
        )

    left_brow = f'<path d="M{128 - eye_dx - 14} {eye_y - 16 + brow_lift} Q{128 - eye_dx} {eye_y - 22} {128 - eye_dx + 12} {eye_y - 14}" fill="none" stroke="{_darken(hair)}" stroke-width="3.2" stroke-linecap="round"/>'
    right_brow = f'<path d="M{128 + eye_dx - 12} {eye_y - 14} Q{128 + eye_dx} {eye_y - 22} {128 + eye_dx + 14} {eye_y - 16 + brow_lift}" fill="none" stroke="{_darken(hair)}" stroke-width="3.2" stroke-linecap="round"/>'

    def draw_eye(cx: int) -> str:
        return (
            f'<ellipse cx="{cx}" cy="{eye_y}" rx="12" ry="8" fill="#f7f1ea"/>'
            f'<circle cx="{cx}" cy="{eye_y}" r="{iris_r + 1}" fill="{eye_color}"/>'
            f'<circle cx="{cx}" cy="{eye_y}" r="{max(3, iris_r - 2)}" fill="#120c08"/>'
            f'<circle cx="{cx + 2}" cy="{eye_y - 2}" r="2" fill="#fff" opacity="0.85"/>'
            f'<path d="M{cx - 12} {eye_y - 1} Q{cx} {eye_y - 10} {cx + 12} {eye_y - 1}" fill="none" stroke="{_darken(skin, 0.35)}" stroke-width="1.4"/>'
        )

    nose = (
        f'<path d="M128 {eye_y + 8} Q122 {eye_y + 24} 128 {eye_y + 28} Q134 {eye_y + 24} 128 {eye_y + 8}" '
        f'fill="{_darken(skin, 0.12)}"/>'
        f'<ellipse cx="124" cy="{eye_y + 28}" rx="3" ry="2.2" fill="{_darken(skin, 0.18)}" opacity="0.5"/>'
        f'<ellipse cx="132" cy="{eye_y + 28}" rx="3" ry="2.2" fill="{_darken(skin, 0.18)}" opacity="0.5"/>'
    )

    blush_svg = (
        f'<ellipse cx="{128 - eye_dx - 8}" cy="{eye_y + 22}" rx="10" ry="6" fill="{blush_c}" opacity="0.28"/>'
        f'<ellipse cx="{128 + eye_dx + 8}" cy="{eye_y + 22}" rx="10" ry="6" fill="{blush_c}" opacity="0.28"/>'
        if blush
        else ""
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-label="{name}">
  <defs>
    <linearGradient id="bg-{uid}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{bg_a}"/>
      <stop offset="100%" stop-color="{bg_b}"/>
    </linearGradient>
    <clipPath id="circ-{uid}"><circle cx="128" cy="128" r="128"/></clipPath>
  </defs>
  <g clip-path="url(#circ-{uid})">
    <rect width="256" height="256" fill="url(#bg-{uid})"/>
    <circle cx="128" cy="90" r="90" fill="#ffffff" opacity="0.06"/>
    {_hair_behind(style, hair, rx, ry)}
    {_clothes(top, cloth, skin)}
    <ellipse cx="70" cy="128" rx="10" ry="16" fill="{skin}"/>
    <ellipse cx="186" cy="128" rx="10" ry="16" fill="{skin}"/>
    <ellipse cx="128" cy="112" rx="{rx}" ry="{ry}" fill="{skin}"/>
    {blush_svg}
    {left_brow}{right_brow}
    {draw_eye(128 - eye_dx)}{draw_eye(128 + eye_dx)}
    {nose}
    {mouth}
    {_beard(beard, hair, skin)}
    {_hair_front(style, hair, rx)}
    {_glasses(glasses)}
    {_earrings(ears_acc, metal)}
  </g>
</svg>
'''


def portrait_url(email: str) -> str:
    return f"/static/uploads/portraits/{_slug(email)}.svg"


def write_portrait(email: str, name: str, gender: str) -> str:
    PORTRAITS_DIR.mkdir(parents=True, exist_ok=True)
    path = PORTRAITS_DIR / f"{_slug(email)}.svg"
    path.write_text(portrait_svg(email, name, gender), encoding="utf-8")
    return portrait_url(email)

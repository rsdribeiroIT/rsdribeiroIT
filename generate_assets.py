#!/usr/bin/env python3
"""Generate the SVG assets for the rsdribeiroIT profile README.

Deterministic: same inputs produce the same bytes. No external services, no
generated images. Palette and type come from rsribeiro.site
(build/app.*.css :root).

Chip widths are not estimated. SVG has no text layout engine, so every label is
measured in headless Chrome first (measure_text.py writes assets/metrics.json)
and the chip is sized from that number. Estimating by character count clipped
labels by up to 17px.

Run measure_text.py before this script, then: python generate_assets.py
Writes: assets/banner.svg, assets/divider.svg,
        assets/stack-light.svg, assets/stack-dark.svg
"""

from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "assets"
OUT.mkdir(parents=True, exist_ok=True)

FONT_SANS = (
    "DM Sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
    "Helvetica, Arial, sans-serif"
)
FONT_SERIF = "DM Serif Display, Georgia, 'Times New Roman', serif"

# --- palette, straight from the site's :root --------------------------------
TURQUOISE = "#40E0D0"
TURQUOISE_DARK = "#14706B"
NAVY = "#2C3E50"
INK = "#1F2A38"
MINT = "#E9F7EF"
SKY = "#C5E8F4"
BORDER = "#E2E8F0"
TEXT = "#334155"
MUTED = "#94A3B8"

# dark-theme counterparts, matched to GitHub's own dark surfaces
D_BG = "#161B22"
D_BORDER = "#30363D"
D_CHIP = "#21262D"
D_TEXT = "#C9D1D9"

CARD_W = 1280
CARD_H = 360

STACK_W = 900
PAD_X = 28
LABEL_GAP = 16
CHIP_H = 46
CHIP_GAP = 12
ROW_GAP = 30
CHIP_PAD_L = 30  # dot + its gap
CHIP_PAD_R = 16
DOT_R = 4
MIN_CHIP_W = 76
# GitHub does not load webfonts inside an SVG rendered as an image, so viewers
# fall back to their own sans. The metrics come from headless Chrome, which was
# already falling back; this headroom covers a different fallback being wider.
WIDTH_SAFETY = 1.08

GROUPS: list[tuple[str, list[str]]] = [
    ("Backend", ["PHP 8", "Symfony", "Laravel", "Doctrine", "REST APIs"]),
    ("Frontend", ["Vue 3", "TypeScript", "Tailwind", "Sass", "Vite"]),
    ("CMS and commerce", ["WordPress", "WooCommerce", "Elementor", "Custom themes"]),
    ("Data and delivery", ["MySQL", "Redis", "Docker", "Nginx", "GitHub Actions"]),
]


def load_metrics() -> dict[str, float]:
    path = OUT / "metrics.json"
    if not path.exists():
        raise SystemExit(
            "assets/metrics.json missing. Run measure_text.py first; "
            "chip widths cannot be guessed."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: float(v) for k, v in data["widths"].items()}


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text_width(label: str, size: int, weight: int, widths: dict[str, float]) -> float:
    key = f"{label}|{size}|{weight}"
    if key not in widths:
        raise SystemExit(f"label not measured: {key!r}. Add it to measure_text.py.")
    return widths[key]


def chip_width(label: str, size: int, widths: dict[str, float]) -> float:
    return max(MIN_CHIP_W, text_width(label, size, 400, widths) * WIDTH_SAFETY + CHIP_PAD_L + CHIP_PAD_R)


def banner(widths: dict[str, float]) -> str:
    """Hero card. Dark by design, so one file covers both GitHub themes."""
    # badge geometry from the measured bold text, so nothing clips
    badges = [
        ("Symfony", TURQUOISE, INK),
        ("Vue", MINT, TURQUOISE_DARK),
        ("WordPress", MINT, TURQUOISE_DARK),
        ("MySQL", SKY, INK),
    ]
    badge_w = {
        label: max(96.0, text_width(label, 16, 700, widths) * WIDTH_SAFETY + 34)
        for label, _, _ in badges
    }
    row1 = badges[:2]
    row2 = badges[2:]
    badge_svg: list[str] = []
    for row_index, row in enumerate((row1, row2)):
        total = sum(badge_w[label] for label, _, _ in row) + 12 * (len(row) - 1)
        x = CARD_W - 92 - total
        y = 122 + row_index * 54
        for label, fill, text_fill in row:
            w = badge_w[label]
            badge_svg.append(
                f'      <rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="38" rx="19" fill="{fill}"/>'
            )
            badge_svg.append(
                f'      <text x="{x + w / 2:.1f}" y="{y + 24}" text-anchor="middle" fill="{text_fill}">{label}</text>'
            )
            x += w + 12
    badge_block = "\n".join(badge_svg)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{CARD_H}" viewBox="0 0 {CARD_W} {CARD_H}" role="img" aria-label="Ricardo Ribeiro, Symfony and Vue web developer in Faro, Portugal">
  <title>Ricardo Ribeiro, Symfony and Vue web developer in Faro, Portugal</title>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{INK}"/>
      <stop offset="1" stop-color="{NAVY}"/>
    </linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{TURQUOISE}"/>
      <stop offset="1" stop-color="{TURQUOISE_DARK}"/>
    </linearGradient>
    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{TURQUOISE}"/>
      <stop offset="1" stop-color="{TURQUOISE}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="round">
      <rect x="0" y="0" width="{CARD_W}" height="{CARD_H}" rx="22"/>
    </clipPath>
  </defs>

  <g clip-path="url(#round)">
    <rect width="{CARD_W}" height="{CARD_H}" fill="url(#bg)"/>
    <rect x="0" y="0" width="9" height="{CARD_H}" fill="url(#edge)"/>
    <circle cx="1176" cy="88" r="196" fill="{TURQUOISE}" opacity="0.07"/>
    <circle cx="1232" cy="322" r="124" fill="{TURQUOISE}" opacity="0.05"/>

    <text x="92" y="128" font-family="{FONT_SERIF}" font-size="70" fill="#FFFFFF">Ricardo Ribeiro</text>
    <text x="95" y="180" font-family="{FONT_SANS}" font-size="25" fill="{TURQUOISE}" letter-spacing="1.4">Symfony and Vue web developer</text>

    <rect x="95" y="214" width="470" height="3" rx="1.5" fill="url(#rule)"/>

    <text x="95" y="262" font-family="{FONT_SANS}" font-size="21" fill="{SKY}">Web apps, e-commerce and the automation in between.</text>
    <text x="95" y="298" font-family="{FONT_SANS}" font-size="21" fill="{MUTED}">Faro, Portugal. Open to remote work.</text>

    <g font-family="{FONT_SANS}" font-size="16" font-weight="700">
{badge_block}
    </g>
  </g>
</svg>
"""


def stack(dark: bool, widths: dict[str, float]) -> str:
    """The 'tools I reach for' card, in both GitHub themes."""
    bg = D_BG if dark else "#F7FAF9"
    border = D_BORDER if dark else BORDER
    label_colour = D_TEXT if dark else NAVY
    chip_bg = D_CHIP if dark else "#FFFFFF"
    chip_border = D_BORDER if dark else BORDER
    chip_text = D_TEXT if dark else TEXT
    dot = TURQUOISE if dark else TURQUOISE_DARK

    label_w = max(
        text_width(name, 16, 700, widths) * WIDTH_SAFETY + CHIP_PAD_L
        for name, _ in GROUPS
    )
    chips_x = PAD_X + label_w + LABEL_GAP

    rows: list[str] = []
    y = 26
    widest = 0.0
    for name, skills in GROUPS:
        rows.append(
            f'  <text x="{PAD_X}" y="{y + 30}" font-family="{FONT_SANS}" '
            f'font-size="16" font-weight="700" fill="{label_colour}">{esc(name)}</text>'
        )
        x = chips_x
        for skill in skills:
            w = chip_width(skill, 15, widths)
            rows.append(
                f'  <rect x="{x:.2f}" y="{y}" width="{w:.2f}" height="{CHIP_H}" '
                f'rx="{CHIP_H / 2}" fill="{chip_bg}" stroke="{chip_border}"/>'
            )
            rows.append(
                f'  <circle cx="{x + 17:.2f}" cy="{y + CHIP_H / 2}" r="{DOT_R}" fill="{dot}"/>'
            )
            rows.append(
                f'  <text x="{x + CHIP_PAD_L:.2f}" y="{y + 30}" font-family="{FONT_SANS}" '
                f'font-size="15" fill="{chip_text}">{esc(skill)}</text>'
            )
            x += w + CHIP_GAP
        widest = max(widest, x - CHIP_GAP)
        y += CHIP_H + ROW_GAP

    height = y - ROW_GAP + 26
    if widest > STACK_W - PAD_X:
        raise SystemExit(
            f"widest row ends at {widest:.1f}, card is {STACK_W} wide. "
            "Shorten a label or widen the card."
        )

    body = "\n".join(rows)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{STACK_W}" height="{height}" viewBox="0 0 {STACK_W} {height}" role="img" aria-label="Tools and platforms Ricardo builds with">
  <title>Tools and platforms Ricardo builds with</title>
  <rect x="1" y="1" width="{STACK_W - 2}" height="{height - 2}" rx="18" fill="{bg}" stroke="{border}"/>
{body}
</svg>
"""


def main() -> None:
    widths = load_metrics()
    files = {
        "banner.svg": banner(widths),
        "stack-light.svg": stack(dark=False, widths=widths),
        "stack-dark.svg": stack(dark=True, widths=widths),
    }
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"{name:20} {(OUT / name).stat().st_size:>6} bytes")


if __name__ == "__main__":
    main()

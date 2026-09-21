#!/usr/bin/env python3
"""Measure real rendered text widths with headless Chrome.

Why: SVG has no text layout, so chip and badge widths must come from actual font
metrics. Estimating from character count clipped labels by up to 17px.

Renders every label at its real size and weight, measures getBBox(), and writes
assets/metrics.json keyed as "label|size|weight".

Usage: python measure_text.py
"""

from __future__ import annotations

import html as html_mod
import json
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "assets"
OUT.mkdir(parents=True, exist_ok=True)

CHROME_CANDIDATES = [
    r"C:/Program Files/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

FONT_SANS = (
    "DM Sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
    "Helvetica, Arial, sans-serif"
)

# (label, size, weight) for everything the generator lays out
TARGETS: list[tuple[str, int, int]] = [
    # stack card: group labels
    ("Backend", 16, 700),
    ("Frontend", 16, 700),
    ("CMS and commerce", 16, 700),
    ("Data and delivery", 16, 700),
    # stack card: chips
    ("PHP 8", 15, 400),
    ("Symfony", 15, 400),
    ("Laravel", 15, 400),
    ("Doctrine", 15, 400),
    ("REST APIs", 15, 400),
    ("Vue 3", 15, 400),
    ("TypeScript", 15, 400),
    ("Tailwind", 15, 400),
    ("Sass", 15, 400),
    ("Vite", 15, 400),
    ("WordPress", 15, 400),
    ("WooCommerce", 15, 400),
    ("Elementor", 15, 400),
    ("Custom themes", 15, 400),
    ("MySQL", 15, 400),
    ("Redis", 15, 400),
    ("Docker", 15, 400),
    ("Nginx", 15, 400),
    ("GitHub Actions", 15, 400),
    # banner badges
    ("Symfony", 16, 700),
    ("Vue", 16, 700),
    ("WordPress", 16, 700),
    ("MySQL", 16, 700),
]


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if pathlib.Path(c).exists():
            return c
    raise SystemExit("no chrome/chromium found; cannot measure text")


def build_probe() -> str:
    items = []
    for label, size, weight in TARGETS:
        key = f"{label}|{size}|{weight}"
        items.append(
            f'<text data-key="{html_mod.escape(key)}" x="0" y="{size}" '
            f'font-family="{FONT_SANS}" font-size="{size}" '
            f'font-weight="{weight}">{html_mod.escape(label)}</text>'
        )
    script = r"""
var out=[];
document.querySelectorAll('text').forEach(function(t){
  var b=t.getBBox();
  out.push(t.dataset.key+'='+b.width.toFixed(3)+'|'+b.height.toFixed(3));
});
document.getElementById('report').textContent=out.join(' ~ ');
"""
    return (
        '<!doctype html><meta charset="utf-8"><style>body{margin:0}</style>'
        '<div id="report">x</div>'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="2400">{"".join(items)}</svg>'
        f"<script>{script}</script>"
    )


def main() -> None:
    probe = HERE / "probe_metrics.html"
    probe.write_text(build_probe(), encoding="utf-8")
    proc = subprocess.run(
        [find_chrome(), "--headless=new", "--disable-gpu", "--no-sandbox",
         "--virtual-time-budget=6000", "--dump-dom", probe.as_uri()],
        capture_output=True, text=True, timeout=180,
    )
    m = re.search(r"""id=['"]report['"]>(.*?)</div>""", proc.stdout, re.S)
    if not m:
        raise SystemExit("metric probe returned no report")

    widths: dict[str, float] = {}
    for chunk in html_mod.unescape(m.group(1)).split(" ~ "):
        chunk = chunk.strip()
        if "=" not in chunk:
            continue
        key, val = chunk.split("=", 1)
        w, _ = val.split("|")
        widths[key] = float(w)

    missing = [f"{l}|{s}|{w}" for l, s, w in TARGETS if f"{l}|{s}|{w}" not in widths]
    if missing:
        raise SystemExit(f"probe missed {len(missing)} labels: {missing[:5]}")

    (OUT / "metrics.json").write_text(
        json.dumps({"widths": widths, "font": FONT_SANS}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"measured {len(widths)} labels -> assets/metrics.json")
    for k in sorted(widths):
        print(f"  {k:30} {widths[k]:>8.2f}")


if __name__ == "__main__":
    main()

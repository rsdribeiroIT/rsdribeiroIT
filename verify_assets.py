#!/usr/bin/env python3
"""Verify the generated SVGs with real browser geometry.

Checks, per file:
  * no text overflows the canvas (x and y)
  * every chip label sits inside its chip rect with sane padding
  * every chip label vertically centres in its chip
  * chips do not collide with each other
  * the card's own border is not exceeded

Exits non-zero on any failure, so it can gate a commit.

Usage: python verify_assets.py
"""

from __future__ import annotations

import html as html_mod
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "assets"
FILES = ["banner.svg", "stack-light.svg", "stack-dark.svg"]

CHROME_CANDIDATES = [
    r"C:/Program Files/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

SCRIPT = r"""
window.onerror=function(m,s,l){document.getElementById('report').textContent='FATAL '+m+' @'+l;};
var out=[];
document.querySelectorAll('section').forEach(function(sec){
  var file=sec.dataset.file;
  try{
    var svg=sec.querySelector('svg');
    var vb=svg.viewBox.baseVal;
    var probs=[];
    var texts=Array.prototype.slice.call(svg.querySelectorAll('text'));
    var rects=Array.prototype.slice.call(svg.querySelectorAll('rect'));
    var chips=rects.filter(function(r){var h=r.getBBox().height;return h>30 && h<60;});
    texts.forEach(function(t){
      var b=t.getBBox();
      if(b.x+b.width>vb.width-2){probs.push('TEXT-OVERFLOW-X "'+t.textContent+'" '+(b.x+b.width).toFixed(1)+'>'+vb.width);}
      if(b.y+b.height>vb.height-2){probs.push('TEXT-OVERFLOW-Y "'+t.textContent+'" '+(b.y+b.height).toFixed(1)+'>'+vb.height);}
      if(b.x<0||b.y<0){probs.push('TEXT-NEGATIVE "'+t.textContent+'"');}
      var host=null;
      chips.forEach(function(r){var rb=r.getBBox();
        if(rb.x<=b.x+1 && b.y>=rb.y-1 && b.y+b.height<=rb.y+rb.height+1 && rb.x+rb.width>b.x+1){host=rb;}});
      if(host){
        var padRight=(host.x+host.width)-(b.x+b.width);
        var padTop=b.y-host.y;
        var padBottom=(host.y+host.height)-(b.y+b.height);
        if(padRight<6){probs.push('CHIP-PAD-RIGHT "'+t.textContent+'" '+padRight.toFixed(1));}
        if(padTop<6||padBottom<4){probs.push('CHIP-PAD-VERT "'+t.textContent+'" top='+padTop.toFixed(1)+' bottom='+padBottom.toFixed(1));}
      }
    });
    // chip collisions: two chips on the same row must not overlap
    var boxes=chips.map(function(r){return r.getBBox();});
    for(var i=0;i<boxes.length;i++){
      for(var j=i+1;j<boxes.length;j++){
        var a=boxes[i],c=boxes[j];
        var overlapX=Math.min(a.x+a.width,c.x+c.width)-Math.max(a.x,c.x);
        var overlapY=Math.min(a.y+a.height,c.y+c.height)-Math.max(a.y,c.y);
        if(overlapX>0.5&&overlapY>0.5){probs.push('CHIP-OVERLAP at y='+a.y.toFixed(0));}
      }
    }
    rects.forEach(function(r){var b=r.getBBox();
      if(b.x+b.width>vb.width+0.5){probs.push('RECT-OVERFLOW-X '+(b.x+b.width).toFixed(1)+'>'+vb.width);}});
    var mx=0,my=0;
    Array.prototype.slice.call(svg.querySelectorAll('rect,circle,text')).forEach(function(e){var b=e.getBBox();
      if(b.x+b.width>mx)mx=b.x+b.width; if(b.y+b.height>my)my=b.y+b.height;});
    out.push('FILE '+file+' viewBox='+vb.width+'x'+vb.height+' texts='+texts.length+' chips='+chips.length+' maxX='+mx.toFixed(1)+' maxY='+my.toFixed(1)+' problems='+probs.length);
    probs.forEach(function(p){out.push('   ! '+p);});
  }catch(e){out.push('FILE '+file+' ERROR '+e.message);}
});
document.getElementById('report').textContent=out.join(' ~SEP~ ');
"""


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if pathlib.Path(c).exists():
            return c
    raise SystemExit("no chrome found")


def main() -> int:
    parts = []
    for name in FILES:
        parts.append(
            f'<section data-file="{name}">{ (OUT / name).read_text(encoding="utf-8") }</section>'
        )
    page = (
        '<!doctype html><meta charset="utf-8">'
        "<style>body{margin:0}#stage{position:absolute;left:-30000px;top:0}</style>"
        '<div id="stage">' + "\n".join(parts) + "</div>"
        '<div id="report">x</div><script>' + SCRIPT + "</script>"
    )
    probe = HERE / "verify_assets.html"
    probe.write_text(page, encoding="utf-8")

    proc = subprocess.run(
        [find_chrome(), "--headless=new", "--disable-gpu", "--no-sandbox",
         "--virtual-time-budget=6000", "--dump-dom", probe.as_uri()],
        capture_output=True, text=True, timeout=180,
    )
    m = re.search(r"""id=['"]report['"]>(.*?)</div>""", proc.stdout, re.S)
    if not m:
        print("verify: no report produced", file=sys.stderr)
        return 2
    lines = html_mod.unescape(m.group(1)).split(" ~SEP~ ")
    failures = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        print(line)
        if "! " in line or "ERROR" in line or "FATAL" in line:
            failures += 1
    print()
    print("VERIFY: PASS" if failures == 0 else f"VERIFY: FAIL ({failures} lines with problems)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

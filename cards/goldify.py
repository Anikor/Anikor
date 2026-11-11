"""Fetch a socialify card and give its background a muted gold circuit pattern (text and icons stay white).

python cards/goldify.py Anikor/hackathon_ZTS_2026 cards/zts2026.svg
"""
import base64
import re
import sys
import time
import urllib.request

PARAMS = "description=1&font=Source%20Code%20Pro&language=1&name=1&owner=1&pattern=Circuit%20Board&theme=Dark"
BG = "#12100c"
PATTERN = "#a88f5e"
OPACITY = "0.2"


def recolor_inner(match):
    inner = base64.b64decode(match.group(1)).decode()
    inner = inner.replace('fill="#eaeaea"', f'fill="{PATTERN}"').replace('fill-opacity="0.2"', f'fill-opacity="{OPACITY}"')
    return 'href="data:image/svg+xml;base64,' + base64.b64encode(inner.encode()).decode() + '"'


def goldify(svg):
    svg = re.sub(r'href="data:image/svg\+xml;base64,([^"]+)"', recolor_inner, svg)
    return svg.replace('fill="#000" transform', f'fill="{BG}" transform')


if __name__ == "__main__":
    repo, out = sys.argv[1], sys.argv[2]
    req = urllib.request.Request(f"https://socialify.git.ci/{repo}/image?{PARAMS}&_={int(time.time())}", headers={"User-Agent": "goldify"})
    svg = urllib.request.urlopen(req, timeout=30).read().decode()
    open(out, "w").write(goldify(svg))

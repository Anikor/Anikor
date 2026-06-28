#!/usr/bin/env python3
import json
import urllib.request
from datetime import datetime, timezone, timedelta

USERNAME = "Anikor"

QUERY = """
query($username: String!) {
  matchedUser(username: $username) {
    userCalendar {
      submissionCalendar
    }
  }
}
"""

def fetch_heatmap():
    payload = json.dumps({"query": QUERY, "variables": {"username": USERNAME}}).encode()
    req = urllib.request.Request(
        "https://leetcode.com/graphql",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    raw = data["data"]["matchedUser"]["userCalendar"]["submissionCalendar"]
    return {int(k): int(v) for k, v in json.loads(raw).items()}

def build_svg(cal: dict) -> str:
    CARD_W   = 495
    PAD      = 20
    CELL     = 10
    CELL_GAP = 2
    STEP     = CELL + CELL_GAP
    WEEKS    = 53
    DAYS     = 7
    INNER_W  = CARD_W - PAD * 2
    GRID_W   = WEEKS * STEP - CELL_GAP
    GRID_H   = DAYS  * STEP - CELL_GAP
    CARD_H   = 255

    BG       = "#1a1a2e"
    BORDER   = "#2d2d44"
    TEXT_PRI = "#e0e0e0"
    TEXT_SEC = "#aaaabb"
    LOGO_ORG = "#ffa116"
    DIV_COL  = "#2d2d44"

    COLORS   = ["#1e2030", "#003820", "#006d32", "#26a641", "#39d353"]

    def color(n):
        if n == 0: return COLORS[0]
        if n == 1: return COLORS[1]
        if n <= 3: return COLORS[2]
        if n <= 6: return COLORS[3]
        return COLORS[4]

    today       = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    days_to_sat = (5 - today.weekday()) % 7
    week_end    = today + timedelta(days=days_to_sat)
    start       = week_end - timedelta(weeks=WEEKS) + timedelta(days=1)

    cells = []
    d = start
    while d <= week_end:
        ts = int(d.replace(tzinfo=timezone.utc).timestamp())
        cells.append((d, cal.get(ts, 0)))
        d += timedelta(days=1)

    col_offset = (start.weekday() + 1) % 7

    month_labels = []
    last_m = -1
    for i, (day, _) in enumerate(cells):
        col = (i + col_offset) // 7
        if day.month != last_m and col < WEEKS:
            month_labels.append((col, day.strftime("%b")))
            last_m = day.month

    y_header  = PAD
    y_divider = y_header + 46
    y_section = y_divider + 14
    y_months  = y_section + 22
    y_grid    = y_months + 14
    y_legend  = y_grid + GRID_H + 8

    grid_x    = PAD + (INNER_W - GRID_W) // 2

    rects = []
    for i, (day, count) in enumerate(cells):
        idx = i + col_offset
        cx  = grid_x + (idx // 7) * STEP
        cy  = y_grid  + (idx  % 7) * STEP
        c   = color(count)
        tip = f"{day.strftime('%Y-%m-%d')}: {count}"
        rects.append(
            f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="2" fill="{c}">'
            f'<title>{tip}</title></rect>'
        )

    month_svgs = "".join(
        f'<text x="{grid_x + col*STEP}" y="{y_months + 10}" '
        f'font-size="10" fill="{TEXT_SEC}" font-family="monospace">{lbl}</text>'
        for col, lbl in month_labels
    )

    lc_w     = CELL
    lc_gap   = 3
    lc_total = len(COLORS) * (lc_w + lc_gap) - lc_gap
    lc_x0    = CARD_W - PAD - lc_total - 34
    lc_y     = y_legend + 2

    legend_cells = "".join(
        f'<rect x="{lc_x0 + i*(lc_w+lc_gap)}" y="{lc_y}" width="{lc_w}" height="{lc_w}" rx="2" fill="{c}"/>'
        for i, c in enumerate(COLORS)
    )

    lx = PAD + 2
    ly = y_header + 2
    logo = (
        f'<polygon points="{lx+8},{ly+2} {lx+4},{ly+6} {lx+8},{ly+10} {lx+6},{ly+12} {lx+1},{ly+6} {lx+6},{ly+0}" fill="{LOGO_ORG}"/>'
        f'<polygon points="{lx+9},{ly+4} {lx+14},{ly+9} {lx+9},{ly+14} {lx+11},{ly+16} {lx+17},{ly+9} {lx+11},{ly+2}" fill="{LOGO_ORG}"/>'
        f'<rect x="{lx+1}" y="{ly+18}" width="14" height="3" rx="1.5" fill="#888"/>'
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{CARD_W}" height="{CARD_H}" viewBox="0 0 {CARD_W} {CARD_H}">\n'
        f'<rect width="{CARD_W}" height="{CARD_H}" rx="8" '
        f'fill="{BG}" stroke="{BORDER}" stroke-width="1.5"/>\n'
        f'{logo}\n'
        f'<text x="{PAD+28}" y="{y_header+22}" font-size="17" font-weight="bold" '
        f'fill="{TEXT_PRI}" font-family="monospace">{USERNAME}</text>\n'
        f'<line x1="{PAD}" y1="{y_divider}" x2="{CARD_W-PAD}" y2="{y_divider}" '
        f'stroke="{DIV_COL}" stroke-width="1"/>\n'
        f'<text x="{PAD}" y="{y_section+10}" font-size="11" '
        f'fill="{TEXT_SEC}" font-family="monospace">Heatmap (Last 52 Weeks)</text>\n'
        f'{month_svgs}\n'
        f'{"".join(rects)}\n'
        f'{legend_cells}\n'
        f'<text x="{lc_x0-5}" y="{lc_y+9}" text-anchor="end" '
        f'font-size="10" fill="{TEXT_SEC}" font-family="monospace">Less</text>\n'
        f'<text x="{lc_x0+lc_total+5}" y="{lc_y+9}" '
        f'font-size="10" fill="{TEXT_SEC}" font-family="monospace">More</text>\n'
        f'</svg>'
    )
    return svg


if __name__ == "__main__":
    cal = fetch_heatmap()
    svg = build_svg(cal)
    with open("leetcode-heatmap.svg", "w") as f:
        f.write(svg)
    print("✓ leetcode-heatmap.svg written")    PAD       = 20
    HEADER_H  = 50
    DIVIDER   = 1
    LABEL_H   = 16
    GAP_AFTER_LABEL = 8
    CELL      = 10
    CELL_GAP  = 2
    STEP      = CELL + CELL_GAP
    WEEKS     = 53
    DAYS      = 7
    MONTH_H   = 14
    GRID_W    = WEEKS * STEP - CELL_GAP
    GRID_H    = DAYS  * STEP - CELL_GAP
    LEGEND_H  = 16
    FOOTER_H  = LEGEND_H + 8

    INNER_W   = CARD_W - PAD * 2
    CARD_H    = PAD + HEADER_H + 1 + PAD//2 + LABEL_H + GAP_AFTER_LABEL + MONTH_H + GRID_H + 10 + FOOTER_H + PAD

    BG        = "#1a1a2e"
    BORDER    = "#2d2d44"
    TEXT_PRI  = "#ffffff"
    TEXT_SEC  = "#aaaabb"
    LOGO_COL  = "#ffa116"
    DIV_COL   = "#2d2d44"

    COLORS = ["#1e2030", "#003820", "#006d32", "#26a641", "#39d353"]

    def color(n):
        if n == 0: return COLORS[0]
        if n == 1: return COLORS[1]
        if n <= 3: return COLORS[2]
        if n <= 6: return COLORS[3]
        return COLORS[4]

    today    = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    days_to_sat = (5 - today.weekday()) % 7
    week_end = today + timedelta(days=days_to_sat)
    start    = week_end - timedelta(weeks=WEEKS) + timedelta(days=1)

    cells = []
    d = start
    while d <= week_end:
        ts = int(d.replace(tzinfo=timezone.utc).timestamp())
        cells.append((d, cal.get(ts, 0)))
        d += timedelta(days=1)

    col_offset = (start.weekday() + 1) % 7

    month_labels = []
    last_m = -1
    for i, (day, _) in enumerate(cells):
        col = (i + col_offset) // 7
        if day.month != last_m and col < WEEKS:
            month_labels.append((col, day.strftime("%b")))
            last_m = day.month

    y_header  = PAD
    y_divider = y_header + HEADER_H + 6
    y_label   = y_divider + DIVIDER + PAD//2
    y_months  = y_label + LABEL_H + GAP_AFTER_LABEL
    y_grid    = y_months + MONTH_H
    y_legend  = y_grid + GRID_H + 10

    grid_x = PAD + (INNER_W - GRID_W) // 2

    rects = []
    for i, (day, count) in enumerate(cells):
        idx = i + col_offset
        cx  = grid_x + (idx // 7) * STEP
        cy  = y_grid  + (idx  % 7) * STEP
        c   = color(count)
        tip = f"{day.strftime('%Y-%m-%d')}: {count} submission{'s' if count!=1 else ''}"
        rects.append(
            f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" '
            f'rx="2" fill="{c}"><title>{tip}</title></rect>'
        )

    month_svgs = "".join(
        f'<text x="{grid_x + col*STEP}" y="{y_months + 10}" '
        f'font-size="10" fill="{TEXT_SEC}" '
        f'font-family="\'Fira Code\',\'Courier New\',monospace">{lbl}</text>'
        for col, lbl in month_labels
    )

    lc_w      = CELL
    lc_gap    = 3
    lc_total  = len(COLORS) * (lc_w + lc_gap) - lc_gap
    lc_x0     = CARD_W - PAD - lc_total - 36
    lc_y      = y_legend + 2

    legend_cells = "".join(
        f'<rect x="{lc_x0 + i*(lc_w+lc_gap)}" y="{lc_y}" '
        f'width="{lc_w}" height="{lc_w}" rx="2" fill="{c}"/>'
        for i, c in enumerate(COLORS)
    )
    legend_less = (
        f'<text x="{lc_x0 - 5}" y="{lc_y + 9}" text-anchor="end" '
        f'font-size="10" fill="{TEXT_SEC}" '
        f'font-family="\'Fira Code\',\'Courier New\',monospace">Less</text>'
    )
    legend_more = (
        f'<text x="{lc_x0 + lc_total + 5}" y="{lc_y + 9}" '
        f'font-size="10" fill="{TEXT_SEC}" '
        f'font-family="\'Fira Code\',\'Courier New\',monospace">More</text>'
    )

    lx, ly = PAD, y_header + 6
    logo = f'''<g transform="translate({lx},{ly}) scale(0.9)">
      <path d="M13.7,9.3 L8.5,14.5 C8.1,14.9 7.5,14.9 7.1,14.5 L5.4,12.8 C5.0,12.4 5.0,11.8 5.4,11.4 L9.3,7.5 L5.4,3.6 C5.0,3.2 5.0,2.6 5.4,2.2 L7.1,0.5 C7.5,0.1 8.1,0.1 8.5,0.5 L13.7,5.7 C14.1,6.1 14.1,6.7 13.7,7.1 Z" fill="{LOGO_COL}"/>
      <rect x="2" y="16" width="12" height="3" rx="1.5" fill="#b3b3b3"/>
    </g>'''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{CARD_H}" viewBox="0 0 {CARD_W} {CARD_H}">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&amp;display=swap');
    </style>
  </defs>
  <rect width="{CARD_W}" height="{CARD_H}" rx="8" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>
  {logo}
  <text x="{PAD + 26}" y="{y_header + 22}"
    font-size="18" font-weight="600" fill="{TEXT_PRI}"
    font-family="'Fira Code','Courier New',monospace">{USERNAME}</text>
  <line x1="{PAD}" y1="{y_divider}" x2="{CARD_W - PAD}" y2="{y_divider}"
    stroke="{DIV_COL}" stroke-width="1"/>
  <text x="{PAD}" y="{y_label + 12}"
    font-size="12" fill="{TEXT_SEC}"
    font-family="'Fira Code','Courier New',monospace">Heatmap (Last 52 Weeks)</text>
  {month_svgs}
  {"".join(rects)}
  {legend_cells}
  {legend_less}
  {legend_more}
</svg>'''

    return svg


if __name__ == "__main__":
    cal = fetch_heatmap()
    svg = build_svg(cal)
    with open("leetcode-heatmap.svg", "w") as f:
        f.write(svg)
    print("✓ leetcode-heatmap.svg written")

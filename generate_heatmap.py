#!/usr/bin/env python3
import json
import urllib.request
import urllib.error
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
    CELL    = 11
    GAP     = 2
    STEP    = CELL + GAP
    WEEKS   = 53
    DAYS    = 7
    TOP_PAD = 24
    LEFT_PAD = 0
    BOT_PAD = 18
    W       = LEFT_PAD + WEEKS * STEP
    H       = TOP_PAD + DAYS * STEP + BOT_PAD

    COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    def color(n):
        if n == 0: return COLORS[0]
        if n == 1: return COLORS[1]
        if n <= 3: return COLORS[2]
        if n <= 6: return COLORS[3]
        return COLORS[4]

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    days_to_sat = (5 - today.weekday()) % 7
    week_end = today + timedelta(days=days_to_sat)
    start = week_end - timedelta(weeks=WEEKS) + timedelta(days=1)

    cells = []
    d = start
    while d <= week_end:
        ts = int(d.replace(tzinfo=timezone.utc).timestamp())
        cells.append((d, cal.get(ts, 0)))
        d += timedelta(days=1)

    col_offset = start.weekday() + 1
    col_offset = col_offset % 7

    month_labels = []
    last_m = -1
    for i, (day, _) in enumerate(cells):
        col = (i + col_offset) // 7
        if day.month != last_m and col < WEEKS:
            month_labels.append((col, day.strftime("%b")))
            last_m = day.month

    rects = []
    for i, (day, count) in enumerate(cells):
        idx = i + col_offset
        cx  = LEFT_PAD + (idx // 7) * STEP
        cy  = TOP_PAD  + (idx  % 7) * STEP
        c   = color(count)
        tip = f"{day.strftime('%Y-%m-%d')}: {count}"
        rects.append(
            f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" '
            f'rx="2" fill="{c}"><title>{tip}</title></rect>'
        )

    month_svgs = "".join(
        f'<text x="{LEFT_PAD + col*STEP}" y="{TOP_PAD - 6}" '
        f'font-size="9" fill="#768390" font-family="\'Fira Code\',monospace">{lbl}</text>'
        for col, lbl in month_labels
    )

    legend_y  = TOP_PAD + DAYS * STEP + 5
    legend_x0 = W - len(COLORS) * (CELL + 2) - 36
    legend_cells = "".join(
        f'<rect x="{legend_x0 + i*(CELL+2)}" y="{legend_y}" '
        f'width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>'
        for i, c in enumerate(COLORS)
    )
    legend_less = (
        f'<text x="{legend_x0 - 4}" y="{legend_y + 9}" '
        f'font-size="9" fill="#768390" text-anchor="end" '
        f'font-family="\'Fira Code\',monospace">Less</text>'
    )
    legend_more = (
        f'<text x="{legend_x0 + len(COLORS)*(CELL+2) + 2}" y="{legend_y + 9}" '
        f'font-size="9" fill="#768390" '
        f'font-family="\'Fira Code\',monospace">More</text>'
    )
    updated = (
        f'<text x="0" y="{legend_y + 9}" '
        f'font-size="9" fill="#444c56" '
        f'font-family="\'Fira Code\',monospace">'
        f'Updated {today.strftime("%Y-%m-%d")}</text>'
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" rx="6" fill="#0d1117"/>
  {month_svgs}
  {"".join(rects)}
  {legend_cells}
  {legend_less}
  {legend_more}
  {updated}
</svg>"""
    return svg


if __name__ == "__main__":
    cal = fetch_heatmap()
    svg = build_svg(cal)
    with open("leetcode-heatmap.svg", "w") as f:
        f.write(svg)
    print("✓ leetcode-heatmap.svg written")

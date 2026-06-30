#!/usr/bin/env python3
import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path


USERNAME = "Anikor"
OUTPUT_FILE = "leetcode-heatmap.svg"

GRAPHQL_URL = "https://leetcode.com/graphql"
QUERY = """
query userProfileCalendar($username: String!) {
  matchedUser(username: $username) {
    username
    userCalendar {
      submissionCalendar
    }
  }
}
"""


COLORS = ["#1e2030", "#003820", "#006d32", "#26a641", "#39d353"]


def fetch_heatmap(username: str) -> dict[int, int]:
    payload = json.dumps(
        {
            "query": QUERY,
            "variables": {"username": username},
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        GRAPHQL_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://leetcode.com",
            "Referer": f"https://leetcode.com/u/{username}/",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            ),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"LeetCode HTTP error: {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LeetCode connection error: {exc.reason}") from exc

    if "errors" in data:
        raise RuntimeError(f"LeetCode GraphQL error: {data['errors']}")

    matched_user = data.get("data", {}).get("matchedUser")
    if not matched_user:
        raise RuntimeError(f"LeetCode user not found: {username}")

    raw_calendar = matched_user.get("userCalendar", {}).get("submissionCalendar")
    if not raw_calendar:
        return {}

    parsed = json.loads(raw_calendar)
    return {int(timestamp): int(count) for timestamp, count in parsed.items()}


def color_for_count(count: int) -> str:
    if count <= 0:
        return COLORS[0]
    if count == 1:
        return COLORS[1]
    if count <= 3:
        return COLORS[2]
    if count <= 6:
        return COLORS[3]
    return COLORS[4]


def build_svg(calendar: dict[int, int]) -> str:
    card_w = 495
    pad = 20

    cell = 10
    cell_gap = 2
    step = cell + cell_gap
    weeks = 53
    days = 7

    grid_w = weeks * step - cell_gap
    grid_h = days * step - cell_gap

    card_h = 255
    inner_w = card_w - pad * 2

    bg = "#1a1a2e"
    border = "#2d2d44"
    text_primary = "#ffffff"
    text_secondary = "#aaaabb"
    orange = "#ffa116"
    divider = "#2d2d44"

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # End the grid on Saturday, like GitHub-style contribution calendars.
    days_to_saturday = (5 - today.weekday()) % 7
    week_end = today + timedelta(days=days_to_saturday)
    start = week_end - timedelta(weeks=weeks) + timedelta(days=1)

    cells: list[tuple[datetime, int]] = []
    current_day = start
    while current_day <= week_end:
        timestamp = int(current_day.timestamp())
        cells.append((current_day, calendar.get(timestamp, 0)))
        current_day += timedelta(days=1)

    # Python: Monday=0, Sunday=6. SVG heatmap: Sunday=0.
    col_offset = (start.weekday() + 1) % 7

    month_labels: list[tuple[int, str]] = []
    last_month = -1
    for i, (day, _) in enumerate(cells):
        col = (i + col_offset) // 7
        if day.month != last_month and col < weeks:
            month_labels.append((col, day.strftime("%b")))
            last_month = day.month

    y_header = pad
    y_divider = y_header + 46
    y_title = y_divider + 28
    y_months = y_title + 22
    y_grid = y_months + 14
    y_legend = y_grid + grid_h + 10
    grid_x = pad + (inner_w - grid_w) // 2

    total_submissions = sum(calendar.values())
    active_days = sum(1 for _, count in cells if count > 0)

    month_svg = "\n".join(
        f'<text x="{grid_x + col * step}" y="{y_months}" '
        f'fill="{text_secondary}" font-size="9" font-family="Inter, Arial, sans-serif">'
        f'{escape(label)}</text>'
        for col, label in month_labels
    )

    rects = []
    for i, (day, count) in enumerate(cells):
        idx = i + col_offset
        x = grid_x + (idx // 7) * step
        y = y_grid + (idx % 7) * step
        fill = color_for_count(count)
        submissions_word = "submission" if count == 1 else "submissions"
        title = f"{day.strftime('%Y-%m-%d')}: {count} {submissions_word}"

        rects.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
            f'fill="{fill}"><title>{escape(title)}</title></rect>'
        )

    legend_cell = cell
    legend_gap = 3
    legend_total_w = len(COLORS) * (legend_cell + legend_gap) - legend_gap
    legend_x = card_w - pad - legend_total_w - 36
    legend_y = y_legend + 2

    legend_svg = "\n".join(
        f'<rect x="{legend_x + i * (legend_cell + legend_gap)}" y="{legend_y}" '
        f'width="{legend_cell}" height="{legend_cell}" rx="2" fill="{color}" />'
        for i, color in enumerate(COLORS)
    )

    logo_x = pad + 2
    logo_y = y_header + 2

    return f'''<svg width="{card_w}" height="{card_h}" viewBox="0 0 {card_w} {card_h}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">LeetCode Heatmap</title>
  <desc id="desc">Last 52 weeks of LeetCode submissions for {escape(USERNAME)}</desc>

  <rect width="{card_w}" height="{card_h}" rx="14" fill="{bg}" stroke="{border}" />

  <circle cx="{logo_x + 16}" cy="{logo_y + 16}" r="16" fill="{orange}" opacity="0.16" />
  <path d="M{logo_x + 22} {logo_y + 8} L{logo_x + 11} {logo_y + 19} L{logo_x + 22} {logo_y + 30}" stroke="{orange}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
  <path d="M{logo_x + 18} {logo_y + 19} H{logo_x + 31}" stroke="{orange}" stroke-width="4" stroke-linecap="round" />

  <text x="{pad + 46}" y="{y_header + 17}" fill="{text_primary}" font-size="16" font-weight="700" font-family="Inter, Arial, sans-serif">{escape(USERNAME)}</text>
  <text x="{pad + 46}" y="{y_header + 36}" fill="{text_secondary}" font-size="11" font-family="Inter, Arial, sans-serif">{total_submissions} submissions · {active_days} active days</text>

  <line x="{pad}" y="{y_divider}" x2="{card_w - pad}" y2="{y_divider}" stroke="{divider}" />

  <text x="{pad}" y="{y_title}" fill="{text_primary}" font-size="13" font-weight="600" font-family="Inter, Arial, sans-serif">Heatmap (Last 52 Weeks)</text>

  {month_svg}

  {"".join(rects)}

  <text x="{legend_x - 30}" y="{legend_y + 9}" fill="{text_secondary}" font-size="9" font-family="Inter, Arial, sans-serif">Less</text>
  {legend_svg}
  <text x="{legend_x + legend_total_w + 7}" y="{legend_y + 9}" fill="{text_secondary}" font-size="9" font-family="Inter, Arial, sans-serif">More</text>
</svg>
'''


def main() -> None:
    calendar = fetch_heatmap(USERNAME)
    svg = build_svg(calendar)
    Path(OUTPUT_FILE).write_text(svg, encoding="utf-8")
    print(f"✓ {OUTPUT_FILE} written")


if __name__ == "__main__":
    main()

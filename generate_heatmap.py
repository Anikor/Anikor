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
            "User-Agent": "Mozilla/5.0",
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


def level_for_count(count: int) -> int:
    if count <= 0:
        return 0
    if count == 1:
        return 1
    if count <= 3:
        return 2
    if count <= 6:
        return 3
    return 4


def build_svg(calendar: dict[int, int]) -> str:
    card_w = 720
    card_h = 205

    pad_x = 20
    pad_y = 18

    cell = 10
    gap = 2
    step = cell + gap

    weeks = 53
    days = 7

    grid_w = weeks * step - gap
    grid_h = days * step - gap

    today = datetime.now(timezone.utc).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    days_since_sunday = (today.weekday() + 1) % 7
    current_week_sunday = today - timedelta(days=days_since_sunday)

    start = current_week_sunday - timedelta(weeks=52)
    end = start + timedelta(days=weeks * days - 1)

    cells: list[tuple[datetime, int]] = []

    current = start
    while current <= end:
        timestamp = int(current.timestamp())
        cells.append((current, calendar.get(timestamp, 0)))
        current += timedelta(days=1)

    visible_total = sum(count for _, count in cells)
    active_days = sum(1 for _, count in cells if count > 0)

    title_y = pad_y + 16
    months_y = pad_y + 42
    grid_y = pad_y + 52
    footer_y = grid_y + grid_h + 24

    grid_x = (card_w - grid_w) // 2

    month_labels: list[tuple[int, str]] = []
    last_month = None

    for i, (day, _) in enumerate(cells):
        col = i // days

        if i == 0 or day.day == 1:
            current_month = (day.year, day.month)

            if current_month != last_month and col < weeks:
                month_labels.append((col, day.strftime("%b")))
                last_month = current_month

    month_svg = "\n".join(
        f'<text class="month" x="{grid_x + col * step}" y="{months_y}">{escape(label)}</text>'
        for col, label in month_labels
    )

    rects = []

    for i, (day, count) in enumerate(cells):
        col = i // days
        row = i % days

        x = grid_x + col * step
        y = grid_y + row * step

        level = level_for_count(count)
        word = "submission" if count == 1 else "submissions"
        tooltip = f"{day.strftime('%Y-%m-%d')}: {count} {word}"

        rects.append(
            f'<rect class="level-{level}" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2">'
            f'<title>{escape(tooltip)}</title>'
            f'</rect>'
        )

    legend_cell = 10
    legend_gap = 4
    legend_w = 5 * legend_cell + 4 * legend_gap

    legend_x = card_w - pad_x - legend_w - 34
    legend_y = footer_y - 10

    legend_rects = "\n".join(
        f'<rect class="level-{i}" x="{legend_x + i * (legend_cell + legend_gap)}" y="{legend_y}" '
        f'width="{legend_cell}" height="{legend_cell}" rx="2" />'
        for i in range(5)
    )

    return f'''<svg width="{card_w}" height="{card_h}" viewBox="0 0 {card_w} {card_h}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">LeetCode Heatmap (Last 52 Weeks)</title>
  <desc id="desc">LeetCode heatmap for {escape(USERNAME)} over the last 52 weeks</desc>

  <style>
    :root {{
      --bg: #0d1117;
      --border: #30363d;
      --title: #e6edf3;
      --text: #8b949e;
      --empty: #161b22;
      --l1: #0e4429;
      --l2: #006d32;
      --l3: #26a641;
      --l4: #39d353;
    }}

    .card {{
      fill: var(--bg);
      stroke: var(--border);
    }}

    .title {{
      fill: var(--title);
      font: 600 16px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    }}

    .month {{
      fill: var(--text);
      font: 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    }}

    .meta {{
      fill: var(--text);
      font: 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    }}

    .legend {{
      fill: var(--text);
      font: 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    }}

    .level-0 {{ fill: var(--empty); }}
    .level-1 {{ fill: var(--l1); }}
    .level-2 {{ fill: var(--l2); }}
    .level-3 {{ fill: var(--l3); }}
    .level-4 {{ fill: var(--l4); }}
  </style>

  <rect class="card" x="0.5" y="0.5" width="{card_w - 1}" height="{card_h - 1}" rx="10" />

  <text class="title" x="{pad_x}" y="{title_y}">LeetCode Heatmap (Last 52 Weeks)</text>

  {month_svg}

  {"".join(rects)}

  <text class="meta" x="{pad_x}" y="{footer_y}">{visible_total} submissions · {active_days} active days</text>

  <text class="legend" x="{legend_x - 30}" y="{legend_y + 9}">Less</text>
  {legend_rects}
  <text class="legend" x="{legend_x + legend_w + 8}" y="{legend_y + 9}">More</text>
</svg>
'''


def main() -> None:
    calendar = fetch_heatmap(USERNAME)
    svg = build_svg(calendar)
    Path(OUTPUT_FILE).write_text(svg, encoding="utf-8")
    print(f"{OUTPUT_FILE} written")


if __name__ == "__main__":
    main()

"""Draw the GitHub contribution calendar of the last year as an SVG, once per theme.

The pipeline, start to end:

1. Ask GitHub's GraphQL API for the user's contribution calendar: 53 weeks, each a list of
   days with a count and a level (NONE, then four quartiles — GitHub's own bucketing).
2. Lay the days out on a grid: one column per week, one row per weekday, as on the profile.
3. Colour each square by its level from the theme's ramp, add month and weekday labels, the
   total and a legend, and write `contributions-<theme>.svg`.

Only the standard library is used, so the workflow needs nothing installed.

    GITHUB_TOKEN=$(gh auth token) python scripts/contributions.py --login ettoremodina --out assets

What the calendar counts is what the profile shows to everyone: work in private repositories
appears only if "Include private contributions on my profile" is on in the account settings.
"""

import argparse
import json
import os
import urllib.request
from datetime import date
from pathlib import Path

API = "https://api.github.com/graphql"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionLevel contributionCount } }
      }
    }
  }
}
"""

LEVELS = ("NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE")

# One ramp per theme, from an empty day to the busiest quartile, and the ink of the labels.
# The greens follow the portfolio's palette; the grounds are transparent, so the squares sit
# on whatever GitHub paints behind the README.
THEMES = {
    "dark": {
        "ramp": ("#1b2731", "#234a3b", "#2f7350", "#4fa263", "#8fd47f"),
        "ink": "#a1aeac",
        "strong": "#e8e5dd",
    },
    "light": {
        "ramp": ("#e4e1d8", "#bcd6b0", "#86b77c", "#4f8f55", "#285640"),
        "ink": "#5c6870",
        "strong": "#1c1c1c",
    },
}

# Geometry, in SVG units.
CELL = 11          # side of a day's square
GAP = 3            # space between squares
STEP = CELL + GAP
LEFT = 30          # room for the weekday labels
TOP = 20           # room for the month labels
FOOT = 30          # room for the total and the legend
RADIUS = 2.5
MONTH_LABEL_COLUMNS = 2   # columns a month's name needs to its right
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
# GitHub's weeks start on Sunday; as on the profile, only three rows are named.
WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}


def fetch_calendar(login: str, token: str) -> dict:
    """Return GitHub's contribution calendar for `login`: its total and its weeks of days."""
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    request = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "contribution-calendar",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors") or not payload["data"]["user"]:
        raise RuntimeError(f"GitHub did not return a calendar: {payload.get('errors')}")
    return payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def render(calendar: dict, theme: dict) -> str:
    """Build the SVG of one theme from the calendar: squares, labels, total and legend."""
    weeks = calendar["weeks"]
    width = LEFT + len(weeks) * STEP
    height = TOP + 7 * STEP + FOOT
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" '
        f'height="{height}" role="img" font-family="{FONT}" font-size="10">',
        f'<title>{calendar["totalContributions"]} contributions in the last year</title>',
    ]

    # Weekday names down the left edge.
    for row, label in WEEKDAY_LABELS.items():
        parts.append(f'<text x="0" y="{TOP + row * STEP + CELL - 2}" fill="{theme["ink"]}">{label}</text>')

    previous_month = None
    for column, week in enumerate(weeks):
        x = LEFT + column * STEP
        days = week["contributionDays"]

        # A month is named above the first week that begins in it. Two cases are left unnamed:
        # the very first column when the month changes again right after (the two names would
        # collide), and a month that begins in the last columns (its name would run off the edge).
        month = date.fromisoformat(days[0]["date"]).month
        if month != previous_month:
            next_month = date.fromisoformat(weeks[column + 1]["contributionDays"][0]["date"]).month \
                if column + 1 < len(weeks) else month
            collides = column == 0 and next_month != month
            runs_off = column > len(weeks) - MONTH_LABEL_COLUMNS
            if not (collides or runs_off):
                parts.append(f'<text x="{x}" y="{TOP - 8}" fill="{theme["ink"]}">{MONTHS[month - 1]}</text>')
            previous_month = month

        for day in days:
            # The first and last weeks are partial: the weekday decides the row, not the index.
            row = (date.fromisoformat(day["date"]).weekday() + 1) % 7
            colour = theme["ramp"][LEVELS.index(day["contributionLevel"])]
            parts.append(
                f'<rect x="{x}" y="{TOP + row * STEP}" width="{CELL}" height="{CELL}" rx="{RADIUS}" '
                f'fill="{colour}"><title>{day["date"]}: {day["contributionCount"]}</title></rect>'
            )

    # Under the grid: the total on the left, the ramp on the right.
    baseline = TOP + 7 * STEP + 18
    parts.append(
        f'<text x="{LEFT}" y="{baseline}" font-size="12" fill="{theme["ink"]}">'
        f'<tspan font-weight="600" fill="{theme["strong"]}">{calendar["totalContributions"]}</tspan>'
        ' contributions in the last year</text>'
    )
    legend = width - len(LEVELS) * STEP - 34
    parts.append(f'<text x="{legend - 6}" y="{baseline}" text-anchor="end" fill="{theme["ink"]}">Less</text>')
    for index, colour in enumerate(theme["ramp"]):
        parts.append(
            f'<rect x="{legend + index * STEP}" y="{baseline - CELL + 1}" width="{CELL}" height="{CELL}" '
            f'rx="{RADIUS}" fill="{colour}"/>'
        )
    parts.append(f'<text x="{legend + len(LEVELS) * STEP + 3}" y="{baseline}" fill="{theme["ink"]}">More</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--login", required=True, help="GitHub user whose calendar is drawn")
    parser.add_argument("--out", default="assets", help="directory the SVGs are written to")
    arguments = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Set GITHUB_TOKEN (locally: GITHUB_TOKEN=$(gh auth token)).")

    calendar = fetch_calendar(arguments.login, token)
    output = Path(arguments.out)
    output.mkdir(parents=True, exist_ok=True)
    for name, theme in THEMES.items():
        path = output / f"contributions-{name}.svg"
        path.write_text(render(calendar, theme), encoding="utf-8")
        print(f"{path}: {calendar['totalContributions']} contributions, {len(calendar['weeks'])} weeks")


if __name__ == "__main__":
    main()

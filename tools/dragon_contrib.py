"""Builds assets/dragon-contrib.svg: a copy of the contribution calendar that Soplón,
seen from above, eats from the fewest contributions to the most. When he is back
in his nest the cells grow back and the loop starts again.

Runs daily from .github/workflows/profile-stats.yml. To run locally:
    GITHUB_TOKEN=$(gh auth token) python tools/dragon_contrib.py
"""
import datetime as dt
import json
import math
import os
import urllib.request
from pathlib import Path

LOGIN = "JhojanECO"
OUT = Path(__file__).resolve().parent.parent / "assets" / "dragon-contrib.svg"

BG, PANEL, GRID = "#0D1117", "#161B22", "#21262D"
TEXT, MUTED = "#E6EDF3", "#8B949E"
CRIMSON, CYAN = "#DC143C", "#00F0FF"
LEVELS = {
    "NONE": PANEL,
    "FIRST_QUARTILE": "#4A0D1A",
    "SECOND_QUARTILE": "#8B0A24",
    "THIRD_QUARTILE": "#C0122F",
    "FOURTH_QUARTILE": "#FF3355",
}
FONT = "DejaVu Sans Mono, Consolas, Menlo, monospace"

W, H = 1000, 228
CELL, PITCH = 12, 16          # cell size / distance between cell origins
GX, GY = 112, 78              # grid origin
NEST = (62, GY + 3.5 * PITCH - 2)

N = 16                        # body segments
SPACING = 7.0                 # px between segments
SNOUT = 22.0                  # px from neck to snout: cells vanish when the snout reaches them
MAX_TRIP = 32.0               # s, the dragon speeds up when there is a lot to eat
MIN_SPEED = 230.0             # px / s
REST = 1.6                    # s in the nest after the cells grow back
WAVE = 1.0                    # s for the regrow wave to sweep left to right

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date weekday contributionCount contributionLevel } }
      }
    }
  }
}
"""


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body:
        raise SystemExit(body["errors"])
    return body["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def cells_of(cal):
    cells = []
    for w, week in enumerate(cal["weeks"]):
        for d in week["contributionDays"]:
            x, y = GX + w * PITCH, GY + d["weekday"] * PITCH
            cells.append({
                "w": w, "x": x, "y": y, "cx": x + CELL / 2, "cy": y + CELL / 2,
                "date": d["date"], "n": d["contributionCount"], "fill": LEVELS[d["contributionLevel"]],
            })
    return cells


def eating_order(cells):
    """Fewest contributions first; among equal counts, always the nearest cell next."""
    order, cur = [], NEST
    for n in sorted({c["n"] for c in cells if c["n"] > 0}):
        left = [c for c in cells if c["n"] == n]
        while left:
            nxt = min(left, key=lambda c: math.dist(cur, (c["cx"], c["cy"])))
            left.remove(nxt)
            order.append(nxt)
            cur = (nxt["cx"], nxt["cy"])
    return order


def fmt(v):
    return f"{v:.5f}".rstrip("0").rstrip(".") if v else "0"


def build(cal):
    cells = cells_of(cal)
    order = eating_order(cells)

    pts = [NEST] + [(c["cx"], c["cy"]) for c in order] + [NEST]
    if len(pts) == 2:                       # nothing to eat: a short patrol over the grid
        pts = [NEST, (GX + 26 * PITCH, GY + 3.5 * PITCH), NEST]
    seg = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    total = sum(seg)
    speed = max(MIN_SPEED, total / MAX_TRIP)
    lag = SPACING / speed
    trip = total / speed
    home = trip + (N + 1) * lag + 0.25     # tail is inside the nest
    dur = home + WAVE + REST

    arc = [0.0]
    for s in seg:
        arc.append(arc[-1] + s)
    key_points = [a / total for a in arc] + [1.0]
    key_times = [a / speed / dur for a in arc] + [1.0]
    route = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    motion = (f'calcMode="linear" keyPoints="{";".join(fmt(k) for k in key_points)}" '
              f'keyTimes="{";".join(fmt(k) for k in key_times)}" rotate="auto"')

    # ---- calendar ----
    eat_at = {id(c): max(0.0, (arc[i + 1] - SNOUT) / speed) for i, c in enumerate(order)}
    grid = []
    for c in cells:
        rect = f'<rect x="{c["x"]}" y="{c["y"]}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c["fill"]}"'
        if id(c) not in eat_at:
            grid.append(rect + "/>")
            continue
        t0 = eat_at[id(c)] / dur
        t1 = t0 + 0.12 / dur
        t2 = (home + WAVE * c["w"] / 52) / dur
        grid.append(
            rect + f'><animate attributeName="fill" dur="{dur:.3f}s" repeatCount="indefinite" calcMode="discrete" '
            f'values="{c["fill"]};{CYAN};{PANEL};{c["fill"]}" keyTimes="0;{fmt(t0)};{fmt(t1)};{fmt(t2)}"/></rect>'
        )

    months, last = [], -9
    for w in range(len(cal["weeks"])):
        first = dt.date.fromisoformat(cal["weeks"][w]["contributionDays"][0]["date"])
        if (w == 0 or first.day <= 7) and w - last >= 3:
            months.append(f'<text x="{GX + w * PITCH}" y="{GY - 8}" font-size="11" fill="{MUTED}">{first:%b}</text>')
            last = w

    legend_x = GX + 53 * PITCH - 5 * 15 - 36
    legend = [f'<text x="{legend_x - 8}" y="{H - 18}" font-size="11" fill="{MUTED}" text-anchor="end">Less</text>']
    for i, col in enumerate(LEVELS.values()):
        legend.append(f'<rect x="{legend_x + i * 15}" y="{H - 28}" width="11" height="11" rx="2.5" fill="{col}"/>')
    legend.append(f'<text x="{legend_x + 5 * 15 + 4}" y="{H - 18}" font-size="11" fill="{MUTED}">More</text>')

    # ---- dragon: every part follows the route; the body runs a little behind the head ----
    def follow(inner, behind):
        # a part `behind` slots back is that much earlier on the same loop
        begin = behind * lag - dur if behind else 0
        # sideways sway, phase-shifted along the body so it slithers
        amp = 0.6 if not behind else 0.8 + 2.2 * min(1, behind / 6)
        sway = (f'<animateTransform attributeName="transform" type="translate" values="0 {amp:.1f};0 {-amp:.1f};0 {amp:.1f}" '
                f'dur="0.9s" begin="{-behind * 0.07:.2f}s" repeatCount="indefinite"/>')
        return (f'<g><g>{inner}{sway}</g><animateMotion path="{route}" dur="{dur:.3f}s" begin="{begin:.3f}s" '
                f'repeatCount="indefinite" {motion}/></g>')

    body = [follow(segment(i), i + 1) for i in reversed(range(N))]
    dragon = "\n".join(body + [follow(HEAD, 0)])

    nx, ny = NEST
    nest = f'''
  <g transform="translate({nx} {ny})">
    <circle r="27" fill="none" stroke="{CYAN}" stroke-width="1.2" stroke-dasharray="3 5" opacity="0.7">
      <animateTransform attributeName="transform" type="rotate" values="0;360" dur="14s" repeatCount="indefinite"/>
    </circle>
    <circle r="21" fill="{BG}" stroke="{CRIMSON}" stroke-width="2.5" filter="url(#glow)"/>
    <circle r="12" fill="none" stroke="{GRID}" stroke-width="1.5"/>
    <text y="46" font-size="11" fill="{MUTED}" text-anchor="middle">nest</text>
  </g>'''

    total_c = cal["totalContributions"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">
  <title id="t">Contribution calendar for the last 12 months ({total_c} contributions). Soplón the dragon leaves his nest, eats the days from the fewest contributions to the most, flies home, and the calendar grows back.</title>
  <defs>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="1.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="{W}" height="{H}" rx="18" fill="{BG}"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{GRID}"/>
  <g font-family="{FONT}">
    <text x="40" y="38" font-size="13" fill="{MUTED}" letter-spacing="2">CONTRIBUTIONS · LAST 12 MONTHS</text>
    <text x="{GX + 53 * PITCH - 4}" y="38" font-size="13" fill="{TEXT}" text-anchor="end">{total_c:,} contributions <tspan fill="{MUTED}">· eaten from fewest to most</tspan></text>
    {"".join(months)}
    {"".join(legend)}
    <g>{"".join(grid)}</g>
{dragon}
{nest}
  </g>
</svg>
'''


def segment(i):
    """Body ring seen from above, facing +x."""
    k = i / (N - 1)
    r = 6.2 * (1 - k) ** 0.7 + 1.8
    parts = [f'<circle r="{r:.1f}" fill="{CRIMSON}"/>',
             f'<path d="M {-r*0.5:.1f} {-r*0.55:.1f} Q {r*0.35:.1f} 0 {-r*0.5:.1f} {r*0.55:.1f}" fill="none" stroke="#A50E2D" stroke-width="1.1"/>']
    if i % 3 == 1 and i < N - 2:
        parts.append(f'<path d="M {r*0.7:.1f} 0 L {-r*0.2:.1f} -1.6 L {-r*0.9:.1f} 0 L {-r*0.2:.1f} 1.6 Z" fill="{CYAN}" opacity="0.9"/>')
    if i in (2, 9):
        parts.append(legs(r, i))
    if i == N - 1:
        parts.append(f'<path d="M 0 0 C -6 -7, -14 -9, -20 -6 C -15 -3, -15 3, -20 6 C -14 9, -6 7, 0 0 Z" fill="{CYAN}" opacity="0.9" filter="url(#glow)"/>')
    return "".join(parts)


def legs(r, i):
    claw = "stroke=\"#00F0FF\" stroke-width=\"1.1\" stroke-linecap=\"round\""
    out = []
    for s in (-1, 1):
        y0, y1, y2 = s * r * 0.6, s * (r + 4), s * (r + 7)
        out.append(
            f'<g><path d="M 0 {y0:.1f} L -3 {y1:.1f} L -7 {y2:.1f}" fill="none" stroke="#A50E2D" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M -7 {y2:.1f} l -3 {-s:.0f} M -7 {y2:.1f} l -2 {s*2.5:.1f}" {claw}/>'
            f'<animateTransform attributeName="transform" type="rotate" values="{-12*s} 0 {y0:.1f};{12*s} 0 {y0:.1f};{-12*s} 0 {y0:.1f}" '
            f'dur="{0.5 + (i % 3) * 0.08:.2f}s" repeatCount="indefinite"/></g>')
    return "".join(out)


# head seen from above, neck at the origin, snout towards +x
HEAD = f'''
  <path d="M 2 -6 L -6 -12 L -3 -5 L -10 -7 L -4 -1 L -10 0 L -4 1 L -10 7 L -3 5 L -6 12 L 2 6 Z" fill="#8B0A24"/>
  <path d="M 6 -5 C 0 -11, -6 -14, -13 -15 C -7 -11, -2 -8, 2 -3 Z" fill="#A50E2D"/>
  <path d="M 6 5 C 0 11, -6 14, -13 15 C -7 11, -2 8, 2 3 Z" fill="#A50E2D"/>
  <g fill="none" stroke="{CYAN}" stroke-width="1.2" stroke-linecap="round" filter="url(#glow)">
    <path d="M 21 -2 C 16 -8, 8 -12, -4 -16"><animateTransform attributeName="transform" type="rotate" values="0 21 -2;-9 21 -2;0 21 -2" dur="1.6s" repeatCount="indefinite"/></path>
    <path d="M 21 2 C 16 8, 8 12, -4 16"><animateTransform attributeName="transform" type="rotate" values="0 21 2;9 21 2;0 21 2" dur="1.6s" repeatCount="indefinite"/></path>
  </g>
  <path d="M -2 -6.5 C 6 -9, 14 -7.5, 18 -4 L 22 -2.5 C 24.5 -1.5, 24.5 1.5, 22 2.5 L 18 4 C 14 7.5, 6 9, -2 6.5 Z" fill="{CRIMSON}"/>
  <path d="M 3 0 L 15 0" stroke="#A50E2D" stroke-width="1.4" stroke-linecap="round"/>
  <circle cx="11" cy="-4.2" r="1.9" fill="{CYAN}" filter="url(#glow)"/>
  <circle cx="11" cy="4.2" r="1.9" fill="{CYAN}" filter="url(#glow)"/>
  <circle cx="21.5" cy="-1.2" r="0.8" fill="#8B0A24"/>
  <circle cx="21.5" cy="1.2" r="0.8" fill="#8B0A24"/>
'''


if __name__ == "__main__":
    OUT.write_text(build(fetch()), encoding="utf-8")
    print(f"wrote {OUT}")

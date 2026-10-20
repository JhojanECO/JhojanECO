"""Builds assets/dragon-contrib.svg: a copy of the contribution calendar that Soplón,
seen from above, eats from the fewest contributions to the most. When he is back
in his nest the cells grow back and the loop starts again.

The flight is simulated, not drawn: Soplón has a heading and steers towards the
next cell with a proportional controller, slowing down in tight turns, so every
change of direction is a smooth arc. The body follows the head's trail by
distance, like a real serpent.

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
REST = 1.6                    # s in the nest after the cells grow back
WAVE = 1.0                    # s for the regrow wave to sweep left to right

# flight
MAX_TRIP = 34.0               # s, Soplón flies faster when there is a lot to eat
V_START = 240.0               # px / s on straight lines
TURN_GAIN = 4.5               # 1/s, heading controller: turn rate = gain * heading error
TURN_MAX = 6.0                # rad / s
SLOW = 0.2                    # fraction of top speed kept in the sharpest turns
HEADING_COST = 45.0           # px per rad: prefers the next cell that is ahead of him
EAT_R = 7.0                   # px, from the head (neck to snout) to the cell centre
DT = 1 / 120                  # s, simulation step
TRAIL_STEP = 4.0              # px between points of the recorded trail
KEY_DT = 0.2                  # s between motion keyframes

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


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def head_dist(c, x, y, th):
    """Distance from a cell centre to the head, taken as the segment from neck to snout."""
    px, py = c["cx"] - x, c["cy"] - y
    along = max(0.0, min(SNOUT, px * math.cos(th) + py * math.sin(th)))
    return math.dist((px, py), (along * math.cos(th), along * math.sin(th)))


def fly(cells, vmax):
    """Simulates the trip. Returns the trail [(x, y, t)], when each cell was eaten, and the trip time."""
    food = [c for c in cells if c["n"] > 0]
    if not food:  # nothing to eat: a short patrol over the middle of the grid
        food = [{"cx": GX + 26 * PITCH, "cy": GY + 3.5 * PITCH, "n": 1}]
    x, y = NEST
    th, t, chase, since = 0.0, 0.0, 0.0, 0.0
    trail, eaten, target = [(x, y, 0.0)], {}, None

    def pick(sx, sy):
        lo = min(c["n"] for c in food)
        return min((c for c in food if c["n"] == lo),
                   key=lambda c: math.dist((sx, sy), (c["cx"], c["cy"]))
                   + HEADING_COST * abs(wrap(math.atan2(c["cy"] - sy, c["cx"] - sx) - th)))

    while t < 600:
        sx, sy = x + SNOUT * math.cos(th), y + SNOUT * math.sin(th)
        if target is None and food:
            target, chase = pick(sx, sy), 0.0
        if target is not None:   # steer the snout onto the cell
            err = wrap(math.atan2(target["cy"] - sy, target["cx"] - sx) - th)
        else:                    # steer the neck into the nest
            err = wrap(math.atan2(NEST[1] - y, NEST[0] - x) - th)
        wmax = TURN_MAX * (2 if chase > 2.5 else 1)   # never orbit a cell forever
        th += max(-wmax, min(wmax, TURN_GAIN * err)) * DT
        v = vmax * (SLOW + (1 - SLOW) * max(0.0, math.cos(err)))
        x += v * math.cos(th) * DT
        y += v * math.sin(th) * DT
        t += DT
        chase += DT
        since += v * DT
        if since >= TRAIL_STEP:
            trail.append((x, y, t))
            since = 0.0

        if target is not None:
            lo = min(c["n"] for c in food)
            for c in [c for c in food if c["n"] == lo and head_dist(c, x, y, th) < EAT_R]:
                eaten[id(c)] = t
                food.remove(c)
                if c is target:
                    target = None
            if target is not None and target not in food:
                target = None
        elif math.dist((x, y), NEST) < 5:
            t += math.dist((x, y), NEST) / v
            trail.append((NEST[0], NEST[1], t))
            break
    if t >= 600:
        raise SystemExit("Soplón got stuck circling a cell; tune TURN_MAX / SLOW")
    return trail, eaten, t


def fmt(v):
    return f"{v:.5f}".rstrip("0").rstrip(".") if v else "0"


def build(cal):
    cells = cells_of(cal)

    vmax = V_START
    while True:
        trail, eaten, trip = fly(cells, vmax)
        if trip <= MAX_TRIP or vmax >= 700:
            break
        vmax *= min(1.5, trip / MAX_TRIP * 1.03)

    # arc length along the trail, and a keyframe every KEY_DT seconds
    arc = [0.0]
    for a, b in zip(trail, trail[1:]):
        arc.append(arc[-1] + math.dist(a[:2], b[:2]))
    total = arc[-1]
    keys, nxt = [], 0.0
    for (_, _, t), s in zip(trail, arc):
        if t >= nxt or t == trip:
            keys.append((t, s))
            nxt = t + KEY_DT
    if keys[-1][0] != trip:
        keys.append((trip, total))
    # after the head is home the trail keeps "flowing" into the nest until the tail is in
    tail_in = (N + 1) * SPACING / (vmax * 0.6)
    home = trip + tail_in + 0.15
    dur = home + WAVE + REST
    keys += [(trip + tail_in, total + (N + 1) * SPACING), (dur, total + (N + 1) * SPACING)]
    key_times = ";".join(fmt(t / dur) for t, _ in keys)

    route = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y, _ in trail)

    # ---- calendar ----
    grid = []
    for c in cells:
        rect = f'<rect x="{c["x"]}" y="{c["y"]}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c["fill"]}"'
        if id(c) not in eaten:
            grid.append(rect + "/>")
            continue
        t0 = eaten[id(c)] / dur
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

    # ---- dragon: every part rides the same trail, `behind` slots back from the head ----
    def follow(inner, behind):
        back = behind * SPACING
        key_points = ";".join(fmt(min(1.0, max(0.0, (s - back) / total))) for _, s in keys)
        # sideways sway, phase-shifted along the body so it slithers
        amp = 0.6 if not behind else 0.8 + 2.2 * min(1, behind / 6)
        sway = (f'<animateTransform attributeName="transform" type="translate" values="0 {amp:.1f};0 {-amp:.1f};0 {amp:.1f}" '
                f'dur="0.9s" begin="{-behind * 0.07:.2f}s" repeatCount="indefinite"/>')
        return (f'<g><g>{inner}{sway}</g><animateMotion dur="{dur:.3f}s" repeatCount="indefinite" calcMode="linear" '
                f'keyPoints="{key_points}" keyTimes="{key_times}" rotate="auto"><mpath href="#trail"/></animateMotion></g>')

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
    print(f"top speed {vmax:.0f}px/s, trip {trip:.1f}s, loop {dur:.1f}s, trail {len(trail)} pts, {len(keys)} keys")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">
  <title id="t">Contribution calendar for the last 12 months ({total_c} contributions). Soplón the dragon leaves his nest, eats the days from the fewest contributions to the most, flies home, and the calendar grows back.</title>
  <defs>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="1.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <path id="trail" d="{route}"/>
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

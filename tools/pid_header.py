"""Simulates a differential-drive line follower with PID control on the header
track and bakes the result (trajectory + left/right PWM) into assets/header.svg.

Re-run after changing gains:  python3 tools/pid_header.py
"""
import math
import numpy as np
from svgpathtools import parse_path

TRACK = "M -60 205 C 40 205, 90 232, 180 220 S 300 172, 400 196 S 540 238, 640 208 S 760 156, 860 172 S 960 206, 1060 186"

# ---- tunables (what the header shows) ----
KP, KI, KD = 0.08, 0.0, 0.2
BASE = 160          # base PWM
PWM_MAX = 255
SPEED_K = 0.022     # px per tick per PWM unit
WHEELBASE = 30.0
LOOKAHEAD = 26.0    # sensor bar distance from wheel axis
SENSOR_SPAN = 1000  # error scale: like a QTR array reading (-1000..1000)
DT = 1.0
FRAMES = 150
DUR = 10.0          # seconds of animation

path = parse_path(TRACK)
pts = np.array([[path.point(t).real, path.point(t).imag] for t in np.linspace(0, 1, 4000)])


def lateral_error(px, py, heading):
    d = np.hypot(pts[:, 0] - px, pts[:, 1] - py)
    i = int(np.argmin(d))
    # signed distance: + when track is to the robot's right
    rx, ry = -math.sin(heading), math.cos(heading)  # right-hand normal (y down)
    off = (pts[i, 0] - px) * rx + (pts[i, 1] - py) * ry
    return off


x, y = -40.0, 205.0
th = 0.0
integ = 0.0
prev_e = 0.0
log = []
while x < 1040 and len(log) < 20000:
    sx, sy = x + LOOKAHEAD * math.cos(th), y + LOOKAHEAD * math.sin(th)
    off = lateral_error(sx, sy, th)
    e = max(-SENSOR_SPAN, min(SENSOR_SPAN, off / 18.0 * SENSOR_SPAN))  # 18px = edge of sensor bar
    integ += e * DT
    u = KP * e + KI * integ + KD * (e - prev_e) / DT
    prev_e = e
    pl = max(0, min(PWM_MAX, BASE + u))
    pr = max(0, min(PWM_MAX, BASE - u))
    vl, vr = pl * SPEED_K, pr * SPEED_K
    v = (vl + vr) / 2
    w = (vl - vr) / WHEELBASE   # y-down: left faster -> turn right (clockwise on screen)
    th += w * DT
    x += v * math.cos(th) * DT
    y += v * math.sin(th) * DT
    log.append((x, y, th, pl, pr, e))

log = np.array(log)
idx = np.linspace(0, len(log) - 1, FRAMES).astype(int)
fr = log[idx]
print(f"steps={len(log)} | PWM L {fr[:,3].min():.0f}-{fr[:,3].max():.0f} | R {fr[:,4].min():.0f}-{fr[:,4].max():.0f} | max |err| {abs(log[:,5]).max():.0f}")

traj = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in log[::4, :2])
kt = ";".join(f"{i/(FRAMES-1):.4f}" for i in range(FRAMES))

# ---- telemetry panel ----
PX, PY = 628, 26
BAR_W = 200
DIG_H = 22


def digits_strip(values, x0, y0, name):
    """Three digit columns that roll to show a 0-255 value each frame."""
    out = []
    for col in range(3):
        ds = [int(f"{int(round(v)):03d}"[col]) for v in values]
        ty = ";".join(f"0 {-d*DIG_H}" for d in ds)
        tsp = "".join(f'<tspan x="{x0+col*12}" y="{y0+i*DIG_H}">{i}</tspan>' for i in range(10))
        out.append(
            f'<g clip-path="url(#clip{name})"><g transform="translate(0 {-ds[0]*DIG_H})"><text font-family="DejaVu Sans Mono, Consolas, Menlo, monospace" '
            f'font-size="18" fill="#E6EDF3">{tsp}</text>'
            f'<animateTransform attributeName="transform" type="translate" dur="{DUR}s" repeatCount="indefinite" '
            f'calcMode="discrete" values="{ty}" keyTimes="{kt}"/></g></g>'
        )
    return "\n".join(out)


def bar(values, y0, name):
    ws = ";".join(f"{v/PWM_MAX*BAR_W:.1f}" for v in values)
    return (
        f'<text x="{PX}" y="{y0+13}" font-family="DejaVu Sans Mono, Consolas, Menlo, monospace" font-size="15" fill="#8B949E">{name}</text>'
        f'<rect x="{PX+52}" y="{y0}" width="{BAR_W}" height="16" rx="4" fill="#161B22" stroke="#30363D"/>'
        f'<rect x="{PX+52}" y="{y0}" height="16" rx="4" fill="#DC143C" width="{values[0]/PWM_MAX*BAR_W:.1f}">'
        f'<animate attributeName="width" dur="{DUR}s" repeatCount="indefinite" values="{ws}" keyTimes="{kt}"/></rect>'
        f'<line x1="{PX+52+BASE/PWM_MAX*BAR_W:.1f}" y1="{y0-3}" x2="{PX+52+BASE/PWM_MAX*BAR_W:.1f}" y2="{y0+19}" stroke="#00F0FF" stroke-width="1.5" opacity="0.8"/>'
    )


panel = f'''
  <g>
    <text x="{PX}" y="{PY+10}" font-family="DejaVu Sans Mono, Consolas, Menlo, monospace" font-size="13" fill="#00F0FF">PID  Kp={KP} Ki={KI} Kd={KD}  base={BASE}</text>
    {bar(fr[:,3], PY+26, "PWM_L")}
    {digits_strip(fr[:,3], PX+262, PY+40, "L")}
    {bar(fr[:,4], PY+54, "PWM_R")}
    {digits_strip(fr[:,4], PX+262, PY+68, "R")}
  </g>'''

robot = f'''
  <g>
   <g transform="scale(1.35)">
    <rect x="-9" y="-16" width="18" height="6" rx="2" fill="#30363D"/>
    <rect x="-9" y="10" width="18" height="6" rx="2" fill="#30363D"/>
    <rect x="-15" y="-11" width="30" height="22" rx="6" fill="#161B22" stroke="#DC143C" stroke-width="2.5"/>
    <circle cx="-4" cy="0" r="3" fill="#DC143C"/>
    <line x1="18" y1="-10" x2="18" y2="10" stroke="#30363D" stroke-width="5" stroke-linecap="round"/>
    <g fill="#00F0FF" filter="url(#g)">
      <circle cx="18" cy="-8" r="1.7"/><circle cx="18" cy="-4" r="1.7"/><circle cx="18" cy="0" r="1.9"/><circle cx="18" cy="4" r="1.7"/><circle cx="18" cy="8" r="1.7"/>
    </g>
   </g>
    <animateMotion dur="{DUR}s" repeatCount="indefinite" rotate="auto" path="{traj}"/>
  </g>'''

# typing "> Hello World!!"
txt = "> Hello World!!"
cw = 12.04
n = len(txt)
widths = [round(i * cw, 1) for i in range(n + 1)]
tvals = widths + [widths[-1], 0]
tdur = 7.0
tkt = [round(i / n * 2.4 / tdur, 4) for i in range(n + 1)] + [0.9, 1.0]
tv = ";".join(map(str, tvals))
tk = ";".join(map(str, tkt))
cur = ";".join(str(round(48 + v + 2, 1)) for v in tvals)

clips = "".join(
    f'<clipPath id="clip{nm}"><rect x="{PX+258}" y="{PY+y-17}" width="40" height="{DIG_H}"/></clipPath>'
    for nm, y in (("L", 40), ("R", 68))
)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 240" width="1000" height="240" role="img" aria-labelledby="t">
  <title id="t">Hello World!! I'm Jhojan Espinoza, Mechatronics Engineering student at UNI. A line-follower robot driven by a PID controller follows a crimson track while its left and right PWM values update live.</title>
  <defs>
    <filter id="g" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="1.8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.2" fill="#21262D"/></pattern>
    <clipPath id="type"><rect x="48" y="40" height="32" width="0">
      <animate attributeName="width" dur="{tdur}s" repeatCount="indefinite" calcMode="discrete" values="{tv}" keyTimes="{tk}"/>
    </rect></clipPath>
    {clips}
  </defs>
  <rect width="1000" height="240" rx="18" fill="#0D1117"/>
  <rect width="1000" height="240" rx="18" fill="url(#dots)"/>

  <text x="48" y="64" clip-path="url(#type)" font-family="DejaVu Sans Mono, Consolas, Menlo, monospace" font-size="20" fill="#00F0FF">&gt; Hello World!!</text>
  <rect x="50" y="47" width="10" height="21" fill="#00F0FF">
    <animate attributeName="x" dur="{tdur}s" repeatCount="indefinite" calcMode="discrete" values="{cur}" keyTimes="{tk}"/>
    <animate attributeName="opacity" dur="1s" repeatCount="indefinite" values="1;0;1" calcMode="discrete" keyTimes="0;0.5;1"/>
  </rect>
  <text x="46" y="128" font-family="Segoe UI, Helvetica Neue, Arial, DejaVu Sans, sans-serif" font-size="54" font-weight="700" fill="#E6EDF3"><tspan fill="#DC143C">Jhojan</tspan> Espinoza</text>
  <text x="48" y="162" font-family="Segoe UI, Helvetica Neue, Arial, DejaVu Sans, sans-serif" font-size="20" fill="#8B949E">Mechatronics Engineering · UNI</text>
  {panel}
  <path d="{TRACK}" fill="none" stroke="#DC143C" stroke-width="7" stroke-linecap="round"/>
  {robot}
</svg>
'''
open("assets/header.svg", "w").write(svg)

# static preview frames for checking
for k in (0, FRAMES // 3, 2 * FRAMES // 3):
    px, py, th, pl, pr, e = fr[k]
    yield_svg = svg
    print(f"frame {k}: x={px:.0f} y={py:.0f} L={pl:.0f} R={pr:.0f} e={e:.0f}")

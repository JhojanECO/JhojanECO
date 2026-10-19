"""Generates assets/dragon.svg: a long Chinese-style crimson dragon that glides across
the profile, does a loop in the middle, looks at the viewer and breathes fire.

Every body segment follows the same path with a time offset, so the body
undulates like a real serpent. Run:  python3 tools/dragon.py
"""
import math
from svgpathtools import parse_path

W, H = 1000, 210
PATH = ("M -460 130 C -300 130, -200 70, -60 92 C 60 112, 160 170, 280 150 "
        "C 380 134, 430 150, 500 150 A 52 52 0 1 0 500 46 A 52 52 0 1 0 500 150 "
        "C 600 150, 650 80, 770 88 C 880 96, 940 150, 1080 124 L 1700 124")

N = 46            # body segments (head excluded)
SPACING = 8.5     # px between segments
SPEED = 120       # px / s

p = parse_path(PATH)
L = p.length()
DUR = L / SPEED
LAG = SPACING / SPEED


def length_at_x(x_target, after=0.0):
    """Arc length where the path first reaches x_target, searching after a given length."""
    s = after
    while s < L:
        t = p.ilength(min(s, L - 1e-6))
        if p.point(t).real >= x_target:
            return s
        s += 2
    return L


# where the loop starts / ends (in arc length)
s_loop0 = length_at_x(498, 300)
s_loop1 = s_loop0 + 2 * math.pi * 52
HEAD_BEGIN = -(N) * LAG   # head is ahead of segment 0


def frac(s):
    return max(0.0, min(1.0, s / L))


def seg_radius(i):
    # thick neck, slim tail
    k = i / (N - 1)
    return 11.5 * (1 - k) ** 0.8 + 2.2


def segment(i):
    r = seg_radius(i)
    begin = -(N - 1 - i) * LAG
    parts = []
    # body
    parts.append(f'<ellipse rx="{max(5.5, r*0.75):.1f}" ry="{r:.1f}" fill="#DC143C"/>')
    # belly (robot's right is +y because rotate=auto)
    parts.append(f'<ellipse cy="{r*0.45:.1f}" rx="{max(4, r*0.55):.1f}" ry="{r*0.42:.1f}" fill="#F25670"/>')
    # scale arc
    if i % 2 == 0 and r > 4:
        parts.append(f'<path d="M {-r*0.4:.1f} {-r*0.6:.1f} Q {r*0.25:.1f} {-r*0.1:.1f} {-r*0.4:.1f} {r*0.2:.1f}" '
                     f'fill="none" stroke="#A50E2D" stroke-width="1.4"/>')
    # dorsal fin: cyan accent, every third segment
    if i % 3 == 1 and i < N - 3:
        h = r * 0.9 + 3
        parts.append(f'<path d="M 3 {-r+1:.1f} L -6 {-r-h:.1f} L -4 {-r+1:.1f} Z" fill="#00F0FF" opacity="0.9"/>')
    # legs
    if i in (5, 26):
        parts.append(leg(r, i))
    # tail fin
    if i == N - 1:
        parts.append('<path d="M 0 0 C -10 -14, -26 -18, -38 -10 C -28 -6, -24 0, -38 8 C -24 12, -10 8, 0 0 Z" fill="#00F0FF" opacity="0.9" filter="url(#glow)"/>')
        parts.append('<path d="M 0 0 C -8 -8, -18 -10, -26 -6 C -18 -2, -18 2, -26 6 C -16 8, -8 6, 0 0 Z" fill="#DC143C"/>')
    return (f'<g>{"".join(parts)}<animateMotion dur="{DUR:.3f}s" begin="{begin:.3f}s" '
            f'repeatCount="indefinite" rotate="auto"><mpath href="#route"/></animateMotion></g>')


def leg(r, i):
    # a small clawed leg on the belly side, paddling
    d = ("M 0 {y0:.1f} L -6 {y1:.1f} L -14 {y2:.1f}").format(y0=r * 0.6, y1=r + 9, y2=r + 13)
    claws = (f'<path d="M -14 {r+13:.1f} l -5 -2 M -14 {r+13:.1f} l -5 3 M -14 {r+13:.1f} l -2 5" '
             f'stroke="#00F0FF" stroke-width="1.6" stroke-linecap="round"/>')
    return (f'<g><path d="{d}" fill="none" stroke="#A50E2D" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>{claws}'
            f'<animateTransform attributeName="transform" type="rotate" values="-14 0 {r*0.6:.1f};14 0 {r*0.6:.1f};-14 0 {r*0.6:.1f}" '
            f'dur="{1.1 + (i % 3) * 0.1:.1f}s" repeatCount="indefinite"/></g>')


# ---- head: faces +x, origin at the neck ----
fa, fb = frac(s_loop1 + 10), frac(s_loop1 + 190)   # reaction window (head's own timeline)
fm = (fa + fb) / 2


def react(values, attr="opacity"):
    """Animate an attribute only during the reaction window of the head's cycle."""
    kt = f"0;{fa:.4f};{fa+0.004:.4f};{fm:.4f};{fb-0.004:.4f};{fb:.4f};1"
    return (f'<animate attributeName="{attr}" dur="{DUR:.3f}s" begin="{HEAD_BEGIN:.3f}s" repeatCount="indefinite" '
            f'values="{values}" keyTimes="{kt}"/>')


head = f'''
<g>
 <g transform="scale(1.3)">
  <!-- mane -->
  <path d="M 2 -12 L -10 -24 L -4 -10 L -18 -14 L -6 -4 L -20 2 L -6 4 L -16 12 L 0 10 Z" fill="#8B0A24"/>
  <!-- antlers -->
  <path d="M 10 -13 C 2 -26, -8 -32, -20 -32 C -10 -27, -2 -21, 4 -11 Z" fill="#A50E2D"/>
  <path d="M -6 -27 L -10 -36 L -2 -29 Z" fill="#A50E2D"/>
  <path d="M 16 -13 C 12 -24, 6 -30, -2 -34 C 4 -27, 8 -20, 10 -12 Z" fill="#8B0A24"/>
  <!-- whiskers (cyan accent) -->
  <g fill="none" stroke="#00F0FF" stroke-width="1.8" stroke-linecap="round" filter="url(#glow)">
    <path d="M 42 -1 C 32 8, 14 12, -8 18 C -24 22, -40 20, -56 28">
      <animateTransform attributeName="transform" type="rotate" values="0 42 -1;5 42 -1;0 42 -1" dur="2.2s" repeatCount="indefinite"/>
    </path>
    <path d="M 42 -5 C 32 -14, 14 -18, -8 -22 C -24 -25, -40 -22, -56 -30">
      <animateTransform attributeName="transform" type="rotate" values="0 42 -5;-5 42 -5;0 42 -5" dur="2.6s" repeatCount="indefinite"/>
    </path>
  </g>
  <!-- skull + snout -->
  <path d="M -4 -12 C 6 -18, 22 -17, 30 -10 L 42 -8 C 47 -7, 47 -1, 42 0 L 30 1 C 22 5, 6 7, -4 6 Z" fill="#DC143C"/>
  <!-- lower jaw -->
  <path d="M 2 4 L 38 4 C 35 10, 16 12, 2 9 Z" fill="#A50E2D"/>
  <path d="M 6 9 L 2 15 L 10 10 L 8 16 L 14 10 Z" fill="#8B0A24"/>
  <circle cx="43" cy="-5" r="1.6" fill="#8B0A24"/>
  <path d="M 10 -13 C 16 -15, 22 -14, 26 -11" fill="none" stroke="#8B0A24" stroke-width="2" stroke-linecap="round"/>
  <!-- eye -->
  <ellipse cx="19" cy="-7" rx="5" ry="3.6" fill="#0D1117"/>
  <g>
    <circle cx="20" cy="-7" r="2.4" fill="#00F0FF" filter="url(#glow)">
      {react("2.4;2.4;3.4;3.4;3.4;2.4;2.4", "r")}
    </circle>
    <circle cx="21" cy="-8" r="0.9" fill="#E6EDF3"/>
  </g>
  <!-- the reaction: it notices you and breathes fire -->
  <g opacity="0">
    {react("0;0;1;1;1;0;0")}
    <path d="M 44 -2 C 60 -12, 80 -16, 100 -18 C 92 -10, 104 -6, 112 -2 C 102 2, 110 8, 104 14 C 84 10, 64 8, 44 2 Z" fill="url(#fOuter)" filter="url(#fireglow)"/>
    <path d="M 44 -1 C 58 -7, 74 -9, 90 -9 C 84 -3, 90 1, 94 4 C 80 6, 64 6, 44 1 Z" fill="url(#fMid)"/>
    <path d="M 44 0 C 56 -4, 70 -4, 86 -2 C 70 3, 56 4, 44 1 Z" fill="url(#fCore)"/>
  </g>
 </g>
  <animateMotion dur="{DUR:.3f}s" begin="{HEAD_BEGIN:.3f}s" repeatCount="indefinite" rotate="auto"><mpath href="#route"/></animateMotion>
</g>'''

body = "\n".join(segment(i) for i in reversed(range(N)))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">
  <title id="t">Soplón, a long crimson Chinese-style dragon, glides across the profile, loops in the middle, looks at you and breathes fire.</title>
  <defs>
    <path id="route" d="{PATH}"/>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="fireglow" x="-30%" y="-60%" width="160%" height="220%">
      <feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <linearGradient id="fOuter" x1="44" y1="0" x2="112" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#DC143C"/><stop offset="0.55" stop-color="#FF4500"/><stop offset="1" stop-color="#FF4500" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="fMid" x1="44" y1="0" x2="94" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#FF8C00"/><stop offset="1" stop-color="#FFC300" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="fCore" x1="44" y1="0" x2="86" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#E6FFFF"/><stop offset="0.5" stop-color="#00F0FF"/><stop offset="1" stop-color="#00F0FF" stop-opacity="0"/>
    </linearGradient>
  </defs>
{body}
{head}
</svg>
'''
open("assets/dragon.svg", "w").write(svg)
print(f"L={L:.0f}px dur={DUR:.1f}s lag={LAG:.3f}s loop@{s_loop0:.0f} reaction={fa:.3f}-{fb:.3f}")


# ---- static preview frame (for checking only) ----
def preview(t_head):
    """Places every part where it would be at a head arc-length of t_head."""
    out = []
    def place(s, inner):
        s = s % L
        tt = p.ilength(min(max(s, 0), L - 1e-6))
        pt = p.point(tt)
        d = p.derivative(tt)
        ang = math.degrees(math.atan2(d.imag, d.real))
        return f'<g transform="translate({pt.real:.1f} {pt.imag:.1f}) rotate({ang:.1f})">{inner}</g>'
    import re
    for i in reversed(range(N)):
        g = segment(i)
        inner = re.sub(r"<animateMotion.*?</animateMotion>", "", g)[3:-4]
        inner = re.sub(r"<animateTransform[^>]*/>", "", inner)
        out.append(place(t_head - (i + 1) * SPACING, inner))
    hi = re.sub(r"<animateMotion.*?</animateMotion>", "", head)
    hi = re.sub(r"<animate[^>]*/>", "", hi)
    hi = hi.replace('<g opacity="0">', '<g opacity="1">')
    out.append(place(t_head, hi))
    return svg.split("\n" + body)[0] + "\n" + "\n".join(out) + "\n</svg>"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        open(sys.argv[2], "w").write(preview(float(sys.argv[1])))

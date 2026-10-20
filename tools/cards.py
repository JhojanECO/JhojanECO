"""Builds the static cards of the profile README in the same style as the header,
the stats card and the dragon calendar: section titles, the About card, one card
per featured project, the PID lab card and the tech stack.

Content lives in the constants below. Re-run after editing them:
    python tools/cards.py
Brand icons come from Simple Icons (CC0), fetched once per run.
"""
import html
import re
import urllib.request
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ICONS = "https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/{}.svg"

BG, PANEL, GRID = "#0D1117", "#161B22", "#21262D"
TEXT, MUTED = "#E6EDF3", "#8B949E"
CRIMSON, CRIMSON_LT, CYAN = "#DC143C", "#FF4D6D", "#00F0FF"
MONO = "DejaVu Sans Mono, Consolas, Menlo, monospace"
SANS = "Segoe UI, Helvetica Neue, Arial, DejaVu Sans, sans-serif"

SECTIONS = ["About", "Featured projects", "PID lab", "Tech stack", "GitHub activity"]

ABOUT = [  # (text, colour) tokens per line
    [("// Mechatronics Engineering student @ UNI", MUTED)],
    [("struct ", CRIMSON_LT), ("Jhojan", TEXT), (" {", MUTED)],
    [("  role", CYAN), ("     = ", MUTED), ('"embedded firmware for competition robots"', TEXT), (";", MUTED)],
    [("  robots", CYAN), ("[]", MUTED), (" = { ", MUTED), ('"line follower"', TEXT), (", ", MUTED), ('"mini-sumo"', TEXT), (", ", MUTED), ('"soccer"', TEXT), (" };", MUTED)],
    [("  mcu", CYAN), ("[]", MUTED), ("    = { ", MUTED), ('"ATmega328P"', TEXT), (", ", MUTED), ('"ESP32"', TEXT), (", ", MUTED), ('"STM32"', TEXT), (" };", MUTED)],
    [("  now", CYAN), ("      = ", MUTED), ('"bare-metal timers + PD on a line follower"', TEXT), (";", MUTED)],
    [("  learning", CYAN), (" = ", MUTED), ('"control theory beyond PID"', TEXT), (";", MUTED)],
    [("  open_to", CYAN), ("  = ", MUTED), ('"embedded, robotics and control projects"', TEXT), (";", MUTED)],
    [("};", MUTED)],
]

PROJECTS = [
    {
        "slug": "minisumo", "glyph": "sumo",
        "kicker": "AUTONOMOUS · ESP32", "title": "Mini-Sumo Senior",
        "text": "Autonomous mini-sumo started over Bluetooth. PID control ported from Arduino "
                "to ESP32, with separate modules for sensors, motors, status LED and strategy.",
        "tags": ["C++", "ESP32", "PlatformIO", "Bluetooth"],
    },
    {
        "slug": "soccer-senior", "glyph": "ball",
        "kicker": "PERUHUB · SENIOR", "title": "Robot Soccer Senior",
        "text": "Firmware for a senior-category soccer robot driven with a PS5 controller "
                "over classic Bluetooth, built for the PERUHUB competition.",
        "tags": ["C++", "ESP32", "Bluetooth"],
    },
    {
        "slug": "soccer-amateur", "glyph": "bluetooth",
        "kicker": "BLUETOOTH CONTROL", "title": "Robot Soccer Amateur",
        "text": "Bluetooth-controlled ESP32 soccer robot, with a step-by-step guide so new "
                "team members can build and flash it.",
        "tags": ["C++", "ESP32", "PlatformIO"],
    },
    {
        "slug": "pwm", "glyph": "pwm",
        "kicker": "ATMEGA328P · BARE-METAL", "title": "High-frequency PWM",
        "text": "Timer0, Timer1 and Timer2 set up for fast PWM, with a small API to set "
                "each channel's duty cycle directly.",
        "tags": ["C++", "ATmega328P", "Registers"],
    },
]

STACK = [
    ("LANGUAGES", [("C++", "cplusplus"), ("C", "c"), ("Python", "python")]),
    ("MICROCONTROLLERS", [("ATmega328P", "chip"), ("ESP32", "espressif"), ("STM32", "stmicroelectronics")]),
    ("TOOLS", [("PlatformIO", "platformio"), ("Arduino", "arduino"), ("Git", "git"),
               ("GitHub", "github"), ("VS Code", "code"), ("Obsidian", "obsidian")]),
]

GLOW = ('<filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="1.6" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')


def esc(s):
    return html.escape(s, quote=False)


def mono_w(text, size, spacing=0.0):
    return len(text) * (size * 0.602 + spacing)


def svg(w, h, title, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-labelledby="t">\n'
            f'  <title id="t">{esc(title)}</title>\n  <defs>{GLOW}{defs}</defs>\n{body}\n</svg>\n')


def card_bg(w, h, rx=18):
    return (f'  <rect width="{w}" height="{h}" rx="{rx}" fill="{BG}"/>\n'
            f'  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="none" stroke="{GRID}"/>')


def wrap(text, chars):
    lines, cur = [], ""
    for word in text.split():
        if len(cur) + len(word) + 1 > chars and cur:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + [cur]


# ---------------------------------------------------------------- section titles
def section(i, label):
    w, h = 1000, 44
    lx = 66 + mono_w(label.upper(), 14, 3)
    body = f'''{card_bg(w, h, 12)}
  <text x="24" y="28" font-family="{MONO}" font-size="13" fill="{CYAN}">{i:02d}</text>
  <text x="58" y="28" font-family="{MONO}" font-size="14" fill="{TEXT}" letter-spacing="3">{esc(label.upper())}</text>
  <rect x="{lx + 14:.0f}" y="21" width="{w - lx - 38:.0f}" height="2" fill="url(#line)"/>
  <g filter="url(#glow)">
    <circle cy="22" r="3" fill="{CYAN}">
      <animate attributeName="cx" values="{lx + 20:.0f};{w - 30};{lx + 20:.0f}" dur="9s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/>
    </circle>
  </g>'''
    defs = (f'<linearGradient id="line" x1="0" x2="1"><stop offset="0" stop-color="{CRIMSON}"/>'
            f'<stop offset="1" stop-color="{CRIMSON}" stop-opacity="0"/></linearGradient>')
    return svg(w, h, label, body, defs)


# ---------------------------------------------------------------- about
def about():
    w, top, lh, size = 1000, 84, 25, 15
    h = top + lh * len(ABOUT) + 22
    per_line, total = 0.32, 0.32 * len(ABOUT) + 0.3
    rows, clips = [], []
    for i, tokens in enumerate(ABOUT):
        y = top + i * lh
        text = "".join(f'<tspan fill="{c}"{" font-style=\"italic\"" if c == MUTED and t.startswith("//") else ""}>{esc(t)}</tspan>' for t, c in tokens)
        width = mono_w("".join(t for t, _ in tokens), size) + 12
        a, b = i * per_line / total, (i + 1) * per_line / total
        clips.append(f'<clipPath id="l{i}"><rect x="76" y="{y - 18}" height="{lh}" width="{width:.0f}">'
                     f'<animate attributeName="width" dur="{total:.2f}s" fill="freeze" values="0;0;{width:.0f}" keyTimes="0;{a:.3f};{b:.3f}"/></rect></clipPath>')
        rows.append(f'  <text x="56" y="{y}" font-family="{MONO}" font-size="13" fill="{GRID}" text-anchor="end">{i + 1}</text>'
                    f'<text x="80" y="{y}" font-family="{MONO}" font-size="{size}" xml:space="preserve" clip-path="url(#l{i})">{text}</text>')
    cursor_x = 80 + mono_w("};", size) + 4
    cursor_y = top + (len(ABOUT) - 1) * lh - 14

    # a little line follower running laps, right side
    tx, ty, tw, tr = 768, 130, 120, 46
    track = f"M {tx} {ty} h {tw} a {tr} {tr} 0 0 1 0 {2 * tr} h {-tw} a {tr} {tr} 0 0 1 0 {-2 * tr} Z"
    robot = f'''
  <g>
    <rect x="-13" y="-10" width="26" height="20" rx="5" fill="{PANEL}" stroke="{TEXT}" stroke-width="1.2"/>
    <rect x="-9" y="-13" width="10" height="4" rx="1.5" fill="{TEXT}"/><rect x="-9" y="9" width="10" height="4" rx="1.5" fill="{TEXT}"/>
    <rect x="10" y="-9" width="4" height="18" rx="2" fill="{CYAN}" filter="url(#glow)"/>
    <animateMotion dur="7s" repeatCount="indefinite" rotate="auto" path="{track}"/>
  </g>'''
    body = f'''{card_bg(w, h)}
  <path d="M 18 0.5 H {w - 18} A 17.5 17.5 0 0 1 {w - 0.5} 18 V 44 H 0.5 V 18 A 17.5 17.5 0 0 1 18 0.5 Z" fill="{PANEL}"/>
  <rect x="24" y="10" width="150" height="34" fill="{BG}"/>
  <rect x="24" y="10" width="150" height="2" fill="{CRIMSON}"/>
  <circle cx="44" cy="28" r="4" fill="{CYAN}" filter="url(#glow)"/>
  <text x="58" y="33" font-family="{MONO}" font-size="13" fill="{TEXT}">about.hpp</text>
  <text x="{w - 28}" y="33" font-family="{MONO}" font-size="12" fill="{MUTED}" text-anchor="end">C++  ·  UTF-8</text>
{chr(10).join(rows)}
  <rect x="{cursor_x:.0f}" y="{cursor_y}" width="9" height="18" fill="{CYAN}" opacity="0.85">
    <animate attributeName="opacity" values="0.85;0;0.85" dur="1.1s" begin="{total:.2f}s" repeatCount="indefinite" calcMode="discrete"/>
  </rect>
  <path d="{track}" fill="none" stroke="{CRIMSON}" stroke-width="5" stroke-linejoin="round" filter="url(#glow)"/>
  {robot}
  <text x="{tx + tw / 2}" y="{ty + 2 * tr + 40}" font-family="{MONO}" font-size="12" fill="{MUTED}" text-anchor="middle">while (1) follow_line();</text>'''
    title = ("About Jhojan, written as a C++ struct: Mechatronics Engineering student at UNI who writes embedded firmware "
             "for competition robots (line follower, mini-sumo, soccer) on ATmega328P, ESP32 and STM32. Now: bare-metal timers "
             "and PD control on a line follower. Learning: control theory beyond PID. Open to embedded, robotics and control projects.")
    return svg(w, h, title, body, "".join(clips))


# ---------------------------------------------------------------- projects
GLYPHS = {
    "sumo": '<circle r="22"/><circle r="15" stroke-dasharray="2 4"/><path d="M -6 -6 V 6 M 6 -6 V 6"/>',
    "ball": ('<circle r="22"/><path d="M 0 -7 L 6.7 -2.2 L 4.1 5.7 L -4.1 5.7 L -6.7 -2.2 Z"/>'
             '<path d="M 0 -7 V -22 M 6.7 -2.2 L 20.9 -6.8 M 4.1 5.7 L 12.9 17.8 M -4.1 5.7 L -12.9 17.8 M -6.7 -2.2 L -20.9 -6.8"/>'),
    "bluetooth": '<circle r="22"/><path d="M -7 -8 L 7 6 L 0 13 V -13 L 7 -6 L -7 8"/>',
    "pwm": '<path d="M -26 10 H -18 V -10 H -8 V 10 H -2 V -10 H 12 V 10 H 16 V -10 H 26"/>',
}


def project(p):
    w, h = 492, 214
    lines = wrap(p["text"], 60)[:3]
    desc = "".join(f'<tspan x="28" dy="{0 if i == 0 else 20}">{esc(l)}</tspan>' for i, l in enumerate(lines))
    chips, x = [], 28
    for tag in p["tags"]:
        cw = mono_w(tag, 12) + 22
        chips.append(f'<rect x="{x}" y="166" width="{cw:.0f}" height="26" rx="13" fill="{PANEL}" stroke="{GRID}"/>'
                     f'<text x="{x + cw / 2:.0f}" y="183" font-family="{MONO}" font-size="12" fill="{TEXT}" text-anchor="middle">{esc(tag)}</text>')
        x += cw + 8
    body = f'''{card_bg(w, h, 16)}
  <rect x="0" y="28" width="3" height="40" rx="1.5" fill="{CRIMSON}"/>
  <text x="28" y="42" font-family="{MONO}" font-size="12" fill="{CRIMSON_LT}" letter-spacing="2">{esc(p["kicker"])}</text>
  <text x="28" y="74" font-family="{SANS}" font-size="23" font-weight="700" fill="{TEXT}">{esc(p["title"])}</text>
  <text y="102" font-family="{SANS}" font-size="14" fill="{MUTED}">{desc}</text>
  {"".join(chips)}
  <g transform="translate(436 54)" fill="none" stroke="{CYAN}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow)" opacity="0.9">{GLYPHS[p["glyph"]]}</g>
  <text x="{w - 24}" y="184" font-family="{MONO}" font-size="12" fill="{CYAN}" text-anchor="end">repo ↗</text>'''
    return svg(w, h, f'{p["title"]}: {p["text"]} Built with {", ".join(p["tags"])}.', body)


# ---------------------------------------------------------------- PID lab
def lab():
    w, h = 1000, 224
    sliders = [("Kp", "0.08", 0.13), ("Ki", "0.00", 0.0), ("Kd", "0.20", 0.02)]
    rows = []
    for i, (name, val, f) in enumerate(sliders):
        y = 62 + i * 30
        x0, x1 = 600, 880
        kx = x0 + max(0.06, f * 4) * (x1 - x0)
        rows.append(f'<text x="572" y="{y + 4}" font-family="{MONO}" font-size="12" fill="{MUTED}">{name}</text>'
                    f'<rect x="{x0}" y="{y - 2}" width="{x1 - x0}" height="4" rx="2" fill="{GRID}"/>'
                    f'<rect x="{x0}" y="{y - 2}" width="{kx - x0:.0f}" height="4" rx="2" fill="{CRIMSON}"/>'
                    f'<circle cx="{kx:.0f}" cy="{y}" r="6" fill="{CYAN}" filter="url(#glow)"/>'
                    f'<text x="{x1 + 52}" y="{y + 4}" font-family="{MONO}" font-size="12" fill="{TEXT}" text-anchor="end">{val}</text>')
    track = "M 520 178 C 600 150, 660 200, 740 176 S 860 150, 980 176"
    body = f'''{card_bg(w, h)}
  <text x="40" y="52" font-family="{MONO}" font-size="12" fill="{CRIMSON_LT}" letter-spacing="2">INTERACTIVE · RUNS IN YOUR BROWSER</text>
  <text x="40" y="92" font-family="{SANS}" font-size="31" font-weight="700" fill="{TEXT}">Tune my line follower</text>
  <text y="124" font-family="{SANS}" font-size="15" fill="{MUTED}"><tspan x="40">Move Kp, Ki, Kd and base PWM and watch the robot hold</tspan><tspan x="40" dy="22">the line or lose it, the same way I tune the real one.</tspan></text>
  <rect x="40" y="166" width="226" height="36" rx="9" fill="{CRIMSON}"/>
  <text x="153" y="189" font-family="{MONO}" font-size="13" font-weight="700" fill="#FFFFFF" text-anchor="middle" letter-spacing="1">OPEN THE PID LAB →</text>
  <rect x="540" y="28" width="436" height="172" rx="12" fill="{PANEL}"/>
  {"".join(rows)}
  <clipPath id="panel"><rect x="540" y="28" width="436" height="172" rx="12"/></clipPath>
  <g clip-path="url(#panel)">
    <path d="{track}" fill="none" stroke="{CRIMSON}" stroke-width="5" stroke-linecap="round" filter="url(#glow)"/>
    <g>
      <rect x="-12" y="-9" width="24" height="18" rx="5" fill="{BG}" stroke="{TEXT}" stroke-width="1.2"/>
      <rect x="9" y="-8" width="4" height="16" rx="2" fill="{CYAN}" filter="url(#glow)"/>
      <animateMotion dur="5s" repeatCount="indefinite" rotate="auto" path="{track}"/>
    </g>
  </g>'''
    return svg(w, h, "Tune my line follower: an interactive PID lab that runs in the browser. Open it to change Kp, Ki, Kd and base PWM.", body)


# ---------------------------------------------------------------- tech stack
def icon(slug):
    if slug == "code":
        return f'<text x="8" y="13" font-family="{MONO}" font-size="12" font-weight="700" fill="{CYAN}" text-anchor="middle">&lt;/&gt;</text>'
    if slug == "chip":
        pins = "".join(f'<path d="M {x} 1 V 3 M {x} 13 V 15 M 1 {x} H 3 M 13 {x} H 15"/>' for x in (5, 8, 11))
        return (f'<g fill="none" stroke="{CYAN}" stroke-width="1.4" stroke-linecap="round"><rect x="3.5" y="3.5" width="9" height="9" rx="1.5"/>{pins}</g>'
                f'<circle cx="6" cy="6" r="1" fill="{CYAN}"/>')
    with urllib.request.urlopen(ICONS.format(slug), timeout=20) as r:
        d = re.search(r' d="([^"]+)"', r.read().decode()).group(1)
    return f'<path transform="scale(0.6667)" d="{d}" fill="{CYAN}"/>'


def stack():
    w, h = 1000, 196
    rows = []
    for i, (label, items) in enumerate(STACK):
        y = 34 + i * 50
        rows.append(f'<text x="40" y="{y + 22}" font-family="{MONO}" font-size="12" fill="{MUTED}" letter-spacing="2">{label}</text>')
        x = 250
        for name, slug in items:
            cw = 44 + len(name) * 8.2
            rows.append(f'<rect x="{x}" y="{y}" width="{cw:.0f}" height="34" rx="9" fill="{PANEL}" stroke="{GRID}"/>'
                        f'<g transform="translate({x + 14} {y + 9})">{icon(slug)}</g>'
                        f'<text x="{x + 38}" y="{y + 22}" font-family="{SANS}" font-size="14" fill="{TEXT}">{esc(name)}</text>')
            x += cw + 10
    names = "; ".join(f'{label.title()}: {", ".join(n for n, _ in items)}' for label, items in STACK)
    return svg(w, h, f"Tech stack. {names}.", f"{card_bg(w, h)}\n  " + "\n  ".join(rows))


if __name__ == "__main__":
    out = {f"title-{i + 1}.svg": section(i + 1, s) for i, s in enumerate(SECTIONS)}
    out["about.svg"] = about()
    out.update({f"project-{p['slug']}.svg": project(p) for p in PROJECTS})
    out["lab.svg"] = lab()
    out["stack.svg"] = stack()
    for name, content in out.items():
        (ASSETS / name).write_text(content, encoding="utf-8")
        print("wrote assets/" + name)

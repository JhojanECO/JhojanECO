"""Builds assets/stats.svg (activity + top languages) from the GitHub GraphQL API,
in the same palette as the header and footer.

Runs daily from .github/workflows/profile-stats.yml. To run locally:
    GITHUB_TOKEN=$(gh auth token) python tools/stats_card.py
"""
import json
import os
import urllib.request
from pathlib import Path

LOGIN = "JhojanECO"
OUT = Path(__file__).resolve().parent.parent / "assets" / "stats.svg"
EXCLUDE = {"HTML", "CSS", "SCSS", "Jupyter Notebook", "Makefile", "CMake", "Batchfile", "Shell"}
EXCLUDE_REPOS = {LOGIN, "FOW"}  # profile repo + web work, so the bar shows firmware
TOP_N = 5

BG, PANEL, GRID = "#0D1117", "#161B22", "#21262D"
TEXT, MUTED = "#E6EDF3", "#8B949E"
CRIMSON, CYAN = "#DC143C", "#00F0FF"
RAMP = [CRIMSON, CYAN, "#E6EDF3", "#FF6B81", "#8B949E"]
FONT = "DejaVu Sans Mono, Consolas, Menlo, monospace"

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar { totalContributions }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        name
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


def fetch():
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body:
        raise SystemExit(body["errors"])
    return body["data"]["user"]


def summarize(u):
    repos = u["repositories"]["nodes"]
    langs = {}
    for repo in repos:
        if repo["name"] in EXCLUDE_REPOS:
            continue
        for e in repo["languages"]["edges"]:
            name = e["node"]["name"]
            if name not in EXCLUDE:
                langs[name] = langs.get(name, 0) + e["size"]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:TOP_N]
    cc = u["contributionsCollection"]
    return {
        "metrics": [
            ("Contributions", cc["contributionCalendar"]["totalContributions"]),
            ("Commits", cc["totalCommitContributions"]),
            ("Public repos", u["repositories"]["totalCount"]),
            ("Stars earned", sum(r["stargazerCount"] for r in repos)),
        ],
        "langs": [(name, size / total) for name, size in top],
    }


def render(s):
    W, H = 1000, 210
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">',
        "  <title id=\"t\">GitHub activity over the last 12 months: "
        + ", ".join(f"{v} {k.lower()}" for k, v in s["metrics"])
        + ". Top languages: "
        + ", ".join(f"{n} {p:.0%}" for n, p in s["langs"])
        + ".</title>",
        f'  <rect width="{W}" height="{H}" rx="18" fill="{BG}"/>',
        f'  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{GRID}"/>',
        f'  <g font-family="{FONT}">',
        f'    <text x="40" y="44" font-size="13" fill="{MUTED}" letter-spacing="2">ACTIVITY · LAST 12 MONTHS</text>',
        f'    <text x="560" y="44" font-size="13" fill="{MUTED}" letter-spacing="2">TOP LANGUAGES</text>',
    ]

    # 2x2 metric tiles
    tw, th = 228, 62
    for i, (label, value) in enumerate(s["metrics"]):
        x = 40 + (i % 2) * (tw + 12)
        y = 62 + (i // 2) * (th + 12)
        accent = CRIMSON if i % 3 == 0 else CYAN
        out += [
            f'    <rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="10" fill="{PANEL}"/>',
            f'    <rect x="{x}" y="{y + 14}" width="3" height="{th - 28}" rx="1.5" fill="{accent}"/>',
            f'    <text x="{x + 18}" y="{y + 34}" font-size="24" font-weight="bold" fill="{TEXT}">{value:,}</text>',
            f'    <text x="{x + 18}" y="{y + 52}" font-size="12" fill="{MUTED}">{label}</text>',
        ]

    out.append(f'    <line x1="530" y1="62" x2="530" y2="198" stroke="{GRID}"/>')

    # stacked language bar, grows in once on load
    bx, by, bw = 560, 66, 400
    out.append(f'    <rect x="{bx}" y="{by}" width="{bw}" height="10" rx="5" fill="{PANEL}"/>')
    out.append(f'    <clipPath id="bar"><rect x="{bx}" y="{by}" height="10" rx="5" width="0">'
               f'<animate attributeName="width" from="0" to="{bw}" dur="1.2s" fill="freeze" '
               f'calcMode="spline" keyTimes="0;1" keySplines="0.2 0.8 0.2 1"/></rect></clipPath>')
    out.append('    <g clip-path="url(#bar)">')
    cx = bx
    for i, (_, p) in enumerate(s["langs"]):
        w = bw * p / (sum(q for _, q in s["langs"]) or 1)
        out.append(f'      <rect x="{cx:.1f}" y="{by}" width="{w + 0.5:.1f}" height="10" fill="{RAMP[i % len(RAMP)]}"/>')
        cx += w
    out.append("    </g>")

    # legend, two columns
    for i, (name, p) in enumerate(s["langs"]):
        x = bx + (i % 2) * 210
        y = 112 + (i // 2) * 30
        out += [
            f'    <circle cx="{x + 6}" cy="{y - 4}" r="5" fill="{RAMP[i % len(RAMP)]}"/>',
            f'    <text x="{x + 20}" y="{y}" font-size="14" fill="{TEXT}">{name}</text>',
            f'    <text x="{x + 190}" y="{y}" font-size="14" fill="{MUTED}" text-anchor="end">{p:.1%}</text>',
        ]

    out += ["  </g>", "</svg>", ""]
    return "\n".join(out)


if __name__ == "__main__":
    OUT.write_text(render(summarize(fetch())), encoding="utf-8")
    print(f"wrote {OUT}")

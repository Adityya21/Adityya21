#!/usr/bin/env python3
"""Draws the animated SVG cards used in README.md. Python standard library only.

Sources (nothing else is used):
  portfolio : https://adityayashovardhan.vercel.app/   -> project count
  GitHub    : contribution calendar + repo info         -> heatmap, activity, repo cards, repo count
  LeetCode  : public GraphQL                            -> problems solved

If a source can't be reached, the last good value in cards/stats.json is reused.
Run locally:  GITHUB_TOKEN=<token> python scripts/render_readme_cards.py
"""
import datetime as dt
import html
import json
import math
import os
import pathlib
import re
import textwrap
import urllib.request

USER = "Adityya21"
LEETCODE = "fvgKStlmkk"
NAME = "Aditya Yashovardhan"
TAGLINE = "B.Tech Computer Science student at NMIMS."
SUBLINE = "I build AI, ML and data projects."
PORTFOLIO = "https://adityayashovardhan.vercel.app/"
FEATURED = ["Bank-Churn-AI-Advisor", "Multi-Agent-AI-Research-System", "AI-Stock-Price-Predictor"]
FALLBACK_DESC = {
    "Bank-Churn-AI-Advisor": "XGBoost churn model (AUC 0.91) explained by SHAP, with Llama 3.1 retention strategies.",
    "Multi-Agent-AI-Research-System": "Multi-agent research automation with LangChain, Groq and Tavily.",
    "AI-Stock-Price-Predictor": "Multi-model stock prediction: Bi-LSTM-GRU, Random Forest and XGBoost.",
}

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
OUT = pathlib.Path("cards")
OUT.mkdir(exist_ok=True)
CACHE_FILE = OUT / "stats.json"

BG, BORDER, TEXT, MUTED, ACCENT = "#0b1220", "#1e2a44", "#e6edf7", "#8fa3c2", "#4da3ff"
LEVELS = ["#131c2e", "#0e3a6e", "#1558a8", "#2b7fe0", "#5aa9ff"]


# ---------- fetching ----------
def http(url, data=None, headers=None):
    h = {"User-Agent": "Mozilla/5.0 (profile-cards)"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def gh_headers():
    return {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}


def fetch_calendar():
    q = ("query($l:String!){user(login:$l){contributionsCollection{contributionCalendar{"
         "weeks{contributionDays{date contributionCount}}}}}}")
    body = json.dumps({"query": q, "variables": {"l": USER}}).encode()
    hdr = dict(gh_headers(), **{"Content-Type": "application/json"})
    d = json.loads(http("https://api.github.com/graphql", body, hdr))
    weeks = d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return {x["date"]: x["contributionCount"] for w in weeks for x in w["contributionDays"]}


def fetch_leetcode():
    q = ("query($u:String!){matchedUser(username:$u){submitStatsGlobal{"
         "acSubmissionNum{difficulty count}}}}")
    body = json.dumps({"query": q, "variables": {"u": LEETCODE}}).encode()
    d = json.loads(http("https://leetcode.com/graphql", body,
                        {"Content-Type": "application/json", "Referer": "https://leetcode.com"}))
    rows = d["data"]["matchedUser"]["submitStatsGlobal"]["acSubmissionNum"]
    return {r["difficulty"]: r["count"] for r in rows}


def fetch_portfolio_projects():
    page = http(PORTFOLIO)
    slugs = set(re.findall(r"github\.com/%s/([A-Za-z0-9_.\-]+)" % USER, page))
    return len(slugs)


def fetch_repo(name):
    d = json.loads(http(f"https://api.github.com/repos/{USER}/{name}", headers=gh_headers()))
    return {"desc": d.get("description") or "", "lang": d.get("language") or "",
            "stars": d.get("stargazers_count", 0)}


def fetch_public_repos():
    d = json.loads(http(f"https://api.github.com/users/{USER}", headers=gh_headers()))
    return d["public_repos"]


def load_cache():
    try:
        return json.loads(CACHE_FILE.read_text())
    except Exception:
        return {}


def safe(label, fn, *a):
    try:
        return fn(*a)
    except Exception as e:  # network, rate limit, bot block...
        print(f"[warn] {label}: {e}")
        return None


# ---------- svg helpers ----------
def esc(s):
    return html.escape(str(s), quote=True)


def svg(w, h, body, css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">'
            "<style>"
            "text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace}"
            ".fade{opacity:0;animation:fade .7s ease forwards}"
            "@keyframes fade{to{opacity:1}}"
            "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}"
            "@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}"
            ".grow{transform-box:fill-box;transform-origin:bottom;animation:grow .9s ease backwards}"
            f"{css}</style>"
            f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="14" fill="{BG}" stroke="{BORDER}"/>'
            f"{body}</svg>")


def write(name, content):
    (OUT / name).write_text(content, encoding="utf-8")


def t(x, y, s, size=12, fill=TEXT, weight="normal", anchor="start", cls="", delay=0):
    style = f' style="animation-delay:{delay}s"' if cls else ""
    c = f' class="{cls}"' if cls else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}"{c}{style}>{esc(s)}</text>')


# ---------- cards ----------
def hero():
    body = (
        t(40, 70, "aditya@github ~ $ whoami", 13, MUTED, cls="fade", delay=0.1)
        + t(40, 125, NAME, 44, TEXT, "bold", cls="fade", delay=0.4)
        + t(40, 160, TAGLINE, 17, ACCENT, cls="fade", delay=0.8)
        + t(40, 186, SUBLINE, 15, MUTED, cls="fade", delay=1.1)
        + f'<circle cx="716" cy="46" r="5" fill="#3ddc84" style="animation:pulse 1.8s infinite"/>'
        + t(730, 51, "Open to opportunities", 13, TEXT)
    )
    write("hero.svg", svg(900, 220, body))


def grid_days():
    today = dt.date.today()
    sunday = today - dt.timedelta(days=(today.weekday() + 1) % 7)
    start = sunday - dt.timedelta(weeks=52)
    return today, start


def heatmap(days):
    today, start = grid_days()
    counts = [days.get((start + dt.timedelta(d)).isoformat(), 0) for d in range(53 * 7)]
    peak = max(counts) or 1
    cells = []
    for w in range(53):
        for d in range(7):
            date = start + dt.timedelta(weeks=w, days=d)
            if date > today:
                continue
            c = days.get(date.isoformat(), 0)
            lvl = 0 if c == 0 else min(4, max(1, math.ceil(4 * c / peak)))
            cells.append(f'<rect class="fade" style="animation-delay:{w*0.03:.2f}s" x="{40+w*15}" y="{58+d*15}" '
                         f'width="12" height="12" rx="2.5" fill="{LEVELS[lvl]}"><title>{date}: {c}</title></rect>')
    legend = t(700, 178, "less", 10, MUTED, "normal", "end")
    legend += "".join(f'<rect x="{710+i*16}" y="169" width="12" height="12" rx="2.5" fill="{c}"/>'
                      for i, c in enumerate(LEVELS))
    legend += t(796, 178, "more", 10, MUTED)
    body = (t(40, 34, "aditya@github ~ $ ./contributions.sh", 13, MUTED)
            + t(860, 34, f"{sum(counts)} in the last year", 13, ACCENT, "bold", "end")
            + "".join(cells) + legend)
    write("heatmap.svg", svg(900, 200, body))


def streaks(days):
    today, start = grid_days()
    seq = [(start + dt.timedelta(d)) for d in range(53 * 7) if start + dt.timedelta(d) <= today]
    longest = run = 0
    for d in seq:
        run = run + 1 if days.get(d.isoformat(), 0) > 0 else 0
        longest = max(longest, run)
    cur = 0
    for d in reversed(seq):
        if days.get(d.isoformat(), 0) > 0:
            cur += 1
        elif d == today:
            continue  # today may still be empty
        else:
            break
    return cur, longest


def activity(days):
    today, _ = grid_days()
    months = []
    y, m = today.year, today.month
    for _ in range(12):
        months.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    months.reverse()
    totals = [sum(v for k, v in days.items() if k.startswith(f"{yy}-{mm:02d}")) for yy, mm in months]
    peak = max(totals) or 1
    bars = ""
    for i, ((yy, mm), v) in enumerate(zip(months, totals)):
        h = max(3, int(100 * v / peak))
        x = 40 + i * 50
        bars += (f'<rect class="grow" style="animation-delay:{i*0.07:.2f}s" x="{x}" y="{150-h}" width="32" '
                 f'height="{h}" rx="4" fill="{ACCENT if v == peak else LEVELS[3]}"/>')
        bars += t(x + 16, 146 - h, v, 10, MUTED, anchor="middle")
        bars += t(x + 16, 172, dt.date(yy, mm, 1).strftime("%b"), 10, MUTED, anchor="middle")
    cur, longest = streaks(days)
    busiest = max(days.items(), key=lambda kv: kv[1], default=("-", 0))
    side = (t(680, 70, "current streak", 11, MUTED) + t(680, 92, f"{cur} days", 20, TEXT, "bold")
            + t(680, 122, "longest streak", 11, MUTED) + t(680, 144, f"{longest} days", 20, TEXT, "bold")
            + t(680, 174, "busiest day", 11, MUTED) + t(680, 196, f"{busiest[1]} · {busiest[0]}", 14, ACCENT, "bold"))
    body = t(40, 34, "aditya@github ~ $ ./activity.sh", 13, MUTED) + bars + side
    write("activity.svg", svg(900, 220, body))


def stat_card(fname, label, value, caption, source):
    body = (t(24, 36, label, 12, MUTED, "bold")
            + t(24, 92, value, 46, ACCENT, "bold", cls="fade", delay=0.3)
            + t(24, 118, caption, 13, TEXT)
            + t(24, 138, f"source: {source}", 10, MUTED))
    write(fname, svg(300, 150, body))


def title_cards():
    for mode, fill in (("dark", "#e6edf7"), ("light", "#1f2a3d")):
        body = (f'<text x="450" y="38" font-size="24" font-weight="bold" fill="{fill}" text-anchor="middle" '
                f'font-family="ui-monospace,Menlo,Consolas,monospace">What I\'m coding</text>')
        s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 60" width="900" height="60" role="img">'
             f"{body}</svg>")
        write(f"title-coding-{mode}.svg", s)


def repo_card(name, info):
    desc = info.get("desc") or FALLBACK_DESC.get(name, "")
    lines = textwrap.wrap(desc, 36)[:3]
    body = t(24, 36, name, 14, TEXT, "bold")
    body += "".join(t(24, 62 + i * 18, ln, 12, MUTED) for i, ln in enumerate(lines))
    meta = info.get("lang", "")
    if meta:
        body += f'<circle cx="30" cy="132" r="5" fill="{ACCENT}"/>' + t(42, 136, meta, 11, TEXT)
    body += t(276, 136, f"★ {info.get('stars', 0)}", 11, MUTED, anchor="end")
    write(f"repo-{name.lower()}.svg", svg(300, 150, body))


# ---------- main ----------
def main():
    cache = load_cache()

    for key, label, fn in (("days", "github calendar", fetch_calendar),
                           ("leetcode", "leetcode", fetch_leetcode),
                           ("projects", "portfolio", fetch_portfolio_projects),
                           ("public_repos", "github profile", fetch_public_repos)):
        val = safe(label, fn)
        if val:
            cache[key] = val
    repos = cache.setdefault("repos", {})
    for name in FEATURED:
        info = safe(f"repo {name}", fetch_repo, name)
        if info:
            repos[name] = info

    days = cache.get("days", {})
    lc = cache.get("leetcode", {})
    projects = cache.get("projects") or 9

    hero()
    heatmap(days)
    activity(days)
    stat_card("build.svg", "BUILD", f"{projects}+", "projects on my portfolio", "portfolio")
    stat_card("code.svg", "CODE", str(cache.get("public_repos", "—")), "public repos on GitHub", "github")
    stat_card("solve.svg", "SOLVE", str(lc.get("All", "—")), "LeetCode problems solved", "leetcode")
    title_cards()
    for name in FEATURED:
        repo_card(name, repos.get(name, {}))

    CACHE_FILE.write_text(json.dumps(cache, indent=1))
    print("cards written to", OUT)


if __name__ == "__main__":
    main()

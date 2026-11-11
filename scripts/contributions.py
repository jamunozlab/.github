
import os
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from collections import Counter
from pathlib import Path

ORG = "jamunozlab"
TOKEN = os.environ["GITHUB_TOKEN"]
today = datetime.now(timezone.utc).date()
start = today - timedelta(days=364)
counts = Counter()

def get_pages(url):
    while url:
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "lab-contributions"
        })
        with urllib.request.urlopen(req) as res:
            data = json.load(res)
            links = res.headers.get("Link", "")
        yield from data
        url = next(
            (p.split(";")[0].strip(" <>")
             for p in links.split(",")
             if 'rel="next"' in p), None
        )

repos = get_pages(
    f"https://api.github.com/orgs/{ORG}/repos"
    "?type=public&per_page=100"
)

for repo in repos:
    if repo["fork"] or not repo["default_branch"]:
        continue

    name = repo["name"]
    url = (
        f"https://api.github.com/repos/{ORG}/{name}/commits"
        f"?sha={repo['default_branch']}"
        f"&since={start.isoformat()}T00:00:00Z&per_page=100"
    )
    for commit in get_pages(url):
        day = commit["commit"]["author"]["date"][:10]
        counts[day] += 1

calendar_start = start - timedelta(
    days=(start.weekday() + 1) % 7
)

colors = [
    "#ebedf0", "#9be9a8", "#40c463",
    "#30a14e", "#216e39"
]

rects = []
for i in range((today - calendar_start).days + 1):
    day = calendar_start + timedelta(days=i)
    count = counts[day.isoformat()]
    level = (
        0 if count == 0 else
        1 if count <= 2 else
        2 if count <= 5 else
        3 if count <= 10 else 4
    )
    x = 18 + (i // 7) * 14
    y = 28 + (i % 7) * 14
    rects.append(
        f'<rect x="{x}" y="{y}" width="11" '
        f'height="11" rx="2" fill="{colors[level]}">'
        f'<title>{day}: {count} commits</title></rect>'
    )

svg = (
    '<svg xmlns="http://www.w3.org/2000/svg" '
    'width="800" height="140" viewBox="0 0 800 140">'
    '<text x="18" y="17" font-size="13" '
    'fill="#57606a">Lab commits — last 365 days</text>'
    + "".join(rects) + "</svg>"
)

Path("profile").mkdir(exist_ok=True)
Path("profile/contributions.svg").write_text(svg)

#!/usr/bin/env python3
"""Build the static site into _site/.
Inputs: config.json, glossary.json, posts/YYYY-MM-DD.html (first line: <!--meta {json} -->), static/
SITE_URL: env SITE_URL, else derived from GITHUB_REPOSITORY (owner/repo) -> https://owner.github.io/repo/
"""
import json, os, re, shutil, html, pathlib, unicodedata

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "_site"
cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
glossary = json.loads((ROOT / "glossary.json").read_text(encoding="utf-8"))

def site_url():
    u = os.environ.get("SITE_URL")
    if u:
        return u.rstrip("/") + "/"
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        if name.lower() == f"{owner.lower()}.github.io":
            return f"https://{owner.lower()}.github.io/"
        return f"https://{owner.lower()}.github.io/{name}/"
    return "http://localhost:8000/"

BASE = site_url()

# Title rules: one topic per line, max 3 lines, each line <= 30 width units
# (full-width char = 2, half-width = 1  -> about 15 Japanese chars)
TITLE_MAX_LINES = 3
TITLE_MAX_WIDTH = 30

def _w(ch):
    return 2 if unicodedata.east_asian_width(ch) in "WFA" else 1

def title_lines(title, slug=""):
    lines = [x.strip() for x in title.split("／") if x.strip()]
    if len(lines) > TITLE_MAX_LINES:
        print(f"WARN {slug}: title has {len(lines)} lines, keeping {TITLE_MAX_LINES}")
        lines = lines[:TITLE_MAX_LINES]
    out = []
    for ln in lines:
        if sum(_w(c) for c in ln) > TITLE_MAX_WIDTH:
            print(f"WARN {slug}: title line too long, truncated: {ln}")
            acc, cut = 0, ""
            for c in ln:
                if acc + _w(c) > TITLE_MAX_WIDTH - 2:
                    break
                acc += _w(c)
                cut += c
            ln = cut + "…"
        out.append(ln)
    return out

def title_html(title, slug=""):
    return "".join('<span class="line">' + html.escape(x) + '</span>' for x in title_lines(title, slug))

esc = html.escape
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700;800&family=JetBrains+Mono:wght@500;700&display=swap">'

def head(title, desc, url, rel, og_type="article"):
    tw = f'<meta name="twitter:site" content="@{esc(cfg["x_handle"])}">' if cfg.get("x_handle") else ""
    return f"""<!doctype html>
<html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(cfg['site_title'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}static/ogp.png">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">{tw}
<link rel="alternate" type="application/rss+xml" title="{esc(cfg['site_title'])}" href="{BASE}feed.xml">
{FONTS}
<link rel="stylesheet" href="{rel}static/style.css">
</head><body><div class="wrap">
<div class="mast"><a href="{rel}"><p class="logo"><span class="prompt">&gt;_</span>{esc(cfg['site_title'])}</p></a><span class="tag">// security × tech, every morning</span></div>
"""

FOOT = """<footer>記事は公開時点の情報です。対応する前に、出典の公式発表を確認してください。黄色いマーカーの用語はタップで解説が出ます。</footer>
</div></body></html>"""

SHEET = """<div class="sheet" id="sheet" hidden role="dialog" aria-live="polite"><div class="in">
<div class="t"><b id="sT"></b><span id="sS"></span></div><p id="sL"></p>
<div class="ctrl"><button class="btn" id="sX" type="button">閉じる</button></div>
</div></div>"""

def load_posts():
    posts = []
    for p in sorted((ROOT / "posts").glob("*.html"), reverse=True):
        txt = p.read_text(encoding="utf-8")
        m = re.match(r"\s*<!--meta\s+(\{.*?\})\s*-->", txt, re.S)
        if not m:
            raise SystemExit(f"meta missing: {p}")
        meta = json.loads(m.group(1))
        meta["slug"] = p.stem
        meta["body"] = txt[m.end():]
        posts.append(meta)
    return posts

def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "posts").mkdir(parents=True)
    shutil.copytree(ROOT / "static", OUT / "static")
    shutil.copy(ROOT / "glossary.json", OUT / "glossary.json")
    gl_json = json.dumps(glossary, ensure_ascii=False).replace("</", "<\\/")
    posts = load_posts()
    for p in posts:
        url = f"{BASE}posts/{p['slug']}.html"
        plain_title = " / ".join(title_lines(p["title"]))
        page = head(f"{plain_title}｜{cfg['site_title']} {p['date']}", p["summary"], url, "../")
        page += f'<span class="date">{esc(p["date"])}</span>\n'
        page += f'<h1 class="title">{title_html(p["title"], p["slug"])}</h1>\n'
        page += f'<div id="article">{p["body"]}</div>\n'
        page += '<section class="gl"><h2>この記事の用語</h2><ul id="gllist"></ul></section>\n'
        page += FOOT.replace("</div></body>", f'</div>{SHEET}<script type="application/json" id="glossary-data">{gl_json}</script><script src="../static/glossary.js"></script></body>')
        (OUT / "posts" / f"{p['slug']}.html").write_text(page, encoding="utf-8")
    # index
    page = head(cfg["site_title"], cfg["site_description"], BASE, "", "website")
    page += f'<p class="lead">{esc(cfg["site_description"])}</p>\n<ul class="list">\n'
    for p in posts:
        page += f'<li><a href="posts/{p["slug"]}.html"><div class="card"><span class="date">{esc(p["date"])}</span><h2 class="title">{title_html(p["title"], p["slug"])}</h2><p>{esc(p["summary"])}</p></div></a></li>\n'
    page += "</ul>\n" + FOOT
    (OUT / "index.html").write_text(page, encoding="utf-8")
    # RSS
    items = "".join(
        f"<item><title>{esc(' / '.join(title_lines(p['title'])))}</title><link>{BASE}posts/{p['slug']}.html</link><guid>{BASE}posts/{p['slug']}.html</guid><pubDate>{p['date']}</pubDate><description>{esc(p['summary'])}</description></item>"
        for p in posts[:30])
    (OUT / "feed.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{esc(cfg["site_title"])}</title><link>{BASE}</link><description>{esc(cfg["site_description"])}</description>{items}</channel></rss>',
        encoding="utf-8")
    (OUT / ".nojekyll").write_text("")
    print(f"built {len(posts)} posts -> {OUT} (base {BASE})")

if __name__ == "__main__":
    build()

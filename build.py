#!/usr/bin/env python3
"""Build the static site into _site/.  (v6: SEO + analytics)
Inputs: config.json, glossary.json, posts/YYYY-MM-DD.html (first line: <!--meta {json} -->), static/
Optional: site_ids.json {"google_site_verification": "", "goatcounter": "", "show_counter": false}
SITE_URL: env SITE_URL, else derived from GITHUB_REPOSITORY (owner/repo) -> https://owner.github.io/repo/
v6 adds: sitemap.xml, robots.txt, NewsArticle JSON-LD, about page, Search Console meta, GoatCounter tag.
"""
import json, os, re, shutil, html, pathlib, unicodedata

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "_site"
cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8-sig"))
glossary = json.loads((ROOT / "glossary.json").read_text(encoding="utf-8-sig"))
_ids = ROOT / "site_ids.json"
ids = json.loads(_ids.read_text(encoding="utf-8-sig")) if _ids.exists() else {}
GSV = (ids.get("google_site_verification") or "").strip()
GC = (ids.get("goatcounter") or "").strip()
SHOW_COUNTER = bool(ids.get("show_counter")) and bool(GC)
PUB_TIME = "T08:20:00+09:00"  # publish time of the daily post (JST)

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
# (full-width char = 2, half-width = 1 -> about 15 Japanese chars)
# A line starting with "T:" is a tech topic (blue marker + TECH badge).
TITLE_MAX_LINES = 3
TITLE_MAX_WIDTH = 30

def _w(ch):
    return 2 if unicodedata.east_asian_width(ch) in "WFA" else 1

def title_lines(title, slug=""):
    raw = [x.strip() for x in title.split("／") if x.strip()]
    if len(raw) > TITLE_MAX_LINES:
        print(f"WARN {slug}: title has {len(raw)} lines, keeping {TITLE_MAX_LINES}")
        raw = raw[:TITLE_MAX_LINES]
    out = []
    for ln in raw:
        kind = "sec"
        if ln[:2] in ("T:", "T："):
            kind, ln = "tech", ln[2:].strip()
        if sum(_w(c) for c in ln) > TITLE_MAX_WIDTH:
            print(f"WARN {slug}: title line too long, truncated: {ln}")
            acc, cut = 0, ""
            for c in ln:
                if acc + _w(c) > TITLE_MAX_WIDTH - 2:
                    break
                acc += _w(c)
                cut += c
            ln = cut + "…"
        out.append((ln, kind))
    return out

def title_plain(title):
    return " / ".join(t for t, _ in title_lines(title))

def title_html(title, slug=""):
    return "".join('<span class="line ' + k + '">' + html.escape(t) + '</span>' for t, k in title_lines(title, slug))

MAX_TOPICS = 6
CAT_LABEL = {"cat-incident": "インシデント", "cat-tech": "新技術"}

def enhance_body(body, slug=""):
    """Assign ids to topics, fold facts into <details>, and build TOC + category tabs."""
    items, cat, n = [], "cat-incident", 0
    out, pos = [], 0
    tok = re.compile(r'<h2 class="part" id="(cat-[a-z]+)"|<article class="topic"([^>]*)>|<dl class="facts">(.*?)</dl>', re.S)
    for m in tok.finditer(body):
        out.append(body[pos:m.start()])
        if m.group(1):
            cat = m.group(1)
            out.append(m.group(0))
        elif m.group(2) is not None:
            n += 1
            attrs = m.group(2)
            tag = (re.search(r'data-tag="([^"]*)"', attrs) or [None, ""])[1]
            short = (re.search(r'data-short="([^"]*)"', attrs) or [None, ""])[1]
            if not short:
                h3 = re.search(r"<h3>(.*?)</h3>", body[m.end():], re.S)
                short = re.sub(r"<[^>]+>", "", h3.group(1)) if h3 else f"topic {n}"
            items.append((n, cat, short, tag))
            out.append(f'<article class="topic" id="t{n}"{attrs}>')
        else:
            out.append(f'<details class="more"><summary>詳細（対象・バージョン）</summary><dl class="facts">{m.group(3)}</dl></details>')
        pos = m.end()
    out.append(body[pos:])
    if n > MAX_TOPICS:
        print(f"WARN {slug}: {n} topics (max {MAX_TOPICS})")
    toc = '<nav class="toc" aria-label="今日のトピック"><h2>今日のトピック</h2><ol>'
    for i, c, short, tag in items:
        chip = f'<span class="tag">{html.escape(tag)}</span>' if tag else ""
        toc += f'<li class="{c}"><a href="#t{i}"><span class="tt">{short}</span>{chip}</a></li>'
    toc += "</ol></nav>"
    cats = [c for c in CAT_LABEL if f'id="{c}"' in body]
    tabs = ""
    if len(cats) > 1:
        tabs = '<nav class="tabs" aria-label="カテゴリ">' + "".join(
            f'<a href="#{c}" data-cat="{c}">{CAT_LABEL[c]}<span>{sum(1 for it in items if it[1] == c)}</span></a>' for c in cats) + "</nav>"
    return toc, tabs, "".join(out), items

esc = html.escape
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700;800&family=JetBrains+Mono:wght@500;700&display=swap">'

def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"

def head(title, desc, url, rel, og_type="article", extra=""):
    tw = f'<meta name="twitter:site" content="@{esc(cfg["x_handle"])}">' if cfg.get("x_handle") else ""
    gsv = f'<meta name="google-site-verification" content="{esc(GSV)}">' if GSV else ""
    gc = f'<script data-goatcounter="https://{esc(GC)}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>' if GC else ""
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
<meta name="twitter:card" content="summary_large_image">{tw}{gsv}
<link rel="alternate" type="application/rss+xml" title="{esc(cfg['site_title'])}" href="{BASE}feed.xml">
{FONTS}
<link rel="stylesheet" href="{rel}static/style.css">{extra}{gc}
</head><body><div class="wrap">
<div class="mast"><a href="{rel}"><p class="logo"><span class="prompt">&gt;_</span>{esc(cfg['site_title'])}</p></a><span class="tag">// security × tech, every morning</span></div>
"""

def foot(rel):
    return f"""<footer>記事は公開時点の情報です。対応する前に、出典の公式発表を確認してください。黄色いマーカーの用語はタップで解説が出ます。<br><a href="{rel}about.html">このサイトについて</a></footer>
</div></body></html>"""

SHEET = """<div class="sheet" id="sheet" hidden role="dialog" aria-live="polite"><div class="in">
<div class="t"><b id="sT"></b><i id="sF" hidden></i></div><p class="s" id="sS"></p><p id="sL"></p>
<div class="ctrl"><button class="btn" id="sX" type="button">閉じる</button></div>
</div></div>"""

def counter_html(path):
    if not SHOW_COUNTER:
        return ""
    return (f'<p class="views" id="views" hidden></p><script>fetch("https://{GC}.goatcounter.com/counter/"+encodeURIComponent("{path}")+".json")'
            '.then(r=>r.ok?r.json():null).then(j=>{if(j&&j.count){const e=document.getElementById("views");e.textContent="この記事は "+j.count+" 回読まれました";e.hidden=false}}).catch(()=>{})</script>\n')

def load_posts():
    posts = []
    for p in sorted((ROOT / "posts").glob("*.html"), reverse=True):
        txt = p.read_text(encoding="utf-8-sig")
        m = re.match(r"\s*<!--meta\s+(\{.*?\})\s*-->", txt, re.S)
        if not m:
            raise SystemExit(f"meta missing: {p}")
        meta = json.loads(m.group(1))
        meta["slug"] = p.stem
        meta["body"] = txt[m.end():]
        meta["mtime"] = p.stat().st_mtime
        posts.append(meta)
    return posts

ABOUT_BODY = """<h1 class="title"><span class="line sec">このサイトについて</span></h1>
<div id="article">
<section class="about">
<h2>IT朝刊とは</h2>
<p>IT初心者から上級者まで、その日に知るべきITのニュースを、1ページ・5分で確認できるようにまとめたサイトです。毎朝8時台に更新します。</p>
<h2>記事の選び方</h2>
<p>前の営業日の朝8時以降に公表された情報から、話題性・新しさ・重大度の3つで点数を付け、点数の高い順に最大6件を載せます。実際に悪用されている脆弱性や大規模な被害を優先し、情報漏えいの公表は1つの記事にまとめます。</p>
<h2>事実確認と出典</h2>
<p>ベンダーの公式発表、米CISAのKEV、JPCERT/CC・JVN・IPA、被害組織の公表など、一次情報で確認できたことだけを書きます。犯行グループの主張だけの情報は載せません。各記事の末尾に出典のリンクを付けています。</p>
<h2>作り方</h2>
<p>記事の候補探し・要約・用語解説にはAIを使い、上の基準と一次情報の確認ルールに沿って作成しています。誤りに気づいた場合は、次の更新で訂正します。</p>
</section>
</div>
"""

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
        toc, tabs, body, items = enhance_body(p["body"], p["slug"])
        ld = jsonld({
            "@context": "https://schema.org", "@type": "NewsArticle",
            "headline": title_plain(p["title"])[:110],
            "description": p["summary"],
            "datePublished": p["date"] + PUB_TIME,
            "dateModified": p["date"] + PUB_TIME,
            "inLanguage": "ja",
            "mainEntityOfPage": url,
            "url": url,
            "image": [f"{BASE}static/ogp.png"],
            "author": {"@type": "Organization", "name": cfg["site_title"], "url": BASE},
            "publisher": {"@type": "Organization", "name": cfg["site_title"], "url": BASE},
            "about": [re.sub(r"<[^>]+>", "", s) for _, _, s, _ in items],
        })
        page = head(f"{title_plain(p['title'])}｜{cfg['site_title']} {p['date']}", p["summary"], url, "../", extra=ld)
        page += f'<span class="date">{esc(p["date"])}</span>\n'
        page += f'<h1 class="title">{title_html(p["title"], p["slug"])}</h1>\n'
        page += counter_html(f"/posts/{p['slug']}.html")
        page += toc + tabs
        page += f'<div id="article">{body}</div>\n'
        page += '<section class="gl"><h2>この記事の用語</h2><ul id="gllist"></ul></section>\n'
        page += foot("../").replace("</div></body>", f'</div>{SHEET}<script type="application/json" id="glossary-data">{gl_json}</script><script src="../static/glossary.js"></script><script src="../static/nav.js"></script><a href="#" class="totop" id="totop" hidden aria-label="上へ戻る">▲</a></body>')
        (OUT / "posts" / f"{p['slug']}.html").write_text(page, encoding="utf-8")
    # index
    site_ld = jsonld({"@context": "https://schema.org", "@type": "WebSite", "name": cfg["site_title"], "url": BASE, "inLanguage": "ja", "description": cfg["site_description"]})
    page = head(cfg["site_title"], cfg["site_description"], BASE, "", "website", extra=site_ld)
    page += f'<p class="lead">{esc(cfg["site_description"])}</p>\n<ul class="list">\n'
    for p in posts:
        page += f'<li><a href="posts/{p["slug"]}.html"><div class="card"><span class="date">{esc(p["date"])}</span><h2 class="title">{title_html(p["title"], p["slug"])}</h2><p>{esc(p["summary"])}</p></div></a></li>\n'
    page += "</ul>\n" + foot("")
    (OUT / "index.html").write_text(page, encoding="utf-8")
    # about
    page = head(f"このサイトについて｜{cfg['site_title']}", "IT朝刊の記事の選び方、事実確認と出典の方針。", f"{BASE}about.html", "", "website")
    page += ABOUT_BODY + foot("")
    (OUT / "about.html").write_text(page, encoding="utf-8")
    # RSS
    items = "".join(
        f"<item><title>{esc(title_plain(p['title']))}</title><link>{BASE}posts/{p['slug']}.html</link><guid>{BASE}posts/{p['slug']}.html</guid><pubDate>{p['date']}</pubDate><description>{esc(p['summary'])}</description></item>"
        for p in posts[:30])
    (OUT / "feed.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{esc(cfg["site_title"])}</title><link>{BASE}</link><description>{esc(cfg["site_description"])}</description>{items}</channel></rss>',
        encoding="utf-8")
    # sitemap + robots
    latest = posts[0]["date"] if posts else ""
    urls = [(BASE, latest), (f"{BASE}about.html", "")] + [(f"{BASE}posts/{p['slug']}.html", p["date"]) for p in posts]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u, d in urls:
        sm += f"<url><loc>{u}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>\n"
    sm += "</urlset>\n"
    (OUT / "sitemap.xml").write_text(sm, encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("")
    print(f"built {len(posts)} posts -> {OUT} (base {BASE}) gsv={'on' if GSV else 'off'} goatcounter={'on' if GC else 'off'} counter={'on' if SHOW_COUNTER else 'off'}")

if __name__ == "__main__":
    build()

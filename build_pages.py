#!/usr/bin/env python3
"""jobs.json থেকে index.html ও sitemap.xml বানায়।"""
import json
from html import escape
from datetime import datetime, timezone, timedelta

SITE = "https://chakrirkhobor.pages.dev"
BD = timezone(timedelta(hours=6))

try:
    with open("jobs.json", encoding="utf-8") as f:
        db = json.load(f)
except Exception:
    db = {}
jobs = db.get("jobs", []) if isinstance(db, dict) else []
updated = db.get("updated", datetime.now(BD).isoformat(timespec="seconds")) if isinstance(db, dict) else ""


def ago(iso):
    try:
        d = datetime.now(BD) - datetime.fromisoformat(iso)
        h = int(d.total_seconds() // 3600)
        return "এইমাত্র" if h < 1 else f"{h} ঘণ্টা আগে" if h < 24 else f"{h // 24} দিন আগে"
    except Exception:
        return ""


cards = []
for j in jobs:
    title = j.get("title_bn") or j["title"]
    kind = "govt" if j.get("type") == "govt" else "private"
    search = escape(f"{title} {j['title']} {j['source']} {j.get('category', '')}".lower())
    cards.append(
        f'<a class="card" href="{escape(j["url"])}" target="_blank" rel="nofollow noopener" '
        f'data-type="{kind}" data-q="{search}">'
        f'<span class="t">{escape(title)}</span>'
        f'<span class="m"><b class="{kind}">{"সরকারি" if kind == "govt" else "বেসরকারি"}</b>'
        f'{escape(j.get("category", ""))} · {escape(j["source"])} · {ago(j.get("first_seen", ""))}</span></a>'
    )

html = f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>চাকরির খবর - বাংলাদেশের সরকারি ও বেসরকারি নতুন চাকরির বিজ্ঞপ্তি</title>
<meta name="description" content="বাংলাদেশের সরকারি ও বেসরকারি সব নতুন চাকরির বিজ্ঞপ্তি এক জায়গায়, প্রতি কয়েক ঘণ্টায় আপডেট।">
<link rel="canonical" href="{SITE}/">
<style>
:root{{--bg:#fff;--fg:#1a1a1a;--card:#f4f5f7;--mut:#667;--ac:#0a7d3b;--bd:#e1e3e8}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0f1115;--fg:#e8e8ea;--card:#1a1d24;--mut:#9aa;--ac:#3ddc84;--bd:#2a2e38}}}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:system-ui,"Noto Sans Bengali",sans-serif;background:var(--bg);color:var(--fg)}}
header{{padding:18px 14px 8px;max-width:760px;margin:auto}}
h1{{margin:0;font-size:1.4rem}}
.sub{{color:var(--mut);font-size:.85rem;margin-top:4px}}
.bar{{position:sticky;top:0;background:var(--bg);padding:10px 14px;max-width:760px;margin:auto;z-index:2}}
input{{width:100%;padding:11px 12px;border-radius:10px;border:1px solid var(--bd);background:var(--card);color:var(--fg);font-size:1rem}}
.tabs{{display:flex;gap:8px;margin-top:8px}}
.tabs button{{flex:1;padding:8px;border-radius:999px;border:1px solid var(--bd);background:var(--card);color:var(--fg);font-size:.9rem}}
.tabs button.on{{background:var(--ac);color:#fff;border-color:var(--ac)}}
main{{max-width:760px;margin:auto;padding:4px 14px 40px;display:grid;gap:10px}}
.card{{display:block;padding:12px 14px;background:var(--card);border:1px solid var(--bd);border-radius:12px;text-decoration:none;color:inherit}}
.t{{display:block;font-weight:600;line-height:1.4}}
.m{{display:block;margin-top:6px;font-size:.8rem;color:var(--mut)}}
.m b{{padding:1px 8px;border-radius:999px;margin-right:6px;font-weight:600;color:#fff}}
.m b.govt{{background:#1565c0}}.m b.private{{background:#ef6c00}}
.empty{{text-align:center;color:var(--mut);padding:30px}}
</style>
</head>
<body>
<header><h1>📢 চাকরির খবর</h1>
<div class="sub">মোট {len(jobs)}টি বিজ্ঞপ্তি · সর্বশেষ আপডেট: {escape(updated[:16].replace("T", " "))}</div></header>
<div class="bar"><input id="q" type="search" placeholder="খুঁজুন: ব্যাংক, শিক্ষক, ইঞ্জিনিয়ার...">
<div class="tabs"><button class="on" data-f="all">সব</button><button data-f="govt">সরকারি</button><button data-f="private">বেসরকারি</button></div></div>
<main id="list">
{chr(10).join(cards) if cards else '<div class="empty">এখনো কোনো বিজ্ঞপ্তি নেই।</div>'}
</main>
<script>
var f="all",q=document.getElementById("q"),cs=[].slice.call(document.querySelectorAll(".card"));
function run(){{var s=q.value.trim().toLowerCase();cs.forEach(function(c){{
c.style.display=((f=="all"||c.dataset.type==f)&&(!s||c.dataset.q.indexOf(s)>-1))?"":"none"}})}}
q.addEventListener("input",run);
document.querySelectorAll(".tabs button").forEach(function(b){{b.onclick=function(){{
document.querySelectorAll(".tabs button").forEach(function(x){{x.classList.remove("on")}});
b.classList.add("on");f=b.dataset.f;run()}}}});
</script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

lastmod = datetime.now(BD).strftime("%Y-%m-%d")
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"<url><loc>{SITE}/</loc><lastmod>{lastmod}</lastmod>"
        "<changefreq>hourly</changefreq><priority>1.0</priority></url>\n</urlset>\n"
    )

print(f"index.html ও sitemap.xml তৈরি ({len(jobs)}টি জব)")

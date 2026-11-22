#!/usr/bin/env python3
"""jobs.json থেকে index.html ও sitemap.xml বানায়।"""
import json
from html import escape
from collections import Counter
from datetime import datetime, timezone, timedelta

SITE = "https://chakrirkhobor.pages.dev"
BD = timezone(timedelta(hours=6))
NOW = datetime.now(BD)
GROUPS = ["আজ", "গতকাল", "এই সপ্তাহ", "আগের"]


def bn(n):
    return str(n).translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))


def parse(iso):
    try:
        return datetime.fromisoformat(iso)
    except Exception:
        return None


def group_of(dt):
    if not dt:
        return "আগের"
    d = (NOW.date() - dt.date()).days
    return "আজ" if d <= 0 else "গতকাল" if d == 1 else "এই সপ্তাহ" if d <= 7 else "আগের"


def ago(dt):
    if not dt:
        return ""
    h = int((NOW - dt).total_seconds() // 3600)
    return "এইমাত্র" if h < 1 else f"{bn(h)} ঘণ্টা আগে" if h < 24 else f"{bn(h // 24)} দিন আগে"


try:
    with open("jobs.json", encoding="utf-8") as f:
        db = json.load(f)
except Exception:
    db = {}
jobs = db.get("jobs", []) if isinstance(db, dict) else []
jobs.sort(key=lambda j: j.get("first_seen", ""), reverse=True)
updated = parse(db.get("updated", "")) if isinstance(db, dict) else None

buckets = {g: [] for g in GROUPS}
cats = Counter()
today_count = 0
for j in jobs:
    dt = parse(j.get("first_seen", ""))
    g = group_of(dt)
    kind = "govt" if j.get("type") == "govt" else "private"
    title = j.get("title_bn") or j["title"]
    cat = j.get("category") or "অন্যান্য"
    cats[cat] += 1
    if g == "আজ":
        today_count += 1
    fresh = dt is not None and (NOW - dt).total_seconds() < 86400
    q = escape(f"{title} {j['title']} {j['source']} {cat}".lower())
    buckets[g].append(
        f'<a class="job {kind}" href="{escape(j["url"])}" target="_blank" rel="nofollow noopener" '
        f'data-k="{kind}" data-c="{escape(cat)}" data-q="{q}">'
        f'<span class="ttl">{escape(title)}{"<i class=dot title=নতুন></i>" if fresh else ""}</span>'
        f'<span class="meta"><b class="tag">{"সরকারি" if kind == "govt" else "বেসরকারি"}</b>'
        f'<span>{escape(cat)}</span><span>{escape(j["source"])}</span>'
        f'<span class="when">{ago(dt)}</span></span></a>'
    )

sections = []
for g in GROUPS:
    if buckets[g]:
        sections.append(
            f'<section class="grp"><h2>{g}<small>{bn(len(buckets[g]))}টি</small></h2>'
            f'<div class="list">{"".join(buckets[g])}</div></section>'
        )
chips = "".join(
    f'<button class="chip" data-c="{escape(c)}">{escape(c)} <small>{bn(n)}</small></button>'
    for c, n in cats.most_common(8)
)
upd = updated.strftime("%d/%m/%Y, %I:%M %p") if updated else "এখনো হয়নি"

PAGE = """<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>চাকরির খবর | বাংলাদেশের সরকারি ও বেসরকারি নতুন চাকরির বিজ্ঞপ্তি</title>
<meta name="description" content="বাংলাদেশের সরকারি ও বেসরকারি সব নতুন নিয়োগ বিজ্ঞপ্তি এক জায়গায়। প্রতি কয়েক ঘণ্টায় আপডেট।">
<meta property="og:title" content="চাকরির খবর">
<meta property="og:description" content="বাংলাদেশের সরকারি ও বেসরকারি নতুন চাকরির বিজ্ঞপ্তি, প্রতি কয়েক ঘণ্টায় আপডেট।">
<link rel="canonical" href="__SITE__/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600&family=Noto+Serif+Bengali:wght@600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#eef3ef;--sf:#fff;--ink:#14201a;--mut:#58675f;--line:#dbe4de;--govt:#0b6b43;--pvt:#2a5db0;--sun:#d62839;--hd:#0b3d2a;--hdi:#f4faf6}
@media(prefers-color-scheme:dark){:root{--bg:#0c1310;--sf:#131c17;--ink:#e6efe9;--mut:#92a49a;--line:#23322a;--govt:#4fd18b;--pvt:#80a9ee;--sun:#ff5d6c;--hd:#08150f;--hdi:#e6efe9}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:400 16px/1.55 "Hind Siliguri","Noto Sans Bengali",system-ui,sans-serif}
a{color:inherit;text-decoration:none}
:focus-visible{outline:3px solid var(--sun);outline-offset:2px}
.mast{background:var(--hd);color:var(--hdi);padding:26px 16px 22px}
.wrap{max-width:720px;margin:0 auto}
.brand{display:flex;align-items:center;gap:12px}
.sun{width:20px;height:20px;border-radius:50%;background:var(--sun);flex:none}
h1{margin:0;font:700 1.9rem/1.2 "Noto Serif Bengali","Hind Siliguri",serif}
.lead{margin:10px 0 0;opacity:.85;max-width:34em}
.stat{margin:14px 0 0;font-weight:500}
.stat span{display:block;opacity:.75;font-weight:400;font-size:.9rem}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);padding:12px 16px 10px;border-bottom:1px solid var(--line)}
#q{width:100%;padding:12px 14px;border:1px solid var(--line);border-radius:12px;background:var(--sf);color:var(--ink);font:inherit}
.row{display:flex;gap:8px;overflow-x:auto;padding:10px 0 2px;scrollbar-width:none}
.row::-webkit-scrollbar{display:none}
.chip{flex:none;border:1px solid var(--line);background:var(--sf);color:var(--ink);padding:6px 13px;border-radius:999px;font:inherit;font-size:.92rem;cursor:pointer}
.chip small{color:var(--mut)}
.chip.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.chip.on small{color:inherit;opacity:.7}
.sep{flex:none;width:1px;background:var(--line);margin:3px 2px}
main{padding:6px 16px 48px}
.grp h2{display:flex;align-items:baseline;gap:8px;margin:26px 0 10px;font:700 1.15rem/1.3 "Noto Serif Bengali","Hind Siliguri",serif}
.grp h2 small{font:400 .85rem "Hind Siliguri",sans-serif;color:var(--mut)}
.list{background:var(--sf);border:1px solid var(--line);border-radius:14px;overflow:hidden}
.job{display:block;padding:13px 16px 12px 14px;border-left:4px solid var(--line);border-bottom:1px solid var(--line)}
.job:last-child{border-bottom:0}
.job.govt{border-left-color:var(--govt)}
.job.private{border-left-color:var(--pvt)}
.job:hover{background:color-mix(in srgb,var(--sf) 92%,var(--ink))}
.ttl{display:block;font-weight:600;line-height:1.45}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--sun);margin-left:8px;vertical-align:middle}
.meta{display:flex;flex-wrap:wrap;gap:4px 12px;margin-top:6px;font-size:.86rem;color:var(--mut)}
.tag{font-weight:600}
.govt .tag{color:var(--govt)}
.private .tag{color:var(--pvt)}
.when{margin-left:auto}
.none{display:none;text-align:center;color:var(--mut);padding:44px 10px}
foot,footer{display:block;max-width:720px;margin:0 auto;padding:0 16px 40px;color:var(--mut);font-size:.85rem}
.empty{text-align:center;color:var(--mut);padding:60px 10px}
</style>
</head>
<body>
<header class="mast"><div class="wrap">
<div class="brand"><i class="sun" aria-hidden="true"></i><h1>চাকরির খবর</h1></div>
<p class="lead">বাংলাদেশের সরকারি ও বেসরকারি নতুন নিয়োগ বিজ্ঞপ্তি, এক জায়গায়।</p>
<p class="stat">আজ __TODAY__টি নতুন <span>মোট __COUNT__টি বিজ্ঞপ্তি, সর্বশেষ আপডেট __UPD__</span></p>
</div></header>
<div class="bar"><div class="wrap">
<input id="q" type="search" placeholder="খুঁজুন: ব্যাংক, শিক্ষক, ইঞ্জিনিয়ার..." aria-label="চাকরি খুঁজুন">
<div class="row" id="kinds">
<button class="chip on" data-k="all">সব</button>
<button class="chip" data-k="govt">সরকারি</button>
<button class="chip" data-k="private">বেসরকারি</button>
<span class="sep"></span>__CHIPS__
</div></div></div>
<main><div class="wrap" id="feed">
__LIST__
<p class="none" id="none">কোনো বিজ্ঞপ্তি মেলেনি। অন্য শব্দ দিয়ে খুঁজুন বা ফিল্টার বদলান।</p>
</div></main>
<footer>তথ্য সরাসরি মূল সাইট থেকে সংগৃহীত। আবেদনের আগে মূল বিজ্ঞপ্তি যাচাই করে নিন।</footer>
<script>
(function(){
var k="all",c="",q=document.getElementById("q"),
jobs=[].slice.call(document.querySelectorAll(".job")),
grps=[].slice.call(document.querySelectorAll(".grp")),
none=document.getElementById("none");
function run(){
var s=q.value.trim().toLowerCase(),shown=0;
jobs.forEach(function(j){
var ok=(k=="all"||j.dataset.k==k)&&(!c||j.dataset.c==c)&&(!s||j.dataset.q.indexOf(s)>-1);
j.style.display=ok?"":"none";if(ok)shown++;});
grps.forEach(function(g){g.style.display=g.querySelector('.job:not([style*="none"])')?"":"none";});
none.style.display=(shown||!jobs.length)?"none":"block";}
document.querySelectorAll(".chip").forEach(function(b){b.addEventListener("click",function(){
if(b.dataset.k){k=b.dataset.k;document.querySelectorAll(".chip[data-k]").forEach(function(x){x.classList.toggle("on",x===b);});}
else{c=(c===b.dataset.c)?"":b.dataset.c;document.querySelectorAll(".chip[data-c]").forEach(function(x){x.classList.toggle("on",x.dataset.c===c);});}
run();});});
q.addEventListener("input",run);
})();
</script>
</body>
</html>
"""

body = "".join(sections) if sections else '<p class="empty">এখনো কোনো বিজ্ঞপ্তি নেই। কিছুক্ষণ পর আবার দেখুন।</p>'
html = (PAGE.replace("__SITE__", SITE).replace("__TODAY__", bn(today_count))
        .replace("__COUNT__", bn(len(jobs))).replace("__UPD__", escape(upd))
        .replace("__CHIPS__", chips).replace("__LIST__", body))

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

lastmod = NOW.strftime("%Y-%m-%d")
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"<url><loc>{SITE}/</loc><lastmod>{lastmod}</lastmod>"
        "<changefreq>hourly</changefreq><priority>1.0</priority></url>\n</urlset>\n"
    )
print(f"index.html ও sitemap.xml তৈরি ({len(jobs)}টি জব)")

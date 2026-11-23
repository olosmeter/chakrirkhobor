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
        f'<span>{escape(cat)}</span><span>{escape(j["source"])}</span>' +
        (f'<span>শেষ: {escape(str(j["deadline"]))}</span>' if j.get("deadline") else "") +
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
:root{--bg:#eef2ee;--sf:#fff;--ink:#14201a;--mut:#5f6f66;--line:#dce4de;--govt:#0a7a4b;--pvt:#2b5bc4;--sun:#d9372b;--hd:#0b3a2a;--hdi:#f2faf5;--on:#0b3a2a;--onink:#fff}
@media(prefers-color-scheme:dark){:root{--bg:#0b1210;--sf:#121b17;--ink:#e7f0ea;--mut:#93a69b;--line:#22322a;--govt:#4fd18b;--pvt:#82abf0;--sun:#ff5a4d;--hd:#08150f;--hdi:#e7f0ea;--on:#4fd18b;--onink:#06150d}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:400 16px/1.6 "Hind Siliguri","Noto Sans Bengali",system-ui,sans-serif}
a{color:inherit;text-decoration:none}
:focus-visible{outline:3px solid var(--sun);outline-offset:2px}

/* Header: লাল সূর্য + গাঢ় সবুজ */
.mast{position:relative;overflow:hidden;background:var(--hd);color:var(--hdi);padding:30px 16px 28px;border-radius:0 0 26px 26px}
.mast::before{content:"";position:absolute;right:-60px;top:-60px;width:clamp(150px,36vw,250px);aspect-ratio:1;border-radius:50%;background:var(--sun)}
.wrap{max-width:720px;margin:0 auto}
.mast .wrap{position:relative;z-index:1}
.brand{display:flex;align-items:center}
.sun{display:none}
h1{margin:0;font:700 2.1rem/1.2 "Noto Serif Bengali","Hind Siliguri",serif;letter-spacing:-.01em}
.lead{margin:10px 0 0;max-width:22em;opacity:.9}
.stat{margin:18px 0 0;font:700 1.35rem/1.3 "Noto Serif Bengali","Hind Siliguri",serif}
.stat span{display:block;margin-top:2px;font:400 .85rem/1.5 "Hind Siliguri",sans-serif;opacity:.78}

/* Search + filters */
.bar{position:sticky;top:0;z-index:5;padding:12px 16px 10px;background:color-mix(in srgb,var(--bg) 90%,transparent);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
#q{width:100%;padding:12px 14px 12px 42px;border:1.5px solid var(--line);border-radius:14px;background:var(--sf) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%238a998f' stroke-width='2.2' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='m20 20-3.5-3.5'/%3E%3C/svg%3E") no-repeat 13px 50%;color:var(--ink);font:inherit;font-size:16px}
#q::placeholder{color:var(--mut)}
#q:focus{outline:0;border-color:var(--govt)}
.row{display:flex;gap:8px;overflow-x:auto;padding:10px 0 2px;scrollbar-width:none}
.row::-webkit-scrollbar{display:none}
.chip{flex:none;min-height:36px;border:1.5px solid var(--line);background:var(--sf);color:var(--ink);padding:5px 14px;border-radius:999px;font:inherit;font-size:.92rem;cursor:pointer}
.chip small{color:var(--mut);font-size:.8rem}
.chip.on{background:var(--on);color:var(--onink);border-color:var(--on)}
.chip.on small{color:inherit;opacity:.75}
.sep{flex:none;width:1px;background:var(--line);margin:4px 2px}

/* List */
main{padding:4px 16px 48px}
.grp h2{display:flex;align-items:center;gap:10px;margin:28px 0 12px;font:700 1.2rem/1.3 "Noto Serif Bengali","Hind Siliguri",serif}
.grp h2::before{content:"";flex:none;width:6px;height:1.1em;border-radius:3px;background:var(--sun)}
.grp h2 small{margin-left:auto;padding:1px 10px;border-radius:999px;background:var(--sf);border:1px solid var(--line);font:400 .82rem/1.6 "Hind Siliguri",sans-serif;color:var(--mut)}
.list{background:var(--sf);border:1px solid var(--line);border-radius:16px;overflow:hidden}
.job{display:block;padding:14px 16px 13px 14px;border-left:5px solid var(--line);border-bottom:1px solid var(--line);content-visibility:auto;contain-intrinsic-size:auto 84px}
.job:last-child{border-bottom:0}
.job.govt{border-left-color:var(--govt)}
.job.private{border-left-color:var(--pvt)}
.job:active{background:color-mix(in srgb,var(--sf) 90%,var(--ink))}
@media(hover:hover){.job:hover{background:color-mix(in srgb,var(--sf) 93%,var(--ink))}}
.ttl{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;overflow:hidden;font-weight:600;font-size:1.02rem;line-height:1.5;overflow-wrap:anywhere}
.dot{display:inline-block;width:8px;height:8px;margin-left:8px;border-radius:50%;background:var(--sun);vertical-align:middle}
.meta{display:flex;flex-wrap:wrap;align-items:center;gap:4px 10px;margin-top:8px;font-size:.84rem;color:var(--mut)}
.tag{padding:1px 10px;border-radius:999px;font-weight:600;font-size:.8rem}
.govt .tag{color:var(--govt);background:color-mix(in srgb,var(--govt) 13%,transparent)}
.private .tag{color:var(--pvt);background:color-mix(in srgb,var(--pvt) 13%,transparent)}
.when{margin-left:auto}

/* Empty state + footer */
.none{display:none;text-align:center;color:var(--mut);padding:44px 10px}
.none p{margin:0 0 14px}
.empty{text-align:center;color:var(--mut);padding:60px 10px}
footer{display:block;max-width:720px;margin:0 auto;padding:0 16px 40px;color:var(--mut);font-size:.85rem}
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
</div>
<div class="row" id="cats"><button class="chip on" data-c="">সব ধরন</button>__CHIPS__</div>
</div></div>
<main><div class="wrap" id="feed">
__LIST__
<div class="none" id="none"><p>এই ফিল্টারে কোনো বিজ্ঞপ্তি মেলেনি।</p><button class="chip" id="reset">সব ফিল্টার মুছুন</button></div>
</div></main>
<footer>তথ্য সরাসরি মূল সাইট থেকে সংগৃহীত। আবেদনের আগে মূল বিজ্ঞপ্তি যাচাই করে নিন।</footer>
<script>
(function(){
var k="all",c="",q=document.getElementById("q"),
jobs=[].slice.call(document.querySelectorAll(".job")),
grps=[].slice.call(document.querySelectorAll(".grp")),
none=document.getElementById("none");
function bn(n){return String(n).replace(/[0-9]/g,function(d){return "০১২৩৪৫৬৭৮৯"[d]})}
function mark(){
document.querySelectorAll("[data-k]").forEach(function(x){if(x.classList.contains("chip"))x.classList.toggle("on",x.dataset.k===k)});
document.querySelectorAll("#cats .chip").forEach(function(x){x.classList.toggle("on",x.dataset.c===c)});}
function run(){
var s=q.value.trim().toLowerCase(),shown=0;
jobs.forEach(function(j){
var ok=(k=="all"||j.dataset.k==k)&&(!c||j.dataset.c==c)&&(!s||j.dataset.q.indexOf(s)>-1);
j.style.display=ok?"":"none";if(ok)shown++;});
grps.forEach(function(g){
var n=0;g.querySelectorAll(".job").forEach(function(j){if(j.style.display!=="none")n++});
g.style.display=n?"":"none";g.querySelector("small").textContent=bn(n)+"টি";});
none.style.display=(shown||!jobs.length)?"none":"block";mark();}
document.querySelectorAll("#kinds .chip").forEach(function(b){b.addEventListener("click",function(){k=b.dataset.k;run()})});
document.querySelectorAll("#cats .chip").forEach(function(b){b.addEventListener("click",function(){c=b.dataset.c;run()})});
document.getElementById("reset").addEventListener("click",function(){k="all";c="";q.value="";run()});
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

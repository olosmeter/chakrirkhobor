#!/usr/bin/env python3
"""jobs.json থেকে index.html ও sitemap.xml বানায়। (ডিজাইন আপডেট; automation/data logic অপরিবর্তিত)"""
import json
from html import escape
from collections import Counter
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit

SITE = "https://chakrirkhobor.pages.dev"
BD = timezone(timedelta(hours=6))
NOW = datetime.now(BD)
GROUPS = ["আজ", "গতকাল", "এই সপ্তাহ", "আগের"]


def bn(n):
    return str(n).translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))


def parse(iso):
    try:
        if not iso:
            return None
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=BD)
        return dt.astimezone(BD)
    except (TypeError, ValueError, OverflowError):
        return None


def safe_url(value):
    if not isinstance(value, str):
        return ""
    value = value.strip()
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() in ("http", "https") and parts.netloc:
            return value
    except ValueError:
        pass
    return ""


def attr(s):
    return escape(str(s), quote=True)


def qtext(s):
    return str(s).lower().replace('"', "&quot;")


def text(s):
    return escape(str(s), quote=False)


def group_of(dt):
    if not dt:
        return "আগের"
    d = (NOW.date() - dt.date()).days
    return "আজ" if d <= 0 else "গতকাল" if d == 1 else "এই সপ্তাহ" if d <= 7 else "আগের"


def ago(dt):
    if not dt:
        return ""
    h = int((NOW - dt).total_seconds() // 3600)
    if h < 1:
        return "এইমাত্র"
    if h < 24:
        return f"{bn(h)} ঘণ্টা আগে"
    return f"{bn(h // 24)} দিন আগে"


try:
    with open("jobs.json", encoding="utf-8") as f:
        db = json.load(f)
except Exception:
    db = {}

if not isinstance(db, dict):
    db = {}

jobs_raw = db.get("jobs", []) if isinstance(db, dict) else []
if not isinstance(jobs_raw, list):
    jobs_raw = []

jobs = [j for j in jobs_raw if isinstance(j, dict) and safe_url(j.get("url"))]
jobs.sort(key=lambda j: str(j.get("first_seen", "") or ""), reverse=True)
updated = parse(db.get("updated", ""))

buckets = {g: [] for g in GROUPS}
cats = Counter()
today_count = 0

for j in jobs:
    try:
        dt = parse(j.get("first_seen", ""))
        g = group_of(dt)
        kind = "govt" if j.get("type") == "govt" else "private"
        raw_title = j.get("title") or j.get("title_bn") or "নিয়োগ বিজ্ঞপ্তি"
        title = j.get("title_bn") or raw_title
        cat = str(j.get("category") or "অন্যান্য")
        source = str(j.get("source") or "উৎস অজানা")
        url = safe_url(j.get("url"))
        
        # প্রকাশের তারিখ ও মেয়াদ শেষের তারিখ চেক
        deadline = j.get("deadline")
        publish_date = j.get("published_date") or j.get("published") or j.get("publish_date")

        cats[cat] += 1
        if g == "আজ":
            today_count += 1

        fresh = dt is not None and 0 <= (NOW - dt).total_seconds() < 86400
        q = qtext(f"{title} {raw_title} {source} {cat}")
        fresh_dot = '<i class="dot" title="নতুন"></i>' if fresh else ""
        
        # তারিখ ফরম্যাট ও কালার
        deadline_html = ""
        if deadline:
            deadline_html = f'<span style="color:var(--red); font-weight:600; background:color-mix(in srgb, var(--red) 10%, transparent); padding:2px 6px; border-radius:4px;">শেষ: {text(deadline)}</span>'
            
        publish_html = ""
        if publish_date:
            publish_html = f'<span style="color:var(--green); font-weight:600; background:color-mix(in srgb, var(--green) 10%, transparent); padding:2px 6px; border-radius:4px;">প্রকাশ: {text(publish_date)}</span>'
            
        kind_bn = "সরকারি" if kind == "govt" else "বেসরকারি"

        buckets[g].append(
            f'<a class="job {kind}" href="{attr(url)}" target="_blank" '
            f'rel="nofollow noopener" data-k="{kind}" '
            f'data-c="{attr(cat)}" data-q="{q}">'
            f'<span class="ttl">{text(title)}{fresh_dot}</span>'
            f'<span class="meta">'
            f'<b class="tag">{kind_bn}</b>'
            f'<span>{text(cat)}</span>'
            f'<span>{text(source)}</span>'
            f'{publish_html}'
            f'{deadline_html}'
            f'<span class="when">{ago(dt)}</span>'
            f'</span></a>'
        )
    except Exception:
        continue

sections = []
for g in GROUPS:
    if buckets[g]:
        sections.append(
            f'<section class="grp"><h2>{g}<small>{bn(len(buckets[g]))}টি</small></h2>'
            f'<div class="list">{"".join(buckets[g])}</div></section>'
        )

chips = "".join(
    f'<button class="chip" data-c="{attr(c)}">{text(c)} <small>{bn(n)}</small></button>'
    for c, n in cats.most_common(8)
)

upd = updated.strftime("%d/%m/%Y, %I:%M %p") if updated else "এখনো হয়নি"
lastmod = (updated or NOW).strftime("%Y-%m-%d")

PAGE = """<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>চাকরির খবর | বাংলাদেশের সরকারি ও বেসরকারি নতুন চাকরির বিজ্ঞপ্তি</title>
<meta name="description" content="বাংলাদেশের সরকারি ও বেসরকারি সব নতুন নিয়োগ বিজ্ঞপ্তি এক জায়গায়। প্রতি কয়েক ঘণ্টায় আপডেট।">
<meta property="og:title" content="চাকরির খবর">
<meta property="og:description" content="বাংলাদেশের সরকারি ও বেসরকারি নতুন চাকরির বিজ্ঞপ্তি, প্রতি কয়েক ঘণ্টায় আপডেট।">
<meta property="og:type" content="website">
<meta property="og:url" content="__SITE__/">
<meta name="twitter:card" content="summary">
<link rel="canonical" href="__SITE__/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&family=Noto+Sans+Bengali:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script>
(function(){try{var t=localStorage.getItem("jobsite-theme");
if(!t&&window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches)t="dark";
if(t)document.documentElement.setAttribute("data-theme",t);}catch(e){}})();
</script>
<style>
:root{
 --bg:#f4f7f5;--surface:#fff;--surface2:#edf4ef;--ink:#14251b;--mut:#64766b;
 --line:#e1e9e3;--green:#16804c;--green2:#dff5e7;--blue:#3868c7;--blue2:#e8efff;
 --red:#f06a53;--shadow:0 2px 10px rgba(22,55,35,.04);--radius:16px;
}
:root[data-theme="dark"]{
 --bg:#09120e;--surface:#111d16;--surface2:#1a2a20;--ink:#eaf5ed;--mut:#99ad9f;
 --line:#273a2e;--green:#65d995;--green2:#193d29;--blue:#91b5ff;--blue2:#1c2c48;
 --red:#ff826c;--shadow:0 4px 12px rgba(0,0,0,.15);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:400 16px/1.65 "Hind Siliguri","Noto Sans Bengali",system-ui,sans-serif;transition:background .2s,color .2s}
a{color:inherit;text-decoration:none}
button,input{font:inherit}
:focus-visible{outline:3px solid var(--red);outline-offset:3px}
.wrap{width:min(800px,calc(100% - 32px));margin:0 auto}

/* top navigation */
.topbar{padding:16px 0;display:flex;align-items:center;justify-content:space-between}
.brand{display:flex;align-items:center;gap:8px;font-weight:700;font-size:1.1rem}
.logo{display:grid;place-items:center;width:34px;height:34px;border-radius:10px;color:#fff;background:var(--green);font-weight:800;font-size:18px}
.navright{display:flex;align-items:center;gap:9px}
.iconbtn{width:36px;height:36px;display:grid;place-items:center;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:10px;cursor:pointer}
.iconbtn svg{width:18px;height:18px}

/* simple compact hero */
.hero{margin-top:4px;padding:16px 18px;border-radius:var(--radius);background:var(--surface);border:1px solid var(--line);box-shadow:var(--shadow)}
.hero-top{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}
.hero-title{font-size:1.15rem;font-weight:700;margin:0;line-height:1.4}
.hero-sub{font-size:0.85rem;color:var(--mut);margin-top:4px}
.stats{display:flex;gap:15px;font-size:0.85rem;color:var(--mut)}
.stat-item strong{color:var(--green);font-size:1rem;margin-right:3px}
.updated{font-size:.75rem;color:var(--mut);margin-top:10px;border-top:1px solid var(--line);padding-top:10px;display:block}

/* search / filters */
.tools{margin-top:12px;padding:12px;border:1px solid var(--line);background:var(--surface);border-radius:var(--radius);box-shadow:var(--shadow)}
.searchwrap{position:relative}
.searchicon{position:absolute;left:12px;top:50%;transform:translateY(-50%);width:18px;height:18px;color:var(--mut)}
#q{width:100%;padding:10px 36px 10px 38px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink);font-size:15px;outline:none}
#q:focus{border-color:var(--green)}
.clearsearch{position:absolute;right:8px;top:50%;transform:translateY(-50%);border:0;background:transparent;color:var(--mut);font-size:18px;cursor:pointer;padding:4px;display:none}
.filterline{display:flex;align-items:center;gap:8px;margin-top:10px}
.filterlabel{font-size:.8rem;color:var(--mut);white-space:nowrap}
.row{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;padding:2px 0;flex:1}
.row::-webkit-scrollbar{display:none}
.chip{flex:none;padding:4px 10px;border:1px solid var(--line);border-radius:999px;background:var(--bg);color:var(--ink);font-size:.85rem;cursor:pointer}
.chip small{color:var(--mut);font-size:.75rem;margin-left:3px}
.chip.on{background:var(--green);border-color:var(--green);color:#fff}
.chip.on small{color:inherit}
.divider{height:1px;background:var(--line);margin:10px 0}

/* jobs */
main{padding:12px 0 40px}
.grp{margin-top:20px}
.grp h2{display:flex;align-items:center;gap:8px;margin:0 0 10px;font-size:1rem;font-weight:700}
.grp h2 small{margin-left:auto;color:var(--mut);font-size:.8rem;font-weight:500}
.list{display:grid;gap:8px}
.job{display:block;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 14px;box-shadow:var(--shadow);transition:border-color .2s}
.job:hover{border-color:var(--green)}
.job.govt{border-left:3px solid var(--green)}
.job.private{border-left:3px solid var(--blue)}
.ttl{display:block;font-weight:600;font-size:.95rem;line-height:1.5;overflow-wrap:anywhere}
.dot{display:inline-block;width:6px;height:6px;margin-left:6px;border-radius:50%;background:var(--red);vertical-align:middle}
.meta{display:flex;flex-wrap:wrap;align-items:center;gap:5px 8px;margin-top:6px;color:var(--mut);font-size:.78rem}
.tag{padding:2px 8px;border-radius:6px;font-size:.75rem;font-weight:600}
.govt .tag{color:var(--green);background:var(--green2)}
.private .tag{color:var(--blue);background:var(--blue2)}
.when{margin-left:auto}
.none{display:none;text-align:center;padding:30px 12px;color:var(--mut)}
.empty{padding:40px 15px;text-align:center;color:var(--mut);border:1px dashed var(--line);border-radius:12px}
footer{padding:20px 0 36px;text-align:center;color:var(--mut);font-size:.8rem;border-top:1px solid var(--line);margin-top:20px}
.mobilebottom{display:none}

@media(max-width:640px){
 .wrap{width:calc(100% - 20px)}
 .hero-top{flex-direction:column;align-items:flex-start;gap:8px}
 .stats{width:100%;justify-content:space-between;background:var(--bg);padding:8px;border-radius:8px}
 .filterline{display:block}
 .filterlabel{display:block;margin-bottom:4px}
 .job{padding:10px 12px}
 .mobilebottom{display:flex;position:fixed;z-index:8;bottom:10px;left:10px;right:10px;justify-content:space-around;padding:8px;background:var(--surface);border:1px solid var(--line);border-radius:14px;box-shadow:0 4px 12px #0002}
 .mobilebottom a{display:flex;flex-direction:column;align-items:center;font-size:.7rem;color:var(--mut)}
 .mobilebottom svg{width:18px;height:18px;margin-bottom:2px}
 .mobilebottom a:first-child{color:var(--green)}
 main{padding-bottom:80px}
 footer{padding-bottom:90px}
}
</style>
</head>
<body>
<div class="wrap">
<header class="topbar">
 <a class="brand" href="__SITE__/"><span class="logo">চ</span><span>চাকরির খবর</span></a>
 <div class="navright">
  <button class="iconbtn" id="theme" aria-label="থিম পরিবর্তন">
   <svg id="themeIcon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/></svg>
  </button>
 </div>
</header>

<section class="hero">
 <div class="hero-top">
  <div>
   <h1 class="hero-title">চাকরির খবর</h1>
   <div class="hero-sub">সরকারি ও বেসরকারি নতুন নিয়োগ বিজ্ঞপ্তি</div>
  </div>
  <div class="stats">
   <div class="stat-item"><strong>__TODAY__</strong> আজকের</div>
   <div class="stat-item"><strong>__COUNT__</strong> মোট</div>
  </div>
 </div>
 <span class="updated">সর্বশেষ আপডেট: __UPD__</span>
</section>

<section class="tools">
 <div class="searchwrap">
  <svg class="searchicon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
  <input id="q" type="search" placeholder="চাকরি খুঁজুন..." aria-label="চাকরি খুঁজুন">
  <button class="clearsearch" id="clearq" type="button">×</button>
 </div>
 <div class="filterline"><span class="filterlabel">ধরন:</span><div class="row" id="kinds">
  <button class="chip on" data-k="all">সব</button><button class="chip" data-k="govt">সরকারি</button><button class="chip" data-k="private">বেসরকারি</button>
 </div></div>
 <div class="divider"></div>
 <div class="filterline"><span class="filterlabel">ক্যাটাগরি:</span><div class="row" id="cats"><button class="chip on" data-c="">সব</button>__CHIPS__</div></div>
</section>

<main><div id="feed">
__LIST__
<div class="none" id="none"><p>কোনো বিজ্ঞপ্তি মেলেনি।</p><button class="chip" id="reset">ফিল্টার মুছুন</button></div>
</div></main>

<footer><div>চাকরির খবর</div>তথ্য সরাসরি মূল সাইট থেকে সংগৃহীত।</footer>
</div>

<nav class="mobilebottom" aria-label="নেভিগেশন">
<a href="__SITE__/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 10 9-7 9 7"/><path d="M5 9v11h14V9M9 20v-6h6v6"/></svg><span>হোম</span></a>
<a href="#q" onclick="document.getElementById('q').focus();return false;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><span>খুঁজুন</span></a>
<a href="#feed"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 5h16M4 12h16M4 19h16"/></svg><span>তালিকা</span></a>
</nav>

<script>
(function(){
var k="all",c="",q=document.getElementById("q"),clearq=document.getElementById("clearq"),
jobs=[].slice.call(document.querySelectorAll(".job")),
grps=[].slice.call(document.querySelectorAll(".grp")),
none=document.getElementById("none");
function bn(n){return String(n).replace(/[0-9]/g,function(d){return "০১২৩৪৫৬৭৮৯"[d]})}
function mark(){
document.querySelectorAll("#kinds .chip").forEach(function(x){x.classList.toggle("on",x.dataset.k===k)});
document.querySelectorAll("#cats .chip").forEach(function(x){x.classList.toggle("on",x.dataset.c===c)});
clearq.style.display=q.value?"block":"none";
}
function run(){
var s=q.value.trim().toLowerCase(),shown=0;
jobs.forEach(function(j){
var ok=(k==="all"||j.dataset.k===k)&&(!c||j.dataset.c===c)&&(!s||j.dataset.q.indexOf(s)>-1);
j.style.display=ok?"":"none";if(ok)shown++;});
grps.forEach(function(g){
var n=0;g.querySelectorAll(".job").forEach(function(j){if(j.style.display!=="none")n++});
g.style.display=n?"":"none";
var sm=g.querySelector("small");if(sm)sm.textContent=bn(n)+"টি";});
none.style.display=(shown||!jobs.length)?"none":"block";mark();}
document.querySelectorAll("#kinds .chip").forEach(function(b){b.addEventListener("click",function(){k=b.dataset.k;run()})});
document.querySelectorAll("#cats .chip").forEach(function(b){b.addEventListener("click",function(){c=b.dataset.c;run()})});
var resetBtn=document.getElementById("reset");
if(resetBtn)resetBtn.addEventListener("click",function(){k="all";c="";q.value="";run()});
clearq.addEventListener("click",function(){q.value="";run();q.focus()});
q.addEventListener("input",run);

var themeBtn=document.getElementById("theme"),root=document.documentElement,icon=document.getElementById("themeIcon");
function setTheme(t){
root.setAttribute("data-theme",t);
try{localStorage.setItem("jobsite-theme",t)}catch(e){}
icon.innerHTML=t==="dark"
?'<path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/>'
:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/>';
}
var saved=null;try{saved=localStorage.getItem("jobsite-theme")}catch(e){}
setTheme(saved||(window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"));
themeBtn.addEventListener("click",function(){setTheme(root.getAttribute("data-theme")==="dark"?"light":"dark")});
})();
</script>
</body>
</html>
"""

body = "".join(sections) if sections else '<p class="empty">এখনো কোনো বিজ্ঞপ্তি নেই। কিছুক্ষণ পর আবার দেখুন।</p>'

html = (
    PAGE.replace("__SITE__", SITE)
        .replace("__TODAY__", bn(today_count))
        .replace("__COUNT__", bn(len(jobs)))
        .replace("__UPD__", text(upd))
        .replace("__CHIPS__", chips)
        .replace("__LIST__", body)
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"<url><loc>{SITE}/</loc><lastmod>{lastmod}</lastmod>"
        "<changefreq>hourly</changefreq><priority>1.0</priority></url>\n</urlset>\n"
    )

print(f"index.html ও sitemap.xml তৈরি ({len(jobs)}টি জব)")

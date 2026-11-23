#!/usr/bin/env python3
"""jobs.json থেকে index.html ও sitemap.xml বানায়। (ডিজাইন আপডেট; automation/data logic অপরিবর্তিত)"""
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
    
    title = j.get("title_bn") or j["title"]
    
    # --- ফিক্স: টাইটেলে সরকারি চাকরির কি-ওয়ার্ড থাকলে অটোমেটিক 'govt' ধরে নেবে ---
    search_text = (title + " " + j.get("title", "")).lower()
    govt_keywords = [
        "কর অঞ্চল", "অধিদপ্তর", "মন্ত্রণালয়", "কমিশনার", "আদালত", 
        "বিশ্ববিদ্যালয়", "পুলিশ", "সেনাবাহিনী", "এনবিআর", "nbr", 
        "প্রশাসন", "সরকারি", "সচিবালয়", "মহাপরিচালক"
    ]
    is_govt_keyword = any(k in search_text for k in govt_keywords)
    kind = "govt" if (j.get("type") == "govt" or is_govt_keyword) else "private"
    # -------------------------------------------------------------------------

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
<link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&family=Noto+Sans+Bengali:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{
 --bg:#f4f7f5;--surface:#fff;--surface2:#edf4ef;--ink:#14251b;--mut:#64766b;
 --line:#e1e9e3;--green:#16804c;--green2:#dff5e7;--blue:#3868c7;--blue2:#e8efff;
 --red:#f06a53;--shadow:0 8px 26px rgba(22,55,35,.055);--radius:18px;
}
:root[data-theme="dark"]{
 --bg:#09120e;--surface:#111d16;--surface2:#1a2a20;--ink:#eaf5ed;--mut:#99ad9f;
 --line:#273a2e;--green:#65d995;--green2:#193d29;--blue:#91b5ff;--blue2:#1c2c48;
 --red:#ff826c;--shadow:0 8px 28px rgba(0,0,0,.22);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:400 16px/1.65 "Hind Siliguri","Noto Sans Bengali",system-ui,sans-serif;transition:background .2s,color .2s}
a{color:inherit;text-decoration:none}
button,input{font:inherit}
:focus-visible{outline:3px solid var(--red);outline-offset:3px}
.wrap{width:min(900px,calc(100% - 32px));margin:0 auto}

/* top navigation */
.topbar{padding:14px 0}
.nav{display:flex;align-items:center;justify-content:space-between;gap:12px}
.brand{display:flex;align-items:center;gap:10px;font-weight:700;font-size:1.18rem}
.logo{display:grid;place-items:center;width:42px;height:42px;border-radius:14px;color:#062313;background:linear-gradient(135deg,#77e5a0,#1b9a59);font-weight:800;font-size:22px;box-shadow:0 5px 15px #16804c22}
.navright{display:flex;align-items:center;gap:9px}
.navlink{color:var(--mut);font-size:.94rem}
.iconbtn{width:40px;height:40px;display:grid;place-items:center;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:13px;cursor:pointer}
.iconbtn svg{width:19px;height:19px}

/* hero */
.hero{position:relative;margin-top:9px;padding:28px 28px 24px;border-radius:26px;background:linear-gradient(120deg,#0d3b26,#145b39 70%,#17804c);color:#f2fff6;overflow:hidden;box-shadow:0 14px 34px rgba(13,59,38,.15)}
.hero:after{content:"";position:absolute;width:290px;height:290px;right:-105px;top:-130px;border-radius:50%;border:1px solid #ffffff20;box-shadow:0 0 0 35px #ffffff08,0 0 0 70px #ffffff06}
.hero-inner{position:relative;z-index:1}
.eyebrow{display:inline-flex;align-items:center;gap:7px;padding:5px 11px;border:1px solid #ffffff25;background:#ffffff12;border-radius:99px;font-size:.86rem;color:#c9f5d8}
.pulse{width:7px;height:7px;background:#77efa4;border-radius:50%;box-shadow:0 0 0 4px #77efa422}
h1{font-size:clamp(1.8rem,5vw,2.65rem);line-height:1.25;margin:13px 0 7px;font-weight:800;letter-spacing:-.4px}
.hero p{margin:0;color:#d3eadb;font-size:1rem;max-width:34em}
.statrow{display:flex;align-items:stretch;gap:10px;flex-wrap:wrap;margin-top:20px}
.statbox{padding:10px 14px;border:1px solid #ffffff22;background:#ffffff0e;border-radius:14px;min-width:135px}
.statbox strong{font-size:1.27rem;line-height:1.2;display:block;font-weight:700}
.statbox span{display:block;font-size:.83rem;color:#d0e8d8;margin-top:3px}
.updated{font-size:.82rem;color:#c5e1cf;align-self:center;padding-left:2px}

/* search / filters */
.tools{margin-top:16px;padding:14px;border:1px solid var(--line);background:var(--surface);border-radius:20px;box-shadow:var(--shadow)}
.searchwrap{position:relative}
.searchicon{position:absolute;left:14px;top:50%;transform:translateY(-50%);width:19px;height:19px;color:var(--mut)}
#q{width:100%;padding:12px 44px 12px 43px;border:1px solid var(--line);border-radius:14px;background:var(--bg);color:var(--ink);font-size:16px;outline:none}
#q:focus{border-color:var(--green);box-shadow:0 0 0 3px color-mix(in srgb,var(--green) 15%,transparent)}
#q::placeholder{color:var(--mut)}
.clearsearch{position:absolute;right:9px;top:50%;transform:translateY(-50%);border:0;background:transparent;color:var(--mut);font-size:20px;cursor:pointer;padding:4px 8px;display:none}
.filterline{display:flex;align-items:center;gap:9px;margin-top:12px}
.filterlabel{font-size:.83rem;color:var(--mut);white-space:nowrap}
.row{display:flex;gap:7px;overflow-x:auto;scrollbar-width:none;padding:1px 0;flex:1}
.row::-webkit-scrollbar{display:none}
.chip{flex:none;min-height:35px;padding:5px 12px;border:1px solid var(--line);border-radius:999px;background:var(--surface);color:var(--ink);font-size:.9rem;cursor:pointer;transition:.16s}
.chip small{color:var(--mut);font-size:.78rem;margin-left:3px}
.chip:hover{border-color:var(--green)}
.chip.on{background:var(--green);border-color:var(--green);color:#fff}
.chip.on small{color:inherit;opacity:.78}
.divider{height:1px;background:var(--line);margin:12px 0}
#cats{padding-bottom:2px}

/* jobs */
main{padding:12px 0 40px}
.grp{margin-top:23px}
.grp h2{display:flex;align-items:center;gap:10px;margin:0 0 11px;font-size:1.12rem;font-weight:700}
.grp h2:before{content:"";width:5px;height:21px;border-radius:5px;background:var(--green)}
.grp h2 small{margin-left:auto;color:var(--mut);background:var(--surface);border:1px solid var(--line);padding:2px 10px;border-radius:999px;font-size:.8rem;font-weight:500}
.list{display:grid;gap:10px}
.job{position:relative;display:block;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:15px 16px 14px 18px;box-shadow:var(--shadow);transition:transform .18s,border-color .18s,box-shadow .18s;overflow:hidden}
.job:before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--line)}
.job.govt:before{background:var(--green)}
.job.private:before{background:var(--blue)}
.job:hover{transform:translateY(-2px);border-color:color-mix(in srgb,var(--green) 35%,var(--line));box-shadow:0 12px 28px rgba(22,55,35,.09)}
.ttl{display:block;font-weight:700;font-size:1.03rem;line-height:1.52;overflow-wrap:anywhere}
.dot{display:inline-block;width:7px;height:7px;margin-left:7px;border-radius:50%;background:var(--red);vertical-align:middle;box-shadow:0 0 0 4px color-mix(in srgb,var(--red) 12%,transparent)}
.meta{display:flex;flex-wrap:wrap;align-items:center;gap:5px 9px;margin-top:9px;color:var(--mut);font-size:.83rem}
.tag{padding:1px 9px;border-radius:999px;font-size:.78rem;font-weight:600}
.govt .tag{color:var(--green);background:var(--green2)}
.private .tag{color:var(--blue);background:var(--blue2)}
.when{margin-left:auto}
.none{display:none;text-align:center;padding:40px 12px;color:var(--mut)}
.none p{margin:0 0 14px}
.empty{padding:50px 15px;text-align:center;color:var(--mut);background:var(--surface);border:1px dashed var(--line);border-radius:18px}
footer{padding:20px 0 36px;text-align:center;color:var(--mut);font-size:.84rem;border-top:1px solid var(--line)}
.footerbrand{font-weight:600;color:var(--ink);margin-bottom:3px}
.mobilebottom{display:none}

/* responsive */
@media(max-width:640px){
 .wrap{width:min(900px,calc(100% - 22px))}
 .topbar{padding:10px 0}
 .brand{font-size:1.05rem}
 .logo{width:38px;height:38px;border-radius:12px}
 .navlink{display:none}
 .hero{padding:23px 18px 20px;border-radius:21px;margin-top:4px}
 .hero:after{width:220px;height:220px;right:-115px;top:-100px}
 h1{font-size:1.8rem}
 .statrow{gap:8px;margin-top:16px}
 .statbox{min-width:calc(50% - 5px);flex:1;padding:9px 11px}
 .statbox strong{font-size:1.18rem}
 .updated{width:100%;padding:3px 0 0}
 .tools{padding:11px;border-radius:17px;margin-top:12px}
 .filterline{display:block}
 .filterlabel{display:block;margin-bottom:6px}
 .row{gap:6px}
 .chip{padding:5px 11px;min-height:34px}
 .divider{margin:10px 0}
 main{padding-top:5px;padding-bottom:80px}
 .grp{margin-top:20px}
 .job{padding:13px 13px 12px 16px;border-radius:14px}
 .ttl{font-size:1rem}
 .meta{font-size:.8rem;gap:4px 8px}
 .when{margin-left:0}
 footer{padding-bottom:95px}
 .mobilebottom{display:flex;position:fixed;z-index:8;bottom:9px;left:10px;right:10px;justify-content:space-around;gap:5px;padding:9px 7px;background:color-mix(in srgb,var(--surface) 92%,transparent);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid var(--line);border-radius:18px;box-shadow:0 10px 28px #0002}
 .mobilebottom a{display:flex;flex-direction:column;align-items:center;gap:1px;font-size:.73rem;color:var(--mut);min-width:55px}
 .mobilebottom svg{width:19px;height:19px}
 .mobilebottom a:first-child{color:var(--green)}
}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
</style>
</head>
<body>
<div class="wrap">
<header class="topbar">
 <div class="nav">
  <a class="brand" href="__SITE__/" aria-label="চাকরির খবর হোম"><span class="logo">চ</span><span>চাকরির খবর</span></a>
  <div class="navright"><a class="navlink" href="#feed">সাম্প্রতিক বিজ্ঞপ্তি</a><button class="iconbtn" id="theme" aria-label="থিম পরিবর্তন" title="থিম পরিবর্তন">
   <svg id="themeIcon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/></svg>
  </button></div>
 </div>
</header>
<section class="hero">
 <div class="hero-inner">
  <span class="eyebrow"><i class="pulse"></i> প্রতিদিন নতুন চাকরির আপডেট</span>
  <h1>আপনার ক্যারিয়ারের <br>পরবর্তী সুযোগ খুঁজুন</h1>
  <p>বাংলাদেশের সরকারি ও বেসরকারি নিয়োগ বিজ্ঞপ্তি—সব এক জায়গায়, সহজে খুঁজুন।</p>
  <div class="statrow">
   <div class="statbox"><strong>__TODAY__টি</strong><span>আজকের নতুন বিজ্ঞপ্তি</span></div>
   <div class="statbox"><strong>__COUNT__টি</strong><span>মোট চাকরির বিজ্ঞপ্তি</span></div>
   <div class="updated">সর্বশেষ আপডেট: __UPD__</div>
  </div>
 </div>
</section>
<section class="tools" aria-label="চাকরি খুঁজুন ও ফিল্টার করুন">
 <div class="searchwrap">
  <svg class="searchicon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
  <input id="q" type="search" placeholder="চাকরি খুঁজুন—ব্যাংক, শিক্ষক, ইঞ্জিনিয়ার..." aria-label="চাকরি খুঁজুন">
  <button class="clearsearch" id="clearq" type="button" aria-label="সার্চ মুছুন">×</button>
 </div>
 <div class="filterline"><span class="filterlabel">চাকরির ধরন</span><div class="row" id="kinds">
  <button class="chip on" data-k="all">সব চাকরি</button><button class="chip" data-k="govt">সরকারি</button><button class="chip" data-k="private">বেসরকারি</button>
 </div></div>
 <div class="divider"></div>
 <div class="filterline"><span class="filterlabel">ক্যাটাগরি</span><div class="row" id="cats"><button class="chip on" data-c="">সব ক্যাটাগরি</button>__CHIPS__</div></div>
</section>
<main><div id="feed">
__LIST__
<div class="none" id="none"><p>এই ফিল্টারে কোনো বিজ্ঞপ্তি মেলেনি।</p><button class="chip" id="reset">ফিল্টার মুছুন</button></div>
</div></main>
<footer><div class="footerbrand">চাকরির খবর</div>তথ্য সরাসরি মূল সাইট থেকে সংগৃহীত। আবেদনের আগে মূল বিজ্ঞপ্তি যাচাই করে নিন।</footer>
</div>
<nav class="mobilebottom" aria-label="দ্রুত নেভিগেশন">
<a href="__SITE__/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m3 10 9-7 9 7"/><path d="M5 9v11h14V9M9 20v-6h6v6"/></svg><span>হোম</span></a>
<a href="#q" onclick="document.getElementById('q').focus()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><span>খুঁজুন</span></a>
<a href="#kinds"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M8 9h8M8 13h5"/></svg><span>ফিল্টার</span></a>
<a href="#feed"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 5h16M4 12h16M4 19h16"/></svg><span>তালিকা</span></a>
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
var ok=(k=="all"||j.dataset.k==k)&&(!c||j.dataset.c==c)&&(!s||j.dataset.q.indexOf(s)>-1);
j.style.display=ok?"":"none";if(ok)shown++;});
grps.forEach(function(g){
var n=0;g.querySelectorAll(".job").forEach(function(j){if(j.style.display!=="none")n++});
g.style.display=n?"":"none";g.querySelector("small").textContent=bn(n)+"টি";});
none.style.display=(shown||!jobs.length)?"none":"block";mark();}
document.querySelectorAll("#kinds .chip").forEach(function(b){b.addEventListener("click",function(){k=b.dataset.k;run()})});
document.querySelectorAll("#cats .chip").forEach(function(b){b.addEventListener("click",function(){c=b.dataset.c;run()})});
document.getElementById("reset").addEventListener("click",function(){k="all";c="";q.value="";run()});
clearq.addEventListener("click",function(){q.value="";run();q.focus()});
q.addEventListener("input",run);

/* Theme toggle; no impact on job collection or scheduled automation */
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

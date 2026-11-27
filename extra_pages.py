# -*- coding: utf-8 -*-
"""extra_pages.py  (build_pages.py-র একদম শেষে exec দিয়ে চলে)

যা বানায়:
  /sarkari-chakri/     সরকারি চাকরি
  /beshorkari-chakri/  বেসরকারি চাকরি
  /<ক্যাটাগরি>/        ব্যাংক, শিক্ষা, স্বাস্থ্য... (৩টির বেশি জব থাকলে)
  /about/              আমাদের সম্পর্কে
  /privacy/            গোপনীয়তা নীতি
  index.html           ওপরের পেজগুলোর লিংকসহ আবার লেখে
  sitemap.xml          সব পেজসহ

build_pages.py-র ভেরিয়েবল (jobs, PAGE, html, cats, kind_of ইত্যাদি) ব্যবহার করে।
প্রতিটা জবের আলাদা পেজ ইচ্ছে করেই বানানো হয়নি: স্ক্র্যাপ করা তথ্যের হাজার হাজার পেজ
গুগল "কম মানের কনটেন্ট" ধরে। তাই পেজ বানানো হয় বিষয় (ক্যাটাগরি) ধরে।
"""
import os
import hashlib

MAX_ROWS = 300  # প্রতি পেজে সর্বোচ্চ কতটা জব দেখাবে

CAT_SLUG = {
    "সেনা-পুলিশ": "army-police-job",
    "শিক্ষা": "education-job",
    "ব্যাংক": "bank-job",
    "স্বাস্থ্য": "health-job",
    "এনজিও": "ngo-job",
    "আইটি": "it-job",
    "প্রকৌশল": "engineering-job",
    "অন্যান্য": "other-job",
}

CAT_INTRO = {
    "ব্যাংক": "সরকারি ও বেসরকারি ব্যাংকের সর্বশেষ নিয়োগ বিজ্ঞপ্তি। আবেদনের আগে পদের নাম, শিক্ষাগত যোগ্যতা, বয়সসীমা ও শেষ তারিখ মূল বিজ্ঞপ্তিতে মিলিয়ে নিন।",
    "শিক্ষা": "স্কুল, কলেজ, মাদ্রাসা ও বিশ্ববিদ্যালয়ের শিক্ষক এবং কর্মকর্তা পদের নিয়োগ বিজ্ঞপ্তি। শিক্ষক পদে আবেদনে সাধারণত সনদ ও অভিজ্ঞতার কাগজ লাগে, তাই বিজ্ঞপ্তির শর্ত ভালো করে পড়ে নিন।",
    "স্বাস্থ্য": "হাসপাতাল, সিভিল সার্জনের কার্যালয়, ফার্মাসিউটিক্যালস ও স্বাস্থ্য খাতের নিয়োগ বিজ্ঞপ্তি। চিকিৎসক ও নার্সিং পদে বিএমডিসি বা নার্সিং কাউন্সিলের নিবন্ধন লাগতে পারে।",
    "সেনা-পুলিশ": "সেনাবাহিনী, নৌবাহিনী, বিমানবাহিনী, পুলিশ ও অন্যান্য বাহিনীর নিয়োগ বিজ্ঞপ্তি। শারীরিক যোগ্যতা ও আবেদনের নিয়ম মূল বিজ্ঞপ্তিতে দেখে নিন।",
    "এনজিও": "দেশি ও আন্তর্জাতিক এনজিও এবং উন্নয়ন সংস্থার নিয়োগ বিজ্ঞপ্তি। অনেক ক্ষেত্রে আবেদন সংস্থার নিজস্ব ক্যারিয়ার পোর্টালে করতে হয়।",
    "আইটি": "সফটওয়্যার, ডেভেলপার, আইটি সাপোর্ট ও ডিজিটাল মার্কেটিং-সহ প্রযুক্তি খাতের নিয়োগ বিজ্ঞপ্তি।",
    "প্রকৌশল": "সিভিল, ইলেকট্রিক্যাল, মেকানিক্যালসহ প্রকৌশল পদের নিয়োগ বিজ্ঞপ্তি।",
}

KIND_PAGES = [
    {
        "kind": "govt",
        "slug": "sarkari-chakri",
        "label": "সরকারি",
        "title": "সরকারি চাকরির খবর | নতুন সরকারি নিয়োগ বিজ্ঞপ্তি",
        "desc": "বাংলাদেশের সরকারি দপ্তর, মন্ত্রণালয়, বাহিনী ও সংস্থার নতুন নিয়োগ বিজ্ঞপ্তি। আবেদনের লিংকসহ নিয়মিত আপডেট।",
        "h1": "সরকারি চাকরির খবর",
        "lead": "সরকারি দপ্তর, অধিদপ্তর, বাহিনী ও সংস্থার সর্বশেষ নিয়োগ বিজ্ঞপ্তি।",
        "intro": "সরকারি চাকরির আবেদন সাধারণত মূল বিজ্ঞপ্তিতে দেওয়া নির্দিষ্ট ওয়েবসাইট বা ঠিকানায় করতে হয়। আবেদনের আগে শেষ তারিখ, বয়সসীমা ও শিক্ষাগত যোগ্যতা মূল বিজ্ঞপ্তিতে মিলিয়ে নিন।",
    },
    {
        "kind": "private",
        "slug": "beshorkari-chakri",
        "label": "বেসরকারি",
        "title": "বেসরকারি চাকরির খবর | নতুন প্রাইভেট জব সার্কুলার",
        "desc": "বাংলাদেশের কোম্পানি, ব্যাংক, এনজিও ও বেসরকারি প্রতিষ্ঠানের নতুন চাকরির বিজ্ঞপ্তি। আবেদনের লিংকসহ নিয়মিত আপডেট।",
        "h1": "বেসরকারি চাকরির খবর",
        "lead": "কোম্পানি, ব্যাংক, এনজিও ও বেসরকারি প্রতিষ্ঠানের সর্বশেষ নিয়োগ বিজ্ঞপ্তি।",
        "intro": "আবেদনের আগে প্রতিষ্ঠানটি যাচাই করুন। চাকরি দেওয়ার নামে অগ্রিম টাকা চাইলে বা ব্যক্তিগত কাগজপত্র আগেই পাঠাতে বললে সতর্ক থাকুন।",
    },
]

OLD_TITLE = "চাকরির খবর | সরকারি ও বেসরকারি নতুন চাকরি"
OLD_DESC = "বাংলাদেশের সরকারি ও বেসরকারি সব নতুন চাকরির বিজ্ঞপ্তি এক জায়গায়। আজকের চাকরির খবর, শেষ তারিখ ও আবেদনের লিংক, প্রতি কয়েক ঘণ্টায় আপডেট।"
OLD_SHORT = "বাংলাদেশের সরকারি ও বেসরকারি নতুন চাকরির বিজ্ঞপ্তি, প্রতি কয়েক ঘণ্টায় আপডেট।"
OLD_H1 = "<h1>আপনার ক্যারিয়ারের <br>পরবর্তী সুযোগ খুঁজুন</h1>"
OLD_LEAD = "<p>বাংলাদেশের সরকারি ও বেসরকারি নিয়োগ বিজ্ঞপ্তি—সব এক জায়গায়, সহজে খুঁজুন।</p>"
OLD_CANON = '<link rel="canonical" href="__SITE__/">'
OLD_OGURL = '<meta property="og:url" content="__SITE__/">'

EXTRA_CSS = (
    ".pagenav{margin-top:14px}.pagenav .row{padding-bottom:3px}"
    "a.chip{display:inline-flex;align-items:center;gap:4px}"
    ".intro{margin-top:14px;padding:13px 16px;background:var(--surface);border:1px solid var(--line);"
    "border-radius:16px;color:var(--mut);font-size:.95rem;line-height:1.7}"
    ".footlinks{margin-top:8px}.footlinks a{margin:0 8px;color:var(--green);font-weight:600}"
    ".article{margin-top:14px;padding:22px;background:var(--surface);border:1px solid var(--line);border-radius:20px}"
    ".article h1{font-size:1.7rem;margin:0 0 12px}"
    ".article h2{font-size:1.1rem;margin:20px 0 6px}"
    ".article a{color:var(--green);font-weight:600}"
)

FOOT_LINKS = ('<div class="footlinks"><a href="/about/">আমাদের সম্পর্কে</a>'
              '<a href="/privacy/">গোপনীয়তা নীতি</a></div>')


def rep(p, old, new, count=-1):
    """পুরনো লেখা না পেলে ক্র্যাশ না করে সতর্কবার্তা ছাপে।"""
    if old not in p:
        print("WARN: টেমপ্লেটে পাওয়া যায়নি ->", old[:45])
        return p
    return p.replace(old, new) if count < 0 else p.replace(old, new, count)


def cat_slug(c):
    return CAT_SLUG.get(c) or "c-" + hashlib.md5(c.encode("utf-8")).hexdigest()[:6]


# ---------- প্রতিটা জবের তথ্য ----------
xitems = []
for _j in jobs:
    _dt = parse(_j.get("first_seen", ""))
    _title = str(_j.get("title_bn") or _j.get("title", ""))
    xitems.append({
        "j": _j,
        "dt": _dt,
        "g": group_of(_dt),
        "title": _title,
        "raw": str(_j.get("title", "")),
        "source": str(_j.get("source", "") or "অজানা সোর্স"),
        "kind": kind_of(_j, _title),
        "cat": cat_of(_j, _title),
    })


def card(it):
    j = it["j"]
    dt = it["dt"]
    kind = it["kind"]
    cat = it["cat"]
    fresh = dt is not None and (NOW - dt).total_seconds() < 86400
    q = escape((it["title"] + " " + it["raw"] + " " + it["source"] + " " + cat).lower())
    dot = "<i class=dot title=নতুন></i>" if fresh else ""
    tag = "সরকারি" if kind == "govt" else "বেসরকারি"
    dl = ("<span>শেষ: " + escape(str(j["deadline"])) + "</span>") if j.get("deadline") else ""
    return (
        '<a class="job ' + kind + '" href="' + escape(str(j["url"]).strip()) +
        '" target="_blank" rel="nofollow noopener" data-k="' + kind + '" data-c="' + escape(cat) +
        '" data-q="' + q + '">'
        '<span class="ttl">' + escape(it["title"]) + dot + "</span>"
        '<span class="meta"><b class="tag">' + tag + "</b><span>" + escape(cat) + "</span><span>" +
        escape(it["source"]) + "</span>" + dl +
        '<span class="when">' + ago(dt) + "</span></span></a>"
    )


def sections_html(its):
    out = []
    for g in GROUPS:
        part = [card(i) for i in its if i["g"] == g]
        if part:
            out.append(
                '<section class="grp"><h2>' + GROUP_TITLE[g] + "<small>" + bn(len(part)) +
                'টি</small></h2><div class="list">' + "".join(part) + "</div></section>"
            )
    return "".join(out) or '<p class="empty">এখনো কোনো বিজ্ঞপ্তি নেই। কিছুক্ষণ পর আবার দেখুন।</p>'


# ---------- কোন কোন ক্যাটাগরির পেজ হবে ----------
_cat_count = Counter(i["cat"] for i in xitems)
cat_pages = [c for c, n in _cat_count.most_common(10) if n >= 3]

NAV_LINKS = [("/", "সব চাকরি")]
for _k in KIND_PAGES:
    NAV_LINKS.append(("/" + _k["slug"] + "/", _k["label"]))
for _c in cat_pages:
    NAV_LINKS.append(("/" + cat_slug(_c) + "/", _c))


def nav_html(active):
    out = []
    for href, label in NAV_LINKS:
        cls = "chip on" if href == active else "chip"
        out.append('<a class="' + cls + '" href="' + href + '">' + escape(label) + "</a>")
    return ('<nav class="pagenav" aria-label="চাকরির বিভাগ"><div class="row">' +
            "".join(out) + "</div></nav>")


def decorate(p, active, intro=""):
    p = rep(p, '<main><div id="feed">', nav_html(active) + "<main>" + intro + '<div id="feed">')
    p = rep(p, "</style>", EXTRA_CSS + "</style>", 1)
    p = rep(p, "</footer>", FOOT_LINKS + "</footer>", 1)
    return p


def strip_filters(p):
    a = p.find('<div class="filterline"><span class="filterlabel">চাকরির ধরন')
    b = p.find("</section>", a) if a != -1 else -1
    if a == -1 or b == -1:
        print("WARN: ফিল্টার অংশ পাওয়া যায়নি")
        return p
    return p[:a] + p[b:]


def fill(p, its, body):
    today = sum(1 for i in its if i["g"] == "আজ")
    return (p.replace("__SITE__", SITE).replace("__CONTACT__", CONTACT)
             .replace("__TODAY__", bn(today)).replace("__COUNT__", bn(len(its)))
             .replace("__UPD__", escape(upd)).replace("__CHIPS__", "")
             .replace("__LIST__", body))


def sub_page(slug, its, title, desc, h1, lead, intro):
    url = SITE + "/" + slug + "/"
    p = PAGE
    p = rep(p, OLD_TITLE, escape(title))
    p = rep(p, OLD_DESC, escape(desc))
    p = rep(p, OLD_SHORT, escape(desc))
    p = rep(p, OLD_CANON, '<link rel="canonical" href="' + url + '">')
    p = rep(p, OLD_OGURL, '<meta property="og:url" content="' + url + '">')
    p = rep(p, OLD_H1, "<h1>" + escape(h1) + "</h1>")
    p = rep(p, OLD_LEAD, "<p>" + escape(lead) + "</p>")
    p = strip_filters(p)
    note = ""
    if len(its) > MAX_ROWS:
        note = ('<p class="intro">সর্বশেষ ' + bn(MAX_ROWS) + 'টি বিজ্ঞপ্তি দেখানো হচ্ছে। '
                'সব দেখতে <a href="/">হোমপেজে</a> সার্চ করুন।</p>')
    p = fill(p, its, sections_html(its[:MAX_ROWS]) + note)
    box = '<div class="intro">' + escape(intro) + "</div>" if intro else ""
    return decorate(p, "/" + slug + "/", box)


def write_page(slug, content):
    os.makedirs(slug, exist_ok=True)
    with open(os.path.join(slug, "index.html"), "w", encoding="utf-8") as f:
        f.write(content)


urls = [SITE + "/"]

# ---------- সরকারি / বেসরকারি পেজ ----------
for k in KIND_PAGES:
    its = [i for i in xitems if i["kind"] == k["kind"]]
    write_page(k["slug"], sub_page(k["slug"], its, k["title"], k["desc"], k["h1"], k["lead"], k["intro"]))
    urls.append(SITE + "/" + k["slug"] + "/")

# ---------- ক্যাটাগরি পেজ ----------
for c in cat_pages:
    slug = cat_slug(c)
    its = [i for i in xitems if i["cat"] == c]
    if c == "অন্যান্য":
        title = "অন্যান্য চাকরির খবর | বিভিন্ন খাতের নতুন নিয়োগ বিজ্ঞপ্তি"
        h1 = "অন্যান্য খাতের চাকরি"
        lead = "বিভিন্ন কোম্পানি ও প্রতিষ্ঠানের সর্বশেষ নিয়োগ বিজ্ঞপ্তি।"
    else:
        title = c + " চাকরির খবর | নতুন " + c + " নিয়োগ বিজ্ঞপ্তি"
        h1 = c + " খাতের চাকরি"
        lead = c + " খাতের সর্বশেষ নিয়োগ বিজ্ঞপ্তি, আবেদনের লিংকসহ।"
    desc = "বাংলাদেশের " + c + " খাতের নতুন চাকরির বিজ্ঞপ্তি, শেষ তারিখ ও আবেদনের লিংক। নিয়মিত আপডেট।"
    intro = CAT_INTRO.get(c, "আবেদনের আগে মূল বিজ্ঞপ্তিতে শেষ তারিখ, যোগ্যতা ও আবেদনের নিয়ম মিলিয়ে নিন।")
    write_page(slug, sub_page(slug, its, title, desc, h1, lead, intro))
    urls.append(SITE + "/" + slug + "/")

# ---------- About ও Privacy ----------
_m = re.search(r"<style>.*?</style>", html, re.S)
STYLE_HTML = _m.group(0).replace("</style>", EXTRA_CSS + "</style>") if _m else ""
_f = re.search(r'<link rel="preconnect" href="https://fonts.googleapis.com">.*?rel="stylesheet">', html, re.S)
FONTS_HTML = _f.group(0) if _f else ""


def static_page(slug, title, desc, h1, body):
    url = SITE + "/" + slug + "/"
    return (
        '<!DOCTYPE html>\n<html lang="bn"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>" + escape(title) + "</title>"
        '<meta name="description" content="' + escape(desc) + '">'
        '<meta name="robots" content="index, follow">'
        '<link rel="canonical" href="' + url + '">' + FONTS_HTML + STYLE_HTML +
        '<script>try{var t=localStorage.getItem("jobsite-theme");if(t)document.documentElement.setAttribute("data-theme",t)}catch(e){}</script>'
        '</head><body><div class="wrap"><header class="topbar"><div class="nav">'
        '<a class="brand" href="/" aria-label="চাকরির খবর হোম"><span class="logo">চ</span><span>চাকরির খবর</span></a>'
        '</div></header><article class="article"><h1>' + escape(h1) + "</h1>" + body + "</article>"
        '<footer><div class="footerbrand">চাকরির খবর</div>'
        "তথ্য সরাসরি মূল সাইট থেকে সংগৃহীত। আবেদনের আগে মূল বিজ্ঞপ্তি যাচাই করে নিন।" +
        FOOT_LINKS + "</footer></div></body></html>\n"
    )


_mail = '<a href="mailto:' + CONTACT + '">' + CONTACT + "</a>"

ABOUT_BODY = (
    "<p>চাকরির খবর বাংলাদেশের সরকারি ও বেসরকারি চাকরির বিজ্ঞপ্তি এক জায়গায় দেখার একটি তালিকা-সাইট।</p>"
    "<h2>বিজ্ঞপ্তি কোথা থেকে আসে</h2>"
    "<p>বিজ্ঞপ্তিগুলো বিভিন্ন সংবাদমাধ্যম ও চাকরির সাইট থেকে স্বয়ংক্রিয়ভাবে সংগ্রহ করে তালিকাভুক্ত করা হয়। "
    "প্রতিটি বিজ্ঞপ্তির সাথে মূল সোর্সের নাম ও লিংক দেওয়া থাকে, এবং আবেদন মূল সাইটেই করতে হয়।</p>"
    "<h2>আমরা যা করি না</h2>"
    "<p>আমরা নিজেরা চাকরি দিই না, কোনো আবেদন গ্রহণ করি না এবং কারও কাছ থেকে টাকা নিই না। "
    "চাকরি দেওয়ার নামে কেউ টাকা চাইলে সতর্ক থাকুন।</p>"
    "<h2>ভুল পেলে জানান</h2>"
    "<p>কোনো বিজ্ঞপ্তির ক্যাটাগরি, তারিখ বা লিংক ভুল মনে হলে ইমেইলে জানান: " + _mail + "। "
    "আবেদনের আগে সবসময় মূল বিজ্ঞপ্তি যাচাই করে নিন।</p>"
)

PRIVACY_BODY = (
    "<p>এই সাইট আপনার কাছ থেকে নাম, ফোন নম্বর বা অন্য কোনো ব্যক্তিগত তথ্য সংগ্রহ করে না।</p>"
    "<h2>ব্রাউজারে সংরক্ষিত তথ্য</h2>"
    "<p>ডার্ক বা লাইট থিমের পছন্দ শুধু আপনার নিজের ব্রাউজারে সংরক্ষিত হয়, আমাদের কাছে পাঠানো হয় না।</p>"
    "<h2>তৃতীয় পক্ষ</h2>"
    "<p>সাইটের ফন্ট Google Fonts থেকে লোড হয়। চাকরির লিংকে ক্লিক করলে আপনি অন্য ওয়েবসাইটে যাবেন, "
    "সেগুলোর নিজস্ব গোপনীয়তা নীতি প্রযোজ্য।</p>"
    "<h2>পরিবর্তন</h2>"
    "<p>ভবিষ্যতে বিজ্ঞাপন বা অ্যানালিটিক্স যোগ হলে এই পেজে সেটা জানানো হবে।</p>"
    "<h2>যোগাযোগ</h2><p>" + _mail + "</p>"
)

for _slug, _t, _d, _h, _b in [
    ("about", "আমাদের সম্পর্কে | চাকরির খবর",
     "চাকরির খবর কীভাবে কাজ করে, বিজ্ঞপ্তি কোথা থেকে আসে এবং আমরা কী করি না।",
     "আমাদের সম্পর্কে", ABOUT_BODY),
    ("privacy", "গোপনীয়তা নীতি | চাকরির খবর",
     "চাকরির খবর সাইটে কোন তথ্য সংগ্রহ হয় এবং কোন তথ্য হয় না।",
     "গোপনীয়তা নীতি", PRIVACY_BODY),
]:
    write_page(_slug, static_page(_slug, _t, _d, _h, _b))
    urls.append(SITE + "/" + _slug + "/")

# ---------- হোমপেজ: নতুন পেজের লিংকসহ আবার লেখা ----------
with open("index.html", "w", encoding="utf-8") as f:
    f.write(decorate(html, "/"))

# ---------- পূর্ণ sitemap ----------
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    for u in urls:
        f.write("<url><loc>" + u + "</loc><lastmod>" + lastmod + "</lastmod></url>\n")
    f.write("</urlset>\n")

print("extra_pages: মোট " + str(len(urls)) + "টি পেজ (সরকারি, বেসরকারি, " +
      str(len(cat_pages)) + "টি ক্যাটাগরি, about, privacy)")

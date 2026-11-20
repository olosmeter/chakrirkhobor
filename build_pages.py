# চাকরির খবর: jobs.json থেকে প্রতিটি সার্কুলারের আলাদা পেজ (job/<slug>/index.html) ও sitemap.xml বানায়।
# scraper.py চলার পর এটা চালাতে হয়: python build_pages.py
import json, os, re, html, shutil, hashlib
from datetime import date
from urllib.parse import urlparse

SITE = "https://chakrirkhobor.pages.dev"   # নিজের ডোমেইন নিলে এখানে বদলান
BNUM = "০১২৩৪৫৬৭৮৯"
MON = ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]


def bn(s):
    return re.sub(r"\d", lambda m: BNUM[int(m.group())], str(s))


def esc(s):
    return html.escape(str(s or ""), quote=True)


def clean(t):
    return re.sub(r"\s+-\s+\S+\s+Apply\s*$", "", t or "", flags=re.I).strip()


def bn_date(iso):
    try:
        d = date.fromisoformat(iso)
        return "%s %s %s" % (bn(d.day), MON[d.month - 1], bn(d.year))
    except Exception:
        return ""


def make_slugs(jobs):
    """একই লিংক সবসময় একই slug পায় (লিংক সাজিয়ে প্রক্রিয়া করি)।"""
    used = {}
    for j in sorted(jobs, key=lambda x: x.get("link", "")):
        link = j.get("link", "")
        last = urlparse(link).path.rstrip("/").split("/")[-1]
        s = re.sub(r"[^a-z0-9]+", "-", last.lower()).strip("-")[:60]
        h = hashlib.md5(link.encode()).hexdigest()[:6]
        if len(s) < 8 or s.isdigit():
            s = (s + "-" if s else "job-") + h
        if s in used and used[s] != link:
            s = s + "-" + h
        used[s] = link
        j["slug"] = s


PAGE = """<!DOCTYPE html>
<html lang="bn"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | চাকরির খবর</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:type" content="article"><meta property="og:url" content="{url}">
<link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&family=Noto+Serif+Bengali:wght@700;800&display=swap" rel="stylesheet">
<style>
:root{{--bg:#f2f6f3;--surf:#fff;--ink:#12241b;--mute:#5d7066;--line:#dbe5de;--green:#0b6b4a;--red:#d9322a;--onb:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0c1511;--surf:#141f1a;--ink:#e8f1ec;--mute:#90a69a;--line:#25362d;--green:#3fc79a;--red:#ff6b5e;--onb:#06241a}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Hind Siliguri",system-ui,sans-serif;line-height:1.65}}
.w{{max-width:720px;margin:0 auto;padding:18px 18px 60px}}
.brand{{font-family:"Noto Serif Bengali",serif;font-weight:800;font-size:22px;color:inherit;text-decoration:none;display:inline-flex;align-items:center;gap:9px}}
.dot{{width:16px;height:16px;border-radius:50%;background:var(--red)}}
.box{{background:var(--surf);border:1px solid var(--line);border-radius:20px;padding:22px;margin-top:18px}}
.cat{{color:var(--green);font-weight:600;font-size:14px}}
h1{{font-family:"Noto Serif Bengali",serif;font-size:clamp(22px,6vw,30px);line-height:1.4;margin:6px 0 12px}}
dl{{display:grid;grid-template-columns:auto 1fr;gap:6px 16px;margin:16px 0}}dt{{color:var(--mute)}}dd{{margin:0;font-weight:500}}
.left{{display:inline-block;background:var(--red);color:var(--onb);border-radius:10px;padding:2px 12px;font-weight:600;font-size:14px}}
.apply{{display:block;text-align:center;background:var(--green);color:var(--onb);text-decoration:none;font-weight:600;border-radius:14px;padding:13px;margin-top:18px}}
a:focus-visible{{outline:3px solid var(--green);outline-offset:2px}}
.back{{display:inline-block;margin-top:18px;color:var(--green);font-weight:600}}
</style></head><body><div class="w">
<a class="brand" href="/"><span class="dot"></span>চাকরির খবর</a>
<article class="box">
<div class="cat">{cat}</div>
<h1>{title}</h1>
<p>{summary}</p>
<dl>{rows}</dl>
<span class="left">{left}</span>
<a class="apply" href="{link}" target="_blank" rel="noopener">মূল বিজ্ঞপ্তি দেখুন ও আবেদন করুন</a>
</article>
<a class="back" href="/">সব সার্কুলার দেখুন</a>
</div></body></html>
"""


def build_page(j):
    title = clean(j.get("title"))
    org = j.get("org", "")
    org_name = org.replace("সূত্র:", "").strip()
    posts = j.get("posts", "")
    has_posts = posts and not re.fullmatch(r"[–—\-\s]*", posts)
    dl = bn_date(j.get("deadline"))
    try:
        days = (date.fromisoformat(j["deadline"]) - date.today()).days
    except Exception:
        days = None
    left = "আজ শেষ দিন" if days == 0 else ("%s দিন বাকি" % bn(days) if days and days > 0 else "")
    rows = ""
    if org_name:
        rows += "<dt>প্রতিষ্ঠান</dt><dd>%s</dd>" % esc(org_name)
    if has_posts:
        rows += "<dt>পদসংখ্যা</dt><dd>%s</dd>" % esc(bn(posts))
    if j.get("grade"):
        rows += "<dt>গ্রেড</dt><dd>%s</dd>" % esc(j["grade"])
    if dl:
        rows += "<dt>আবেদনের শেষ তারিখ</dt><dd>%s</dd>" % esc(dl)
    parts = [title + "।"]
    if has_posts:
        parts.append("মোট পদ: %s।" % bn(posts))
    if dl:
        parts.append("আবেদনের শেষ তারিখ %s।" % dl)
    parts.append("আবেদনের আগে মূল বিজ্ঞপ্তি ভালো করে পড়ে নিন।")
    summary = " ".join(parts)
    link = j.get("link", "#")
    if not link.startswith(("http://", "https://")):
        link = "#"
    return PAGE.format(title=esc(title), desc=esc(summary[:155]), url=SITE + "/job/" + j["slug"] + "/",
                       cat=esc(j.get("cat", "")), summary=esc(summary), rows=rows, left=esc(left), link=esc(link))


def main():
    jobs = json.load(open("jobs.json", encoding="utf-8"))
    jobs = [j for j in jobs if j.get("link") and j.get("title")]
    make_slugs(jobs)
    shutil.rmtree("job", ignore_errors=True)   # মেয়াদোত্তীর্ণ জবের পেজ মুছে যায়
    for j in jobs:
        os.makedirs("job/" + j["slug"], exist_ok=True)
        with open("job/%s/index.html" % j["slug"], "w", encoding="utf-8") as f:
            f.write(build_page(j))
    # sitemap
    today = date.today().isoformat()
    urls = ['  <url><loc>%s/</loc><lastmod>%s</lastmod><changefreq>hourly</changefreq><priority>1.0</priority></url>' % (SITE, today)]
    for j in jobs:
        urls.append('  <url><loc>%s/job/%s/</loc><lastmod>%s</lastmod></url>' % (SITE, j["slug"], j.get("added") or today))
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n")
    # slug jobs.json-এ লিখি, যাতে index.html আলাদা পেজে লিংক দিতে পারে
    with open("jobs.json.tmp", "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    os.replace("jobs.json.tmp", "jobs.json")
    print("পেজ বানানো হয়েছে:", len(jobs), "| sitemap.xml আপডেট")


if __name__ == "__main__":
    main()

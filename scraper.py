# চাকরির খবর স্ক্র্যাপার: শিরোনাম, শেষ তারিখ ও মূল লিংক নেয়। Gemini দিয়ে প্রতিষ্ঠান/পদসংখ্যা/গ্রেড বের করে।
import json, re, os, time, urllib.request, urllib.parse, urllib.error
from datetime import date
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

EZ_RE = r"^/job-circular/(?!govt-job$|bank-job$|ngo-job$)[a-z0-9\-]+$"
SOURCES = [
    {"name": "প্রথম আলো", "list_url": "https://www.prothomalo.com/chakri/employment", "frag": "chakri/employment/", "link_re": r"^/chakri/employment/[a-z0-9]+$"},
    {"name": "যুগান্তর", "list_url": "https://www.jugantor.com/job-seek", "frag": "job-seek/", "link_re": r"^/job-seek/\d+$"},
    {"name": "বাংলা ট্রিবিউন", "list_url": "https://www.banglatribune.com/jobs", "frag": "jobs/", "link_re": r"^/jobs/\d+"},
    {"name": "বিডি প্রতিদিন", "list_url": "https://www.bd-pratidin.com/career", "frag": "career/", "link_re": r"^/career/\d{4}/\d\d/\d\d/\d+$"},
    {"name": "ইত্তেফাক", "list_url": "https://www.ittefaq.com.bd/topic/%E0%A6%A8%E0%A6%BF%E0%A7%9F%E0%A7%8B%E0%A6%97-%E0%A6%AC%E0%A6%BF%E0%A6%9C%E0%A7%8D%E0%A6%9E%E0%A6%AA%E0%A7%8D%E0%A6%A4%E0%A6%BF", "frag": "ittefaq-none/", "link_re": r"^/\d+/.+"},
    {"name": "সমকাল", "list_url": "https://samakal.com/career", "frag": "article/", "link_re": r"^/[a-z\-]+/article/\d+"},
    {"name": "জাগো নিউজ", "list_url": "https://www.jagonews24.com/job", "frag": "job/", "link_re": r"^/job/.*\d{4,}"},
    {"name": "ঢাকা পোস্ট", "list_url": "https://www.dhakapost.com/job", "frag": "job/", "link_re": r"^/job/.*\d{4,}"},
    {"name": "ইনকিলাব", "list_url": "https://www.dailyinqilab.com/jobs", "frag": "jobs/", "link_re": r"^/jobs?/.*\d{4,}"},
    {"name": "নয়া দিগন্ত", "list_url": "https://www.dailynayadiganta.com/job", "frag": "job/", "link_re": r"^/job[^/]*/.*\d{4,}"},
    {"name": "জনকণ্ঠ", "list_url": "https://www.dailyjanakantha.com/jobs", "frag": "jobs/", "link_re": r"^/jobs?/.*\d{4,}"},
    {"name": "EZ Jobs সরকারি", "org": "EZ Jobs", "cat": "সরকারি", "page_title": True, "list_url": "https://ezjobsbangla.com/job-circular/govt-job", "frag": "job-circular/", "link_re": EZ_RE},
    {"name": "EZ Jobs সরকারি-২", "org": "EZ Jobs", "cat": "সরকারি", "page_title": True, "list_url": "https://ezjobsbangla.com/job-circular/govt-job?page=2", "frag": "job-circular/", "link_re": EZ_RE},
    {"name": "EZ Jobs ব্যাংক", "org": "EZ Jobs", "cat": "ব্যাংক", "page_title": True, "list_url": "https://ezjobsbangla.com/job-circular/bank-job", "frag": "job-circular/", "link_re": EZ_RE},
    {"name": "EZ Jobs এনজিও", "org": "EZ Jobs", "cat": "এনজিও", "page_title": True, "list_url": "https://ezjobsbangla.com/job-circular/ngo-job", "frag": "job-circular/", "link_re": EZ_RE},
]
MAX_NEW = 15
MONTHS = {"জানুয়ারি":1,"ফেব্রুয়ারি":2,"মার্চ":3,"এপ্রিল":4,"মে":5,"জুন":6,"জুলাই":7,
          "আগস্ট":8,"সেপ্টেম্বর":9,"অক্টোবর":10,"নভেম্বর":11,"ডিসেম্বর":12}
EN_MONTHS = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

# ---- Gemini সেটিং ----
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
# একটা মডেল কাজ না করলে (404/400/403) পরেরটা চেষ্টা করবে। GEMINI_MODEL দিয়ে নিজের মডেলও দেওয়া যায়।
GEMINI_MODELS = ([os.environ["GEMINI_MODEL"]] if os.environ.get("GEMINI_MODEL") else []) + [
    "gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]
MAX_AI = 40          # প্রতি রানে সর্বোচ্চ Gemini কল (ফ্রি কোটা বাঁচাতে)
MAX_BACKFILL = 15    # পুরনো জবের তথ্য ঠিক করতে প্রতি রানে সর্বোচ্চ কতটা
AI = {"calls": 0, "off": not GEMINI_KEY, "model": 0}
ALLOWED_CATS = {"সরকারি", "ব্যাংক", "এনজিও", "শিক্ষক", "বেসরকারি"}
EMPTY_POSTS = ("—", "–", "", None)

def fetch(url):
    req = urllib.request.Request(urllib.parse.quote(url, safe=":/?&=%#"), headers={"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36", "Accept-Language": "bn,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.href=None; self.text=""; self.out=[]
    def handle_starttag(self, tag, attrs):
        if tag == "a": self.href = dict(attrs).get("href"); self.text = ""
    def handle_data(self, d):
        if self.href: self.text += d
    def handle_endtag(self, tag):
        if tag == "a" and self.href:
            self.out.append((self.href, " ".join(self.text.split()))); self.href = None

def find_deadline(text):
    pat = r"শেষ\s*তারিখ[^০-৯]{0,20}([০-৯]{1,2})\s*(" + "|".join(MONTHS) + r")\s*([০-৯]{4})"
    best = None
    for d, m, y in re.findall(pat, text):
        try:
            dt = date(int(y.translate(BN)), MONTHS[m], int(d.translate(BN)))
        except ValueError:
            continue
        best = dt if best is None or dt > best else best
    return best

def find_deadline_en(text):
    pats = [(r"deadline[^0-9]{0,60}?(\d{1,2})(?:st|nd|rd|th)?\s*,?\s*([A-Za-z]{3,9})\.?,?\s*(\d{4})", "dmy"),
            (r"deadline[^0-9]{0,60}?\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", "mdy")]
    best = None
    for pat, order in pats:
        for a, b, y in re.findall(pat, text, re.I):
            d, m = (a, b) if order == "dmy" else (b, a)
            mon = EN_MONTHS.get(m[:3].lower())
            if not mon: continue
            try:
                dt = date(int(y), mon, int(d))
            except ValueError:
                continue
            best = dt if best is None or dt > best else best
    return best

def guess_cat(t):
    rules = [("ব্যাংক",["ব্যাংক","ব্যাংকে"]),("এনজিও",["এনজিও","ফাউন্ডেশন","ট্রাস্ট"]),
             ("শিক্ষক",["শিক্ষক","বিশ্ববিদ্যালয়","কলেজ","স্কুল","প্রভাষক"]),
             ("সরকারি",["অধিদপ্তর","মন্ত্রণালয়","বিভাগ","কমিশন","বোর্ড","পরিষদ","গ্রেড","কর অঞ্চল","সরকারি"])]
    for cat, words in rules:
        if any(w in t for w in words): return cat
    return "বেসরকারি"

def guess_posts(t):
    m = re.search(r"([০-৯]+)\s*(?:টি\s*)?পদ", t)
    return m.group(1) if m else "—"

def clean_text(page):
    page = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", page)
    return " ".join(re.sub(r"<[^>]+>", " ", page).split())

def gemini_extract(title, body):
    """চাকরির পেজের লেখা পড়ে {org, posts, grade, cat} ফেরত দেয়। ব্যর্থ হলে {}।"""
    if AI["off"] or AI["calls"] >= MAX_AI:
        return {}
    prompt = (
        "তুমি বাংলাদেশের চাকরির বিজ্ঞপ্তি বিশ্লেষক। নিচের বিজ্ঞপ্তির লেখা থেকে শুধু JSON দাও, এই চারটি key সহ:\n"
        '"org": যে প্রতিষ্ঠান লোক নিচ্ছে তার নাম (পত্রিকা বা ওয়েবসাইটের নাম নয়)। বাংলায় লেখো, না পেলে ইংরেজি নাম। না পেলে "".\n'
        '"posts": মোট পদসংখ্যা, শুধু সংখ্যা (যেমন "১২০")। নিশ্চিত না হলে "".\n'
        '"grade": বেতন গ্রেড (যেমন "১০ম গ্রেড")। না থাকলে "".\n'
        '"cat": এগুলোর একটা: সরকারি, ব্যাংক, এনজিও, শিক্ষক, বেসরকারি।\n'
        "অনুমান করবে না। লেখায় যা নেই তা খালি রাখো।\n\n"
        "শিরোনাম: " + title + "\n\nলেখা:\n" + body[:6000])
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}).encode()
    while AI["model"] < len(GEMINI_MODELS):
        model = GEMINI_MODELS[AI["model"]]
        req = urllib.request.Request(
            "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent", data=data,
            headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_KEY})
        AI["calls"] += 1
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                res = json.loads(r.read().decode("utf-8"))
            out = json.loads(res["candidates"][0]["content"]["parts"][0]["text"])
            time.sleep(4)  # ফ্রি টিয়ারের প্রতি মিনিট সীমার জন্য
            if not isinstance(out, dict): return {}
            org = str(out.get("org", "")).strip()[:80]
            posts = str(out.get("posts", "")).strip()
            grade = str(out.get("grade", "")).strip()[:40]
            cat = str(out.get("cat", "")).strip()
            return {"org": org,
                    "posts": posts if re.fullmatch(r"[0-9০-৯]{1,5}", posts) else "",
                    "grade": grade,
                    "cat": cat if cat in ALLOWED_CATS else ""}
        except urllib.error.HTTPError as e:
            if e.code in (400, 403, 404):
                print("Gemini মডেল কাজ করেনি:", model, e.code); AI["model"] += 1; continue
            if e.code == 429:
                print("Gemini কোটা শেষ, এই রানে আর AI হবে না"); AI["off"] = True; return {}
            print("Gemini ত্রুটি:", e.code); return {}
        except Exception as e:
            print("Gemini ত্রুটি:", type(e).__name__); return {}
    print("কোনো Gemini মডেল কাজ করেনি, AI বন্ধ"); AI["off"] = True
    return {}

def apply_ai(j, ai):
    if not ai: return
    if ai.get("org") and j.get("org", "").startswith("সূত্র:"): j["org"] = ai["org"]
    if ai.get("posts") and j.get("posts") in EMPTY_POSTS: j["posts"] = ai["posts"]
    if ai.get("grade") and not j.get("grade"): j["grade"] = ai["grade"]
    j["ai"] = True

def main():
    try: jobs = json.load(open("jobs.json", encoding="utf-8"))
    except Exception: jobs = []
    jobs = [j for j in jobs if not j.get("demo")]
    seen = {j["link"] for j in jobs if "link" in j}
    today = date.today(); added = 0
    if AI["off"]: print("GEMINI_API_KEY নেই, AI ছাড়া চলছে")
    for src in SOURCES:
        try:
            html = fetch(src["list_url"])
        except Exception as e:
            print("লিস্ট পেজ আনা যায়নি:", src["name"], e); continue
        p = Links(); p.feed(html)
        cands = []
        def add(u, t):
            if re.match(src["link_re"], urlparse(u).path) and u not in seen and u not in [c[0] for c in cands]:
                cands.append((u, t))
        for href, text in p.out:
            if len(text) > 12:
                add(urljoin(src["list_url"], href.split("?")[0]), "" if src.get("page_title") else text)
        for m in re.findall(re.escape(src["frag"]) + r"[A-Za-z0-9_\-]+", html):
            add(urljoin(src["list_url"], "/" + m), "")
        print(src["name"], "- নতুন লিংক:", len(cands))
        for url, title in cands[:MAX_NEW]:
            try:
                page = fetch(url)
                text = re.sub(r"<[^>]+>", " ", page)
                dl = find_deadline(text) or find_deadline_en(text)
                if len(title) < 13:
                    m = re.search(r'og:title"\s+content="([^"]+)"', page) or re.search(r"<title>([^<]+)</title>", page)
                    title = " ".join(m.group(1).split()).split(" | ")[0] if m else ""
            except Exception as e:
                print("স্কিপ:", url, e); continue
            if not title: continue
            time.sleep(1)
            if not dl or dl < today: continue
            posts = guess_posts(title)
            if posts == "—":
                m = re.search(r"Total\s+Vacanc\w*\D{0,30}(\d+)", text, re.I)
                if m: posts = m.group(1)
            ai = gemini_extract(title, clean_text(page))
            job = {"title": title, "org": "সূত্র: " + src.get("org", src["name"]),
                   "cat": src.get("cat") or ai.get("cat") or guess_cat(title), "posts": posts, "grade": "",
                   "deadline": dl.isoformat(), "link": url, "added": today.isoformat()}
            apply_ai(job, ai)
            jobs.append(job)
            seen.add(url); added += 1
    # পুরনো জবগুলোর খালি তথ্য (প্রতিষ্ঠান/পদ/গ্রেড) Gemini দিয়ে ভরা
    if not AI["off"]:
        todo = [j for j in jobs if not j.get("ai") and j.get("link") and j.get("ai_try", 0) < 2]
        for j in todo[:MAX_BACKFILL]:
            if AI["off"] or AI["calls"] >= MAX_AI: break
            try:
                page = fetch(j["link"])
            except Exception as e:
                j["ai_try"] = j.get("ai_try", 0) + 1; continue
            ai = gemini_extract(j.get("title", ""), clean_text(page))
            if ai: apply_ai(j, ai)
            else: j["ai_try"] = j.get("ai_try", 0) + 1
            time.sleep(1)
    jobs = [j for j in jobs if j.get("deadline", "") >= today.isoformat()]
    jobs.sort(key=lambda j: j.get("deadline", ""))
    json.dump(jobs, open("jobs.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("যোগ হয়েছে:", added, "মোট:", len(jobs), "Gemini কল:", AI["calls"])

main()

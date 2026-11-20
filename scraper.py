# চাকরির খবর স্ক্র্যাপার (v6): জব সাইট থেকে শিরোনাম, শেষ তারিখ ও মূল লিংক নেয়।
# Gemini দিয়ে প্রতিষ্ঠান / পদসংখ্যা / গ্রেড / ক্যাটেগরি বের করে (কী না থাকলে AI ছাড়াই চলে)।
# v4 পরিবর্তন: যেসব সাইট GitHub থেকে আটকে দেয় সেগুলো বাদ, BD Govt Job যোগ, ত্রুটির কোড (403/404) লগে দেখায়।
import json, re, os, time, html, urllib.request, urllib.parse, urllib.error
from datetime import date, timedelta
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

# ------------------------------------------------------------------
# সোর্স তালিকা
#   name    : দেখানোর নাম
#   url     : লিস্ট পেজ
#   cat     : নির্দিষ্ট ক্যাটেগরি (না দিলে AI/অনুমান)
#   link_re : জবের লিংকের path-এর রেজেক্স (না দিলে generic মোড)
#   title_from_page : লিস্টের লেখা বাদ দিয়ে পেজ থেকে টাইটেল নেবে
# নতুন সাইট যোগ করতে শুধু একটা লাইন বাড়ান। কোনো সাইটে "নতুন লিংক: 0" এলে link_re ঠিক করুন।
# ------------------------------------------------------------------
EZ_RE = r"^/job-circular/(?!govt-job$|bank-job$|ngo-job$)[a-z0-9\-]+$"

BDG = "https://bdgovtjob.net/category/"          # BD Govt Job (.net)
BDS = "https://bdgovtjobs.com/category/"         # BD Govt Jobs (.com)
JNB = "https://jobsnoticebd.com/"                # Jobs Notice BD
BDI = "https://bdgovt.info/category/"            # BD Govt Info
MBJ = "https://mybdjob.com/category/"            # My BD Job
BDI_RE = r"^/(?!ongoing)[a-z0-9\-]*circula[a-z0-9\-]*/$"
BDG_RE = r"^/(?!ongoing)[a-z0-9\-]*job-circular[a-z0-9\-]*/$"
JNB_RE = r"^/(?!university-job-circular/$)[a-z0-9\-]*circular[a-z0-9\-]*/$"


def wp(site, slug, cat, label, rx, pages=(1,)):
    """WordPress ক্যাটাগরি পেজ (এবং চাইলে পেজ ২, ৩...) থেকে জবের লিংক নেওয়ার সোর্স।
    ai_cat: সাইডবারে অন্য ক্যাটাগরির জবও থাকে, তাই ক্যাটাগরি Gemini ঠিক করবে (না পারলে এটাই)।"""
    out = []
    for p in pages:
        u = site + slug + "/" + ("page/%d/" % p if p > 1 else "")
        out.append({"name": "%s %s%s" % (label, cat, "" if p == 1 else "-%d" % p), "org": label, "cat": cat,
                    "ai_cat": True, "title_from_page": True, "url": u, "link_re": rx})
    return out


SOURCES = (
    # --- BD Govt Job (.net) ---
    wp(BDG, "government-jobs-circular", "সরকারি", "BD Govt Job", BDG_RE, (1, 2))
    + wp(BDG, "bank-jobs", "ব্যাংক", "BD Govt Job", BDG_RE)
    + wp(BDG, "private-jobs", "বেসরকারি", "BD Govt Job", BDG_RE, (1, 2))
    + wp(BDG, "ngo-job-circular", "এনজিও", "BD Govt Job", BDG_RE)
    + wp(BDG, "pharmaceuticals-job-circular", "বেসরকারি", "BD Govt Job", BDG_RE)
    + wp(BDG, "educational-institution-jobs", "শিক্ষক", "BD Govt Job", BDG_RE)
    + wp(BDG, "university-job-circular", "শিক্ষক", "BD Govt Job", BDG_RE)
    + wp(BDG, "defence-job-circular", "সরকারি", "BD Govt Job", BDG_RE)
    # --- BD Govt Jobs (.com): সব চাকরির প্রথম ৪ পেজ + ব্যাংক ---
    + wp(BDS, "all-jobs", "সরকারি", "BD Govt Jobs", BDG_RE, (1, 2, 3, 4))
    + wp(BDS, "bank-jobs-2019", "ব্যাংক", "BD Govt Jobs", BDG_RE)
    + wp(BDS, "ngo-jobs", "এনজিও", "BD Govt Jobs", BDG_RE)
    # --- Jobs Notice BD ---
    + wp(JNB, "government-job", "সরকারি", "Jobs Notice BD", JNB_RE, (1, 2))
    + wp(JNB, "defense-jobs", "সরকারি", "Jobs Notice BD", JNB_RE)
    + wp(JNB, "university-job-circular", "শিক্ষক", "Jobs Notice BD", JNB_RE)
    + wp(JNB, "private-company-jobs", "বেসরকারি", "Jobs Notice BD", JNB_RE)
    + wp(JNB, "ngo-jobs", "এনজিও", "Jobs Notice BD", JNB_RE)
    + wp(JNB, "bank-job", "ব্যাংক", "Jobs Notice BD", JNB_RE)
    + wp(JNB, "pharmaceutical-company-job", "বেসরকারি", "Jobs Notice BD", JNB_RE)
    + wp(JNB, "hot-jobs", "সরকারি", "Jobs Notice BD", JNB_RE)
    # --- BD Govt Info ---
    + wp(BDI, "govt-job", "সরকারি", "BD Govt Info", BDI_RE, (1, 2))
    + wp(BDI, "private-job", "বেসরকারি", "BD Govt Info", BDI_RE)
    + wp(BDI, "ngo-job", "এনজিও", "BD Govt Info", BDI_RE)
    + wp(BDI, "bank-job", "ব্যাংক", "BD Govt Info", BDI_RE)
    + wp(BDI, "university-job", "শিক্ষক", "BD Govt Info", BDI_RE)
    + wp(BDI, "educational-job", "শিক্ষক", "BD Govt Info", BDI_RE)
    + wp(BDI, "pharmaceuticals-job-circular", "বেসরকারি", "BD Govt Info", BDI_RE)
    + wp(BDI, "defence-job-circular", "সরকারি", "BD Govt Info", BDI_RE)
    # --- My BD Job ---
    + wp(MBJ, "govt-job-circular", "সরকারি", "My BD Job", BDG_RE)
    + wp(MBJ, "private-job-circular", "বেসরকারি", "My BD Job", BDG_RE)
    + wp(MBJ, "ngo-job-circular", "এনজিও", "My BD Job", BDG_RE)
    + wp(MBJ, "bank-job-circular", "ব্যাংক", "My BD Job", BDG_RE)
    + wp(MBJ, "pharmaceutical-job-circular", "বেসরকারি", "My BD Job", BDG_RE)
    + wp(MBJ, "defence-job-circular", "সরকারি", "My BD Job", BDG_RE)
    + wp(MBJ, "teaching-job-circular", "শিক্ষক", "My BD Job", BDG_RE)
    + wp(MBJ, "railway-job-circular", "সরকারি", "My BD Job", BDG_RE)
    # --- EZ Jobs ---
    + [
        {"name": "EZ Jobs সরকারি", "org": "EZ Jobs", "cat": "সরকারি", "title_from_page": True, "url": "https://ezjobsbangla.com/job-circular/govt-job", "link_re": EZ_RE},
        {"name": "EZ Jobs সরকারি-২", "org": "EZ Jobs", "cat": "সরকারি", "title_from_page": True, "url": "https://ezjobsbangla.com/job-circular/govt-job?page=2", "link_re": EZ_RE},
        {"name": "EZ Jobs ব্যাংক", "org": "EZ Jobs", "cat": "ব্যাংক", "title_from_page": True, "url": "https://ezjobsbangla.com/job-circular/bank-job", "link_re": EZ_RE},
        {"name": "EZ Jobs এনজিও", "org": "EZ Jobs", "cat": "এনজিও", "title_from_page": True, "url": "https://ezjobsbangla.com/job-circular/ngo-job", "link_re": EZ_RE},
    ]
)

MAX_NEW = 15           # প্রতি সোর্সে প্রতি রানে সর্বোচ্চ নতুন লিংক যাচাই
SKIP_DAYS = 3          # তারিখ না পাওয়া/মেয়াদোত্তীর্ণ লিংক কত দিন পর আবার দেখা হবে
SCRAPE_LIMIT = 1500    # পুরো স্ক্র্যাপিং সর্বোচ্চ ২৫ মিনিট, তারপর থামে (বাকিটা পরের রানে)
MAX_BODY = 8000        # Gemini-কে পাঠানো লেখার সীমা

MONTHS = {"জানুয়ারি": 1, "জানুয়ারী": 1, "ফেব্রুয়ারি": 2, "ফেব্রুয়ারী": 2, "মার্চ": 3, "এপ্রিল": 4, "মে": 5, "জুন": 6,
          "জুলাই": 7, "আগস্ট": 8, "সেপ্টেম্বর": 9, "অক্টোবর": 10, "নভেম্বর": 11, "ডিসেম্বর": 12}
EN_MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
DIG = r"[0-9০-৯]"

# ---- Gemini সেটিং ----
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODELS = ([os.environ["GEMINI_MODEL"]] if os.environ.get("GEMINI_MODEL") else []) + [
    "gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash"]
MAX_AI_NEW = 30        # প্রতি রানে নতুন জবের জন্য সর্বোচ্চ Gemini কল
MAX_AI_BACKFILL = 15   # পুরনো জবের তথ্য ভরার জন্য আলাদা সীমা
AI_TIMEOUT = 30        # প্রতিবার Gemini-র উত্তরের জন্য সর্বোচ্চ অপেক্ষা (সেকেন্ড)
AI_TIME_LIMIT = 480    # পুরো রানে Gemini-র পেছনে সর্বোচ্চ সময় (৮ মিনিট), তারপর AI বন্ধ
AI_STREAK_LIMIT = 3    # পরপর এতবার সব মডেল ব্যর্থ হলে এই রানে AI বন্ধ
AI_MODEL_FAILS = 2     # একটা মডেল এতবার ব্যর্থ হলে এই রানে আর সেটা চেষ্টা করা হবে না
# calls = কতগুলো জবের জন্য Gemini ডাকা হয়েছে, tries = মোট HTTP চেষ্টা (ফলব্যাকসহ)
AI = {"calls": 0, "tries": 0, "off": not GEMINI_KEY, "streak": 0, "start": time.time(), "mfail": {}}
ALLOWED_CATS = {"সরকারি", "ব্যাংক", "এনজিও", "শিক্ষক", "বেসরকারি"}
EMPTY_POSTS = ("—", "–", "", None)
JOB_WORDS = re.compile(r"নিয়োগ|বিজ্ঞপ্তি|চাকরি|চাকুরি|সার্কুলার|job|career|recruit|vacanc|circular|hiring|apply", re.I)
BAD_WORDS = re.compile(r"login|register|signup|contact|about|privacy|terms|facebook|twitter|youtube|linkedin|\.(jpg|png|gif|css|js)(\?|$)", re.I)


def fetch(url):
    req = urllib.request.Request(
        urllib.parse.quote(url, safe=":/?&=%#"),
        headers={"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                 "Accept-Language": "bn,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=25) as r:
        ct = r.headers.get("Content-Type", "")
        if "pdf" in ct.lower() or "image" in ct.lower():
            return ""
        return r.read(3_000_000).decode("utf-8", "ignore")


def err_name(e):
    """HTTP ত্রুটি হলে কোড (403/404...), না হলে ত্রুটির ধরন।"""
    return getattr(e, "code", None) or type(e).__name__


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.href = None; self.text = ""; self.out = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href"); self.text = ""
    def handle_data(self, d):
        if self.href: self.text += d
    def handle_endtag(self, tag):
        if tag == "a" and self.href:
            self.out.append((self.href, " ".join(html.unescape(self.text).split()))); self.href = None


def clean_text(page):
    page = re.sub(r"(?is)<(script|style|noscript|nav|footer|header|aside)[^>]*>.*?</\1>", " ", page)
    page = re.sub(r"(?s)<!--.*?-->", " ", page)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", page)).split())


# ------------------------ তারিখ বের করা ------------------------
KEY = r"(?:শেষ\s*তারিখ|আবেদনের\s*শেষ\s*(?:তারিখ|সময়)|আবেদন\s*(?:গ্রহণের\s*)?শেষ|আবেদনের\s*সময়সীমা|last\s*date|closing\s*date|application\s*deadline|deadline|apply\s*(?:by|before)|end\s*date)"
BN_MON = "|".join(MONTHS)


def to_int(s):
    return int(s.translate(BN))


def dates_in(chunk):
    """একটা ছোট টুকরোর ভেতরের সব তারিখ (date অবজেক্ট) ফেরত দেয়।"""
    found = []
    # ১৫ ডিসেম্বর ২০২৬ / ১৫ ডিসেম্বর, ২০২৬
    for d, m, y in re.findall(r"(%s{1,2})\s*(%s)[,\s]*(%s{4})" % (DIG, BN_MON, DIG), chunk):
        found.append((to_int(y), MONTHS[m], to_int(d)))
    # 15 December 2026 / 15th Dec, 2026
    for d, m, y in re.findall(r"(\d{1,2})(?:st|nd|rd|th)?[\s\-]*([A-Za-z]{3,9})\.?,?[\s\-]*(\d{4})", chunk):
        if m[:3].lower() in EN_MONTHS: found.append((int(y), EN_MONTHS[m[:3].lower()], int(d)))
    # December 15, 2026
    for m, d, y in re.findall(r"([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", chunk):
        if m[:3].lower() in EN_MONTHS: found.append((int(y), EN_MONTHS[m[:3].lower()], int(d)))
    # ১৫/১২/২০২৬, ১৫-১২-২০২৬, ১৫.১২.২০২৬ (দিন/মাস/বছর)
    for d, m, y in re.findall(r"(%s{1,2})\s*[/\-.]\s*(%s{1,2})\s*[/\-.]\s*(%s{4})" % (DIG, DIG, DIG), chunk):
        found.append((to_int(y), to_int(m), to_int(d)))
    # 2026-12-15
    for y, m, d in re.findall(r"(\d{4})-(\d{1,2})-(\d{1,2})", chunk):
        found.append((int(y), int(m), int(d)))
    out = []
    for y, m, d in found:
        try: out.append(date(y, m, d))
        except ValueError: pass
    return out


def find_deadline(text):
    """শেষ তারিখ-জাতীয় শব্দের ঠিক পরের ৮০ অক্ষরের তারিখ। পেজের প্রথম মিলটাই ধরে (সাইডবারের তারিখ এড়াতে)।"""
    for m in re.finditer(KEY, text, re.I):
        ds = dates_in(text[m.end(): m.end() + 80])
        if ds: return ds[0]
    # "... তারিখ পর্যন্ত" ধরনের লেখা: তারিখের পরে "পর্যন্ত"
    for m in re.finditer(r"পর্যন্ত|until|till", text, re.I):
        ds = dates_in(text[max(0, m.start() - 40): m.start()])
        if ds: return ds[-1]
    return None


def guess_cat(t):
    rules = [("ব্যাংক", ["ব্যাংক", "bank"]), ("এনজিও", ["এনজিও", "ফাউন্ডেশন", "ট্রাস্ট", "ngo"]),
             ("শিক্ষক", ["শিক্ষক", "বিশ্ববিদ্যালয়", "কলেজ", "স্কুল", "প্রভাষক", "madrasa", "মাদ্রাসা"]),
             ("সরকারি", ["অধিদপ্তর", "মন্ত্রণালয়", "বিভাগ", "কমিশন", "বোর্ড", "পরিষদ", "গ্রেড", "কর অঞ্চল", "সরকারি"])]
    low = t.lower()
    for cat, words in rules:
        if any(w in low for w in words): return cat
    return "বেসরকারি"


def guess_posts(t):
    m = re.search(r"([০-৯]+)\s*(?:টি\s*)?পদ", t)
    return m.group(1) if m else "—"


# ------------------------ Gemini ------------------------
def usable_models():
    """এই রানে যে মডেলগুলো এখনো চেষ্টা করার মতো।"""
    return [m for m in GEMINI_MODELS if AI["mfail"].get(m, 0) < AI_MODEL_FAILS]


def model_failed(model, hard=False):
    """hard=True হলে (মডেল নেই / কোটা শেষ) এই রানে মডেলটা পুরোপুরি বাদ।"""
    AI["mfail"][model] = 99 if hard else AI["mfail"].get(model, 0) + 1


def gemini_extract(title, body, budget):
    """{org, posts, grade, cat} ফেরত দেয়। ব্যর্থ হলে None (খালি dict নয়, যাতে বোঝা যায় ব্যর্থ)।
    একটা মডেল 503/Timeout/429 দিলে পরের মডেলে চেষ্টা করে।"""
    if AI["off"] or AI["calls"] >= budget:
        return None
    if time.time() - AI["start"] > AI_TIME_LIMIT:
        print("Gemini-র সময়সীমা শেষ, এই রানে আর AI হবে না"); AI["off"] = True
        return None
    # টাইটেলের কাছাকাছি থেকে কেটে নিই, যাতে মেনুতেই সীমা শেষ না হয়
    i = body.find(title[:25]) if title else -1
    body = body[i:] if i > 0 else body
    prompt = (
        "তুমি বাংলাদেশের চাকরির বিজ্ঞপ্তি বিশ্লেষক। নিচের বিজ্ঞপ্তির লেখা থেকে শুধু JSON দাও, এই চারটি key সহ:\n"
        '"org": যে প্রতিষ্ঠান লোক নিচ্ছে তার পুরো নাম (পত্রিকা বা ওয়েবসাইটের নাম নয়)। বাংলায় লেখো, না পেলে ইংরেজি নাম। না পেলে "".\n'
        '"posts": মোট পদসংখ্যা, শুধু সংখ্যা (যেমন "১২০")। নিশ্চিত না হলে "".\n'
        '"grade": বেতন গ্রেড (যেমন "১০ম গ্রেড")। না থাকলে "".\n'
        '"cat": এগুলোর একটা: সরকারি, ব্যাংক, এনজিও, শিক্ষক, বেসরকারি।\n'
        "অনুমান করবে না। লেখায় যা নেই তা খালি রাখো।\n\n"
        "শিরোনাম: " + title + "\n\nলেখা:\n" + body[:MAX_BODY])
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}).encode()
    AI["calls"] += 1
    for model in usable_models():
        req = urllib.request.Request(
            "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent", data=data,
            headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_KEY})
        AI["tries"] += 1
        try:
            with urllib.request.urlopen(req, timeout=AI_TIMEOUT) as r:
                res = json.loads(r.read().decode("utf-8"))
            out = json.loads(res["candidates"][0]["content"]["parts"][0]["text"])
        except urllib.error.HTTPError as e:
            msg = ""
            try: msg = e.read().decode("utf-8", "ignore")[:200]
            except Exception: pass
            if e.code == 404:
                print("Gemini মডেল পাওয়া যায়নি:", model); model_failed(model, hard=True)
            elif e.code in (400, 401, 403) and re.search(r"api[\s_-]*key|permission|denied|unauthenticated", msg, re.I):
                print("Gemini key সমস্যা", e.code, msg); AI["off"] = True
                return None   # key ভুল: মডেল বদলে লাভ নেই
            elif e.code == 429:
                print("Gemini কোটা শেষ (429):", model); model_failed(model, hard=True)
            else:
                print("Gemini ত্রুটি:", e.code, model); model_failed(model)
            time.sleep(2); continue
        except Exception as e:
            print("Gemini ত্রুটি:", type(e).__name__, model); model_failed(model)
            time.sleep(2); continue
        # সফল
        AI["mfail"][model] = 0; AI["streak"] = 0
        time.sleep(4)  # ফ্রি টিয়ারের প্রতি মিনিট সীমা
        if isinstance(out, list) and out: out = out[0]
        if not isinstance(out, dict): return {}
        posts = str(out.get("posts", "")).strip()
        cat = str(out.get("cat", "")).strip()
        return {"org": str(out.get("org", "")).strip()[:80],
                "posts": posts if re.fullmatch(r"[0-9০-৯]{1,5}", posts) else "",
                "grade": str(out.get("grade", "")).strip()[:40],
                "cat": cat if cat in ALLOWED_CATS else ""}
    # কোনো মডেলই সাড়া দেয়নি
    AI["streak"] += 1
    if not usable_models():
        print("কোনো Gemini মডেল কাজ করছে না, এই রানে AI বন্ধ"); AI["off"] = True
    elif AI["streak"] >= AI_STREAK_LIMIT:
        print("পরপর", AI["streak"], "বার Gemini ব্যর্থ, এই রানে AI বন্ধ"); AI["off"] = True
    return None


def dkey(j):
    """একই প্রতিষ্ঠান + একই শেষ তারিখ = একই জব (বিভিন্ন সাইট থেকে এলে ডুপ্লিকেট এড়াতে)।"""
    o = (j.get("org") or "").strip().lower()
    return None if (not o or o.startswith("সূত্র:")) else (o, j.get("deadline"))


def apply_ai(j, ai):
    if not ai: return
    if ai.get("org") and j.get("org", "").startswith("সূত্র:"): j["org"] = ai["org"]
    if ai.get("posts") and j.get("posts") in EMPTY_POSTS: j["posts"] = ai["posts"]
    if ai.get("grade") and not j.get("grade"): j["grade"] = ai["grade"]
    j["ai"] = True


# ------------------------ লিংক বাছাই ------------------------
def candidates(src, html_text):
    base = src["url"]; host = urlparse(base).netloc.replace("www.", "")
    p = Links(); p.feed(html_text)
    out = []; have = set()
    def add(u, t):
        u = u.split("#")[0]
        if u and u not in have: have.add(u); out.append((u, t))
    for href, text in p.out:
        if not href or href.startswith(("javascript:", "mailto:", "tel:")): continue
        url = urljoin(base, href)
        path = urlparse(url).path
        if src.get("link_re"):
            url = url.split("?")[0]; path = urlparse(url).path
            if re.match(src["link_re"], path) and (len(text) > 12 or src.get("title_from_page")):
                add(url, "" if src.get("title_from_page") else text)
        else:
            # generic মোড: একই হোস্ট, লেখা/লিংকে চাকরির শব্দ, অপ্রয়োজনীয় লিংক বাদ
            same = urlparse(url).netloc.replace("www.", "").endswith(host)
            if same and len(text) > 12 and JOB_WORDS.search(text + " " + path) and not BAD_WORDS.search(url) and url.rstrip("/") != base.rstrip("/"):
                add(url, text)
    return out


def main():
    try: jobs = json.load(open("jobs.json", encoding="utf-8"))
    except Exception: jobs = []
    jobs = [j for j in jobs if not j.get("demo")]
    try: skipped = json.load(open("skipped.json", encoding="utf-8"))
    except Exception: skipped = {}
    today = date.today()
    cutoff = (today - timedelta(days=SKIP_DAYS)).isoformat()
    skipped = {u: d for u, d in skipped.items() if d >= cutoff}
    seen = {j["link"] for j in jobs if "link" in j} | set(skipped)
    added = 0; tried_ai = set()
    have_keys = {dkey(j) for j in jobs} - {None}
    if AI["off"]: print("GEMINI_API_KEY নেই, AI ছাড়া চলছে")

    for src in SOURCES:
        if time.time() - AI["start"] > SCRAPE_LIMIT:
            print("সময়সীমা শেষ, বাকি সোর্স পরের রানে"); break
        try: html_text = fetch(src["url"])
        except Exception as e:
            print("লিস্ট পেজ আনা যায়নি:", src["name"], err_name(e)); continue
        cands = [(u, t) for u, t in candidates(src, html_text) if u not in seen]
        print(src["name"], "- নতুন লিংক:", len(cands))
        for url, title in cands[:MAX_NEW]:
            if time.time() - AI["start"] > SCRAPE_LIMIT: break
            try:
                page = fetch(url)
                if not page: skipped[url] = today.isoformat(); continue
                text = clean_text(page)
                dl = find_deadline(text)
                if len(title) < 13:
                    m = re.search(r'og:title"\s+content="([^"]+)"', page) or re.search(r"<title>([^<]+)</title>", page)
                    title = " ".join(html.unescape(m.group(1)).split()).split(" | ")[0] if m else ""
            except Exception as e:
                print("স্কিপ:", url, err_name(e)); continue
            time.sleep(1)
            if not title or not dl or dl < today:
                skipped[url] = today.isoformat()   # মনে রাখি, যাতে প্রতি রানে স্লট নষ্ট না হয়
                continue
            posts = guess_posts(title)
            if posts == "—":
                m = re.search(r"(?:Total\s+Vacanc\w*|পদসংখ্যা|মোট\s*পদ)\D{0,30}([0-9০-৯]+)", text, re.I)
                if m: posts = m.group(1)
            ai = gemini_extract(title, text, MAX_AI_NEW); tried_ai.add(url)
            job = {"title": title, "org": "সূত্র: " + src.get("org", src["name"]),
                   "cat": ((ai or {}).get("cat") if src.get("ai_cat") else "") or src.get("cat") or (ai or {}).get("cat") or guess_cat(title), "posts": posts, "grade": "",
                   "deadline": dl.isoformat(), "link": url, "added": today.isoformat()}
            apply_ai(job, ai)
            k = dkey(job)
            if k and k in have_keys:
                skipped[url] = today.isoformat(); continue   # অন্য সাইট থেকে আগেই এসেছে
            if k: have_keys.add(k)
            jobs.append(job); seen.add(url); added += 1

    # পুরনো জবের খালি তথ্য ভরা (এই রানে যেগুলো ইতিমধ্যে চেষ্টা হয়েছে সেগুলো বাদ)
    if not AI["off"]:
        todo = [j for j in jobs if not j.get("ai") and j.get("link") and j["link"] not in tried_ai and j.get("ai_try", 0) < 2]
        used = 0
        for j in todo:
            if AI["off"] or used >= MAX_AI_BACKFILL: break
            try: page = fetch(j["link"])
            except Exception: continue
            ai = gemini_extract(j.get("title", ""), clean_text(page), 10**6); used += 1
            if ai is None: continue            # নেটওয়ার্ক/কোটা সমস্যা: চেষ্টা গোনা হবে না
            if ai: apply_ai(j, ai)
            else: j["ai_try"] = j.get("ai_try", 0) + 1   # সফল কিন্তু খালি উত্তর
            time.sleep(1)

    jobs = [j for j in jobs if j.get("deadline", "") >= today.isoformat()]
    jobs.sort(key=lambda j: j.get("deadline", ""))
    # অ্যাটমিক লেখা: মাঝপথে ক্র্যাশ করলেও আগের ডেটা অক্ষত থাকবে
    for name, obj in (("jobs.json", jobs), ("skipped.json", skipped)):
        json.dump(obj, open(name + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        os.replace(name + ".tmp", name)
    ok_ai = sum(1 for j in jobs if j.get("ai"))
    print("যোগ হয়েছে:", added, "মোট:", len(jobs), "Gemini কল:", AI["calls"], "(চেষ্টা:", str(AI["tries"]) + ")",
          "AI-ভরা জব:", ok_ai)


if __name__ == "__main__":
    main()
    # আলাদা সার্কুলার পেজ ও sitemap (build_pages.py রিপোতে থাকলেই চলবে)
    try:
        import build_pages
        build_pages.main()
    except ImportError:
        pass

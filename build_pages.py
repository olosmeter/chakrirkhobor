#!/usr/bin/env python3
"""jobs.json থেকে index.html, sitemap.xml ও robots.txt বানায়।"""
import json
import os
import re
from html import escape
from collections import Counter
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit

SITE = "https://chakrirkhobor.pages.dev"
CONTACT = "nazmul.24x@gmail.com"
BD = timezone(timedelta(hours=6))
NOW = datetime.now(BD)

# টাইমজোনহীন (naive) সময় কোন জোনে ধরা হবে। আপনার বট/স্ক্র্যাপার UTC-তে naive সময়
# লিখলে এটি timezone.utc করুন। এখন আগের মতোই BD ধরা হচ্ছে (আচরণ বদলায়নি)।
NAIVE_TZ = BD

GROUPS = ["আজ", "গতকাল", "এই সপ্তাহ", "নির্ধারিত", "আগের"]

GROUP_TITLE = {
    "আজ": "আজকের চাকরির খবর",
    "গতকাল": "গতকালের চাকরির খবর",
    "এই সপ্তাহ": "এই সপ্তাহের চাকরির খবর",
    "নির্ধারিত": "নির্ধারিত চাকরির বিজ্ঞপ্তি",
    "আগের": "আগের চাকরির বিজ্ঞপ্তি",
}

# ---------- সরকারি / বেসরকারি শনাক্তকরণ ----------
GOVT_STRONG = [
    "সোনালী ব্যাংক", "জনতা ব্যাংক", "অগ্রণী ব্যাংক", "রূপালী ব্যাংক",
    "বাংলাদেশ ব্যাংক", "বেসিক ব্যাংক", "বিডিবিএল", "কৃষি ব্যাংক",
    "বাংলাদেশ ডেভেলপমেন্ট ব্যাংক", "মন্ত্রণালয়", "অধিদপ্তর",
    "অধিদফতর", "গোয়েন্দা",
]

# "কমিশন" ও "কর্তৃপক্ষ" খুব সাধারণ শব্দ ("কমিশন ভিত্তিক সেলস") — তাই সরাসরি না রেখে
# নির্দিষ্ট প্রতিষ্ঠানের নাম রাখা হয়েছে।
GOVT_KW = [
    "অধিদপ্তর", "অধিদফতর", "মন্ত্রণালয়", "জেলা প্রশাসক",
    "সিভিল সার্জন", "মহাপরিচালক", "কর অঞ্চল", "কমিশনার",
    "পাবলিক সার্ভিস কমিশন", "দুর্নীতি দমন কমিশন", "নির্বাচন কমিশন",
    "বিদ্যুৎ কমিশন", "এনবিআর", "সচিবালয়", "সেনাবাহিনী",
    "বিমানবাহিনী", "নৌবাহিনী", "আনসার", "বিজিবি",
    "কোস্ট গার্ড", "উপজেলা পরিষদ", "জেলা পরিষদ",
    "ইউনিয়ন পরিষদ", "বিসিএস",
    "পুলিশ", "আদালত", "জজ কোর্ট", "ডিএসসিসি",
    "ডিএনসিসি", "সিটি করপোরেশন", "ব্যানবেইস",
    "বোয়েসেল", "সরকারিভাবে", "সরকারি চাকরি",
    "উন্নয়ন বোর্ড", "শিক্ষা বোর্ড",
    "বিমান চলাচল কর্তৃপক্ষ", "বন্দর কর্তৃপক্ষ", "প্রাথমিক বিদ্যালয়",
    "পৌরসভা", "ওয়াসা", "রেলওয়ে", "ডাক বিভাগ", "বিটিসিএল", "বিআরটিএ",
    "ফায়ার সার্ভিস", "কারা অধিদ", "ট্রাইব্যুনাল", "পিডিবি", "পল্লী বিদ্যুৎ",
    "বাংলাদেশ বিমান", "বিসিক", "জাতীয় সংসদ", "রাষ্ট্রায়ত্ত",
    "বেপজা", "বিআইডব্লিউটিসি", "পেট্রোলিয়াম করপোরেশন",
    "পার্বত্য জেলা পরিষদ",
]

PRIVATE_KW = [
    "লিমিটেড", "পিএলসি", "এনজিও", "প্রাইভেট",
    "বেসরকারি", "গ্রুপ", "গ্রামীণফোন",
    "ফাউন্ডেশন", "ইউনিভার্সিটি",
]

PRIVATE_EN = re.compile(
    r"\b(ltd|limited|plc|ngo|private|pvt|group|foundation|university)\b",
    re.I
)

# "ব্লাড গ্রুপ", "গ্রুপ-সি" ইত্যাদি বেসরকারি-সংকেত নয়
NOT_GROUP = re.compile(
    r"ব্লাড\s*গ্রুপ|গ্রুপ\s*[-–]\s*\S+|\bgroup\s*[-–]\s*\w+|blood\s*group",
    re.I
)

PRIVATE_UNI = [
    "নর্থ সাউথ", "ইস্ট ওয়েস্ট", "ব্র্যাক", "ইউআইইউ",
    "ইউনাইটেড ইন্টারন্যাশনাল", "ড্যাফোডিল", "স্টামফোর্ড",
    "ইস্টার্ন", "সাউথইস্ট", "সাউথ ইস্ট", "গ্রিন",
    "ইন্ডিপেন্ডেন্ট", "আহসানউল্লাহ",
    "আমেরিকান ইন্টারন্যাশনাল", "প্রাইম এশিয়া",
    "সিটি ইউনিভার্সিটি", "বাংলাদেশ ইউনিভার্সিটি",
    "ইউসিএসআই", "লিডিং",
]


# "সরকারি" শব্দ — কিন্তু "বেসরকারি"-র ভেতরের "সরকারি" নয়
GOVT_WORD = re.compile(r"(?<!বে)সরকারি")

# বেসরকারি হলেও "সরকারি" লেখা থাকতে পারে এমন বাক্যাংশ (যেমন "সরকারি অনুমোদিত")
GOVT_WORD_FALSE = re.compile(r"সরকারি\s*(অনুমোদিত|নিবন্ধিত|স্বীকৃত)")


def kind_of(j, title):
    """সরকারি/বেসরকারি নির্ণয়। অগ্রাধিকার ক্রম:
    1. বট/জেমিনি যদি type দেয় (govt/private) — সেটাই চূড়ান্ত
    2. নিশ্চিত সরকারি নাম (মন্ত্রণালয়, সরকারি ব্যাংক ইত্যাদি)
    3. নিশ্চিত বেসরকারি সংকেত (লিমিটেড, পিএলসি, এনজিও, বেসরকারি)
    4. শিরোনামে আলাদা শব্দ হিসেবে "সরকারি" (সরকারি হাসপাতাল, সরকারি কলেজ)
    5. বিশ্ববিদ্যালয়: পরিচিত প্রাইভেট তালিকায় থাকলে বেসরকারি, নইলে সরকারি
    6. সাধারণ সরকারি কীওয়ার্ড
    7. বটের category == "সরকারি"
    8. কিছুই না মিললে বেসরকারি
    """
    t = str(j.get("type", "")).strip().lower()

    if t in ("govt", "private"):
        return t

    # বট type-এ বাংলা/ভিন্ন বানান দিলেও ধরার চেষ্টা
    if t in ("সরকারি", "government", "gov"):
        return "govt"
    if t in ("বেসরকারি", "pvt"):
        return "private"

    text = f"{title} {j.get('title', '')}".lower()
    text = NOT_GROUP.sub(" ", text)
    text = GOVT_WORD_FALSE.sub(" ", text)

    if any(k in text for k in GOVT_STRONG):
        return "govt"

    if any(k in text for k in PRIVATE_KW) or PRIVATE_EN.search(text):
        return "private"

    if GOVT_WORD.search(text):
        return "govt"

    if "বিশ্ববিদ্যালয়" in text:
        return (
            "private"
            if any(k in text for k in PRIVATE_UNI)
            else "govt"
        )

    if any(k in text for k in GOVT_KW):
        return "govt"

    if j.get("category") == "সরকারি":
        return "govt"

    return "private"


CAT_RULES = [
    ("সেনা-পুলিশ", [
        "সেনাবাহিনী", "বিমানবাহিনী", "নৌবাহিনী",
        "পুলিশ", "আনসার", "বিজিবি", "সৈনিক"
    ]),
    ("শিক্ষা", [
        "অধ্যাপক", "প্রভাষক", "লেকচারার", "শিক্ষক",
        "বিশ্ববিদ্যালয়", "ইউনিভার্সিটি", "স্কুল",
        "কলেজ", "মাদ্রাসা", "ইনস্ট্রাক্টর",
        "professor", "lecturer"
    ]),
    ("ব্যাংক", ["ব্যাংক", "bank", "ইসলামী ব্যাংক"]),
    ("স্বাস্থ্য", [
        "সিভিল সার্জন", "হাসপাতাল", "স্বাস্থ্য",
        "নার্স", "ডাক্তার", "মেডিকেল", "ফার্মা",
        "প্যারামেডিক", "ল্যাব", "medical", "hospital"
    ]),
    ("এনজিও", ["এনজিও", "ngo", "ফাউন্ডেশন", "foundation"]),
    ("আইটি", [
        "সফটওয়্যার", "প্রোগ্রামার", "ডেভেলপার",
        "developer", "software", "আইটি"
    ]),
    ("প্রকৌশল", [
        "ইঞ্জিনিয়ার", "প্রকৌশলী", "টেকনিশিয়ান",
        "আর্কিটেক্ট", "engineer"
    ]),
    ("সেলস ও মার্কেটিং", [
        "সেলস", "মার্কেটিং", "বিজনেস ডেভেলপমেন্ট",
        "টেলিসেলস", "টেরিটরি", "sales", "marketing"
    ]),
    ("অ্যাকাউন্টস ও ফাইন্যান্স", [
        "অ্যাকাউন্ট", "একাউন্ট", "হিসাব",
        "ফাইন্যান্স", "ফিন্যান্স", "অডিট",
        "নিরীক্ষা", "accounts", "finance", "audit"
    ]),
    ("ডিজাইন ও মিডিয়া", [
        "গ্রাফিক", "ভিডিও এডিটর", "ভিডিওগ্রাফার",
        "কনটেন্ট", "ডিজাইনার", "ফটোগ্রাফার",
        "সাংবাদিক", "রিপোর্টার", "ভিডিও এডিটিং"
    ]),
    ("প্রশাসন ও অফিস", [
        "অফিস সহায়ক", "অফিস সহকারী", "অফিস সাপোর্ট",
        "রিসেপশন", "ফ্রন্ট ডেস্ক", "পার্সোনাল",
        "অ্যাডমিন", "এইচআর", "ডেটা এন্ট্রি",
        "ডাটা এন্ট্রি", "কম্পিউটার অপারেটর",
        "টাইপিস্ট", "সেক্রেটারি", "কাস্টমার"
    ]),
    ("নিরাপত্তা ও ড্রাইভার", [
        "সিকিউরিটি", "নিরাপত্তা প্রহরী", "গার্ড",
        "ড্রাইভার", "রাইডার", "পিয়ন",
        "ক্লিনার", "মালী", "লিফট", "অপারেটর"
    ]),
]

NOT_CATS = {"", "সরকারি", "বেসরকারি", "অন্যান্য"}


def cat_of(j, title):
    c = str(j.get("category") or "").strip()

    if c not in NOT_CATS:
        return c

    text = f"{title} {j.get('title', '')}".lower()

    for name, kws in CAT_RULES:
        if any(k in text for k in kws):
            return name

    return "অন্যান্য"


# ---------- হেল্পার ----------
def bn(n):
    return str(n).translate(
        str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
    )


def parse(iso):
    if not iso:
        return None

    try:
        dt = datetime.fromisoformat(
            str(iso).replace("Z", "+00:00")
        )
    except (ValueError, TypeError):
        return None

    return (
        dt.replace(tzinfo=NAIVE_TZ).astimezone(BD)
        if dt.tzinfo is None
        else dt.astimezone(BD)
    )


def group_of(dt):
    if not dt:
        return "আগের"

    d = (NOW.date() - dt.date()).days

    if d < 0:
        return "নির্ধারিত"
    if d == 0:
        return "আজ"
    if d == 1:
        return "গতকাল"
    if d <= 7:
        return "এই সপ্তাহ"

    return "আগের"


def ago(dt):
    if not dt:
        return ""

    seconds = (NOW - dt).total_seconds()

    if seconds < 0:
        return "প্রকাশের সময় আসেনি"

    h = int(seconds // 3600)

    if h < 1:
        return "এইমাত্র"
    if h < 24:
        return f"{bn(h)} ঘণ্টা আগে"

    days = h // 24

    if days < 30:
        return f"{bn(days)} দিন আগে"
    if days < 365:
        return f"{bn(days // 30)} মাস আগে"

    return f"{bn(days // 365)} বছর আগে"


def bn_period(hour):
    if hour < 4:
        return "রাত"
    if hour < 6:
        return "ভোর"
    if hour < 12:
        return "সকাল"
    if hour < 15:
        return "দুপুর"
    if hour < 18:
        return "বিকাল"
    if hour < 20:
        return "সন্ধ্যা"
    return "রাত"


def fmt_updated(dt):
    h12 = dt.hour % 12 or 12
    return (
        f"{bn(dt.strftime('%d/%m/%Y'))}, "
        f"{bn_period(dt.hour)} {bn(h12)}:{bn(dt.strftime('%M'))}"
    )


def fmt_deadline(d):
    if not d:
        return ""

    dt = parse(d)

    return bn(dt.strftime("%d/%m/%Y")) if dt else str(d)


BAD_SCRIPT = re.compile(
    r"[\u0400-\u04FF\u0600-\u06FF\u0900-\u097F]"
)

JUNK_URL = (
    "/policies/",
    "privacy-policy",
    "terms-and-conditions",
    "terms-of-service",
    "shipping-policy",
    "refund-policy",
    "rmgjobs.com/pages/",
)


def clean_title(j):
    tb = str(j.get("title_bn") or "")
    raw = str(j.get("title") or "")

    if (
        tb and BAD_SCRIPT.search(tb)
        and raw and not BAD_SCRIPT.search(raw)
    ):
        tb = raw

    t = tb or raw

    if BAD_SCRIPT.search(t):
        t = BAD_SCRIPT.sub("", t)

    return re.sub(r"\s+", " ", t).strip()


def norm_title(t):
    """সোর্স-নিরপেক্ষ ডুপ্লিকেট ধরার জন্য শিরোনাম স্বাভাবিক করে।"""
    # \W ব্যবহার করা যাবে না: বাংলা স্বরচিহ্ন (ি, া ইত্যাদি) \w নয়, মুছে যেত
    return re.sub(r"[\s।,.;:!?\-–—_'\"()\[\]]+", "", t.lower())


def _write_atomic(path, text):
    """আগে .tmp-এ লিখে পরে বদলায়, যাতে মাঝপথে ব্যর্থ হলে অর্ধেক ফাইল না থাকে।"""
    tmp = path + ".tmp"

    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)

    os.replace(tmp, path)


# ---------- ডেটা লোড ----------
try:
    with open("jobs.json", encoding="utf-8") as f:
        db = json.load(f)

except FileNotFoundError:
    raise SystemExit("ERROR: jobs.json ফাইল পাওয়া যায়নি")

except json.JSONDecodeError as e:
    raise SystemExit(
        f"ERROR: jobs.json-এ JSON সমস্যা আছে: {e}"
    )

if not isinstance(db, dict):
    raise SystemExit(
        "ERROR: jobs.json-এর মূল ডেটা অবজেক্ট হতে হবে"
    )

raw_jobs = db.get("jobs", [])

if not isinstance(raw_jobs, list):
    raise SystemExit(
        "ERROR: jobs.json-এর jobs অবশ্যই একটি তালিকা হতে হবে"
    )


jobs = []
seen_urls, seen_titles, seen_global = set(), set(), set()

for j in raw_jobs:
    if not isinstance(j, dict):
        continue

    url = str(j.get("url", "")).strip()

    if not url.lower().startswith(("http://", "https://")):
        continue

    low = url.lower()

    if any(x in low for x in JUNK_URL):
        continue

    ukey = low.split("#")[0].rstrip("/")

    if ukey in seen_urls:
        continue

    title_fixed = clean_title(j)

    if not title_fixed:
        continue

    tkey = (title_fixed, str(j.get("source", "")))

    if tkey in seen_titles:
        continue

    # একই বিজ্ঞপ্তি ভিন্ন সোর্সে এলে বাদ দেওয়া হয়। শুধু লম্বা (নির্দিষ্ট) শিরোনামে
    # প্রযোজ্য, যাতে "অফিস সহায়ক"-এর মতো ছোট সাধারণ শিরোনাম ভুলে বাদ না পড়ে।
    gkey = norm_title(title_fixed)
    use_global = len(gkey) >= 20

    if use_global and gkey in seen_global:
        continue

    seen_urls.add(ukey)
    seen_titles.add(tkey)

    if use_global:
        seen_global.add(gkey)

    j["title_bn"] = title_fixed
    jobs.append(j)


# টাইমজোন-সেফ সর্ট; ম্যালফর্মেড first_seen সবার শেষে
_MIN_DT = datetime.min.replace(tzinfo=BD)

jobs.sort(
    key=lambda j: parse(j.get("first_seen", "")) or _MIN_DT,
    reverse=True
)

updated = parse(db.get("updated", ""))

buckets = {g: [] for g in GROUPS}
cats = Counter()
today_count = 0

for j in jobs:
    dt = parse(j.get("first_seen", ""))
    g = group_of(dt)

    raw_title = str(j.get("title", ""))
    title = str(j.get("title_bn") or raw_title)
    source = str(j.get("source", "") or "অজানা সোর্স")

    kind = kind_of(j, title)
    cat = cat_of(j, title)

    cats[cat] += 1

    if g == "আজ":
        today_count += 1

    age_seconds = (
        (NOW - dt).total_seconds()
        if dt is not None
        else None
    )

    fresh = (
        age_seconds is not None
        and 0 <= age_seconds < 86400
    )

    q = escape(
        f"{title} {raw_title} {source} {cat}".lower()
    )

    deadline_html = (
        f'<span>শেষ: {escape(fmt_deadline(j.get("deadline")))}</span>'
        if j.get("deadline")
        else ""
    )

    dot_html = '<i class="dot" title="নতুন"></i>' if fresh else ""

    buckets[g].append(
        f'<a class="job {kind}" href="{escape(str(j["url"]).strip())}" '
        f'target="_blank" rel="nofollow noopener noreferrer" '
        f'data-k="{kind}" data-c="{escape(cat)}" data-q="{q}">'
        f'<span class="ttl">{escape(title)}'
        f'{dot_html}</span>'
        f'<span class="meta">'
        f'<b class="tag">{"সরকারি" if kind == "govt" else "বেসরকারি"}</b>'
        f'<span>{escape(cat)}</span>'
        f'<span>{escape(source)}</span>'
        + deadline_html +
        f'<span class="when">{ago(dt)}</span>'
        f'</span></a>'
    )


sections = []

for g in GROUPS:
    if buckets[g]:
        sections.append(
            f'<section class="grp">'
            f'<h2>{GROUP_TITLE[g]}'
            f'<small>{bn(len(buckets[g]))}টি</small></h2>'
            f'<div class="list">{"".join(buckets[g])}</div>'
            f'</section>'
        )


chips = "".join(
    f'<button class="chip" data-c="{escape(c)}">'
    f'{escape(c)} <small>{bn(n)}</small></button>'
    for c, n in cats.most_common(8)
)

upd = fmt_updated(updated) if updated else "এখনো হয়নি"


PAGE = """<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>চাকরির খবর | সরকারি ও বেসরকারি নতুন চাকরি</title>
<meta name="description" content="বাংলাদেশের সরকারি ও বেসরকারি সব নতুন চাকরির বিজ্ঞপ্তি এক জায়গায়। আজকের চাকরির খবর, শেষ তারিখ ও আবেদনের লিংক, প্রতি কয়েক ঘণ্টায় আপডেট।">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#16804c">
<link rel="canonical" href="__SITE__/">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%2316804c'/%3E%3Ctext x='32' y='45' font-size='38' text-anchor='middle' fill='white'%3E%E0%A6%9A%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="website">
<meta property="og:site_name" content="চাকরির খবর">
<meta property="og:locale" content="bn_BD">
<meta property="og:url" content="__SITE__/">
<meta property="og:title" content="চাকরির খবর | সরকারি ও বেসরকারি নতুন চাকরি">
<meta property="og:description" content="বাংলাদেশের সরকারি ও বেসরকারি নতুন চাকরির বিজ্ঞপ্তি, প্রতি কয়েক ঘণ্টায় আপডেট।">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="চাকরির খবর | সরকারি ও বেসরকারি নতুন চাকরি">
<meta name="twitter:description" content="বাংলাদেশের সরকারি ও বেসরকারি নতুন চাকরির বিজ্ঞপ্তি, প্রতি কয়েক ঘণ্টায় আপডেট।">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"চাকরির খবর","url":"__SITE__/","inLanguage":"bn-BD"}</script>
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

.topbar{padding:14px 0}
.nav{display:flex;align-items:center;justify-content:space-between;gap:12px}
.brand{display:flex;align-items:center;gap:10px;font-weight:700;font-size:1.18rem}
.logo{display:grid;place-items:center;width:42px;height:42px;border-radius:14px;color:#062313;background:linear-gradient(135deg,#77e5a0,#1b9a59);font-weight:800;font-size:22px;box-shadow:0 5px 15px #16804c22}
.navright{display:flex;align-items:center;gap:9px}
.navlink{color:var(--mut);font-size:.94rem}
.iconbtn{width:40px;height:40px;display:grid;place-items:center;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:13px;cursor:pointer}
.iconbtn svg{width:19px;height:19px}

.hero{position:relative;margin-top:9px;padding:28px 28px 24px;border-radius:26px;background:linear-gradient(120deg,#0d3b26,#145b39 70%,#17804c);color:#f2fff6;overflow:hidden;box-shadow:0 14px 34px rgba(13,59,38,.15)}
.hero:after{content:"";position:absolute;width:290px;height:290px;right:-105px;top:-130px;border-radius:50%;border:1px solid #ffffff20;box-shadow:0 0 0 35px #ffffff08,0 0 0 70px #ffffff06}
.hero-inner{position:relative;z-index:1}
.eyebrow{display:inline-flex;align-items:center;gap:7px;padding:5px 11px;border:1px solid #ffffff25;background:#ffffff12;border-radius:99px;font-size:.86rem;color:#c9f5d8}
.pulse{width:7px;height:7px;background:#77efa4;border-radius:50%;box-shadow:0 0 0 4px #77efa422}
.eyerow{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.mailbtn{display:grid;place-items:center;width:34px;height:34px;border:1px solid #ffffff25;background:#ffffff12;border-radius:50%;color:#c9f5d8}
.mailbtn svg{width:17px;height:17px}
.mailbtn:hover{background:#ffffff22}
h1{font-size:clamp(1.8rem,5vw,2.65rem);line-height:1.25;margin:13px 0 7px;font-weight:800;letter-spacing:-.4px}
.hero p{margin:0;color:#d3eadb;font-size:1rem;max-width:34em}
.statrow{display:flex;align-items:stretch;gap:10px;flex-wrap:wrap;margin-top:20px}
.statbox{padding:10px 14px;border:1px solid #ffffff22;background:#ffffff0e;border-radius:14px;min-width:135px}
.statbox strong{font-size:1.27rem;line-height:1.2;display:block;font-weight:700}
.statbox span{display:block;font-size:.83rem;color:#d0e8d8;margin-top:3px}
.updated{font-size:.82rem;color:#c5e1cf;align-self:center;padding-left:2px}

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
  <div class="eyerow"><span class="eyebrow"><i class="pulse"></i> প্রতিদিন নতুন চাকরির আপডেট</span>
  <a class="mailbtn" href="mailto:__CONTACT__" aria-label="ইমেইলে যোগাযোগ" title="যোগাযোগ করুন"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg></a></div>
  <h1>আপনার ক্যারিয়ারের <br>পরবর্তী সুযোগ খুঁজুন</h1>
  <p>বাংলাদেশের সরকারি ও বেসরকারি নিয়োগ বিজ্ঞপ্তি—সব এক জায়গায়, সহজে খুঁজুন।</p>
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
var ok=(k==="all"||j.dataset.k===k)&&(!c||j.dataset.c===c)&&(!s||j.dataset.q.indexOf(s)>-1);
j.style.display=ok?"":"none";if(ok)shown++;});
grps.forEach(function(g){
var n=0;g.querySelectorAll(".job").forEach(function(j){if(j.style.display!=="none")n++});
g.style.display=n?"":"none";
var sm=g.querySelector("small");if(sm)sm.textContent=bn(n)+"টি";});
/* ধরন + সার্চ উভয়ই চিপের সংখ্যায় ধরা হয়; সিলেক্টেড চিপ ০ হলেও দৃশ্যমান থাকে */
document.querySelectorAll("#cats .chip:not([data-c=''])").forEach(function(b){
var n=jobs.filter(function(j){return (k==="all"||j.dataset.k===k)&&(!s||j.dataset.q.indexOf(s)>-1)&&j.dataset.c===b.dataset.c}).length;
b.style.display=(n||b.dataset.c===c)?"":"none";
var sm=b.querySelector("small");if(sm)sm.textContent=bn(n);});
none.style.display=(shown||!jobs.length)?"none":"block";
mark();}
document.querySelectorAll("#kinds .chip").forEach(function(b){b.addEventListener("click",function(){k=b.dataset.k;run()})});
document.querySelectorAll("#cats .chip").forEach(function(b){b.addEventListener("click",function(){c=b.dataset.c;run()})});
document.getElementById("reset").addEventListener("click",function(){k="all";c="";q.value="";run()});
clearq.addEventListener("click",function(){q.value="";run();q.focus()});
q.addEventListener("input",run);

/* থিম টগল — চাকরি সংগ্রহ বা শিডিউল অটোমেশনে কোনো প্রভাব নেই */
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


body = (
    "".join(sections)
    if sections
    else '<p class="empty">এখনো কোনো বিজ্ঞপ্তি নেই। কিছুক্ষণ পর আবার দেখুন।</p>'
)

html = (
    PAGE.replace("__SITE__", SITE)
    .replace("__CONTACT__", CONTACT)
    .replace("__TODAY__", bn(today_count))
    .replace("__COUNT__", bn(len(jobs)))
    .replace("__UPD__", escape(upd))
    .replace("__CHIPS__", chips)
    .replace("__LIST__", body)
)

_write_atomic("index.html", html)


def write_sitemap(extra_urls=None):
    """Home URL এবং বৈধ অতিরিক্ত URL দিয়ে sitemap.xml তৈরি করে।"""

    lastmod = (updated or NOW).strftime("%Y-%m-%d")
    site_host = urlsplit(SITE).netloc.lower()

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f"<url><loc>{escape(SITE + '/')}</loc>"
        f"<lastmod>{lastmod}</lastmod></url>",
    ]

    seen = {SITE.rstrip("/") + "/"}

    if isinstance(extra_urls, (list, tuple, set)):
        for u in extra_urls:
            raw = str(u).strip()

            if not raw:
                continue

            if raw.startswith("/") and not raw.startswith("//"):
                loc = SITE.rstrip("/") + raw

            elif raw.lower().startswith(("http://", "https://")):
                loc = raw

            else:
                continue

            parsed = urlsplit(loc)

            if parsed.scheme not in ("http", "https"):
                continue

            if parsed.netloc.lower() != site_host:
                continue

            if loc in seen:
                continue

            seen.add(loc)

            lines.append(
                f"<url><loc>{escape(loc)}</loc>"
                f"<lastmod>{lastmod}</lastmod></url>"
            )

    lines.append("</urlset>")

    _write_atomic("sitemap.xml", "\n".join(lines) + "\n")


write_sitemap()

_write_atomic(
    "robots.txt",
    f"User-agent: *\n"
    f"Allow: /\n\n"
    f"Sitemap: {SITE}/sitemap.xml\n"
)

print(
    f"index.html, sitemap.xml ও robots.txt তৈরি ({len(jobs)}টি জব)"
)


# extra_pages.py এই স্ক্রিপ্টের গ্লোবাল ভ্যারিয়েবল (jobs, SITE, bn, NOW ইত্যাদি) ব্যবহার করে,
# তাই exec পদ্ধতি ইচ্ছা করেই রাখা হয়েছে — import করলে ওই ফাইল ভেঙে যেত।
try:
    with open("extra_pages.py", encoding="utf-8") as _f:
        _src = _f.read()

    exec(compile(_src, "extra_pages.py", "exec"), globals())

    _extra = globals().get("EXTRA_URLS")

    if _extra:
        try:
            write_sitemap(_extra)
            print(
                f"sitemap.xml extended with {len(_extra)} extra URL(s)"
            )

        except Exception as e:
            print("sitemap extend ব্যর্থ:", e)

except FileNotFoundError:
    print(
        "extra_pages.py পাওয়া যায়নি, শুধু হোমপেজ তৈরি হয়েছে"
    )

except Exception as e:
    import traceback
    traceback.print_exc()
    print("extra_pages ব্যর্থ:", e)

#!/usr/bin/env python3
"""চাকরির খবর - স্ক্র্যাপার
বাংলাদেশের সরকারি/বেসরকারি সাইট থেকে নতুন বিজ্ঞপ্তি সংগ্রহ করে jobs.json আপডেট করে।
- Gemini (GEMINI_API_KEY) থাকলে: ননজব লিংক বাদ + বাংলা শিরোনাম + ক্যাটাগরি
- Telegram (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) থাকলে: নতুন জবের নোটিফিকেশন
"""
import os, re, json, time, hashlib, sys
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BD_TZ = timezone(timedelta(hours=6))
KEEP_DAYS = 30
MAX_PER_SOURCE = 80
MAX_GEMINI_CALLS = 8
GEMINI_MODELS = [os.getenv("GEMINI_MODEL") or "gemini-3.8-flash",
                 "gemini-3.7-flash", "gemini-flash-latest"]
GEMINI_DOWN = False
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "bn,en;q=0.8",
}

# ---------------------------------------------------------------- সোর্স তালিকা
# নতুন সাইট যোগ করতে শুধু একটা লাইন যোগ করুন।
SOURCES = [
    # ---- সরকারি ----
    {"name": "Teletalk সরকারি চাকরি", "type": "govt", "url": "https://alljobs.teletalk.com.bd/"},
    {"name": "BPSC", "type": "govt", "url": "https://www.bpsc.gov.bd/site/view/notices"},
    {"name": "Bangladesh Bank", "type": "govt", "url": "https://erecruitment.bb.org.bd/"},
    {"name": "NTRCA (শিক্ষক নিয়োগ)", "type": "govt", "url": "https://ntrca.gov.bd/"},
    {"name": "প্রাথমিক শিক্ষা অধিদপ্তর", "type": "govt", "url": "https://dpe.gov.bd/site/view/notices"},
    {"name": "মাধ্যমিক ও উচ্চশিক্ষা", "type": "govt", "url": "https://dshe.gov.bd/site/view/notices"},
    {"name": "জনপ্রশাসন মন্ত্রণালয়", "type": "govt", "url": "https://mopa.gov.bd/site/view/notices"},
    {"name": "স্বাস্থ্য অধিদপ্তর (DGHS)", "type": "govt", "url": "https://dghs.gov.bd/site/view/notices"},
    {"name": "মন্ত্রিপরিষদ বিভাগ", "type": "govt", "url": "https://cabinet.gov.bd/site/view/notices"},
    # ---- বেসরকারি ----
    {"name": "Bdjobs", "type": "private", "js": True, "url": "https://www.bdjobs.com/"},
    {"name": "Chakri.com", "type": "private", "js": True, "url": "https://www.chakri.com/"},
    {"name": "Skill.Jobs", "type": "private", "js": True, "url": "https://www.skill.jobs/"},
    {"name": "Shomvob", "type": "private", "js": True, "url": "https://shomvob.co/"},
]

JOB_RE = re.compile(
    r"নিয়োগ|বিজ্ঞপ্তি|চাকরি|চাকুরি|পদে|লোকবল|আবেদন|সার্কুলার|"
    r"recruit|circular|vacanc|career|job|hiring|position|apply|opening|"
    r"manager|officer|engineer|executive|assistant|teacher|lecturer",
    re.I,
)
NAV_RE = re.compile(
    r"login|log in|sign ?up|sign ?in|register|about|contact|privacy|terms|cookie|"
    r"facebook|twitter|youtube|linkedin|instagram|whatsapp|\bfaq\b|\bhelp\b|\bcv\b|"
    r"resume|employer|post a job|blog|advert|সাইন|লগইন|রেজিস্ট|যোগাযোগ|আমাদের সম্পর্কে|গোপনীয়তা",
    re.I,
)


def now():
    return datetime.now(BD_TZ)


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def fetch(url):
    err = None
    for _ in range(2):
        try:
            try:
                r = requests.get(url, headers=HEADERS, timeout=(8, 15))
            except requests.exceptions.SSLError:
                r = requests.get(url, headers=HEADERS, timeout=(8, 15), verify=False)
            r.raise_for_status()
            if not r.encoding or r.encoding.lower() == "iso-8859-1":
                r.encoding = r.apparent_encoding
            return r.text
        except Exception as e:  # noqa
            err = e
            time.sleep(1.5)
    raise err


def scrape_source(src):
    return parse_html(src, fetch(src["url"]))


def parse_html(src, html):
    soup = BeautifulSoup(html, "lxml")
    found = {}
    base = src["url"].rstrip("/")
    for a in soup.find_all("a", href=True):
        text = " ".join(a.get_text(" ", strip=True).split())
        if not (8 <= len(text) <= 220):
            continue
        href = urljoin(src["url"], a["href"].strip())
        if not href.startswith("http") or href.rstrip("/") == base:
            continue
        path = urlparse(href).path
        if NAV_RE.search(text) or NAV_RE.search(path):
            continue
        if not (JOB_RE.search(text) or JOB_RE.search(href)):
            continue
        jid = hashlib.md5(href.encode()).hexdigest()[:12]
        found.setdefault(jid, {
            "id": jid, "title": text, "url": href,
            "source": src["name"], "type": src["type"],
        })
        if len(found) >= MAX_PER_SOURCE:
            break
    return list(found.values())


def browser_scrape(sources, budget=200):
    """JavaScript-নির্ভর সাইটের জন্য আসল ব্রাউজার (Playwright)।"""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:  # noqa
        print(f"[browser] Playwright নেই: {e}")
        return [], 0
    out, ok, start = [], 0, time.time()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
            ctx = browser.new_context(user_agent=HEADERS["User-Agent"], locale="bn-BD",
                                      viewport={"width": 1280, "height": 900})
            for src in sources:
                if time.time() - start > budget:
                    print(f"[browser] সময় শেষ, বাদ: {src['name']}")
                    continue
                page = ctx.new_page()
                try:
                    page.goto(src["url"], wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(4000)
                    for _ in range(3):
                        page.mouse.wheel(0, 2500)
                        page.wait_for_timeout(1000)
                    items = parse_html(src, page.content())
                    ok += 1
                    print(f"[ok-browser] {src['name']}: {len(items)}টি লিংক")
                    out.extend(items)
                except Exception as e:  # noqa
                    print(f"[fail-browser] {src['name']}: {type(e).__name__}: {str(e)[:120]}")
                finally:
                    page.close()
            browser.close()
    except Exception as e:  # noqa
        print(f"[browser] চালু হয়নি: {str(e)[:150]}")
    return out, ok


def gemini_classify(items):
    """রিটার্ন: {id: {"is_job":bool,"title_bn":str,"category":str}}"""
    global GEMINI_DOWN
    default = {i["id"]: {"is_job": True, "title_bn": "", "category": "অন্যান্য"} for i in items}
    key = os.getenv("GEMINI_API_KEY")
    if not key or not items or GEMINI_DOWN:
        return default
    result = dict(default)
    models = list(GEMINI_MODELS)
    for n, i in enumerate(range(0, len(items), 30)):
        if n >= MAX_GEMINI_CALLS:
            break
        chunk = items[i:i + 30]
        lines = "\n".join(f'{c["id"]} | {c["source"]} | {c["title"]}' for c in chunk)
        prompt = (
            "নিচে বাংলাদেশের চাকরির সাইট থেকে পাওয়া লিংকের তালিকা (id | সোর্স | শিরোনাম)।\n"
            "প্রতিটির জন্য JSON array দাও: "
            '[{"id":"...","is_job":true/false,"title_bn":"সংক্ষিপ্ত পরিষ্কার বাংলা শিরোনাম","category":"..."}]\n'
            "is_job=true শুধু আসল নিয়োগ বিজ্ঞপ্তি/চাকরির পোস্ট হলে; মেনু, বিজ্ঞাপন, প্রশিক্ষণ, "
            "রেজাল্ট, সাধারণ খবর হলে false।\n"
            'category হবে এর একটি: "সরকারি","ব্যাংক","শিক্ষা","এনজিও","আইটি","প্রকৌশল","স্বাস্থ্য","অন্যান্য"।\n'
            "শুধু JSON দাও।\n\n" + lines
        )
        text = None
        for m in list(models):
            for attempt in range(2):
                try:
                    r = requests.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                        headers={"x-goog-api-key": key}, timeout=45,
                        json={"contents": [{"parts": [{"text": prompt}]}],
                              "generationConfig": {"responseMimeType": "application/json"}},
                    )
                except requests.RequestException as e:
                    print(f"[gemini] {m} -> {type(e).__name__}")
                    break
                if r.ok:
                    try:
                        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    except Exception:  # noqa
                        text = None
                    break
                try:
                    detail = r.json().get("error", {}).get("message", "")[:220].replace("\n", " ")
                except Exception:  # noqa
                    detail = r.text[:220].replace("\n", " ")
                print(f"[gemini] {m} -> HTTP {r.status_code} {detail}")
                if r.status_code == 404:
                    models.remove(m)
                    break
                if r.status_code in (429, 500, 502, 503, 504):
                    time.sleep(4)
                    continue
                break
            if text:
                models = [m]
                print(f"[gemini] মডেল: {m}")
                break
        if not text:
            print("[gemini] এখন কাজ করছে না, এই রানে বাকিটা ফিল্টার ছাড়াই চলবে")
            GEMINI_DOWN = True
            break
        try:
            text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
            for row in json.loads(text):
                if row.get("id") in result:
                    result[row["id"]] = {
                        "is_job": bool(row.get("is_job", True)),
                        "title_bn": str(row.get("title_bn", ""))[:200],
                        "category": str(row.get("category", "অন্যান্য")),
                    }
        except Exception as e:  # noqa
            print(f"[gemini] উত্তর পড়া যায়নি: {e}")
    return result


def notify_telegram(new_jobs):
    tok, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (tok and chat and new_jobs):
        return
    lines = [f"🆕 {len(new_jobs)}টি নতুন চাকরির বিজ্ঞপ্তি"]
    for j in new_jobs[:15]:
        lines.append(f"\n• {j.get('title_bn') or j['title']}\n  [{j['source']}] {j['url']}")
    try:
        requests.post(
            f"https://api.telegram.org/bot{tok}/sendMessage",
            data={"chat_id": chat, "text": "\n".join(lines)[:4000], "disable_web_page_preview": "true"},
            timeout=20,
        )
    except Exception as e:  # noqa
        print(f"[telegram] ব্যর্থ: {e}")


def main():
    db = load_json("jobs.json", {})
    jobs = db.get("jobs", []) if isinstance(db, dict) else []
    skipped = load_json("skipped.json", [])
    if not isinstance(skipped, list):
        skipped = []
    known = {j["id"] for j in jobs} | {s["id"] for s in skipped if isinstance(s, dict)}

    collected, ok = [], 0
    retry = [s for s in SOURCES if s.get("js")]
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(scrape_source, s): s for s in SOURCES if not s.get("js")}
        try:
            for f in as_completed(futs, timeout=240):
                s = futs[f]
                try:
                    items = f.result()
                    if not items:
                        print(f"[empty] {s['name']}: ০টি লিংক, ব্রাউজারে আবার চেষ্টা হবে")
                        retry.append(s)
                        continue
                    ok += 1
                    print(f"[ok]   {s['name']}: {len(items)}টি লিংক")
                    collected.extend(items)
                except Exception as e:  # noqa
                    print(f"[fail] {s['name']}: {type(e).__name__}: {str(e)[:120]} -> ব্রাউজারে আবার চেষ্টা")
                    retry.append(s)
        except Exception:
            print("[warn] কিছু সোর্স সময়মতো শেষ হয়নি, যা পাওয়া গেছে তা নিয়েই এগোচ্ছি")

    if retry:
        got, okb = browser_scrape(retry)
        collected.extend(got)
        ok += okb

    new_items = [i for i in {c["id"]: c for c in collected}.values() if i["id"] not in known]
    print(f"নতুন লিংক: {len(new_items)}")

    info = gemini_classify(new_items)
    added = []
    ts = now().isoformat(timespec="seconds")
    for it in new_items:
        meta = info.get(it["id"], {})
        if not meta.get("is_job", True):
            skipped.append({"id": it["id"], "title": it["title"]})
            continue
        it.update({
            "title_bn": meta.get("title_bn", ""),
            "category": meta.get("category") or ("সরকারি" if it["type"] == "govt" else "অন্যান্য"),
            "first_seen": ts,
        })
        added.append(it)

    jobs = added + jobs

    # আগে Gemini ছাড়া যোগ হওয়া জবগুলো আবার ফিল্টার/বাংলা শিরোনাম
    pending = [j for j in jobs if not j.get("title_bn")][:120]
    if pending and os.getenv("GEMINI_API_KEY") and not GEMINI_DOWN:
        old = gemini_classify(pending)
        drop = set()
        for j in pending:
            meta = old.get(j["id"], {})
            if not meta.get("is_job", True):
                drop.add(j["id"])
                skipped.append({"id": j["id"], "title": j["title"]})
            elif meta.get("title_bn"):
                j["title_bn"] = meta["title_bn"]
                j["category"] = meta.get("category") or j.get("category", "অন্যান্য")
        jobs = [j for j in jobs if j["id"] not in drop]
    cutoff = now() - timedelta(days=KEEP_DAYS)
    jobs = [j for j in jobs if datetime.fromisoformat(j["first_seen"]) >= cutoff]

    save_json("jobs.json", {"updated": ts, "count": len(jobs), "jobs": jobs})
    save_json("skipped.json", skipped[-3000:])
    print(f"যোগ হয়েছে: {len(added)}, মোট: {len(jobs)}, সফল সোর্স: {ok}/{len(SOURCES)}")

    if known:  # প্রথম রানে স্প্যাম এড়াতে
        notify_telegram(added)
    if ok == 0:
        print("কোনো সোর্সই কাজ করেনি!")
        sys.exit(1)


if __name__ == "__main__":
    main()

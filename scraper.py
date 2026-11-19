# প্রথম আলোর চাকরি পেজ থেকে শুধু শিরোনাম, শেষ তারিখ ও মূল লিংক নেয়।
import json, re, time, urllib.request
from datetime import date
from html.parser import HTMLParser
from urllib.parse import urljoin

SOURCES = [
    {"name": "প্রথম আলো", "list_url": "https://www.prothomalo.com/chakri/employment",
     "link_re": r"^/chakri/employment/[a-z0-9]+$"},
    # নতুন সোর্স যোগ করতে এখানে আরেকটা {...} বসান
]
MAX_NEW = 15
MONTHS = {"জানুয়ারি":1,"ফেব্রুয়ারি":2,"মার্চ":3,"এপ্রিল":4,"মে":5,"জুন":6,"জুলাই":7,
          "আগস্ট":8,"সেপ্টেম্বর":9,"অক্টোবর":10,"নভেম্বর":11,"ডিসেম্বর":12}
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (chakrirkhobor bot)"})
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

def main():
    try: jobs = json.load(open("jobs.json", encoding="utf-8"))
    except Exception: jobs = []
    jobs = [j for j in jobs if not j.get("demo")]
    seen = {j["link"] for j in jobs}
    today = date.today(); added = 0
    for src in SOURCES:
        try:
            p = Links(); p.feed(fetch(src["list_url"]))
        except Exception as e:
            print("লিস্ট পেজ আনা যায়নি:", src["name"], e); continue
        cands = []
        for href, text in p.out:
            path = href.split("?")[0]
            if re.match(src["link_re"], path.replace("https://www.prothomalo.com", "")) and len(text) > 12:
                url = urljoin(src["list_url"], path)
                if url not in seen and url not in [c[0] for c in cands]: cands.append((url, text))
        print(src["name"], "- নতুন লিংক:", len(cands))
        for url, title in cands[:MAX_NEW]:
            try:
                dl = find_deadline(re.sub(r"<[^>]+>", " ", fetch(url)))
            except Exception as e:
                print("স্কিপ:", url, e); continue
            time.sleep(1)
            if not dl or dl < today: continue
            jobs.append({"title": title, "org": "সূত্র: " + src["name"], "cat": guess_cat(title),
                         "posts": guess_posts(title), "grade": "", "deadline": dl.isoformat(),
                         "link": url, "source": src["name"]})
            added += 1
    jobs = [j for j in jobs if j["deadline"] >= today.isoformat()]
    jobs.sort(key=lambda j: j["deadline"])
    json.dump(jobs[:200], open("jobs.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("যোগ হয়েছে:", added, "মোট:", len(jobs))

if __name__ == "__main__":
    main()

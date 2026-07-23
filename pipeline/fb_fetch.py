#!/usr/bin/env python3
"""Portfolio-A — pick finished-project photos from FB page posts, download, register in DB."""
import json, os, re, urllib.request
from db import connect

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "data", "photos", "_fb")
CANDIDATES = os.path.join(HERE, "data", "fb_candidates.json")

# caption keywords that signal a FINISHED / beauty / handover post
FINISH_HINTS = [
    "အပ်နှံ", "ပြီးတော့မယ်", "လက်စသတ်", "white cottage", "နန်းရှေ့", "classic",
    "တံတားဦး", "ရဲမွန်တောင်", "အောင်သာယာ", "ပြင်ဦးလွင်", "ကျောက်ဆည်", "အလှလေး",
    "အိမ်လှ", "အလှဆုံး", "လေးထပ်", "နှစ်ထပ်",
]
# captions that are site-progress / educational / promo, NOT finished showcase
SKIP_HINTS = ["ဆိုက်လေး", "site", "Site", "မြေဝယ်", "အက်ကြောင်း", "Stiffener", "form လေးပိတ်",
              "ဗုဒ္ဓဘာသာ", "မင်္ဂလာတိုင်ထူ", "မင်္ဂလာရှိတဲ့", "99.99", "ဖုန်းရွှေ", "ငွေစျေး",
              "Home Tour is coming", "မကြာခင်", "Good Morning", "Today", "သိန်း (၁၇၂၀)",
              "ကမ္မဝါ", "နွေရာသီ", "ဒေါ်တော", "မုန့်တီ", "လမ်းကြုံရင်", "ကိုယ်ဆောက်တဲ့အိမ်"]

def pick(cands, n=30):
    out, seen_first = [], set()
    for c in cands:
        first = c["msg"].splitlines()[0].strip()
        if any(k in c["msg"] for k in SKIP_HINTS):
            continue
        if not any(k in c["msg"] for k in FINISH_HINTS):
            continue
        key = first[:12]
        if key in seen_first:
            continue
        seen_first.add(key)
        out.append(c)
        if len(out) >= n:
            break
    return out

def main():
    os.makedirs(OUT, exist_ok=True)
    cands = json.load(open(CANDIDATES, encoding="utf-8"))
    chosen = pick(cands)
    print(f"chosen {len(chosen)} finished-project posts\n")
    con = connect()
    for c in chosen:
        title = c["msg"].splitlines()[0].strip()[:90]
        img_url = c["imgs"][0]
        fname = f"fb_{c['id'].replace('_', '-')}.jpg"
        path = os.path.join(OUT, fname)
        if not os.path.exists(path):
            try:
                urllib.request.urlretrieve(img_url, path)
            except Exception as e:
                print(f"  DL FAIL {c['id']}: {e}")
                continue
        size = os.path.getsize(path)
        if size < 15000:  # tiny/broken image
            os.remove(path); print(f"  skip tiny {fname} ({size}B)"); continue
        con.execute(
            "INSERT OR REPLACE INTO portfolio(category,title,subtitle,path,source,created) "
            "VALUES('finished',?,?,?,'facebook',?)",
            (title, c["date"], path, c["date"]))
        con.commit()
        print(f"  ✓ {c['date']} | {size//1024:4d}KB | {title[:60]}")
    n = con.execute("SELECT COUNT(*) c FROM portfolio WHERE category='finished'").fetchone()["c"]
    print(f"\nDB finished items: {n}")

main()

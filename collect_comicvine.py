"""Collects every US Marvel issue Comic Vine lists for each character, into raw.json.

For each character: walk its "Comics" pages (every series it appears in), keep series
published by Marvel (US), then read the issues the character appears in for each one.
Run:  py collect_comicvine.py raw.json   (then: py build_data.py raw.json)
Takes several minutes; it's gentle on Comic Vine (4 requests at a time).
"""
import datetime
import html
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

CV = "https://comicvine.gamespot.com"
CHARACTERS = {"jubilee": "/jubilee/4005-4562/", "venom": "/venom/4005-1486/"}
SKIP = re.compile(r"previews|handbook|marvel age|catalog|year in review|wizard|index|encyclopedia|sketchbook", re.I)
UA = {"User-Agent": "LongboxFinder/1.0 (personal comic catalog)"}


def get(path):
    for attempt in range(4):
        try:
            req = urllib.request.Request(CV + path, headers=UA)
            return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:
            pass
        time.sleep(2 * (attempt + 1))
    return None


def text(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s or "")).replace("\xa0", " ").strip()


LIST_ITEM = re.compile(r'<li>\s*<a href="(/[^"]+/4050-\d+/)">\s*(?:<div[^>]*>.*?</div>\s*)?<p class="issue-number">(.*?)</p>\s*(?:</a>\s*)?'
                       r'<a href="([^"]+/object-appearances/[^"]+)"[^>]*>\s*(\d+) appearance', re.S)
ISSUE_ITEM = re.compile(r'<li>\s*<a href="/[^"]+/4000-\d+/">(.*?)</a>\s*</li>', re.S)


def series_list(base):
    first = get(base + "issues-cover/")
    last = max([1] + [int(n) for n in re.findall(r"issues-cover/\?page=(\d+)", first)])
    pages = [first] + [get(base + "issues-cover/?page=%d" % p) for p in range(2, last + 1)]
    out = []
    for h in pages:
        for vol, name, app, count in LIST_ITEM.findall(h or ""):
            out.append({"vol": vol, "name": text(name), "app": app, "count": int(count)})
    return out


def volume(item):
    if SKIP.search(item["name"]):
        return None
    h = get(item["vol"])
    if not h:
        return None
    m = re.search(r'Published by <a href="/marvel/4010-31/">Marvel</a>\.\s*Started in (\d{4})', h)
    if not m:
        return None
    t = text(h)
    t = re.sub(r"\s+", " ", t)
    deck = re.search(r"View full history (.{0,180}?) (?:Collected Editions|Expand full wiki|\d+ issues in this volume)", t)
    deck = deck.group(1).strip() if deck else ""
    if deck == "No description":
        deck = ""
    issues = []
    for p in range(1, 30):
        ah = get(item["app"] + ("?page=%d" % p if p > 1 else ""))
        if not ah:
            break
        for block in ISSUE_ITEM.findall(ah):
            num = re.search(r'<p class="issue-number">(.*?)</p>', block, re.S)
            if not num:
                continue
            name = re.search(r'<p class="issue-name">(.*?)</p>', block, re.S)
            date = re.search(r'<p class="issue-date">(.*?)</p>', block, re.S)
            n = re.sub(r"^.*?#\s*", "", text(num.group(1)))
            issues.append([n, text(date.group(1)) if date else "", text(name.group(1)) if name else ""])
        if "?page=%d" % (p + 1) not in ah:
            break
    return {"name": item["name"], "year": int(m.group(1)), "cv": item["vol"], "deck": deck, "count": item["count"], "issues": issues}


def main(dest):
    result = {"collected": datetime.date.today().isoformat(), "out": {}}
    for key, base in CHARACTERS.items():
        items = series_list(base)
        print(f"{key}: {len(items)} series on Comic Vine", flush=True)
        kept = []
        with ThreadPoolExecutor(4) as pool:
            for i, v in enumerate(pool.map(volume, items), 1):
                if v:
                    kept.append(v)
                if i % 100 == 0:
                    print(f"  {key}: checked {i}/{len(items)}, kept {len(kept)}", flush=True)
        result["out"][key] = kept
        print(f"{key}: kept {len(kept)} US Marvel series, {sum(len(v['issues']) for v in kept)} issues", flush=True)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
    print("done", flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "raw.json")

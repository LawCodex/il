#!/usr/bin/env python3
"""Fetch the Open Law Book (ספר החוקים הפתוח) from Hebrew Wikisource via the MediaWiki API.

Lists all pages of the bot-maintained category "קטגוריה:בוט חוקים" (every page of the
Open Law Book), then downloads the current wikitext of each page in batches of 50 into
_raw/il/pages/<pageid>.json (cached; re-runs only refetch pages whose revision changed).

Usage: python il_fetch.py [RAW_DIR]
"""
import json, os, sys, time
import requests

API = "https://he.wikisource.org/w/api.php"
UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
CATS = ["קטגוריה:בוט חוקים", "קטגוריה:חוקי יסוד"]
RAW = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "_raw", "il")
PAGES = os.path.join(RAW, "pages")
os.makedirs(PAGES, exist_ok=True)

S = requests.Session()
S.headers["User-Agent"] = UA


def api(params):
    params = dict(params, format="json", formatversion="2", maxlag="5")
    for attempt in range(8):
        try:
            r = S.get(API, params=params, timeout=60)
            if r.status_code == 200:
                d = r.json()
                if "error" in d:
                    if d["error"].get("code") == "maxlag":
                        time.sleep(5 * (attempt + 1)); continue
                    raise RuntimeError(d["error"])
                return d
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(int(r.headers.get("Retry-After", 5 * (attempt + 1)))); continue
            r.raise_for_status()
        except requests.RequestException as e:
            print("retry", e, file=sys.stderr); time.sleep(5 * (attempt + 1))
    raise RuntimeError("failed: %r" % params)


def list_members():
    pages = {}
    for cat in CATS:
        p = {"action": "query", "list": "categorymembers", "cmtitle": cat,
             "cmlimit": "500", "cmnamespace": "0", "cmprop": "ids|title"}
        while True:
            d = api(p)
            for m in d["query"]["categorymembers"]:
                pages[m["pageid"]] = m["title"]
            if "continue" not in d:
                break
            p.update(d["continue"]); time.sleep(1)
    return pages


def main():
    members = list_members()
    print("members:", len(members))
    json.dump(members, open(os.path.join(RAW, "members.json"), "w"), ensure_ascii=False)
    # current revision ids, to skip unchanged cached pages
    ids = sorted(members)
    todo = []
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        d = api({"action": "query", "pageids": "|".join(map(str, chunk)), "prop": "info"})
        for pg in d["query"]["pages"]:
            fn = os.path.join(PAGES, "%d.json" % pg["pageid"])
            if os.path.exists(fn):
                try:
                    if json.load(open(fn))["revisions"][0]["revid"] == pg.get("lastrevid"):
                        continue
                except Exception:
                    pass
            todo.append(pg["pageid"])
        time.sleep(0.5)
    print("to fetch:", len(todo))
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        d = api({"action": "query", "pageids": "|".join(map(str, chunk)),
                 "prop": "revisions|categories", "rvprop": "ids|timestamp|content",
                 "rvslots": "main", "cllimit": "max"})
        for pg in d["query"]["pages"]:
            if "revisions" not in pg:
                continue
            with open(os.path.join(PAGES, "%d.json" % pg["pageid"]), "w") as f:
                json.dump(pg, f, ensure_ascii=False)
        print("fetched", i + len(chunk), "/", len(todo), flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()

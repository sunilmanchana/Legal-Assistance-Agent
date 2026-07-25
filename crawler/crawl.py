"""
Stage 1 — Crawler (proposal §7.1 crawl etiquette implemented in code).

- robots.txt parsed and honored BEFORE any page is fetched
- <= 1 request/second (enforced globally)
- Descriptive User-Agent containing the team contact email
- Raw bytes saved to disk with URL, timestamp, and content hash BEFORE parsing
- Login-walled / case-status / directory pages excluded via deny patterns
- Deduplication by content hash

Usage:
    python crawler/crawl.py --sources all --out data/raw
    python crawler/crawl.py --sources USCISPM CFR --out data/raw
"""
import argparse
import hashlib
import json
import re
import time
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urldefrag, urlparse

import requests
from bs4 import BeautifulSoup

from sources import SOURCES, GLOBAL_DENY

USER_AGENT = (
    "MSAI633-ResidencyProject-LegalAssistanceAgent/1.0 "
    "(student research crawler; contact: mbteja999@gmail.com)"
)
RATE_LIMIT_SECONDS = 1.0

_last_request_time = [0.0]
_robots_cache = {}


def polite_wait():
    elapsed = time.time() - _last_request_time[0]
    if elapsed < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - elapsed)
    _last_request_time[0] = time.time()


def robots_allows(url: str) -> bool:
    origin = "{0.scheme}://{0.netloc}".format(urlparse(url))
    if origin not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(origin + "/robots.txt")
        try:
            polite_wait()
            rp.read()
        except Exception:
            rp = None  # robots unreachable -> be conservative, allow but log
        _robots_cache[origin] = rp
    rp = _robots_cache[origin]
    return True if rp is None else rp.can_fetch(USER_AGENT, url)


def url_allowed(url: str, cfg) -> bool:
    if any(re.search(p, url, re.I) for p in GLOBAL_DENY):
        return False
    if any(re.search(p, url, re.I) for p in cfg.get("deny", [])):
        return False
    return any(re.search(p, url) for p in cfg["allow"])


def fetch(url: str):
    polite_wait()
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp


def save_raw(out_dir: Path, source: str, url: str, resp, visa_hint):
    raw = resp.content
    h = hashlib.sha256(raw).hexdigest()
    ctype = resp.headers.get("Content-Type", "")
    ext = ".pdf" if ("pdf" in ctype or url.lower().endswith(".pdf")) else ".html"
    fname = f"{source}_{h[:16]}{ext}"
    (out_dir / fname).write_bytes(raw)
    record = {
        "source": source,
        "url": url,
        "file": fname,
        "sha256": h,
        "content_type": ctype,
        "bytes": len(raw),
        "visa_hint": visa_hint,
        "crawl_ts": datetime.now(timezone.utc).isoformat(),
    }
    with open(out_dir / "manifest.jsonl", "a") as f:
        f.write(json.dumps(record) + "\n")
    return h, ext


def extract_links(base_url: str, html: bytes):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        url = urldefrag(urljoin(base_url, a["href"]))[0]
        if url.startswith("http"):
            links.add(url)
    return links


def crawl_source(name: str, cfg, out_dir: Path, seen_hashes: set, log):
    queue = list(cfg["seeds"])
    visited, saved = set(), 0
    while queue and saved < cfg["max_pages"]:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        if not url_allowed(url, cfg):
            continue
        if not robots_allows(url):
            log(f"  ROBOTS-DISALLOWED {url}")
            continue
        try:
            resp = fetch(url)
        except Exception as e:
            log(f"  FETCH-FAIL {url} ({e})")
            continue
        h, ext = save_raw(out_dir, name, url, resp, cfg["visa_hint"])
        if h in seen_hashes:
            log(f"  DUP {url}")
            continue
        seen_hashes.add(h)
        saved += 1
        log(f"  [{saved}/{cfg['max_pages']}] {url}")
        if ext == ".html":
            for link in extract_links(url, resp.content):
                if link not in visited and url_allowed(link, cfg):
                    queue.append(link)
    return saved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", nargs="+", default=["all"])
    ap.add_argument("--out", default="data/raw")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    names = list(SOURCES) if args.sources == ["all"] else args.sources

    seen_hashes = set()
    total = 0
    for name in names:
        print(f"== {name} ==")
        total += crawl_source(name, SOURCES[name], out_dir, seen_hashes, print)
    print(f"\nDone: {total} unique pages saved to {out_dir}/ "
          f"(manifest: {out_dir}/manifest.jsonl)")


if __name__ == "__main__":
    main()

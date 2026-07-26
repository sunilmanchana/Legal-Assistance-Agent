"""
add_new_pages.py (v2, corrected) — Fetches specific new pages and adds them
to your existing data/raw/ folder, using the EXACT manifest field names
crawler/extract.py requires: file, url, source, crawl_ts.

Run from your project root:
    python3 add_new_pages.py
"""
import hashlib
import json
import time
from pathlib import Path
import requests

USER_AGENT = "MSAI633-ResidencyProject-LegalAssistanceAgent/1.0 (student research crawler)"

NEW_URLS = [
    ("SEVP", "https://studyinthestates.dhs.gov/elimination-of-duration-of-status-quick-facts"),
    ("SEVP", "https://studyinthestates.dhs.gov/final-rule-establishing-a-fixed-time-period-of-admission-and-an-extension-of-stay-procedure-faq"),
]

raw_dir = Path("data/raw")
raw_dir.mkdir(parents=True, exist_ok=True)
manifest_path = raw_dir / "manifest.jsonl"

for source, url in NEW_URLS:
    print(f"Fetching: {url}")
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    content = resp.content
    content_hash = hashlib.sha256(content).hexdigest()[:16]
    fname = f"{source}_{content_hash}.html"
    fpath = raw_dir / fname
    fpath.write_bytes(content)

    with open(manifest_path, "a") as f:
        f.write(json.dumps({
            "url": url,
            "source": source,
            "file": fname,
            "crawl_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sha256": hashlib.sha256(content).hexdigest(),
        }) + "\n")

    print(f"  -> saved as {fname}")
    time.sleep(1)

print("\nDone. Now re-run your normal pipeline to pick these up:")
print("  python3 crawler/extract.py --raw data/raw --out data/extracted")
print("  python3 crawler/chunk.py --extracted data/extracted --out data/chunks")
print("  python3 crawler/embed_index.py --chunks data/chunks --db data/vectordb")

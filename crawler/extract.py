"""
Stage 2 — Extraction.

Reads the raw pages saved by crawler/crawl.py (data/raw/manifest.jsonl +
the .html/.pdf files) and produces one normalized JSON per document in
data/extracted/, containing clean text, tables kept intact, and metadata:
doc_id, source_url, title, heading_path, page_type, effective_date (if
discoverable), crawl_timestamp.

This is the ONLY place that touches raw HTML/PDF parsing. Stage 3
(chunking) reads exclusively from data/extracted/, so re-chunking never
requires re-crawling (proposal Stage 6 requirement).

Usage:
    python crawler/extract.py --raw data/raw --out data/extracted
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import pdfplumber
from bs4 import BeautifulSoup, Comment

NOISE_TAGS = ["nav", "header", "footer", "script", "style", "noscript", "form", "aside"]
NOISE_SELECTORS = [
    ".breadcrumb", ".site-header", ".site-footer", "#block-uscis-mainnavigation",
    ".skip-link", ".usa-banner", "[role=navigation]", "[role=banner]",
    "[role=contentinfo]",
]
DATE_RE = re.compile(
    r"(?:Effective(?: Date)?|As of|Last (?:Reviewed|Updated))\s*[:\-]?\s*"
    r"([A-Z][a-z]+ \d{1,2},? \d{4}|\d{1,2}/\d{1,2}/\d{2,4})",
    re.IGNORECASE,
)


def clean_html(raw: bytes):
    soup = BeautifulSoup(raw, "html.parser")

    for tag in soup.find_all(NOISE_TAGS):
        tag.decompose()
    for sel in NOISE_SELECTORS:
        for tag in soup.select(sel):
            tag.decompose()
    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()

    title = (soup.title.string.strip() if soup.title and soup.title.string else "") or ""
    if not title:
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else ""

    # heading path: sequence of h1/h2 text, gives structure-aware chunking (Stage 3) something to key on
    headings = [h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2"]) if h.get_text(strip=True)]

    # pull tables out as intact markdown tables, replace with a placeholder in flow
    tables = []
    for i, table in enumerate(soup.find_all("table")):
        rows = []
        for tr in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
        if rows:
            md = "\n".join("| " + " | ".join(r) + " |" for r in rows)
            tables.append(md)
            placeholder = soup.new_string(f"\n[TABLE_{i}]\n")
            table.replace_with(placeholder)

    main = soup.find("main") or soup.find(attrs={"role": "main"}) or soup.body or soup
    text = main.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)

    m = DATE_RE.search(text)
    effective_date = m.group(1) if m else None

    return {
        "title": title,
        "heading_path": headings,
        "text": text,
        "tables": tables,
        "effective_date": effective_date,
    }


def clean_pdf(path: Path):
    text_parts, tables = [], []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            text_parts.append(t)
            for tbl in page.extract_tables() or []:
                rows = [[c or "" for c in row] for row in tbl if any(row)]
                if rows:
                    md = "\n".join("| " + " | ".join(r) + " |" for r in rows)
                    tables.append(md)
    text = "\n".join(text_parts)
    text = re.sub(r"\n{3,}", "\n\n", text)
    first_line = next((l.strip() for l in text.splitlines() if l.strip()), path.stem)
    m = DATE_RE.search(text)
    return {
        "title": first_line[:150],
        "heading_path": [],
        "text": text,
        "tables": tables,
        "effective_date": m.group(1) if m else None,
    }


def doc_id_for(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/extracted")
    args = ap.parse_args()

    raw_dir, out_dir = Path(args.raw), Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = raw_dir / "manifest.jsonl"
    records = [json.loads(l) for l in manifest_path.read_text().splitlines() if l.strip()]

    seen_text_hash = set()
    n_ok, n_dup, n_fail = 0, 0, 0
    for rec in records:
        fpath = raw_dir / rec["file"]
        try:
            if fpath.suffix == ".pdf":
                parsed = clean_pdf(fpath)
            else:
                parsed = clean_html(fpath.read_bytes())
        except Exception as e:
            print(f"  FAIL {rec['url']} ({e})")
            n_fail += 1
            continue

        text_hash = hashlib.sha256(parsed["text"].encode("utf-8", "ignore")).hexdigest()
        if text_hash in seen_text_hash:
            n_dup += 1
            continue
        seen_text_hash.add(text_hash)

        doc_id = doc_id_for(rec["url"])
        out_record = {
            "doc_id": doc_id,
            "source_url": rec["url"],
            "source": rec["source"],
            "visa_hint": rec.get("visa_hint", []),
            "title": parsed["title"],
            "heading_path": parsed["heading_path"],
            "page_type": "pdf" if fpath.suffix == ".pdf" else "html",
            "effective_date": parsed["effective_date"],
            "crawl_ts": rec["crawl_ts"],
            "text": parsed["text"],
            "tables": parsed["tables"],
        }
        (out_dir / f"{doc_id}.json").write_text(json.dumps(out_record, indent=1))
        n_ok += 1

    print(f"Extracted {n_ok} documents ({n_dup} near-duplicate by clean text, "
          f"{n_fail} failed) -> {out_dir}/")


if __name__ == "__main__":
    main()

# Report 01 — Ingestion (Stage 1: Scrape)

> Fill every number from a real crawl before submitting. Placeholders score as missing.

## Crawl policy compliance (proposal §7.1)
- robots.txt parsed and honored in code: `crawler/crawl.py::robots_allows()` — disallowed URLs are logged and skipped
- Rate limit: 1 request/second enforced globally (`polite_wait()`)
- User-Agent: `MSAI633-ResidencyProject-LegalAssistanceAgent/1.0 (student research crawler; contact: mbteja999@gmail.com)`
- Raw bytes saved with URL, timestamp, SHA-256 before any parsing (`data/raw/manifest.jsonl`)
- Excluded: login-walled pages, case-status tools, directories (GLOBAL_DENY patterns)

## Results (TODO: fill after crawl)
| Source | Pages saved | PDFs | Robots-blocked | Fetch failures |
|---|---|---|---|---|
| USCISPM | | | | |
| I129 | | | | |
| I539 | | | | |
| SEVP | | | | |
| CFR | | | | |
| FAM | | | | |
| **Total** | (target ≥150) | (target ≥5) | | |

## Reproduce
```
python crawler/crawl.py --sources all --out data/raw
```

## Extraction (Stage 2)
Run `python crawler/extract.py --raw data/raw --out data/extracted` and fill in:

| Metric | Value |
|---|---|
| Documents extracted | |
| Near-duplicates dropped (by clean text) | |
| Failed to parse | |
| Pages with an effective/last-reviewed date detected | |
| Tables preserved | |

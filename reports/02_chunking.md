# Report 02 — Chunking

## Strategies implemented
1. **Fixed-size** — sliding window (~3200 chars, ~480 char overlap), no structural awareness.
2. **Structure-aware** — splits on H1/H2 headings, carries the heading path into each chunk;
   any section still over ~4000 chars is sub-split with overlap.

## Chunk ID scheme (proposal Sec. 5)
`{visa_category}_{source_abbrev}_{section_or_heading_slug}_{chunk_index}_{content_hash8}`
Deterministic: verified identical output across repeated runs on unchanged input
(see crawler/chunk.py — content_hash8 is SHA-256 of normalized chunk text).

## Results (from real corpus run, 191 extracted documents)
Run: `python crawler/chunk.py --extracted data/extracted --out data/chunks`

| Strategy | Chunk count (raw) | Duplicates merged | Final count | Mean words | Median words | P90 words |
|---|---|---|---|---|---|---|
| Fixed-size | 1226 | 0 | 1226 | 468.6 | 502.0 | 532 |
| Structure-aware | 1543 | 220 | 1323 | 384.5 | 461 | 644 |

**Note on the 220 merged duplicates:** these are chunks with byte-identical
normalized text appearing under different source documents — primarily
repeated cross-reference boilerplate shared across USCIS Policy Manual
chapters (e.g. standard "see Volume 1, Part E" references). Per the chunk ID
scheme (Sec. 5), identical content deterministically produces the identical
ID; deduping at this stage removes redundant boilerplate from the corpus
before embedding, rather than storing 220 wasted near-copies in the vector DB.

## Reproduce
```
python crawler/extract.py --raw data/raw --out data/extracted
python crawler/chunk.py --extracted data/extracted --out data/chunks
```

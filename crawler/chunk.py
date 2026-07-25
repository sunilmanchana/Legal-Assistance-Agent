"""
Stage 3 — Chunking.

Implements BOTH required strategies from data/extracted/*.json:
  1. fixed-size  — sliding window over raw text, with overlap
  2. structured  — splits on headings (h1/h2), carries the heading path
                    into each chunk, then sub-splits any still-too-long section

Deterministic chunk ID scheme (proposal Sec. 5):
  chunk_id = {visa_category}_{source_abbrev}_{section_or_heading_slug}_{chunk_index}_{content_hash8}
  example  = H1B_CFR_214-2h4iii_003_9f21ab7c

  - content_hash8 is the first 8 hex chars of SHA-256 of the NORMALIZED chunk
    text, so identical content always produces the same ID (re-chunking a
    document that hasn't changed reproduces the same IDs; changed text gets
    a new hash -> Stage 6 re-chunk migration is a clean delete-by-ID diff).
  - visa_category is the chunk's primary tag (first entry of the source
    document's visa_hint list); the FULL list is also stored on the chunk
    as `visa_categories` for metadata filtering in the vector DB (Stage 5).

Usage:
    python crawler/chunk.py --extracted data/extracted --out data/chunks
Output:
    data/chunks/fixed.json
    data/chunks/structured.json
    data/chunks/stats.json   (counts + token-length distribution for both)
"""
import argparse
import hashlib
import json
import re
import statistics
from pathlib import Path

FIXED_CHARS = 3200      # ~ target chunk size for the fixed-size strategy
FIXED_OVERLAP = 480     # ~15% overlap
STRUCT_MAX_CHARS = 4000
STRUCT_OVERLAP = 400

SEC_IN_URL_RE = re.compile(r"section-(\d+[A-Za-z]?(?:\.\d+)?)")


def slugify(s: str, maxlen: int = 40) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:maxlen] or "doc"


def normalize_for_hash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def content_hash8(text: str) -> str:
    return hashlib.sha256(normalize_for_hash(text).encode("utf-8")).hexdigest()[:8]


def section_slug_for_doc(doc: dict) -> str:
    m = SEC_IN_URL_RE.search(doc["source_url"])
    if m:
        return m.group(1).replace(".", "-")
    if doc["heading_path"]:
        return slugify(doc["heading_path"][0])
    return slugify(doc["title"] or doc["doc_id"])


def make_chunk_id(visa_category, source_abbrev, section_slug, chunk_index, text):
    return (f"{visa_category}_{source_abbrev}_{section_slug}_"
            f"{chunk_index:03d}_{content_hash8(text)}")


def word_count(text: str) -> int:
    return len(text.split())


def split_fixed(text: str, size=FIXED_CHARS, overlap=FIXED_OVERLAP):
    if len(text) <= size:
        return [text] if text.strip() else []
    out, start = [], 0
    while start < len(text):
        end = start + size
        cut = text.rfind(" ", start + size - 200, end)
        if cut == -1 or cut <= start:
            cut = end
        piece = text[start:cut].strip()
        if piece:
            out.append(piece)
        if cut >= len(text):
            break
        start = max(cut - overlap, start + 1)
    return out


def split_long(text: str, size=STRUCT_MAX_CHARS, overlap=STRUCT_OVERLAP):
    if len(text) <= size:
        return [text]
    out, start = [], 0
    while start < len(text):
        end = start + size
        cut = text.rfind("\n", start + size - 500, end)
        if cut == -1 or cut <= start:
            cut = text.rfind(" ", start + size - 200, end)
        if cut == -1 or cut <= start:
            cut = end
        out.append(text[start:cut])
        if cut >= len(text):
            break
        start = max(cut - overlap, start + 1)
    return out


def split_structured(doc: dict):
    """Split on h1/h2 heading lines (as they appear in the flattened text),
    carrying the running heading path into each resulting section."""
    text = doc["text"]
    headings = doc["heading_path"]
    if not headings:
        return [{"path": [doc["title"]] if doc["title"] else [], "text": text}]

    # locate each heading's first occurrence as a line boundary
    positions = []
    search_from = 0
    for h in headings:
        idx = text.find(h, search_from)
        if idx == -1:
            continue
        positions.append((idx, h))
        search_from = idx + len(h)
    if not positions:
        return [{"path": [], "text": text}]

    sections = []
    if positions[0][0] > 0:
        sections.append({"path": [], "text": text[: positions[0][0]]})

    path_stack = []
    for i, (idx, h) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        # crude h1-vs-h2 nesting: if this heading is the doc's first heading, treat as h1
        if i == 0:
            path_stack = [h]
        else:
            path_stack = [path_stack[0], h] if len(path_stack) >= 1 else [h]
        sections.append({"path": list(path_stack), "text": text[idx:end]})
    return sections


def chunk_document(doc: dict):
    source_abbrev = doc["source"]
    visa_cats = doc.get("visa_hint") or ["GEN"]
    primary_cat = visa_cats[0]
    sec_slug_base = section_slug_for_doc(doc)

    fixed_chunks, struct_chunks = [], []

    # --- strategy 1: fixed-size ---
    for i, piece in enumerate(split_fixed(doc["text"])):
        cid = make_chunk_id(primary_cat, source_abbrev, sec_slug_base, i, piece)
        fixed_chunks.append({
            "chunk_id": cid, "doc_id": doc["doc_id"], "source_url": doc["source_url"],
            "source": source_abbrev, "visa_category": primary_cat,
            "visa_categories": visa_cats, "title": doc["title"],
            "heading_path": [], "page_type": doc["page_type"],
            "effective_date": doc["effective_date"], "text": piece,
        })

    # --- strategy 2: structure-aware ---
    idx = 0
    for sec in split_structured(doc):
        slug = slugify(sec["path"][-1]) if sec["path"] else sec_slug_base
        for piece in split_long(sec["text"]):
            if not piece.strip():
                continue
            cid = make_chunk_id(primary_cat, source_abbrev, slug, idx, piece)
            struct_chunks.append({
                "chunk_id": cid, "doc_id": doc["doc_id"], "source_url": doc["source_url"],
                "source": source_abbrev, "visa_category": primary_cat,
                "visa_categories": visa_cats, "title": doc["title"],
                "heading_path": sec["path"], "page_type": doc["page_type"],
                "effective_date": doc["effective_date"], "text": piece,
            })
            idx += 1

    return fixed_chunks, struct_chunks


def distribution(chunks):
    lens = [word_count(c["text"]) for c in chunks] or [0]
    lens_sorted = sorted(lens)
    p90 = lens_sorted[int(0.9 * (len(lens_sorted) - 1))]
    return {
        "count": len(chunks),
        "mean_words": round(statistics.mean(lens), 1),
        "median_words": statistics.median(lens),
        "p90_words": p90,
        "min_words": min(lens),
        "max_words": max(lens),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extracted", default="data/extracted")
    ap.add_argument("--out", default="data/chunks")
    args = ap.parse_args()

    ext_dir, out_dir = Path(args.extracted), Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    docs = [json.loads(p.read_text()) for p in sorted(ext_dir.glob("*.json"))]

    all_fixed, all_struct = [], []
    for doc in docs:
        f, s = chunk_document(doc)
        all_fixed += f
        all_struct += s

    # Chunk IDs are content-addressed by design (proposal Sec. 5): identical
    # chunk text -> identical ID, even across different source documents
    # (common with boilerplate/cross-reference text repeated across chapters).
    # That's intentional, not a bug -- dedupe by chunk_id, keeping the first
    # occurrence, and report how many were merged for transparency.
    def dedupe(chunks):
        seen, out = set(), []
        for c in chunks:
            if c["chunk_id"] in seen:
                continue
            seen.add(c["chunk_id"])
            out.append(c)
        return out, len(chunks) - len(out)

    all_fixed, n_dup_fixed = dedupe(all_fixed)
    all_struct, n_dup_struct = dedupe(all_struct)

    (out_dir / "fixed.json").write_text(json.dumps(all_fixed, indent=1))
    (out_dir / "structured.json").write_text(json.dumps(all_struct, indent=1))

    stats = {"fixed": distribution(all_fixed), "structured": distribution(all_struct),
              "documents_processed": len(docs),
              "duplicate_chunk_ids_merged": {"fixed": n_dup_fixed, "structured": n_dup_struct}}
    (out_dir / "stats.json").write_text(json.dumps(stats, indent=2))

    print(f"Documents processed: {len(docs)}")
    print(f"Fixed-size chunks:      {stats['fixed']}  "
          f"({n_dup_fixed} identical-content duplicates merged)")
    print(f"Structure-aware chunks: {stats['structured']}  "
          f"({n_dup_struct} identical-content duplicates merged)")
    print(f"-> {out_dir}/fixed.json, {out_dir}/structured.json, {out_dir}/stats.json")


if __name__ == "__main__":
    main()

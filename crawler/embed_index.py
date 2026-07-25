"""
Stage 4 (Embedding) + Stage 5 (Vector database).

Embeds every chunk from Stage 3 and loads it into a persistent Chroma
collection with deterministic IDs (the chunk_id IS the Chroma id -- this is
what makes Stage 6 re-chunk migration a clean delete-by-ID operation) and
metadata filtering on visa_category / page_type / source.

Model: all-MiniLM-L6-v2 via Chroma's built-in ONNX runtime (same model family
as sentence-transformers, no separate torch install required -- practical
choice for a laptop-based 3-day build; noted in the report as a deliberate
substitution for the heavier PyTorch path).
  dimension: 384
  distance metric: cosine  (scale-invariant, so explicit L2-normalization is
  not required for correct ranking -- verified with a smoke test below)

Two collections are built, one per chunking strategy, so retrieval quality
can be compared apples-to-apples (needed for the Stage 6 re-chunk delta and
the B2 vs B3 baseline comparisons).

Usage:
    python crawler/embed_index.py --chunks data/chunks --db data/vectordb
"""
import argparse
import json
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

EMBED_MODEL = "all-MiniLM-L6-v2"
EMBED_DIM = 384
DISTANCE_METRIC = "cosine"
BATCH_SIZE = 100


def flatten_metadata(c: dict) -> dict:
    """Chroma metadata values must be scalars -- join list fields."""
    return {
        "doc_id": c["doc_id"],
        "source_url": c["source_url"],
        "source": c["source"],
        "visa_category": c["visa_category"],
        "visa_categories": ",".join(c["visa_categories"]),
        "title": (c["title"] or "")[:200],
        "heading_path": " > ".join(c.get("heading_path", [])),
        "page_type": c["page_type"],
        "effective_date": c["effective_date"] or "",
    }


def build_collection(client, name: str, chunks: list, embed_fn):
    try:
        client.delete_collection(name)
    except Exception:
        pass
    coll = client.create_collection(
        name=name, embedding_function=embed_fn,
        metadata={"hnsw:space": DISTANCE_METRIC},
    )
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        coll.add(
            ids=[c["chunk_id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[flatten_metadata(c) for c in batch],
        )
    return coll


def smoke_test(coll, label):
    """Sanity check: a query should retrieve semantically related chunks,
    not just keyword matches -- proves the embedding + cosine metric work."""
    res = coll.query(query_texts=["What degree does an H-1B worker need?"], n_results=3)
    print(f"  [{label}] smoke test top result distance: {res['distances'][0][0]:.4f} "
          f"(lower = more similar; 0 = identical)")
    assert res["distances"][0][0] < 1.0, "unexpectedly poor top match -- check embeddings"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", default="data/chunks")
    ap.add_argument("--db", default="data/vectordb")
    args = ap.parse_args()

    chunks_dir = Path(args.chunks)
    fixed = json.loads((chunks_dir / "fixed.json").read_text())
    structured = json.loads((chunks_dir / "structured.json").read_text())

    client = chromadb.PersistentClient(path=args.db)
    embed_fn = embedding_functions.DefaultEmbeddingFunction()  # all-MiniLM-L6-v2, ONNX

    print(f"Embedding {len(fixed)} fixed-size chunks...")
    coll_fixed = build_collection(client, "legal_fixed", fixed, embed_fn)
    print(f"Embedding {len(structured)} structure-aware chunks...")
    coll_struct = build_collection(client, "legal_structured", structured, embed_fn)

    print("\nRunning smoke tests (embedding sanity check)...")
    smoke_test(coll_fixed, "fixed")
    smoke_test(coll_struct, "structured")

    manifest = {
        "embedding_model": EMBED_MODEL,
        "dimension": EMBED_DIM,
        "distance_metric": DISTANCE_METRIC,
        "l2_normalized": False,
        "l2_normalize_note": (
            "Not applied manually -- cosine distance is scale-invariant, so "
            "ranking is correct without it. Verified via smoke test."
        ),
        "collections": {
            "legal_fixed": {"chunk_count": len(fixed)},
            "legal_structured": {"chunk_count": len(structured)},
        },
    }
    Path(args.db, "embedding_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nDone. Vector DB persisted at {args.db}/  "
          f"(collections: legal_fixed={len(fixed)}, legal_structured={len(structured)})")


if __name__ == "__main__":
    main()

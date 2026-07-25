"""
Stage 7 — Retrieval.

Three modes, all implemented and independently measurable (proposal + course
requirement):
  1. dense   — Chroma vector search (cosine similarity over embeddings)
  2. bm25    — keyword search over the same chunk set (catches exact
               statutory/form terms embeddings can miss, e.g. "I-129", "214(h)")
  3. hybrid  — Reciprocal Rank Fusion (RRF) of the two rankings above

Retrieves a candidate pool of >= POOL_SIZE (default 20), which rerank.py then
narrows to the top N for generation. Recall@20 on this pool is the ceiling on
what the reranker can ever recover -- report it in reports/04.

Usage (library):
    from retrieval import Retriever
    r = Retriever(chunks_path="data/chunks/structured.json", db_path="data/vectordb",
                   collection="legal_structured")
    results = r.hybrid(query, k=20)
"""
import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

POOL_SIZE = 20
RRF_K = 60  # standard RRF constant


def tokenize(s: str):
    return re.findall(r"[a-z0-9]+", s.lower())


class Retriever:
    def __init__(self, chunks_path: str, db_path: str, collection: str):
        self.chunks = json.loads(Path(chunks_path).read_text())
        self.by_id = {c["chunk_id"]: c for c in self.chunks}
        self._bm25 = BM25Okapi([tokenize(c["text"]) for c in self.chunks])
        self._chunk_ids_in_order = [c["chunk_id"] for c in self.chunks]

        import chromadb
        from chromadb.utils import embedding_functions
        client = chromadb.PersistentClient(path=db_path)
        self.coll = client.get_collection(
            collection, embedding_function=embedding_functions.DefaultEmbeddingFunction()
        )

    def dense(self, query: str, k: int = POOL_SIZE, where: dict = None):
        res = self.coll.query(query_texts=[query], n_results=k, where=where)
        out = []
        for cid, dist in zip(res["ids"][0], res["distances"][0]):
            c = dict(self.by_id.get(cid, {}))
            c["chunk_id"] = cid
            c["dense_score"] = 1 - dist  # cosine distance -> similarity
            out.append(c)
        return out

    def bm25(self, query: str, k: int = POOL_SIZE, where: dict = None):
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        out = []
        for i in ranked:
            cid = self._chunk_ids_in_order[i]
            c = self.by_id[cid]
            if where and not all(c.get(k2) == v for k2, v in where.items()):
                continue
            cc = dict(c)
            cc["bm25_score"] = float(scores[i])
            out.append(cc)
            if len(out) >= k:
                break
        return out

    def hybrid(self, query: str, k: int = POOL_SIZE, where: dict = None):
        """Reciprocal Rank Fusion of dense + BM25 rankings."""
        dense_list = self.dense(query, k=max(k, POOL_SIZE), where=where)
        bm25_list = self.bm25(query, k=max(k, POOL_SIZE), where=where)

        rrf_scores = {}
        for rank, c in enumerate(dense_list):
            rrf_scores[c["chunk_id"]] = rrf_scores.get(c["chunk_id"], 0) + 1 / (RRF_K + rank + 1)
        for rank, c in enumerate(bm25_list):
            rrf_scores[c["chunk_id"]] = rrf_scores.get(c["chunk_id"], 0) + 1 / (RRF_K + rank + 1)

        ranked_ids = sorted(rrf_scores, key=lambda cid: rrf_scores[cid], reverse=True)[:k]
        out = []
        for cid in ranked_ids:
            c = dict(self.by_id[cid])
            c["rrf_score"] = rrf_scores[cid]
            out.append(c)
        return out

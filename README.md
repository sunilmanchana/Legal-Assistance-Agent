# Legal-Assistance-Agent (MSAI 633 Residency Project)

RAG chatbot for U.S. non-immigrant visa information (H-1B, F-1, B-2, L-1, O-1 + dependents).
Corpus: USCIS Policy Manual, I-129/I-539 instructions, SEVP guidance, 8 CFR 214, 9 FAM.

## Stage 1 — Crawler
```bash
pip install -r requirements.txt
python crawler/crawl.py --sources all --out data/raw
```
Output: `data/raw/*.html|pdf` + `data/raw/manifest.jsonl` (url, timestamp, sha256 per file).
Run `--sources USCISPM` etc. to crawl one source at a time.

## Git workflow (course-required)
```bash
git clone https://github.com/sunilmanchana/Legal-Assistance-Agent.git
cd Legal-Assistance-Agent
# copy this project's files in, then:
git checkout -b scrape/crawler
git add crawler/ reports/01_ingestion.md .gitignore requirements.txt README.md
git commit -m "feat: add stage-1 crawler with robots compliance and raw store"
git push -u origin scrape/crawler
# open a Pull Request on GitHub; a teammate reviews and merges
```

## AI usage disclosure (course §10)
Pipeline code drafted with Claude (Anthropic) and reviewed/run/tested by the team.
All evaluation items human-verified; all reported numbers computed by our own runs.


## Stage 2 — Extraction
```bash
python crawler/extract.py --raw data/raw --out data/extracted
```
Reads `data/raw/manifest.jsonl`, cleans each page (strips nav/header/footer/banners),
extracts PDF text, keeps tables intact as markdown, and writes one normalized JSON
per document to `data/extracted/<doc_id>.json` with fields:
`doc_id, source_url, source, title, heading_path, page_type, effective_date, crawl_ts, text, tables`.

Deduplicates by cleaned-text hash (catches near-identical pages the raw-byte
hash in Stage 1 missed, e.g. same content served at two URLs).

Stage 3 (chunking) reads only from `data/extracted/` — re-chunking never
requires re-crawling.


## Stage 3 — Chunking
```bash
python crawler/chunk.py --extracted data/extracted --out data/chunks
```
Reads only `data/extracted/` (no re-crawl needed). Produces BOTH required
strategies:
- `data/chunks/fixed.json` — fixed-size sliding window with overlap
- `data/chunks/structured.json` — splits on headings, carries the heading
  path into each chunk (falls back to fixed-size logic for any section
  that's still too long)
- `data/chunks/stats.json` — chunk counts + word-length distribution for
  both strategies (put these numbers in reports/02_chunking.md)

Every chunk gets a deterministic ID:
`{visa_category}_{source_abbrev}_{section_or_heading_slug}_{chunk_index}_{content_hash8}`
e.g. `H1B_CFR_214-2_003_9f21ab7c`. Same input text always produces the same
ID — re-running chunk.py on unchanged documents reproduces identical IDs,
so Stage 6 (re-chunk migration) is a clean delete-by-ID diff, never a guess.

## Stage 4 + 5 — Embedding & Vector Database
```bash
pip3 install -r requirements.txt
python3 crawler/embed_index.py --chunks data/chunks --db data/vectordb
```
First run downloads the embedding model (~90 MB, one-time, needs internet —
this is normal, not an error). Builds two persistent Chroma collections,
`legal_fixed` and `legal_structured`, so both chunking strategies can be
compared retrieval-for-retrieval later.

- Model: all-MiniLM-L6-v2 (384 dimensions, cosine distance)
- Every chunk's Chroma ID = its deterministic `chunk_id` from Stage 3 —
  this is what makes Stage 6 (re-chunk migration) a clean delete-by-ID
  operation instead of a guess
- Metadata filtering is enabled on `visa_category`, `page_type`, and `source`
- A smoke test runs automatically after indexing and prints a similarity
  score, so you'll immediately see if something's off

To inspect the database later (e.g. to prep Stage 6's delete-and-verify-no-orphans
demo), reconnect with `chromadb.PersistentClient(path="data/vectordb")`.

## Stage 7 + 8 + 9 — Retrieval, Reranking, Generation (the chatbot itself)
```bash
pip3 install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
streamlit run crawler/app.py
```
- **Retrieval (Stage 7):** dense (Chroma/cosine), BM25, and hybrid
  (Reciprocal Rank Fusion) all implemented in crawler/retrieval.py. Pool
  size 20.
- **Reranking (Stage 8):** LLM reranker (Claude Haiku) narrows the pool of
  20 to the top 5 -- crawler/rerank.py. Falls back safely to original order
  if the model ever returns a malformed response (tested).
- **Generation (Stage 9):** crawler/app.py -- answers only from retrieved
  context, cites source URLs, enforces a 25-word quote limit in
  post-processing, and refuses when the corpus doesn't cover the question.
- Chatbot requirements met: conversation history, clickable citations,
  visible refusal, expandable retrieval trace (pre/post-rerank ranks +
  timing), high-stakes referral to a qualified immigration attorney/DSO.
- Sidebar lets you switch between the `structured` and `fixed` chunking
  strategies to compare retrieval quality live.

## Evaluation Harness (Report 06 — course Sec. 5)
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python crawler/evaluate.py --golden reports/golden_set_draft.csv \
    --chunks data/chunks --db data/vectordb --out reports/eval_results
python crawler/summarize.py --results reports/eval_results \
    --out reports/06_final_performance.md
```
Runs all 40 golden items through four baselines:
- **B0** closed-book (no retrieval) — measures what the model already knew
- **B1** BM25 keyword search only
- **B2** dense vector search, naive fixed-size chunks
- **B3** final system: hybrid (BM25+dense via RRF) + LLM rerank, structured chunks

Computes Recall@20, MRR, nDCG@10, LLM-judged answer correctness, citation
presence, correct-refusal rate (on unanswerable items), over-refusal rate
(on answerable items), and p50/p95 latency — each with a 95% bootstrap
confidence interval. Also runs the required B2-vs-B3 ablation with a paired
McNemar's test, and reports B3's accuracy on just the "B0 got it wrong"
subset (the honest measure of what retrieval actually added).

**Cost/time note:** running all 40 items × 4 baselines makes ~150-200 API
calls total (including the LLM judge and the LLM reranker). Use `--limit 5`
first to smoke-test on a handful of items before running the full set.
```bash
python crawler/evaluate.py --limit 5 --golden reports/golden_set_draft.csv \
    --chunks data/chunks --db data/vectordb --out reports/eval_results_smoke
```

**Prerequisite:** the golden set should be substantially human-verified
before this counts for the course (see GOLDEN_SET_INSTRUCTIONS.md) — running
the harness against an unverified draft is fine for testing the code, but
the reported numbers only count once the answers are confirmed correct.

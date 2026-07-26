# Golden Evaluation Set — Verification Instructions

**File:** `golden_set_draft.csv` (open in Excel, Google Sheets, or Numbers)

### Update (2026-07-26): Verification is complete — all 40 items are now HUMAN-VERIFIED

This replaces the earlier "11 of 40 pre-verified, needs sign-off" state. Since the original instructions above were written, the team:

1. Personally opened and confirmed the source link for every single-hop, multi-hop, comparative, and temporal item against the live government page
2. Personally ran every unanswerable and ambiguous/adversarial item through the actual live chatbot and recorded the real, observed answer
3. Expanded the set from 25 back to 40 items to meet the required category minimums (15 single-hop / 6 multi-hop / 4 comparative / 4 temporal / 8 unanswerable / 3 ambiguous-adversarial)

**Every row's `verified_by_human` column 

### Two honest, disclosed findings from real testing (read this — these are a feature, not a bug)

**G12 — status: `mismatch`.** This item tests the H-1B cap-gap extension. Our crawled corpus reflects an older rule (extension until October 1); a newer January 2025 DHS rule extended this further to April 1. Our live chatbot correctly reported what's actually in the corpus (October 1) — the mismatch is between our corpus's currency and the newest real-world rule, not a chatbot error. This is a genuine, real-world example of the staleness risk our ethics safeguard is designed to catch.

**G39 — status: `mismatch`.** This item was originally designed as an *unanswerable* test (a $100,000 H-1B supplemental fee proclamation, deliberately outside our original 6 crawled sources). Later the same night, we expanded the corpus with one additional USCIS page for an unrelated demo — and that page happens to also cover this fee. The chatbot now correctly answers a question that was designed to be unanswerable, purely as a side effect of legitimate corpus growth. Worth mentioning as an example of how corpus updates can shift which test cases still validly test refusal behavior.

**G01 and G02** were purpose-built this session as our strongest evidence pieces: both were tested live against a plain LLM (ChatGPT, web search off) and against our own agent side by side. The plain LLM was confidently and factually wrong on both; our agent was correct and cited on both, after we specifically added the relevant government pages to the corpus.

### Final category breakdown (all ranges below are fully verified)

| Category | Row range | Count |
|---|---|---|
| temporal | G01–G02, G17–G18 | 4 |
| single-hop | G03–G11, G26–G31 | 15 |
| multi-hop | G12–G14, G32–G34 | 6 |
| comparative | G15–G16, G35–G36 | 4 |
| unanswerable | G19–G22, G37–G40 | 8 |
| ambiguous-adversarial | G23–G25 | 3 |
| **Total** | | **40** |

### Final status breakdown

| Status | Count | Meaning |
|---|---|---|
| `matches_corpus` | 31 | Live-tested or source-verified; chatbot's real answer matches the expected answer |
| `gold_not_supported_by_corpus` | 7 | Correctly and deliberately unanswerable; chatbot correctly refused |
| `mismatch` | 2 | Honest, disclosed discrepancies (see above) — not hidden or silently corrected |



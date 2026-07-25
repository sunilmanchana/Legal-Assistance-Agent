# Golden Evaluation Set — Verification Instructions

**File:** `golden_set_draft.csv` (open in Excel, Google Sheets, or Numbers)

## Update: 11 of 40 items are now AI-pre-verified
I went and directly fetched the real government pages myself and checked the
numbers. Rows marked **AI-VERIFIED** in the `verified_by_human` column
(G01, G02, G03, G04, G14, G15, G16, G17 partial, G24 partial, G27, G28, G29,
G35, G36) had their facts confirmed against the live page text on 2026-07-25
— including catching one of my own original guesses that needed a source
change (G04) and confirming another that I wasn't sure about (G28's "6
years" turned out correct).

**"AI-VERIFIED" still needs your sign-off, not a full re-investigation.**
Per the course rule, you personally still need to open each AI-VERIFIED
row's link once and confirm it looks right — but this should take seconds
per row, not minutes, since the fact-checking legwork is done. Change
`verified_by_human` from `AI-VERIFIED` to your initials once you've glanced
at it.

**Rows WITHOUT "AI-VERIFIED"** (about 29 rows) still need real work — I
either didn't have time to check them this session, or I was upfront that I
wasn't confident (see G23, G25, G12, G13 etc.). These are your priority.

## One important discovery while verifying (read this)
While checking F-1 grace-period facts, I found that DHS has a **new rule
taking effect September 15, 2026** that cuts the standard F-1 post-completion
grace period from 60 days down to 30 days, as part of eliminating "duration
of status." Your corpus was crawled before that date, so it almost certainly
only reflects the *old* 60-day rule. I turned this into golden item **G20**
— it's simultaneously a real multi-hop test and a staleness test, and it's
directly relevant to your own CPT situation, not just an assignment
exercise. Worth flagging in your final report as a genuine, non-synthetic
example of the staleness risk your ethics safeguard is designed to catch.

## What "verified" means for each category

**single-hop / multi-hop / comparative / temporal (items G01–G29):**
1. Open the `source_url`.
2. Confirm the `draft_answer` is correct on that page (quick glance for
   AI-VERIFIED rows; real check for the rest).
3. Put your initials in `verified_by_human`, today's date in
   `verified_date`.
4. If wrong: fix the `draft_answer`, or replace the row's question/source
   with something you find directly on the page. Do not leave a wrong
   answer in the set.

**unanswerable (G30–G37):** confirm these are genuinely absent from your
corpus. G35 and G36 I confirmed are real facts that exist elsewhere on the
internet but are NOT in your crawled pages — good hallucination tests.

**ambiguous / adversarial (G38–G40):** run these through your actual
chatbot and record what it said. G38 is essentially already validated by
your own "will my H-1B be approved" live test.

## After verification
Split 60/40 into dev/test, stratified by category. Tune only on dev, run
test once at the end.


# Sprint v5 — Tasks: Build the Eval Dataset

Goal (see `PRD.md`): a trustworthy, diverse, **verified, held-out** 22-doc eval dataset
(10 dev / 12 held-out test; **17 new docs** need ground truth via **Option B** independent
**multi-model** annotation — 5 frontier models from 5 labs (Opus 5 · GPT-5.6 Sol · Grok 4.5 ·
Kimi K3 · Qwen3.8-Max; slugs in PRD §4.4); current 5 keep their v3-verified GT).

Sequenced so the protocol exists *before* we annotate, and data exists *before* we score.

- [x] **Task 1 — Annotation protocol + match-strategy catalog** (P0, do first)
    Acceptance: `tests/fixtures/DATASET_CARD.md` scaffolded with the ground-truth **protocol**
    (Option B multi-model annotation, per-field value + `match` + `notes`/source-quote,
    ambiguous-field rules) and the **match-strategy catalog** (`exact` · `contains` · `date` ·
    `numeric`). Done 2026-08-06 — built example-first across the 16 fields; key rule captured:
    *ground truth encodes the extractor's current policy* (the capex lesson generalized).

- [x] **Task 2 — Coverage plan + source shortlist** (P0)
    Acceptance: a target matrix (technology × geography × source/style) with candidate URLs.
    Done 2026-08-06 — `sprints/v5/SOURCES.md`. Reallocated for sourceability (hydro/hybrid up,
    **offshore wind → documented gap**; source-style capped at single-project dev-bank).

- [x] **Task 3 — Acquire dev-bank docs (WB PADs)** (P0)
    Acceptance: download → `extract_text()` → keep only **text-native** → `real_samples/`.
    Done 2026-08-06 — 12 new WB PADs (curl works; ADB blocked) validated text-native + field-rich;
    dropped field-poor ones (India/Ukraine hybrids, Kambarata, PP4206). **17 total eval docs**
    (5 current + 12 new): 4 techs (solar/wind/hydro/hybrid), 4 regions (Asia/Africa/Caucasus/
    LatAm), ~10 long docs for RAG. Effort-gated stop short of 20.

- [x] **Task 4 — Private-sector docs → investigated, decision made** (P0)
    Done 2026-08-06 — **finding: single-project *private* docs are scarce publicly.** Adani =
    blocked + corporate/portfolio; investment trusts (Greencoat) = portfolio-level (many assets,
    no single-project fields). **Decision:** keep the eval **single-project (dev-bank)**; note the
    style limitation in the dataset card; **park Greencoat in `tests/fixtures/rag_material/`** for
    v7 RAG (it's ideal there). So the 17-doc set is all dev-bank single-project.

- [ ] **Task 5 — Build the GT multi-model draft + reconcile tool** (P0) · needs `OPENROUTER_API_KEY`
    Acceptance: a minimal script that, per doc, gets independent drafts from the **5 models**
    (5 labs; slugs in PRD §4.4, via OpenRouter), then reconciles per field —
    **unanimous** → auto-accept · **majority** → accept (flag) · **split** → report (doc · field
    · each model's value+quote). *Purpose-built for GT data creation — NOT the v6 eval-harness.*

- [ ] **Task 6 — Multi-model draft ground truth for the 17 new docs** (P0) · needs `OPENROUTER_API_KEY`
    Acceptance: run Task-5 tool over all 17 new docs → unanimous/majority consensus written to
    `ground_truth/<name>.json`; splits collected for Task 7; inter-annotator agreement recorded.

- [ ] **Task 7 — Adjudicate splits → verified ground truth** (P0)
    Acceptance: the user resolves each split against the source doc; ambiguous decisions
    (IRR vs ROE, debt % vs ratio) recorded in `notes`; all 17 fixtures marked **verified**.

- [ ] **Task 8 — Record & enforce the train/test split** (P0)
    Acceptance: split recorded (10 dev = current 5 + 5 new; 12 held-out test) via
    `dataset_split.json` or a per-fixture `split` field. Anti-leakage rule documented: few-shot
    examples may come **only** from dev; test docs are quarantined from prompt iteration.

- [ ] **Task 9 — Validate the set (run harness; surface bugs)** (P0)
    Acceptance: `evaluate_extraction_accuracy.py` runs cleanly on all 22 (extractability
    confirmed). **Not** chasing accuracy — bugs (date matching, numeric/unit formatting) are
    **logged to `design-backlog.md` for v6**, not fixed here.

- [ ] **Task 10 — Finalize dataset card + commit the sprint** (P1)
    Acceptance: `DATASET_CARD.md` completed (composition, per-doc source/tech/geo/split,
    limitations). Commit `real_samples/`, `ground_truth/`, split manifest, card, `sprints/v5/`.

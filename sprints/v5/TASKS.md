# Sprint v5 — Tasks: Build the Eval Dataset

Goal (see `PRD.md`): a trustworthy, diverse, **verified, held-out** 22-doc eval dataset
(10 dev / 12 held-out test; **17 new docs** need ground truth via **Option B** independent
dual annotation; current 5 keep their v3-verified GT).

Sequenced so the protocol exists *before* we annotate, and data exists *before* we score.

- [ ] **Task 1 — Annotation protocol + match-strategy catalog** (P0, do first)
    Acceptance: `tests/fixtures/DATASET_CARD.md` scaffolded with the ground-truth **protocol**
    (Option B dual-annotation, per-field value + `match` + `notes`/source-quote, ambiguous-field
    rules) and the **match-strategy catalog** (`exact` · `contains` · `date` · `numeric`).

- [ ] **Task 2 — Coverage plan + source shortlist** (P0)
    Acceptance: a 17-slot target matrix (technology × geography × source/style) with a candidate
    URL per slot, hitting the diversity targets incl. **≥6 docs where the hard fields are
    genuinely stated**. Builds on `EVAL_DOCS_CANDIDATES.md`.

- [ ] **Task 3 — Acquire dev-bank docs (WB PADs, IFC, AIIB)** (P0)
    Acceptance: download → `extract_text()` → keep only **text-native** → save to
    `tests/fixtures/real_samples/`. Skip scanned/blocked (note them). ~9 docs.
    *(Collaborative: some sources need manual browser download.)*

- [ ] **Task 4 — Acquire private-sector docs (bond prospectus, investment trust)** (P0)
    Acceptance: same download→`extract_text()`→keep-text-native loop; fill remaining
    diversity/coverage gaps. Reach **17 new** + 5 current = 22 total.

- [ ] **Task 5 — Build the GT dual-draft + reconcile tool** (P0) · needs `OPENROUTER_API_KEY`
    Acceptance: a minimal script that, per doc, produces **Draft A** (Claude) and **Draft B**
    (independent model via OpenRouter), then **auto-diffs** them field-by-field → a
    **disagreements report** (doc · field · A value+quote · B value+quote); agreements
    auto-accepted. *Purpose-built for GT data creation — NOT the v6 eval-harness.*

- [ ] **Task 6 — Dual-draft ground truth for the 17 new docs** (P0) · needs `OPENROUTER_API_KEY`
    Acceptance: run Task-5 tool over all 17 new docs → auto-accepted agreements written to
    `ground_truth/<name>.json` (marked from-agreement); disagreements collected for Task 7.

- [ ] **Task 7 — Adjudicate disagreements → verified ground truth** (P0)
    Acceptance: the user resolves each disagreement against the source doc; ambiguous decisions
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

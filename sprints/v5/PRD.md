# Sprint v5 — PRD: Build the Eval Dataset

**Status:** draft for review (uncommitted)
**Sprint:** v5 (Week 2) · learning theme: **L10 — benchmarks / datasets**
**Depends on:** v4 (extractor + current eval) · **Blocks:** v6 (eval machinery) and everything downstream

---

## 1. Problem & motivation

Our eval is the **ruler** every future sprint is measured against — and right now it's not
trustworthy:
- **N=5** — too small; "net +1" improvements sit inside the noise.
- **Not reproducible** — proven: two `temperature=0` runs scored 96.2% vs 81.2% (no setting
  fixes this; it's inference non-determinism).
- **Train/test leakage** — our 5 few-shot examples were designed around the *same 5 docs* we
  score on. We've been tuning on the test set.
- **One source style** — all dev-bank-flavored; risks overfitting to that format.

Before we build *anything* else (RAG, agents…), we need a ruler we can trust. This sprint
builds it: a bigger, **diverse, verified, held-out** dataset with a written annotation
protocol. *(Machinery — self-consistency, multi-model, metric fixes — is v6, not this sprint.)*

## 2. Goals

1. **25 total documents**, all **text-native** (our `extract_text()` returns real content).
2. **Diverse** across technology, geography, source, and *field coverage* (below).
3. **Verified ground truth** for every doc, built via a written, repeatable protocol.
4. A clean **train/dev vs held-out test split** that eliminates leakage.
5. A **dataset card** (datasheet) documenting composition, sources, and the annotation rules.

## 3. Non-goals (explicitly deferred to v6)

- ❌ Self-consistency / multi-run voting.
- ❌ Multi-model comparison (OpenRouter + `instructor`).
- ❌ Implementing new match logic in the harness (date-aware, numeric-tolerance) — v5 *defines*
  the match strategy per field; v6 *implements* the new ones.
- ❌ Chasing the accuracy number. We run the harness on the new set only to **validate
  extractability and surface bugs**, which we **log for v6**.

## 4. Requirements

### 4.1 Composition — 22 docs
| Split | Count | Which |
|---|---|---|
| **Train / dev** | 10 | the current 5 (already informed the prompt) **+ 5 new diverse** (so we can tune on offshore wind, private-sector style, etc.) |
| **Held-out test** | 12 (new) | never seen by prompt design; the accuracy signal |

→ **17 new docs need ground truth**; the current 5 keep their v3-verified GT.
*(Test is deliberately the majority-ish, because it's a measurement set — bigger = less noise.)*

### 4.2 Diversity targets (spread the 20 new across these)
| Axis | Spread |
|---|---|
| **Technology** | solar PV · onshore wind · offshore wind · hydro · BESS / hybrid |
| **Geography** | ≥4 regions (Asia, Africa, Europe, Americas) |
| **Source / style** | dev-bank (World Bank PAD, IFC) **and** private (project/green-bond prospectus, listed investment trust) |
| **Field coverage** | ≥6 docs where the *hard* fields (IRR, debt%, equity%, capex_per_mw) are **genuinely stated** — so a "lazy `not_found`" model can't score well |

### 4.3 Sources (validated in `EVAL_DOCS_CANDIDATES.md`)
- **Primary (text-native, fetchable):** World Bank PADs (`documents1.worldbank.org`).
- **Dev-bank:** IFC SII (HTML for ground-truth cross-check), AIIB PSI.
- **Private:** a project/green-bond prospectus, a listed investment-trust report.
- ⚠️ ADB blocks bots (403) → manual download. Skip scanned/compressed PDFs (no OCR in scope).

### 4.4 Ground-truth protocol — Option B (independent dual annotation)
The real-world method: two annotators label independently, a human adjudicates disagreements.
Here, two *models* are the annotators. Runs on the **17 new docs only** (current 5 keep v3 GT).

For each new doc, produce `tests/fixtures/ground_truth/<name>.json` (per field:
`expected_found`, `expected_value`, `match`, `notes` with source quote + ambiguity reasoning):
1. **Draft A** — Claude reads the source, fills GT with source quotes.
2. **Draft B** — an *independent* model (GPT-5 / Gemini via **OpenRouter**) drafts it separately.
3. **Auto-reconcile** — a script diffs A vs B per field: **agreements auto-accepted**;
   **disagreements** → a report (doc · field · A value+quote · B value+quote).
4. **Human adjudication** — the user resolves *only the disagreements* against the source.

**Scope guardrails (keep v5 ≠ v6):** the Draft-B call is a *minimal, purpose-built GT-drafting
script* (data creation) — **not** the v6 eval-harness (benchmarking the extractor across models).
A thin shared "call model X" helper is all they share; **no full multi-model abstraction in v5.**

- **Ambiguous fields** (IRR vs ROE, debt as % vs ratio) → record the *decision* in `notes`,
  consistent with v4's "faithful extraction, derive in code" rules.
- **Match-strategy catalog** (defined here; new ones implemented in v6):
  `exact` · `contains` · **`date`** (compare as dates, format-agnostic) · **`numeric`**
  (compare with small tolerance for rounding/units).
- **Dependency:** requires `OPENROUTER_API_KEY` in the env.

### 4.5 Split & anti-leakage policy
- Few-shot examples in the prompt may be drawn **only from train/dev**, never from test.
- Test docs are **quarantined** from prompt iteration.
- A `dataset_split.json` (or a `split` field per fixture) records which set each doc is in.

### 4.6 Dataset card
`tests/fixtures/DATASET_CARD.md` — composition table, per-doc (source URL, tech, geo, split),
the annotation protocol, and known limitations.

## 5. Acceptance criteria
- [ ] 25 docs present, all pass `extract_text()` (text-native).
- [ ] Diversity targets met (tech / geo / source / hard-field-coverage).
- [ ] Verified ground truth for all 25; ambiguous decisions noted.
- [ ] Train/dev (5) vs held-out test (20) split recorded and enforced.
- [ ] `DATASET_CARD.md` written.
- [ ] Harness runs cleanly on all 25; bugs surfaced are **logged for v6** (not fixed here).

## 6. Risks & mitigations
| Risk | Mitigation |
|---|---|
| Ground-truth quality (garbage in → garbage eval) | Written protocol + verification pass + source quotes in `notes` |
| Sourcing friction (403s, scanned PDFs) | WB PADs are reliable; manual download for blocked; skip non-text-native |
| 25 docs of GT is a lot of labor | Batch by source; assisted drafting + targeted human verification of hard fields only |
| Accidentally re-introducing leakage | Quarantine test set; split manifest; few-shot from dev only |

## 7. Decisions (confirmed 2026-08-06)
1. **Split:** 10 dev (current 5 + 5 new diverse) / 12 held-out test → 22 total; **17 new need GT**.
2. **GT verification:** **Option B** — independent dual annotation (Claude + GPT-5/Gemini) with
   human adjudication of *disagreements only* (§4.4); scoped as a minimal GT-drafting tool, not
   the v6 harness.
3. **Second model** via OpenRouter → needs `OPENROUTER_API_KEY` in the env.

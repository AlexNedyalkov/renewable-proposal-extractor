# Sprint v5 — Task 2: Coverage plan + candidate shortlist

Working shortlist (candidates to validate in Task 3). **Validation = download → `extract_text()`
→ keep only text-native.** Some are PDFs (pipeline-ready); some are IFC **HTML** (data-rich but
*not* a PDF — use for ground-truth cross-reference, not as the doc itself).

## Coverage matrix (17 new; revised for what's publicly sourceable)
| Tech | Target | Source reality |
|---|---|---|
| Hydro | 4 | WB PADs — plentiful, **long** (RAG material), hard fields |
| Solar PV | 4 | WB PADs + 1 private bond |
| Onshore wind | 4 | WB PAD + IFC + 1 investment trust |
| Solar + BESS / hybrid | 4 | dev-bank hybrids |
| Offshore wind | 1 (or 0) | **documented gap** — no clean single-project disclosure exists |

Also spread **geography** (Asia / Africa / Europe / Americas) and include **3–4 long docs**
(WB PADs/prospectuses) for v7 RAG. **Split:** 5 → dev, 12 → held-out test.

## Candidate shortlist (validate in Task 3)

### Hydro
- ⭐ **Rogun Hydropower (Tajikistan)** — 3,780 MW, $2.44B — *long doc.* `documents1.worldbank.org/curated/en/099072123165041455/pdf/P1810290716f920e08543049a566c86b4c.pdf`
- **Zambia renewables PAD** (110675-ZM) — `documents1.worldbank.org/curated/en/974771487473237766/pdf/PAD-01302017.pdf`
- _(2 more WB hydro — Bhutan/Nepal/Georgia; backfill in Task 3)_

### Solar PV
- **Uzbekistan Scaling Solar 2 IPP** — `documents1.worldbank.org/curated/en/099213002152311969/pdf/BOSIB0a174245f01209bc004f8b1fe86732.pdf`
- **Morocco Noor CSP** — `documents1.worldbank.org/curated/en/138481528687821561/pdf/Morocco-Noor-AF-project-paper-P164288-May17-clean-05212018.pdf`
- **Adani Green** (private USD bond offering) — `adanigreenenergy.com/-/media/Project/GreenEnergy/Corporate-Announcement/Board/USD-denominated-Offerings.pdf`
- _(1 more — Africa/Americas geography)_

### Onshore wind
- **WB PAD651** (P146055) — `documents1.worldbank.org/curated/en/156751468335513164/pdf/PAD6510P146055010Box382145B00OUO090.pdf`
- **Greencoat UK Wind** annual report (private, *long*) — `greencoat-ukwind.com/download_file/view/69a1b4d8-ce1f-45e6-978a-b150c43a2302/`
- **Green Infra Wind** (IFC, India) — ⚠️ HTML only: `disclosures.ifc.org/project-detail/SII/35415/green-infra-wind`
- _(1 more WB/IFC onshore wind)_

### Solar + BESS / hybrid
- **UZ Solar 3** (250 MWac + BESS) — ⚠️ HTML only: `disclosures.ifc.org/project-detail/SII/47285/uz-solar-3`
- **AIIB India Distributed Solar** (PDF, text-native w/ minor artifacts; *portfolio* facility) — `aiib.org/en/projects/details/2023/_download/India/AIIB-PSI-P000637-India-Distributed-Solar-Financing-Transaction-vDisclosed.pdf`
- _(2 more dev-bank solar+storage PADs)_

### Offshore wind
- **Gap** — accept 0–1; if 1, extract one named asset from a trust report (fields won't map cleanly). Note in the dataset card's limitations.

## Notes / gotchas
- **WB PADs = the backbone** — fetchable (not blocked like ADB), text-native, long, hard-field-rich. Prioritize these.
- **IFC pages are HTML** — great for cross-checking ground truth, but not a PDF input. Find the SII PDF or use HTML only for reference.
- **ADB is blocked** (403) → manual download if we want any.
- Reaching a clean 17 will need **backfill during Task 3** as some candidates fail the text-native check.

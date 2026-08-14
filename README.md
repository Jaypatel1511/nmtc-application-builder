# NMTC Application Builder

**The open-source intelligence platform for competitive CDFI Fund applications.**

[![PyPI version](https://img.shields.io/pypi/v/nmtc-application-builder.svg)](https://pypi.org/project/nmtc-application-builder/)
[![Python](https://img.shields.io/pypi/pyversions/nmtc-application-builder.svg)](https://pypi.org/project/nmtc-application-builder/)
[![Tests](https://img.shields.io/badge/tests-658%20passing-brightgreen.svg)](https://github.com/Jaypatel1511/nmtc-application-builder/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg)](https://jaypatel1511.github.io/nmtc-application-builder/)

**[Documentation](https://jaypatel1511.github.io/nmtc-application-builder/) · [Streamlit Demo](https://nmtc-application-builder.streamlit.app) · [Examples](examples/) · [PyPI](https://pypi.org/project/nmtc-application-builder/)**

---

CDEs spend months preparing NMTC allocation applications without knowing how their pipeline compares to historical winners. This library changes that — scoring your pipeline against five years of CDFI Fund award data in seconds, generating competition-ready document drafts automatically, and telling you exactly what to fix.

```python
app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
app.add_pipeline(Pipeline.from_csv("pipeline.csv"))
score = app.score_win_probability()
print(f"Alignment: {score.composite_score:.0f}/100 [{score.tier}]")
# → Alignment: 90/100 [Highly Qualified]
paths = app.generate("./drafts/")
# → Word, Excel, PDF, and Markdown application package ready in ./drafts/
```

---

## The Problem

CDE teams preparing NMTC allocation applications work blind. They spend weeks manually assembling pipeline data in Excel, draft narrative sections without knowing how their distress concentration or geographic diversity compares to past winners, and submit applications with no objective measure of competitiveness. The CDFI Fund receives 280–340 applications per round with a ~35% acceptance rate — yet most CDEs have no systematic way to benchmark their position before the deadline.

## The Solution

`nmtc-application-builder` gives CDEs a programmatic intelligence layer aligned to the CDFI Fund's **published CY 2024-2025 Review Process** criteria. Load your pipeline from CSV, run `analyze()`, and immediately see where you stand on Business Strategy, Community Outcomes, and Priority Points — the three sections the CDFI Fund scores. Get specific, numbered recommendations with CDFI Fund citations. Optimize your project subset automatically. Generate the Word, Excel, PDF, and Markdown drafts that go directly into your application package.

---

## Quickstart

```bash
pip install nmtc-application-builder[output,viz]
```

```python
from nmtcapp import Application, CDEProfile, Pipeline
from nmtcapp.optimizer import OptimizationConstraints

# 1. Define your CDE
cde = CDEProfile.sample()                           # or CDEProfile.from_yaml("cde.yaml")

# 2. Load your pipeline
pipeline = Pipeline.from_csv("pipeline.csv")        # or Pipeline.sample(n=20) for demo

# 3. Analyze
app = Application(cde=cde, requested_allocation=65_000_000)
app.add_pipeline(pipeline)
analysis = app.analyze()
analysis.summary()

# 4. Score alignment with historical winners
score = app.score_win_probability()                 # alignment score, not win probability
print(f"{score.composite_score:.0f}/100 [{score.competitive_tier}]")

# 5. Get quantified recommendations
recs = app.recommendations()
print(recs.summary())

# 6. Optimize your pipeline subset
result = app.optimize_pipeline(
    constraints=OptimizationConstraints(max_total_qei=65_000_000, min_states=5)
)
print(f"Score: {result.alignment_score_before*100:.0f} → {result.alignment_score_after*100:.0f}")

# 7. Generate the full application package
paths = app.generate("./drafts/")
```

Or bootstrap a starter project in 60 seconds:

```bash
nmtcapp init my-application/
cd my-application/
jupyter notebook analysis.ipynb
```

---

## Pipeline Template v1.1

Download [`nmtcapp/templates/pipeline_template.xlsx`](https://github.com/Jaypatel1511/nmtc-application-builder/blob/main/nmtcapp/templates/pipeline_template.xlsx) for the recommended way to provide pipeline and CDE data to the Streamlit analyzer.

### Template structure

| Sheet | Purpose |
|---|---|
| **CDE Profile** | One row — 30 CDE-level scoring inputs (Business Strategy, Community Outcomes, Priority Points, Phase 2 flags) |
| **Pipeline** | One row per project — 28 columns including all new v1.1 per-project flags |
| **Instructions** | Field-by-field documentation, scoring formula summary, graceful-degradation notes |
| **Valid Values** | Dropdown source lists (do not edit) |

### New per-project flags (Pipeline sheet)

These Y/N flags in the Pipeline sheet automatically compute CDE-level scoring inputs — you don't need to manually calculate percentages:

| Column | Drives | Sub-score |
|---|---|---|
| `Native Area (Y/N)` | `pct_native_area` | CO Special Targeting |
| `High Migration Rural (Y/N)` | `pct_high_migration_rural` | CO Special Targeting |
| `US Territory (Y/N)` | `pct_us_territories` | CO Special Targeting |
| `Persistent Poverty (Y/N)` | `pct_persistent_poverty` | CO Special Targeting |
| `Below-Market Rate (Y/N)` | `products_below_market_pct` | BS Product Flexibility |
| `Unrelated Entity (Y/N)` | `unrelated_entities_pct` | PP Unrelated Entities |

If you also supply the CDE-level percentage in the CDE Profile sheet, it takes precedence over the computed value.

### Default behaviour when flags are absent

All six flags are **optional**. When a column is missing from the file, or a cell is blank, the flag defaults to `None`, which the scoring engine treats identically to `N` — the project contributes **zero QEI** to the relevant percentage. This is a conservative default: you will not be penalised for leaving a flag blank, but you also will not receive credit for that targeting category.

> **Version requirement:** The Streamlit analyzer and `Pipeline.from_csv()` both accept v1.0 files (without the flag columns) and will score them correctly — but the Special Targeting sub-score, pipeline-derived Product Flexibility, and pipeline-derived Unrelated Entities will all default to 0 without warning. Use the v1.1 xlsx template or add the flag columns to your CSV to get accurate scores for those sub-criteria.

### Graceful degradation

When CDE Profile fields are missing, the Streamlit analyzer displays which sub-scores will use defaults and what those defaults are — so you can see exactly what data gaps are costing you points.

---

## What It Does

- **Pipeline ingestion** — Load from CSV or v1.1 xlsx template; validates all required fields
- **NMTC eligibility enrichment** — Census tract lookup, distress level classification (deep / severe / LIC), opportunity zone and native area flags
- **Distress concentration analysis** — Deep/severe QEI percentage vs. CDFI Fund competitive thresholds (target: ≥75%)
- **Geographic diversity scoring** — State count, HHI concentration index, urban/rural split
- **Sector mix analysis** — Shannon entropy, dominant sector, high-priority sector alignment
- **Impact projection** — Jobs per $MM QEI benchmarked against historical winner distributions
- **CDFI Fund alignment scoring** — Business Strategy (0–50), Community Outcomes (0–50), Priority Points (0–10 bonus) against the published CY 2024-2025 review criteria; tier: Not Qualified / Highly Qualified / Top Tier
- **Quantified recommendations** — Specific, numbered improvement actions per dimension with estimated score impact
- **Pipeline optimizer** — Greedy + local-search selects the best project subset for your target budget
- **Output generation** — Word, Excel, PDF, and Markdown application drafts in one call
- **Geographic visualizations** — Publication-quality pipeline maps, radar charts, and benchmark plots at 300 DPI
- **CLI** — `nmtcapp init` / `nmtcapp analyze` for quick command-line workflows

> **Methodology note:** Alignment scores measure similarity to historical winner patterns — they are not win probabilities. The CDFI Fund does not publish rejected application data, so a true probability model cannot be built from public information alone.

---

## Sample Output Gallery

Sample output — Word, Excel, PDF and Markdown for a fictional CDE — is generated at
docs-build time and published at
[Sample Output](https://jaypatel1511.github.io/nmtc-application-builder/sample-output/).
It is deliberately **not** committed: the four files that used to live in
`examples/sample_output/` went stale and kept serving fabricated statistics that had
already been removed from the generator. Run `mkdocs build` to produce them locally.

The three example notebooks tell a complete story:

| Notebook | What it demonstrates |
|---|---|
| [01_quickstart.ipynb](examples/01_quickstart.ipynb) | End-to-end workflow in 10 minutes |
| [02_full_application_walkthrough.ipynb](examples/02_full_application_walkthrough.ipynb) | Complete document generation |
| [03_intelligence_and_optimization.ipynb](examples/03_intelligence_and_optimization.ipynb) | **16 → 90 → 96/100** — Not Qualified → Highly Qualified → Top Tier |

---

## Architecture

```
nmtc-application-builder/
├── nmtcapp/
│   ├── core/               Application · CDEProfile · Pipeline
│   ├── intelligence/       PipelineAnalyzer · WinProbabilityModel · RecommendationEngine
│   ├── optimizer/          PipelineOptimizer · CandidatePool · Objectives
│   ├── validation/         EligibilityCheck · CompletenessCheck · ReadinessScore
│   ├── integrations/       nmtc-mapper · nmtc-calc · cdfidata · impact-ledger
│   ├── visualization/      pipeline maps · distress heatmap · radar · alignment charts
│   ├── renderers/          Word · Excel · PDF · Markdown builders
│   ├── data/               historical awards · benchmark thresholds · schema
│   ├── templates/          pipeline_template.xlsx (v1.1) · pipeline_template.csv · cde_profile_template.yaml
│   └── cli.py              nmtcapp init / analyze / version
├── examples/               3 executed Jupyter notebooks + sample output
├── streamlit_app/          Interactive web demo (4 pages)
└── docs/                   MkDocs documentation site
```

### Built on the Open-Source CDFI Analytics Stack

This library integrates six companion libraries built for the CDFI space:

| Library | Role in this project |
|---|---|
| `nmtc-mapper` | Census tract geocoding and eligibility classification (deep / severe / LIC) |
| `nmtc-calc` | NMTC leveraged deal economics (QEI → NMTCs → investor equity) |
| `cdfidata` | CDFI Fund TLR/CLR/Awards ETL and dataset loader |
| `impact-ledger` | Portfolio-level impact tracking by sector |

---

## Use Cases

**CDE application teams** — Run `analyze()` on your pipeline weekly during application season. Watch your readiness score improve as you add projects and address recommendations. Generate the first draft of every section automatically.

**CDFI consultants** — Drop a client's pipeline CSV in and produce a competitive benchmark report in minutes. Show exactly where they stand vs. historical winners before committing to a full engagement.

**Researchers and policy analysts** — Query the embedded CY2020–2024 CDFI Fund award statistics. Study what differentiates winning applications across distress concentration, geographic reach, and impact intensity.

**CDEs evaluating pipeline strategy** — Use the optimizer to understand what subset of your project pipeline maximizes competitive alignment given a target allocation amount and diversity constraints.

---

## Limitations & Honest Disclosures

- **Not a win probability model.** Alignment score ≠ probability of receiving an allocation. The CDFI Fund does not publish rejected application data, so a calibrated probability model cannot be built from public information alone.
- **Historical patterns, not current NOFA.** Benchmarks derive from CY2020–2024 award data. CDFI Fund priorities shift — always check the current NOFA for updated criteria.
- **Approximate geographic data.** Pipeline maps use state centroids, not actual project addresses. Eligibility enrichment uses `nmtc-mapper` (live CDFI Fund data only — see *Degraded mode* below; there is no offline fallback).
- **Not a substitute for expert review.** Always have a qualified CDFI practitioner or attorney review application materials before submission.
- **No investor or underwriting analysis.** This library covers competitive positioning, not deal structuring, investor sourcing, or legal compliance.

---

## Degraded mode & partial scores

Eligibility enrichment uses live CDFI Fund data via `nmtc-mapper`. As of 1.1.5 there
is **no offline fallback** — if that data cannot be loaded, the run degrades
explicitly instead of substituting anything:

- The pipeline is marked `eligibility_data_status = "unavailable"` (the underlying
  error is kept in `eligibility_data_error`), and eligibility, distress, and census
  tract fields stay `None` — **unverified, not ineligible**.
- Every affected surface — analyzer summaries, readiness and alignment scores, the
  Streamlit pages, and generated Word/PDF/Excel drafts — shows an "eligibility data
  unavailable" banner at the top of the section. The app keeps working; it never
  hard-blocks.
- A project whose address cannot be geocoded gets `geocode_success = False` and a
  "location could not be verified" marker. It keeps no tract and is never counted
  as eligible *or* ineligible.

**What a "partial" score means:** the score was computed *without* the
eligibility-dependent components, and the label says exactly which — e.g. a readiness
score of "72.4/100 (PARTIAL) — score computed without eligibility verification (4 of
6 components)". Partial scores are comparable only to other partial scores, and no
CDFI Fund tier is assigned from them. Restore data access (network + `nmtc-mapper`
≥ 0.3.4) and re-run the analysis to get a full score.

---

## Documentation

Full documentation at **[jaypatel1511.github.io/nmtc-application-builder](https://jaypatel1511.github.io/nmtc-application-builder/)**

- [Installation guide](https://jaypatel1511.github.io/nmtc-application-builder/installation/)
- [60-second quickstart](https://jaypatel1511.github.io/nmtc-application-builder/quickstart/)
- [Pipeline analysis workflow](https://jaypatel1511.github.io/nmtc-application-builder/workflow/pipeline-analysis/)
- [Win alignment scoring & methodology](https://jaypatel1511.github.io/nmtc-application-builder/workflow/win-alignment/)
- [Full API reference](https://jaypatel1511.github.io/nmtc-application-builder/reference/api/)
- [Honest limitations](https://jaypatel1511.github.io/nmtc-application-builder/about/limitations/)

---

## Release process

Use `scripts/release.sh` — never upload manually. The script enforces the full pipeline atomically:

```bash
bash scripts/release.sh
```

What it does, in order:
1. **Runs the test suite** (`pytest -m "not wheel"`) — aborts on any failure
2. **Clean build** — deletes `dist/`, `build/`, and egg-info, then runs `python -m build` to produce both wheel and sdist
3. **`twine check`** — validates metadata; aborts if malformed
4. **`twine upload --verbose`** — uploads to PyPI; aborts on non-zero exit
5. **Polls PyPI** (`pip index versions`) until the new version appears (60s timeout) — this is the gate that catches silent upload failures
6. **Updates `streamlit_app/requirements.txt`** and commits — only after PyPI confirms the version is live

Before running: bump `version` in `pyproject.toml`. The script reads the version from there automatically.

---

## Contributing

Contributions welcome — bug fixes, additional data sources, visualization improvements, and documentation all help.

```bash
git clone https://github.com/Jaypatel1511/nmtc-application-builder.git
cd nmtc-application-builder
pip install -e ".[dev]"
PYTHONPATH=. pytest tests/ -v          # 544 tests, should all pass
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on pull requests, code style, and issue reporting.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built by [Jay Patel](https://github.com/Jaypatel1511) as part of an open-source CDFI analytics portfolio. Not affiliated with the CDFI Fund or the US Treasury.*

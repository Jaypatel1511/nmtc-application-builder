# nmtc-application-builder

**Weeks 1–2 of 4 — Foundation, Pipeline Intelligence & Output Renderers**

The flagship library in a 17-library community development finance portfolio. Purpose-built for CDEs preparing New Markets Tax Credit (NMTC) allocation applications to the CDFI Fund.

---

## What This Is

`nmtc-application-builder` gives CDEs a programmatic intelligence layer for NMTC application preparation. A single `generate()` call produces a complete, competition-ready application package:

- Load and validate your project pipeline from CSV or Python
- Enrich each project with NMTC eligibility, distress level, and census tract data
- Get comprehensive analytics: distress concentration, geographic diversity, sector mix, impact projections
- Score your application readiness (0–100) against historical winning application patterns
- Generate **Word**, **Excel**, **PDF**, and **Markdown** drafts — automatically

---

## Quick Start

```python
from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline

# 1. Define your CDE
cde = CDEProfile.sample()          # or CDEProfile.from_yaml("my_cde.yaml")

# 2. Load your pipeline
pipeline = Pipeline.sample(n=20)   # or Pipeline.from_csv("pipeline.csv")

# 3. Create and analyze the application
app = Application(cde=cde, requested_allocation=65_000_000)
app.add_pipeline(pipeline)
analysis = app.analyze()
analysis.summary()

# 4. Generate the full document package
paths = app.generate("./drafts/")
# → ./drafts/CDE-2018-0117_application.md    (31 KB)
# → ./drafts/CDE-2018-0117_application.docx  (51 KB)
# → ./drafts/CDE-2018-0117_application.xlsx  (24 KB)
# → ./drafts/CDE-2018-0117_application.pdf   (37 KB)
```

### Sample Analysis Output

```
======================================================================
  NMTC APPLICATION ANALYSIS
  CDE:   Heartland Impact CDE, LLC
  Round: CY2025  |  Requested: $65,000,000
======================================================================
── Distress Concentration ─────────────────────────────
  Deep/Severe:     87%  (✓ target)
  Native Area:     10%
  Historical Rank: top_quartile
── Geographic Diversity ────────────────────────────────
  States:          20
  HHI:             549  (diverse)
── Impact Projections ──────────────────────────────────
  Jobs Created:    864
  Jobs/$MM QEI:    7.0
  Benchmark:       average
============================================================
  APPLICATION READINESS SCORE: 86.6/100  [A]
  [█████████████████████████░░░░░] 86.6%
============================================================
```

---

## Installation

```bash
pip install nmtc-application-builder   # coming Week 4
```

For development:

```bash
git clone https://github.com/Jaypatel1511/nmtc-application-builder.git
cd nmtc-application-builder
pip install -e ".[dev]"
```

Optional output dependencies (included in `[dev]` extra):

```bash
pip install "nmtc-application-builder[output]"   # Word + Excel + PDF
pip install "nmtc-application-builder[word]"      # python-docx only
pip install "nmtc-application-builder[excel]"     # openpyxl only
pip install "nmtc-application-builder[pdf]"       # reportlab only
```

---

## Output Formats

Each output includes: cover page, executive summary, readiness score callout, Sections A–E, and Appendices A–F (pipeline, distress, geographic, impact, track record, methodology).

| Format | Class | Contents |
|---|---|---|
| **Markdown** | `MarkdownApplicationBuilder` | Full narrative draft, version-control friendly |
| **Word** | `WordApplicationBuilder` | Professional `.docx` with tables, shading, footers |
| **Excel** | `ExcelApplicationBuilder` | 7-sheet workbook with frozen panes, conditional formatting, chart |
| **PDF** | `PDFApplicationBuilder` | Board-ready PDF via ReportLab |

### Word Document

The `.docx` output includes:
- Dark blue banner cover page with gold accent
- Details table (round, allocation, date, readiness grade)
- Key metrics table and readiness score callout
- All five application sections (A–E) with narrative and tables
- Six appendices including pipeline detail and distress documentation
- Page numbers in footer with CDE name and confidentiality notice

### Excel Workbook (7 sheets)

| Sheet | Contents |
|---|---|
| Summary Dashboard | Key metrics, readiness score breakdown, bar chart |
| Pipeline Detail | Full pipeline with deal economics; conditional formatting by distress level |
| Distress Documentation | ACS data and distress classification per project |
| Geographic Targeting | State-level QEI breakdown with color-scale formatting |
| Impact Projections | Jobs, units, cost-per-job per project |
| Investor Commitments | Scaffold for Section D investor lineup |
| Track Record | Prior award deployment history |

---

## Section Generators

Sections A–E are generated from structured content dicts — renderer-agnostic so the same content goes to Word, Markdown, and PDF:

```python
from nmtcapp.sections import ALL_SECTIONS

for section_gen in ALL_SECTIONS:
    content = section_gen.generate_content(app, analysis)
    # content["subsections"] → list of {"heading", "body", "type"}
    
    md = section_gen.generate_markdown(app, analysis)
    section_gen.generate_word(doc, app, analysis)
```

| Section | Title | Subsections |
|---|---|---|
| A | Business Strategy | Investment thesis, target markets, pipeline overview, deployment strategy |
| B | Community Outcomes | Impact narrative, distress commitments, HMDA community need |
| C | Management Capacity | Organizational history, governance, underwriting process |
| D | Capitalization Strategy | Deal economics, investor narrative, leverage structure |
| E | Prior Awards | Deployment history (skipped if no prior awards) |

---

## Architecture

```
nmtcapp/
├── core/
│   ├── application.py     # Application — master entry point + generate()
│   ├── cde.py             # CDEProfile dataclass
│   └── pipeline.py        # Pipeline + PipelineProject
├── intelligence/
│   ├── pipeline_analyzer.py
│   ├── distress_analysis.py
│   ├── geographic_analysis.py
│   ├── sector_analysis.py
│   └── impact_aggregator.py
├── validation/
│   ├── eligibility_check.py
│   ├── completeness_check.py
│   ├── consistency_check.py
│   └── readiness_score.py     # 0–100 weighted readiness score
├── sections/
│   ├── base.py                # SectionGenerator ABC
│   ├── section_a_business.py
│   ├── section_b_outcomes.py
│   ├── section_c_management.py
│   ├── section_d_capitalization.py
│   └── section_e_prior_awards.py
├── tables/
│   ├── pipeline_table.py
│   ├── distress_table.py
│   ├── geographic_table.py
│   ├── impact_table.py
│   ├── investor_table.py
│   └── track_record_table.py
├── renderers/
│   ├── styles.py              # Shared color + typography constants
│   ├── markdown_builder.py
│   ├── word_builder.py
│   ├── excel_builder.py
│   └── pdf_builder.py
├── integrations/
│   ├── nmtc_mapper_adapter.py
│   ├── nmtc_calc_adapter.py
│   ├── hmda_adapter.py
│   ├── cdfidata_adapter.py
│   └── impact_adapter.py
└── data/
    └── schema.py              # Constants, thresholds, ValidationResult
```

---

## Ecosystem Integration

| Package | Purpose | Used For |
|---|---|---|
| `nmtc-mapper` | NMTC eligibility + geocoding | Enriching pipeline census tract data |
| `nmtc-calc` | Deal economics modeling | Computing QEI, NMTCs, investor equity |
| `hmda-analyzer` | HMDA lending disparity | Community need documentation |
| `cdfidata` | CDFI Fund TLR/Awards ETL | CDE track record pull |
| `impact-ledger` | Impact portfolio tracking | Portfolio-level impact reporting |

All adapters include offline fallbacks — tests run without internet access.

---

## Readiness Score

The 0–100 readiness score weights six components against CDFI Fund scoring criteria:

| Component | Weight | What It Measures |
|---|---|---|
| Eligibility Quality | 25% | % of pipeline in LIC tracts |
| Distress Concentration | 25% | % of QEI in deep/severe distress tracts |
| Geographic Diversity | 15% | States served, HHI concentration |
| Impact Metrics | 20% | Jobs/units vs CDFI Fund historical benchmarks |
| Validation Pass Rate | 10% | % of validation checks passing |
| Completeness | 5% | Required fields populated |

**Competitive thresholds:** Deep/severe distress ≥ 75% of QEI → top-tier; ≥ 3 states → minimum geographic diversity.

---

## Running Tests

```bash
PYTHONPATH=. pytest tests/ -v
```

297 tests, all passing.

---

## Deliverables

### Week 1 ✓ — Foundation & Pipeline Intelligence
- [x] CDEProfile with YAML loading and sample data
- [x] Pipeline with CSV loading, 20-project sample, DataFrame export
- [x] PipelineAnalyzer orchestrating distress, geographic, sector, and impact modules
- [x] Eligibility, completeness, and consistency validation
- [x] 0–100 readiness score with grade and recommendations
- [x] Adapters for nmtc-mapper, nmtc-calc, hmda-analyzer, cdfidata, impact-ledger
- [x] 132 passing tests
- [x] `examples/01_quickstart.ipynb`

### Week 2 ✓ — Section Generators, Tables & Output Renderers
- [x] Section generators A–E (narrative, list, table subsection types)
- [x] Table builders: pipeline, distress, geographic, impact, investor, track record
- [x] Word output — professional `.docx` with cover page, sections, appendices, footer
- [x] Excel output — 7-sheet workbook with conditional formatting, frozen panes, chart
- [x] PDF output — board-ready PDF via ReportLab
- [x] Markdown output — version-control-friendly full draft
- [x] `Application.generate()` — one call produces all four formats
- [x] 297 passing tests (165 new)
- [x] `examples/02_full_application_walkthrough.ipynb`
- [x] Sample outputs in `examples/sample_output/`

---

## Roadmap

| Week | Deliverable |
|---|---|
| **Week 1** ✓ | Foundation + Pipeline Intelligence |
| **Week 2** ✓ | Section Generators + Output Renderers (Word/Excel/PDF/Markdown) |
| Week 3 | Win probability model + allocation optimizer |
| Week 4 | Visualizations, PyPI publish, final polish |

---

## License

MIT © Jay Patel

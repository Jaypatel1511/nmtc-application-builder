# nmtc-application-builder

**Week 1 of 4 — Foundation & Pipeline Intelligence**

The flagship library in a 17-library community development finance portfolio. Purpose-built for CDEs preparing New Markets Tax Credit (NMTC) allocation applications to the CDFI Fund.

---

## What This Is

`nmtc-application-builder` gives CDEs a programmatic intelligence layer for NMTC application preparation:

- Load and validate your project pipeline from CSV or Python
- Enrich each project with NMTC eligibility, distress level, and census tract data
- Get comprehensive analytics: distress concentration, geographic diversity, sector mix, impact projections
- Score your application readiness (0–100) against historical winning application patterns
- Validate completeness and consistency before submission

This is **Week 1** of a 4-week build. See the roadmap below for what's coming.

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

# 4. Review results
analysis.summary()
```

### Sample Output

```
======================================================================
  NMTC APPLICATION ANALYSIS
  CDE:   Heartland Impact CDE, LLC
  Round: CY2025  |  Requested: $65,000,000
  Analyzed: 2025-01-01T12:00:00
======================================================================
  ...

APPLICATION READINESS SCORE: 82.4/100  [B]
  [█████████████████████████░░░░░] 82.4%
  ...
  Strengths:
  + Strong deep/severe distress concentration
  + Good geographic diversity across multiple states
  ...
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

---

## Ecosystem Integration

This library integrates with 5 other published PyPI packages in the community development finance ecosystem:

| Package | Purpose | Used For |
|---|---|---|
| `nmtc-mapper` | NMTC eligibility + geocoding | Enriching pipeline census tract data |
| `nmtc-calc` | Deal economics modeling | Computing QEI, NMTCs, investor equity |
| `hmda-analyzer` | HMDA lending disparity | Community need documentation |
| `cdfidata` | CDFI Fund TLR/Awards ETL | CDE track record pull |
| `impact-ledger` | Impact portfolio tracking | Portfolio-level impact reporting |

All adapters include offline fallbacks — tests run without internet access.

---

## Architecture

```
nmtcapp/
├── core/
│   ├── application.py     # Application — master entry point
│   ├── cde.py             # CDEProfile dataclass
│   └── pipeline.py        # Pipeline + PipelineProject
├── intelligence/
│   ├── pipeline_analyzer.py   # Orchestrator
│   ├── distress_analysis.py   # Distress concentration
│   ├── geographic_analysis.py # Geographic diversity + HHI
│   ├── sector_analysis.py     # Sector mix + Shannon diversity
│   └── impact_aggregator.py   # Jobs, units, cost-per-job
├── validation/
│   ├── eligibility_check.py   # NMTC eligibility validation
│   ├── completeness_check.py  # Required field validation
│   ├── consistency_check.py   # Cross-field consistency
│   └── readiness_score.py     # 0–100 weighted readiness score
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

## Loading Your Pipeline

### From CSV

Create a CSV with these required columns:

```
project_id, project_name, qalicb_name, address, city, state,
sector, project_type, total_project_cost, qei_request, qlici_amount,
expected_jobs_created
```

Optional columns: `expected_jobs_retained`, `expected_units_built`, `expected_sq_ft`,
`closing_target_date`, `construction_start`, `operations_start`

```python
pipeline = Pipeline.from_csv("my_pipeline.csv")
```

### From Python

```python
from nmtcapp.core.pipeline import PipelineProject

project = PipelineProject(
    project_id="PRJ-001",
    project_name="Southside Health Center",
    qalicb_name="Southside HC QALICB, LLC",
    address="3400 S Michigan Ave",
    city="Chicago",
    state="IL",
    sector="healthcare",
    project_type="real_estate",
    total_project_cost=12_500_000,
    qei_request=8_500_000,
    qlici_amount=8_500_000,
    expected_jobs_created=52,
    expected_jobs_retained=18,
)
app.add_project(project)
```

---

## CDE Profile

```python
from nmtcapp.core.cde import CDEProfile

cde = CDEProfile(
    name="Midwest Impact CDE, LLC",
    cde_id="CDE-2019-0042",
    certification_date="2019-03-15",
    mission="Deploy NMTC capital in deep-distress Midwest communities",
    target_markets=["Illinois", "Ohio", "Michigan"],
    prior_awards=[
        {"year": 2021, "amount": 45_000_000, "deployment_status": "fully_deployed",
         "states": ["IL", "OH"]},
    ],
    contact={"name": "Jane Smith", "email": "jsmith@midwestimpact.org"},
    governance={"board_members": 7, "community_representatives": 3},
)

# Or load from YAML
cde = CDEProfile.from_yaml("cde_profile.yaml")
```

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

**Competitive thresholds** (from historical award data):
- Deep/severe distress ≥ 75% of QEI → top-tier applications
- ≥ 3 states → minimum geographic diversity

---

## Distress Levels

| Code | Definition |
|---|---|
| `deep` | Poverty >30% or unemployment >1.5× national avg |
| `severe` | LIC plus additional distress factors |
| `lic` | Low Income Community (AMI ≤80% or poverty ≥20%) |
| `ineligible` | Not NMTC eligible |

---

## Running Tests

```bash
PYTHONPATH=. pytest tests/ -v
```

132 tests, all passing.

---

## Week 1 Deliverables ✓

- [x] CDEProfile with YAML loading and sample data
- [x] Pipeline with CSV loading, 20-project sample, DataFrame export
- [x] PipelineAnalyzer orchestrating all intelligence modules
- [x] Distress, geographic, sector, and impact analysis
- [x] Eligibility, completeness, and consistency validation
- [x] 0–100 readiness score with grade and recommendations
- [x] Adapters for nmtc-mapper, nmtc-calc, hmda-analyzer, cdfidata, impact-ledger
- [x] 132 passing tests
- [x] examples/01_quickstart.ipynb

---

## Roadmap

| Week | Deliverable |
|---|---|
| **Week 1** ✓ | Foundation + Pipeline Intelligence |
| Week 2 | Word/Excel output — narrative sections, pro forma tables |
| Week 3 | Win probability model + allocation optimizer |
| Week 4 | Visualizations, PyPI publish, final polish |

---

## License

MIT © Jay Patel

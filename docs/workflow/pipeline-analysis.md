# Pipeline Analysis

The `analyze()` method is the central operation of NMTC Application Builder. It orchestrates five sequential steps, caches the result, and returns an `ApplicationAnalysis` object that feeds every downstream operation: scoring, recommendations, optimization, and output generation.

---

## What happens when you call analyze()

```python
analysis = app.analyze()
```

Internally, five steps run in sequence:

### Step 1: Eligibility enrichment (nmtc-mapper)

Every `PipelineProject` in the pipeline is passed through `enrich_pipeline_eligibility()`, which calls the `nmtc-mapper` library to look up the census tract for each project address and determine NMTC eligibility and distress level. After enrichment, each project has its `census_tract`, `is_nmtc_eligible`, `distress_level`, `is_native_area`, `is_high_migration_rural`, and `is_opportunity_zone` fields populated.

The four distress level codes:

| Code | Meaning |
|------|---------|
| `deep` | Deep Distress — poverty rate >30% or unemployment >1.5× national average |
| `severe` | Severe Distress — LIC with additional qualifying distress factors |
| `lic` | Low Income Community — AMI ≤80% or poverty rate ≥20% |
| `ineligible` | Not NMTC Eligible — does not meet LIC threshold |

Projects with pre-populated eligibility fields (as returned by `Pipeline.sample()`) skip the API call.

### Step 2: Deal economics (nmtc-calc)

`compute_pipeline_economics()` calculates the NMTC deal economics for the full pipeline: total NMTCs generated (39% of QEI over 7 years), investor equity raised at the current market credit price (~$0.83/credit dollar), estimated CDE fees (2.5% of QEI), and QEI less CDE fees. These figures populate `deal_economics_summary` in the result.

!!! warning "`net_subsidy` is not a net subsidy"

    The `total_net_subsidy` key and the row it feeds were renamed in 1.2.1. The figure is QEI minus the CDE fee and includes the whole leverage loan, which is repaid or refinanced; a net subsidy is the benefit net of that loan. See [Output formats](output-formats.md) for the full note. The dictionary key is retained because 1.2.1 is a patch release.

### Step 3: Intelligence analyses

Four analyses run in parallel on the enriched pipeline:

- **Distress concentration** — what percentage of QEI is deployed into deep, severe, LIC, and ineligible tracts; native area and high-migration rural percentages; comparison against this tool's own **HOUSE** reference bands (there is no winner distribution — see below)
- **Geographic diversity** — states count, MSA count, a three-way Non-Metropolitan County split of QEI (non-metro / metropolitan / not determined), Herfindahl-Hirschman Index (HHI) for geographic concentration
- **Sector mix** — sectors represented, dominant sector, high-priority sector percentage (healthcare + affordable housing + education), sector diversity score
- **Impact aggregation** — total jobs created and retained, units built, square footage, and the jobs-per-million-QEI metric compared against this tool's own **HOUSE** impact band

### Step 4: Validation

Three validation checks run automatically:

- **Eligibility check** — confirms all projects have valid census tracts and eligibility determinations; flags ineligible projects
- **Completeness check** — verifies all required fields are populated on every project and the `CDEProfile`
- **Consistency check** — checks that `qei_request <= total_project_cost`, `qlici_amount <= qei_request`, and other internal consistency rules

### Step 5: Readiness score

`compute_readiness_score()` computes a weighted 0–100 score from six components with a letter grade (A–F):

| Component | Weight |
|-----------|--------|
| Eligibility quality | 25% |
| Distress concentration | 25% |
| Impact metrics | 20% |
| Geographic diversity | 15% |
| Validation pass rate | 10% |
| Completeness | 5% |

Grade thresholds: A ≥ 85, B ≥ 70, C ≥ 55, D ≥ 40, F below 40.

---

## PipelineProject fields

### Required fields (must be set at construction)

| Field | Type | Description |
|-------|------|-------------|
| `project_id` | `str` | Unique identifier (e.g. "PRJ-001") |
| `project_name` | `str` | Human-readable project name |
| `qalicb_name` | `str` | Legal name of the QALICB entity |
| `address` | `str` | Street address |
| `city` | `str` | City |
| `state` | `str` | Two-letter state abbreviation |
| `sector` | `str` | One of the valid sectors (see below) |
| `project_type` | `str` | `real_estate`, `operating_business`, or `mixed_use` |
| `total_project_cost` | `float` | Total project cost in dollars (must be > 0) |
| `qei_request` | `float` | Qualified Equity Investment request in dollars (must be > 0) |
| `qlici_amount` | `float` | QLICI amount in dollars (must be > 0) |
| `expected_jobs_created` | `int` | FTE jobs expected to be created (must be ≥ 0) |

### Optional fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `expected_jobs_retained` | `int` | 0 | FTE jobs expected to be retained |
| `expected_units_built` | `int \| None` | None | Affordable housing units (if applicable) |
| `expected_sq_ft` | `float \| None` | None | Gross square footage |
| `closing_target_date` | `str \| None` | None | Target closing date (ISO format: "2025-09-30") |
| `construction_start` | `str \| None` | None | Construction start date |
| `operations_start` | `str \| None` | None | Operations start date |

### Enrichment fields (populated by analyze())

These begin as `None` and are set by the eligibility enrichment step. Do not set them manually unless using pre-enriched data (as `Pipeline.sample()` does).

| Field | Type | Description |
|-------|------|-------------|
| `census_tract` | `str \| None` | 11-digit FIPS census tract ID |
| `is_nmtc_eligible` | `bool \| None` | True if tract qualifies as LIC or deeper |
| `distress_level` | `str \| None` | `deep`, `severe`, `lic`, or `ineligible` |
| `is_native_area` | `bool \| None` | True if BIA-designated Native American area |
| `is_high_migration_rural` | `bool \| None` | True if USDA high-migration rural county |
| `is_opportunity_zone` | `bool \| None` | True if Opportunity Zone designation applies |

### Valid sector values

```python
VALID_SECTORS = [
    "healthcare",
    "affordable_housing",
    "education",
    "small_business",
    "mixed_use",
    "community_facility",
    "clean_energy",
    "other",
]
```

CDFI Fund priority sectors are `healthcare`, `affordable_housing`, and `education`. Projects in these sectors score highest on the sector diversity dimension.

---

## Loading from CSV

The `Pipeline.from_csv()` class method reads a CSV file with columns matching `PipelineProject` field names. Required columns are the 12 required fields above. Optional columns are read when present and default to `None` when absent.

```python
pipeline = Pipeline.from_csv("my_pipeline.csv")
```

A template CSV is available at `nmtcapp/templates/pipeline_template.csv` in the repository. A sample strong pipeline is at `nmtcapp/templates/pipeline_sample_strong.csv`.

**Example CSV structure (abbreviated):**

```csv
project_id,project_name,qalicb_name,address,city,state,sector,project_type,total_project_cost,qei_request,qlici_amount,expected_jobs_created
PRJ-001,Southside Health Center,Southside HC QALICB LLC,3400 S Michigan Ave,Chicago,IL,healthcare,real_estate,12500000,8500000,8500000,52
PRJ-002,East Houston Charter Academy,East Houston Academy QALICB LLC,5200 Lawndale St,Houston,TX,education,real_estate,9800000,7000000,7000000,38
```

---

## Building programmatically

```python
from nmtcapp.core.pipeline import Pipeline, PipelineProject

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
    expected_sq_ft=24_000,
    closing_target_date="2025-09-30",
)

pipeline = Pipeline(projects=[project])
# or:
pipeline = Pipeline()
pipeline.add(project)
```

---

## Reading the analysis output

```python
analysis = app.analyze()

# High-level summary to terminal
analysis.summary()

# Access individual analyses
print(analysis.distress_analysis["pct_deep_or_severe"])   # e.g. 0.82
print(analysis.geographic_analysis["states_count"])        # e.g. 10
print(analysis.sector_analysis["sectors_represented"])     # e.g. 6
print(analysis.impact_summary["jobs_per_million_qei"])    # e.g. 14.2

# Readiness score
rs = analysis.readiness_score
print(f"Grade: {rs.grade}, Score: {rs.overall_score}")    # e.g. Grade: B, Score: 74.5

# Serialize to dict (JSON-safe)
import json
print(json.dumps(analysis.to_dict(), indent=2))
```

### Distress analysis keys

```python
d = analysis.distress_analysis
d["pct_deep_or_severe"]       # float — fraction of QEI in deep + severe tracts
d["pct_lic"]                  # float — fraction in standard LIC tracts
d["pct_non_lic"]              # float — fraction in non-LIC (ineligible) tracts
d["pct_native_area"]          # float — fraction in Native American areas
d["meets_target_threshold"]   # bool — True if pct_deep_or_severe >= 0.75
```

`vs_historical_winners` is **not** a key and must not be added back. It was
removed in 1.2.0 and `tests/intelligence/test_distress_analysis.py` asserts it
never returns: it ranked a CDE against a winner distribution that was never
loaded and is not published, off a hardcoded ladder that disagreed with
`WINNER_PATTERN_THRESHOLDS` in the same package. See
`nmtcapp/intelligence/distress_analysis.py` for the full ruling. This line
documented it for four releases after the deletion — 1.2.0 through 1.4.0 — and
`tests/test_documented_keys.py` now fails on that class rather than waiting for
someone to notice.

### Geographic analysis keys

```python
g = analysis.geographic_analysis
g["states_count"]                  # int — number of distinct states
g["msa_count"]                     # int — number of MSAs represented
g["non_metro_pct"]                 # float — share of QEI in verified Non-Metropolitan Counties
g["metro_pct"]                     # float — share of QEI in verified Metropolitan Counties
g["metro_undetermined_pct"]        # float — share of QEI whose county status is UNKNOWN
                                   #         (not geocoded, or tract absent from the Fund
                                   #         table). NOT metropolitan. The three sum to 1.0.
g["metro_status_qei"]              # dict  — the three buckets in dollars, plus project counts
g["hhi"]                           # float — Herfindahl-Hirschman Index (lower = more diverse)
g["geographic_concentration_label"] # str — "highly_concentrated" | "moderate" | "diverse"
g["state_breakdown"]               # dict — per-state QEI and project counts
```

### Readiness score interpretation

**The readiness grade has no external referent.** It is this tool's own weighted
composite over six components this tool chose, with weights this tool assigned
(`READINESS_SCORING_WEIGHTS`). It is not calibrated against award data, the CDFI
Fund publishes no such score or weighting, and **no winner population is
involved in it at any point.** A grade is a restatement of the composite, not a
finding about the application.

The cut points below are `schema.GRADE_THRESHOLDS` — this tool's own bands, not
a CDFI Fund threshold.

| Grade | Score Range | What it means |
|-------|-------------|---------------|
| A | 85–100 | Scores in this tool's top band across its six components |
| B | 70–84 | Scores in this tool's second band |
| C | 55–69 | Scores in this tool's middle band |
| D | 40–54 | Scores in this tool's fourth band; one or more components are low |
| F | 0–39 | Scores in this tool's lowest band |

**These rows previously read as claims about the applicant pool** — "Below
typical winner patterns" for C and "Application not viable in current form" for
F, with "Submission-ready" and "Competitive" above them. Every one of those was
a winner-population claim attached to a score that has never been compared to a
winner population, and this package's attribution registry rules every `WINNER_*`
key HOUSE and unsourced. The same error was deleted from `_assess_vs_winners`,
`sector_analysis` and `_benchmark_label`; it survived here, in the documentation,
after all three code deletions.

"Not viable" was the sharper half. A CDE reading that about its own pipeline may
not file at all, and this tool has no basis on which to tell anyone that.

**Do not read a low grade as a reason not to apply.** Whether an application is
worth filing is a judgement this tool cannot make. For what the CDFI Fund
actually scores, use the alignment score, which is assessed against the
published CY 2024-2025 Review Process criteria — not against winner patterns —
and read the recommendations, each of which cites the Review Process section
behind it.

---

## Caching behavior

`analyze()` caches its result after the first call. Calling `analyze()` again on the same `Application` object returns the cached result immediately. The cache is invalidated if you call `add_pipeline()` or `add_project()` after the initial analysis.

```python
analysis1 = app.analyze()    # runs full analysis
analysis2 = app.analyze()    # returns cached result
assert analysis1 is analysis2  # True — same object
```

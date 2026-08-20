# API Reference

---

## Application

`nmtcapp.core.application.Application`

Master orchestration class — the single entry point for all NMTC application functionality. Combines a `CDEProfile` and a project `Pipeline`, then produces intelligence reports, scores, recommendations, optimizations, and document outputs.

### `__init__`

```python
Application(
    cde: CDEProfile,
    requested_allocation: float,
    application_round: str = "CY2025",
)
```

**Parameters:**

- `cde` — A `CDEProfile` instance. Required.
- `requested_allocation` — Requested NMTC allocation in dollars (e.g., `65_000_000`). Must be > 0.
- `application_round` — Application round label used for display and acceptance rate lookup. Default: `"CY2025"`.

**Raises:** `TypeError` if `cde` is not a `CDEProfile`. `ValueError` if `requested_allocation <= 0`.

---

### `add_pipeline`

```python
add_pipeline(pipeline: Pipeline) -> None
```

Set the project pipeline, replacing any existing pipeline. Clears the analysis cache.

**Parameters:**
- `pipeline` — A `Pipeline` instance.

---

### `add_project`

```python
add_project(project: PipelineProject) -> None
```

Add a single project to the pipeline. Creates a new `Pipeline` if none exists. Clears the analysis cache.

---

### `analyze`

```python
analyze() -> ApplicationAnalysis
```

Run comprehensive analysis and return an `ApplicationAnalysis`. Orchestrates eligibility enrichment, deal economics, distress/geographic/sector/impact analyses, validation, and readiness scoring. Results are cached — calling `analyze()` multiple times returns the same object unless the pipeline is modified.

**Raises:** `ValueError` if no pipeline has been added. `RuntimeError` if any analysis step fails.

---

### `score_win_probability`

```python
score_win_probability() -> WinProbabilityScore
```

Score this application's alignment with historical NMTC winner patterns (CY2020–CY2024). Returns a composite 0–100 alignment score and per-dimension breakdown. **Not a win probability** — see the methodology disclosure in `WinProbabilityScore.methodology_disclosure`.

---

### `benchmark`

```python
benchmark() -> BenchmarkComparison
```

Compare this application against historical NMTC winner benchmarks. Returns a `BenchmarkComparison` with per-metric tier classifications and percentile positions.

---

### `recommendations`

```python
recommendations() -> RecommendationSet
```

Generate actionable, quantified recommendations for improving competitiveness. Runs benchmarking and win scoring internally. Returns a `RecommendationSet` sorted by priority (critical → high → medium).

---

### `optimize_pipeline`

```python
optimize_pipeline(
    constraints: OptimizationConstraints = None,
    max_iterations: int = 500,
) -> OptimizationResult
```

Optimize the pipeline to maximize alignment with historical winner patterns. Uses greedy construction + swap-based local search. Always returns a result — infeasible constraints are reported in `OptimizationResult.infeasibility_reason`.

**Parameters:**
- `constraints` — `OptimizationConstraints` instance. If `None`, runs unconstrained (all projects eligible, no budget cap).
- `max_iterations` — Maximum local-search swap iterations. Default: 500.

---

### `generate`

```python
generate(
    output_dir: str = "./drafts",
    formats: list = None,
) -> dict
```

Generate the full NMTC application document package. Runs `analyze()` internally (using cache). Creates `output_dir` if it does not exist.

**Parameters:**
- `output_dir` — Destination directory for generated files. Default: `"./drafts"`.
- `formats` — List of formats to generate. Defaults to `["markdown", "word", "excel", "pdf"]`. Formats with missing dependencies are skipped with a warning.

**Returns:** Dict mapping format name (`"markdown"`, `"word"`, `"excel"`, `"pdf"`) to the generated file path.

---

## ApplicationAnalysis

`nmtcapp.core.application.ApplicationAnalysis`

Dataclass returned by `Application.analyze()`. All fields are populated by the analysis orchestrator.

| Field | Type | Description |
|-------|------|-------------|
| `cde_name` | `str` | CDE name from the profile |
| `requested_allocation` | `float` | Allocation requested in dollars |
| `application_round` | `str` | Round label (e.g. "CY2025") |
| `pipeline_result` | `PipelineAnalysisResult` | Full pipeline analysis result |
| `distress_analysis` | `dict` | Distress concentration breakdown |
| `geographic_analysis` | `dict` | Geographic diversity metrics |
| `sector_analysis` | `dict` | Sector mix breakdown |
| `impact_summary` | `dict` | Aggregate impact metrics |
| `deal_economics` | `dict` | NMTC deal economics summary |
| `validation_results` | `list[ValidationResult]` | Eligibility, completeness, consistency |
| `readiness_score` | `ReadinessScore` | Weighted readiness score and grade |
| `analyzed_at` | `str` | ISO timestamp of analysis |

**Methods:**
- `summary() -> None` — Print a human-readable multi-section summary
- `to_dict() -> dict` — Serialize to a JSON-safe dictionary

---

## Pipeline

`nmtcapp.core.pipeline.Pipeline`

Container for a CDE's pipeline of NMTC candidate projects.

### `__init__`

```python
Pipeline(projects: list[PipelineProject] = None)
```

### `add`

```python
add(project: PipelineProject) -> None
```

Append a single project to the pipeline.

### `from_csv`

```python
@classmethod
from_csv(path: str) -> Pipeline
```

Load a pipeline from a CSV file. Required columns match `PipelineProject` required fields. Optional columns are read when present. Raises `FileNotFoundError` if the file does not exist; `ValueError` if required columns are missing or a row cannot be parsed.

### `sample`

```python
@classmethod
sample(n: int = 20) -> Pipeline
```

Return a realistic sample pipeline of `n` projects (max 20) for testing and demos. All eligibility fields are pre-populated — no API calls made.

### `to_dataframe`

```python
to_dataframe() -> pandas.DataFrame
```

Convert the pipeline to a pandas DataFrame with one row per project and columns matching `PipelineProject` field names.

**Also supports:** `len(pipeline)`, `for project in pipeline`, `repr(pipeline)` (shows project count and total QEI).

---

## PipelineProject

`nmtcapp.core.pipeline.PipelineProject`

Dataclass representing a single QALICB project.

### Required fields

| Field | Type | Validation |
|-------|------|------------|
| `project_id` | `str` | Non-empty |
| `project_name` | `str` | Non-empty |
| `qalicb_name` | `str` | Non-empty |
| `address` | `str` | Non-empty |
| `city` | `str` | Non-empty |
| `state` | `str` | Two-letter abbreviation |
| `sector` | `str` | Must be in `VALID_SECTORS` (warning if not) |
| `project_type` | `str` | `"real_estate"`, `"operating_business"`, or `"mixed_use"` |
| `total_project_cost` | `float` | Must be > 0 |
| `qei_request` | `float` | Must be > 0 |
| `qlici_amount` | `float` | Must be > 0 |
| `expected_jobs_created` | `int` | Must be ≥ 0 |

### Optional fields

| Field | Type | Default |
|-------|------|---------|
| `expected_jobs_retained` | `int` | 0 |
| `expected_units_built` | `int \| None` | None |
| `expected_sq_ft` | `float \| None` | None |
| `closing_target_date` | `str \| None` | None |
| `construction_start` | `str \| None` | None |
| `operations_start` | `str \| None` | None |

### Enrichment fields (set by analyze())

| Field | Type |
|-------|------|
| `census_tract` | `str \| None` |
| `is_nmtc_eligible` | `bool \| None` |
| `distress_level` | `str \| None` — `"deep"`, `"severe"`, `"lic"`, or `"ineligible"` |
| `is_native_area` | `bool \| None` |
| `is_high_migration_rural` | `bool \| None` |
| `is_opportunity_zone` | `bool \| None` |

### Properties

- `full_address: str` — `"{address}, {city}, {state}"`
- `is_enriched: bool` — `True` if `is_nmtc_eligible` is not None
- `is_deep_distress: bool` — `True` if `distress_level` is `"deep"` or `"severe"`

### Methods

- `to_dict() -> dict` — Serialize all fields to a JSON-safe dictionary

---

## CDEProfile

`nmtcapp.core.cde.CDEProfile`

Dataclass representing a Community Development Entity.

### `__init__`

```python
CDEProfile(
    name: str,
    cde_id: str,
    certification_date: str,
    mission: str,
    target_markets: list[str],
    prior_awards: list[dict],
    contact: dict,
    governance: dict,
    website: str = None,
)
```

### `from_yaml`

```python
@classmethod
from_yaml(path: str) -> CDEProfile
```

Load a profile from a YAML file. Raises `FileNotFoundError` if the file does not exist; `ValueError` if required fields are missing.

Required YAML keys: `name`, `cde_id`, `certification_date`, `mission`, `target_markets`, `prior_awards`, `contact`, `governance`.

### `sample`

```python
@classmethod
sample() -> CDEProfile
```

Return a realistic sample CDE profile (Riverbend Community Capital CDE, LLC) for testing and demos.

### `total_prior_allocation`

```python
total_prior_allocation() -> float
```

Sum of all prior award amounts in dollars.

### `to_dict`

```python
to_dict() -> dict
```

Serialize to a JSON-safe dictionary including computed `total_prior_allocation`.

---

## OptimizationConstraints

`nmtcapp.optimizer.constraints.OptimizationConstraints`

Dataclass defining constraints for the pipeline optimizer.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `min_total_qei` | `float` | 0.0 | Minimum total QEI in selected set |
| `max_total_qei` | `float` | inf | Maximum total QEI (set to requested allocation) |
| `min_projects` | `int` | 1 | Minimum projects to include |
| `max_projects` | `int` | 9999 | Maximum projects to include |
| `required_sectors` | `list[str]` | `[]` | Sectors requiring at least one project |
| `excluded_states` | `list[str]` | `[]` | States to exclude from selection |
| `min_distress_pct` | `float` | 0.0 | Minimum fraction of QEI in deep/severe tracts |
| `min_states` | `int` | 1 | Minimum distinct states required |
| `max_single_sector_pct` | `float` | 1.0 | Maximum QEI fraction for any one sector |
| `min_eligibility_pct` | `float` | 0.0 | Minimum NMTC-eligible project fraction |

### `is_feasible`

```python
is_feasible(projects: list[PipelineProject]) -> tuple[bool, str]
```

Check whether a candidate project list satisfies all constraints. Returns `(True, "")` if satisfied, or `(False, reason)` describing the first violated constraint.

---

## WinProbabilityScore

`nmtcapp.intelligence.win_probability.WinProbabilityScore`

Returned by `Application.score_win_probability()`.

| Field | Type | Description |
|-------|------|-------------|
| `composite_score` | `float` | 0–100 alignment score |
| `dimensional_scores` | `dict` | Per-dimension scores (0–100 each) |
| `acceptance_rate_baseline` | `float` | Historical acceptance rate (e.g., 0.345) |
| `competitive_tier` | `str` | `"strong"`, `"competitive"`, `"marginal"`, or `"weak"` |
| `peer_comparison` | `str` | Narrative assessment |
| `methodology_disclosure` | `str` | Always-present framing disclaimer |

**Methods:** `summary() -> str`, `to_dict() -> dict`

**Dimensional score keys:** `"distress_concentration"`, `"geographic_diversity"`, `"impact_intensity"`, `"sector_diversity"`, `"pipeline_quality"`

---

## RecommendationSet and Recommendation

`nmtcapp.intelligence.recommendations.RecommendationSet`

Returned by `Application.recommendations()`.

| Field | Type | Description |
|-------|------|-------------|
| `recommendations` | `list[Recommendation]` | All recommendations, sorted by priority |
| `overall_assessment` | `str` | High-level narrative summary |
| `quick_wins` | `list[Recommendation]` | Medium-priority recommendations |
| `strategic_changes` | `list[Recommendation]` | Critical + high priority recommendations |

**Methods:** `summary() -> str`, `to_dict() -> dict`

`Recommendation` fields:

| Field | Type | Description |
|-------|------|-------------|
| `category` | `str` | `"distress"`, `"geographic"`, `"impact"`, `"sector"`, `"pipeline"` |
| `priority` | `str` | `"critical"`, `"high"`, `"medium"` |
| `finding` | `str` | What the analysis found |
| `action` | `str` | Specific action to take |
| `expected_impact` | `str` | Qualitative outcome |
| `quantified_improvement` | `str` | Numeric estimate of score/metric change |

---

## OptimizationResult

`nmtcapp.optimizer.pipeline_optimizer.OptimizationResult`

Returned by `Application.optimize_pipeline()`.

| Field | Type | Description |
|-------|------|-------------|
| `selected_projects` | `list[PipelineProject]` | Projects in the optimized subset |
| `objective_score` | `float` | Composite alignment score [0.0–1.0] |
| `alignment_score_before` | `float` | Score of full pipeline [0.0–1.0] |
| `alignment_score_after` | `float` | Score of optimized subset [0.0–1.0] |
| `constraints_satisfied` | `bool` | True if all constraints were satisfied |
| `infeasibility_reason` | `str` | Empty if feasible; describes violation otherwise |
| `dimensional_improvements` | `dict[str, float]` | Per-dimension score delta |
| `iterations` | `int` | Accepted swap count in local search |
| `methodology_note` | `str` | Always-present disclosure about the objective function |

**Methods:** `summary() -> str`, `to_dict() -> dict`

# Changelog

All notable changes to `nmtc-application-builder` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.4] — 2026-06-22

Release-infrastructure release. No functional or behavioral changes to the application.

### Added
- CI workflow (`.github/workflows/ci.yml`): runs the test suite on push/PR across Python 3.9–3.12.
- Release workflow (`.github/workflows/release.yml`): tag-triggered, builds wheel + sdist,
  tests the built wheel in a clean venv across 3.9–3.12, and publishes to PyPI via OIDC
  Trusted Publisher (PEP 740 attestations). All actions SHA-pinned; a tomllib guard fails
  the release if the git tag and pyproject version disagree.

### Changed
- `scripts/release.sh` no longer uploads to PyPI; publishing is CI-only. It now runs a
  local pre-flight (tests + build) only.

### Notes
- 1.1.4 is the first release published via CI from a tagged commit. Earlier releases 1.1.0
  and 1.1.3 were published pre-CI from a local working tree and have no corresponding git
  tag; that historical gap is accepted and not reconstructed. Tagging discipline starts here.

---

## [1.1.3] — 2026-05-14

Bug-fix release: xlsx upload, CSV encoding fallback, and column name alignment for the
Pipeline Analyzer. The v1.1 template download-and-upload round trip now works end-to-end.

### Fixed

**Critical — xlsx upload broken (Bug 1)**
- **`streamlit_app/pages/1_Pipeline_Analyzer.py` / `nmtcapp/core/upload_handler.py`** —
  Uploading the v1.1 `.xlsx` template failed with `"Pipeline CSV missing required columns"`
  because `pd.read_excel(..., sheet_name="Pipeline")` defaulted to `header=0`, reading
  the title row ("Pipeline — NMTC Application Builder v1.1 | One row per project") as
  the sole column header and leaving all 28 real columns unnamed.
  Fixed by reading the Pipeline sheet via openpyxl directly (same pattern as CDE Profile
  sheet), detecting the v1.1 3-row preamble (title / section banners / column headers)
  by checking cell A1, and using row 3 as the header row.

**Critical — column name drift between template and parser (Bug 3)**
- The upload handler contained a dead alias mapping that expected column names
  (`qei_millions`, `total_project_cost_millions`, `jobs_created`) that exist in neither
  the xlsx template ("QEI ($M)", "Total Cost ($M)", "Jobs Created") nor the CSV files
  (`qei_request`, `total_project_cost`, `expected_jobs_created`). This meant that even
  after fixing Bug 1, a template upload would still fail column-name validation.
  Fixed by adding `_XLSX_PIPELINE_COL_MAP` — a complete display-name → snake_case mapping
  for all 28 Pipeline sheet columns — and multiplying the `QEI ($M)` / `Total Cost ($M)`
  columns by 1,000,000 to convert from the template's human-readable millions to the
  parser's raw-dollar convention.

**High — CSV encoding failure on Windows-1252 files (Bug 2)**
- `pd.read_csv()` defaulted to UTF-8, causing `"'utf-8' codec can't decode byte 0xd2"`
  when users uploaded a CSV exported from Excel on Windows (default cp1252/Windows-1252
  encoding). Fixed with a `utf-8 → utf-8-sig → cp1252 → latin-1` fallback chain; a
  `logging.WARNING` is emitted when a non-UTF-8 encoding is used.

### Changed

- **`nmtcapp/core/upload_handler.py`** (new module) — `load_uploaded_pipeline()` and all
  its helpers (`_read_pipeline_sheet_from_wb`, `_read_csv_with_encoding_fallback`,
  `_parse_cde_profile_from_wb`, `_XLSX_PIPELINE_COL_MAP`) extracted from the Streamlit
  page into this importable module so they can be unit-tested without a Streamlit runtime.

- **Sidebar help text** — updated to reflect that the `.xlsx` template can be uploaded
  directly (no "save as CSV" step), and that CSV files must use the snake_case column
  names from `pipeline_template.csv` with raw dollar values (not millions). UTF-8 and
  Windows-1252 encodings are both noted as accepted.

- **Download button tooltip** — updated from "Edit, save as CSV, then upload" to
  "Fill in your projects, save, and upload the .xlsx directly."

### Added

**Tests**
- `tests/test_template_roundtrip.py` — 3 tests verifying the primary user journey:
  (1) loading the v1.1 template, adding 3 data rows, saving as xlsx bytes, passing to
  `load_uploaded_pipeline`, and asserting a `Pipeline` with 3 projects;
  (2) correct QEI / cost / jobs values after $M → raw-dollar conversion;
  (3) CDE Profile sheet parses to a non-empty dict without error.
- `tests/test_csv_encoding.py` — 5 tests verifying that cp1252-encoded CSVs (smart
  quotes, accented characters, byte 0xd2, trademark symbols) parse correctly, and that
  UTF-8 and UTF-8-with-BOM files still work.

---

## [1.1.2] — 2026-05-13

Documentation and visualization correctness release: all user-visible references to the old 5-dimension model replaced with the current CDFI Fund CY 2024-2025 framework.

### Fixed

**Critical — broken visualizations (C1, H7)**
- **`plot_readiness_radar`** (`nmtcapp/visualization/maps.py`) — `_DIM_MAP` updated from five old objective keys (`distress_concentration`, `geographic_diversity`, `impact_intensity`, `sector_diversity`, `pipeline_quality`) to the three current CDFI Fund section keys (`business_strategy`, `community_outcomes`, `priority_points`). All axis values were previously 0.0; now render correctly. Benchmark reference lines updated to HQ section minimums (BS/CO: 80/100, PP: 70/100). Title updated to "CDFI Fund Section Score Radar". Tier colors updated to `Top Tier / Highly Qualified / Not Qualified`.
- **Streamlit Pipeline Optimizer before/after chart** (`streamlit_app/pages/3_Pipeline_Optimizer.py`) — Replaced broken grouped bar chart (which looked up old objective keys in the new CDFI Fund `dimensional_scores` dict, producing all-zero bars) with: (a) a 3-metric display of CDFI Fund section scores before optimization when `win_score` is in session state, and (b) the optimizer dimension delta chart that was already working correctly as the fallback.

**Critical — stale documentation (C2, C3)**
- **`docs/workflow/win-alignment.md`** — Full rewrite. Previous 174-line document described the old 5-dimension model (Distress 35%, Impact 25%, Geographic 20%, Sector 15%, Pipeline 5%) with stale code examples. New document is a workflow companion to `docs/reference/methodology.md`, covering: basic usage, reading `WinProbabilityScore` output fields, tier classification logic with code examples, CDE attribute supply (YAML vs. inline dict), graceful degradation table, sub-score drill-down pattern, and Phase 2 flags.
- **`docs/index.md`** — Three targeted edits: "five analyses… distress concentration, geographic diversity…" → CDFI Fund CY 2024-2025 three-section framework; Win Alignment Scoring card updated to "Not Qualified / Highly Qualified / Top Tier"; methodology disclosure updated to reference published criteria rather than "historical winner patterns".

**High — stale content and broken notebook (H1–H8)**
- **`CITATION.cff`** — `version` updated `1.0.0` → `1.1.2`; `date-released` updated `2025-05-09` → `2026-05-13`; abstract rewritten to describe CY 2024-2025 scoring framework.
- **`docs/installation.md`** — Version comment `# "1.0.0"` → `# prints the installed version` (version-agnostic; no update needed on each release).
- **`README.md` quickstart comment** — `66/100 [competitive]` → `90/100 [Highly Qualified]` (actual output from `CDEProfile.sample()`). Also updated `score.competitive_tier` to `score.tier` in the print statement.
- **`README.md` "The Solution" paragraph** — Replaced "every dimension the CDFI Fund scores: distress concentration, geographic diversity…" with CDFI Fund CY 2024-2025 three-section framing.
- **`README.md` "What It Does" bullet** — Replaced "5-dimensional score (0–100) against CY2020–2024 winner patterns" with current CDFI Fund section framework.
- **`README.md` notebook table** — Updated notebook 03 description from `5.5 → 65.9 → 79.1/100 — weak→competitive` (old model scores) to `16 → 90 → 96/100 — Not Qualified → Highly Qualified → Top Tier` (actual executed output).
- **`examples/03_intelligence_and_optimization.ipynb`** — Fixed code bug in 7 cells: `result_weak.pipeline_result` and `result_improved.pipeline_result` (attribute does not exist on `PipelineAnalysisResult`) → `result_weak` and `result_improved` directly. Executed all 27 cells; 16/17 code cells have saved outputs (import cell has none, as expected). Arc confirmed: Not Qualified (16/100) → Highly Qualified (90/100) → Top Tier (96/100).
- **`templates/cde_profile_sample.yaml`** — Calibration comments corrected: Community Outcomes `45/50` → `47/50`, Priority Points `7/10` → `9/10`, Aggregate `~88/100` → `~90/100`.

### Added

**Tests**
- `tests/test_radar_chart_keys.py` — 4 tests asserting: (1) `dimensional_scores` has exactly the 3 CDFI Fund section keys, (2) old 5-dimension keys are absent, (3) radar chart axis values are non-zero for the sample pipeline, (4) `plot_readiness_radar` source does not reference old dimension keys. This is the structural test that would have caught the C1/H7 regression.
- `tests/test_sample_score.py` — 2 smoke tests asserting `CDEProfile.sample()` composite score is within ±2 of 90 and tier is Highly Qualified or Top Tier. Catches future scoring drift without a README update.
- `tests/test_sample_yaml_score.py` — 5 smoke tests asserting `cde_profile_sample.yaml` section scores (BS: 43/50, CO: 47/50, PP: 9/10, aggregate: 90/100) are within ±2 of documented values. Catches drift between YAML calibration comments and the scoring model.

---

## [1.1.1] — 2026-05-13

Patch release: fix `__version__` mismatch and add packaging guard tests.

### Fixed

- **`__version__` mismatch** — `nmtcapp.__version__` now reads from package metadata via `importlib.metadata` instead of a hardcoded string, eliminating the `1.0.0` / `1.1.0` drift introduced in the 1.1.0 release.
- **Version sync test** — `tests/test_version.py::test_version_sync` asserts `nmtcapp.__version__ == importlib.metadata.version("nmtc-application-builder")`; fails immediately if the two diverge again.
- **Wheel completeness test** — `tests/test_wheel_completeness.py::test_wheel_completeness` builds the wheel from source, installs it in an isolated venv, and imports every public submodule; run with `pytest -m wheel`.

---

## [1.1.0] — 2026-05-12

Methodology realignment: scoring framework replaced with CDFI Fund's published CY 2024-2025 Review Process criteria.

### Changed

**Scoring framework — `nmtcapp/intelligence/win_probability.py`**
- Replaced 5-dimension winner-pattern alignment model (Distress 25%, Geographic 20%, Sector 15%, Impact 25%, Pipeline 15%) with the CDFI Fund's published two-section framework
- `WinProbabilityScore` now reports: Business Strategy (0–50 pts), Community Outcomes (0–50 pts), Priority Points (0–10 pts), aggregate base score (0–100), aggregate with priority (0–110), tier classification, and gating notes
- Tier classification: **Not Qualified** (< 85 aggregate or either section < 40) → **Highly Qualified** (85–94, both sections ≥ 40) → **Top Tier** (≥ 95, both sections ≥ 45)
- `WinProbabilityModel.score()` accepts an optional `cde_attributes` dict for CDE-level inputs (product flexibility, track record, board composition) that are not derivable from pipeline data alone
- Old `composite_score`, `dimensional_scores`, `competitive_tier` fields retained for backward compatibility

**Recommendations — `nmtcapp/intelligence/recommendations.py`**
- `Recommendation` dataclass gains a `citation` field — each recommendation now cites the specific CDFI Fund Review Process section it addresses
- Valid categories updated: `business_strategy`, `community_outcomes`, `priority_points`, `pipeline`
- Engine dispatches to section-specific recommendation generators when a `WinProbabilityScore` is available; falls back to pipeline-level analysis otherwise

**CDE profile — `nmtcapp/core/cde.py`**
- `CDEProfile` gains an `extra: Dict` field; `from_yaml()` captures unknown YAML keys into `extra` so new scoring attributes can be added without changing the schema
- `CDEProfile.sample()` updated for Riverbend Community Capital to include CDFI Fund scoring attributes (products, track record, governance) targeting the Highly Qualified tier (~87–88/100)
- `Application.score_win_probability()` passes `cde.extra` as `cde_attributes` automatically

**Thresholds — `nmtcapp/data/benchmark_thresholds.py`**
- Added CDFI Fund CY 2024-2025 published thresholds: `HIGHLY_QUALIFIED_AGGREGATE_MIN=85`, `HIGHLY_QUALIFIED_SECTION_MIN=40`, `TOP_TIER_AGGREGATE_MIN=95`, `TOP_TIER_SECTION_MIN=45`, `SEVERE_DISTRESS_MIN_PCT=0.85`, `DEEP_DISTRESS_MIN_PCT=0.20`, `DBC_PRIORITY_YEARS_MIN=5`, `DBC_VOLUME_PCT_MIN=0.70`, `UNRELATED_ENTITIES_MIN_PCT=0.90`
- Legacy winner-pattern thresholds retained for `HistoricalBenchmarks` backward compatibility

**Streamlit demo — `streamlit_app/pages/2_Win_Alignment_Scorer.py`**
- Replaced 5-dimension radar chart with stacked horizontal bar showing all 9 CDFI Fund sub-criteria (4 Business Strategy + 5 Community Outcomes)
- Added aggregate gauge with tier zone color coding (Not Qualified / Highly Qualified / Top Tier)
- Added section minimum status badges and tier badge
- Recommendations panel now displays CDFI Fund citation per recommendation

**Methodology documentation**
- `docs/reference/methodology.md` — fully rewritten: sub-score formulas, gating thresholds, Phase 2 considerations, and "what is not modeled" disclosure
- `streamlit_app/pages/4_About_and_Methodology.py` — updated to reflect the new framework
- `templates/cde_profile_sample.yaml` — updated for Riverbend Community Capital with new scoring fields

**Demo notebook — `examples/03_intelligence_and_optimization.ipynb`**
- Rewritten to walk through Not Qualified → Highly Qualified → Top Tier arc
- Each stage shows CDFI Fund section scores, gating notes, and the specific attribute changes required to advance tiers

### Added

- `distress_breakdown` dict now includes both `pct_deep_or_severe` (combined) and `pct_deep` (deep-only) keys, supporting separate Deep Distress Commitment scoring

**`Pipeline.from_csv()` crash-safety hardening**
- Blank required numeric fields (`total_project_cost`, `qei_request`, `qlici_amount`, `expected_jobs_created`) now raise a friendly `ValueError("'field_name' is required but was left blank")` instead of a raw `cannot convert float NaN to integer` traceback
- Blank required string fields (`project_id`, `state`, etc.) now raise a friendly error instead of silently producing `"nan"` string values
- `expected_jobs_retained` left blank now defaults to 0 instead of crashing
- Comment rows (lines where `project_id` starts with `#`) are silently skipped — uploading `pipeline_template.csv` (which contains inline documentation comments) no longer triggers a confusing parse error
- Empty files / header-only files now raise: `"No project rows found. The file contains only column headers or comments. Please add your project data rows before uploading."`
- Added `_required_str()`, `_required_float()`, `_required_int()`, `_int_with_default()` private helpers

**Tests — `tests/test_csv_robustness.py`** (19 new tests)
- `TestBlankRequiredNumericFields` (6): blank jobs_created, total_cost, qei, qlici, jobs_retained defaults, missing jobs_retained column
- `TestBlankRequiredStringFields` (4): blank project_id, blank state, error includes row ID, bad row in multi-row file
- `TestCommentRowsAndEmptyTemplates` (5): single comment skipped, multiple comments skipped, comment-only → no-data error, empty header-only → no-data error, actual `pipeline_template.csv` file triggers no-data error (not a raw crash)
- `TestValidCsvStillParses` (4): good row, strong sample, weak sample, v1.0 CSV without flag columns
- Sub-score formulas documented in `docs/reference/methodology.md` with explicit disclosure that within-section point weights are this tool's interpretation (the CDFI Fund does not publish exact sub-criterion point values)

**Template v1.1 — `templates/pipeline_template.xlsx`**
- Rebuilt as a 4-sheet Excel workbook: **CDE Profile**, **Pipeline**, **Instructions**, **Valid Values**
- **CDE Profile sheet** (Sheet 1): 30 columns covering CDE identity + all CDE-level scoring inputs (Business Strategy, Community Outcomes, Priority Points, Phase 2 flags). One data row per CDE; Y/N, state, org-type, and application-round dropdowns.
- **Pipeline sheet** (Sheet 2): 28 columns — all prior fields retained plus 7 new fields:
  - `qalicb_name` — QALICB legal entity name (was synthesised automatically, now explicit)
  - `closing_target_date` — target closing date (was in CSV template but missing from xlsx)
  - `native_area` (Y/N) → `pct_native_area` → Community Outcomes Special Targeting sub-score
  - `high_migration_rural` (Y/N) → `pct_high_migration_rural` → Special Targeting
  - `us_territory` (Y/N) → `pct_us_territories` → Special Targeting
  - `persistent_poverty` (Y/N) → `pct_persistent_poverty` → Special Targeting
  - `below_market_rate` (Y/N) → `products_below_market_pct` → BS Product Flexibility sub-score
  - `unrelated_entity` (Y/N) → `unrelated_entities_pct` → Priority Points Unrelated Entities
  - `opportunity_zone` (Y/N) — informational
- **Instructions sheet** (Sheet 3): field-by-field documentation, scoring framework summary, graceful-degradation table, methodology disclosure
- **Valid Values sheet** (Sheet 4): dropdown source lists for all validated fields
- Brand styling: navy `#1B438C` section banners, section color coding per category, frozen header rows, sample data rows

**`PipelineProject` v1.1 — `nmtcapp/core/pipeline.py`**
- 4 new optional boolean fields: `is_us_territory`, `is_persistent_poverty`, `is_below_market_rate`, `is_unrelated_entity`
- `from_csv()` reads the new flag columns (`us_territory`, `persistent_poverty`, `below_market_rate`, `unrelated_entity`, `opportunity_zone`, `native_area`, `high_migration_rural`) with Y/N/yes/no/true/false/1/0 parsing via `_optional_bool()`
- `to_dict()` includes all new flags

**`analyze_distress_concentration()` v1.1 — `nmtcapp/intelligence/distress_analysis.py`**
- Returns 4 new QEI-weighted percentage keys computed from per-project flags: `pct_us_territories`, `pct_persistent_poverty`, `pct_below_market_rate`, `pct_unrelated_entity`

**`WinProbabilityModel` v1.1 — `nmtcapp/intelligence/win_probability.py`**
- `_score_product_flexibility()`: falls back to pipeline-derived `pct_below_market_rate` when `products_below_market_pct` is absent from `cde_attributes`
- `_score_special_targeting()`: reads `pct_persistent_poverty` and `pct_us_territories` from pipeline distress breakdown as fallback when not in `cde_attributes`
- `_score_unrelated_entities()`: falls back to pipeline-derived `pct_unrelated_entity` when `unrelated_entities_pct` is absent from `cde_attributes`

**Streamlit Pipeline Analyzer v1.1 — `streamlit_app/pages/1_Pipeline_Analyzer.py`**
- Accepts v1.1 xlsx template: reads CDE Profile sheet with openpyxl (version-agnostic) and passes all 19 scoring attrs to the Win Alignment Scorer via `CDEProfile.extra`
- Computes pipeline-derived CDE-level pcts from per-project flags during file parsing and merges into `cde_attributes`
- Graceful degradation: when CDE Profile fields are absent, displays "not provided — sub-score defaulted to X" info panel before running analysis
- `get_or_create_app()` gains optional `cde_extra` parameter for injecting user-supplied CDE attributes

**Tests — `tests/test_template_fields.py`**
- `test_template_has_all_methodology_fields`: 11 assertions verifying the xlsx has all 4 sheets with the correct columns, sample data, and scoring flags
- `test_scoring_engine_inputs_match_template`: 5 assertions verifying the canonical scoring-engine attr key set matches the template, WinProbabilityModel reads all keys, distress analysis surfaces all pipeline-derived keys, and pipeline fallbacks work correctly for `below_market_rate` and `unrelated_entity`
- 16 new tests for template field alignment; total suite: 637 passing (up from 602)

---

## [1.0.0] — 2025-05-09

Initial public release. Four weeks of development, 544 tests passing.

### Added

**Week 1 — Core Foundation**
- `Pipeline` and `PipelineProject` classes with CSV ingestion and 20-project sample data
- `CDEProfile` class with YAML loading and sample data
- `Application` orchestration class — single entry point for all functionality
- Eligibility validation, completeness check, and consistency check
- Readiness scoring (0–100, grades A–D) across 5 weighted dimensions
- NMTC eligibility enrichment via `nmtc-mapper` with offline fallback
- Deal economics computation via `nmtc-calc` with manual fallback
- `PipelineAnalyzer` — distress, geographic, sector, and impact sub-analyses

**Week 2 — Output Renderers**
- `WordApplicationBuilder` — full NMTC application draft in `.docx`
- `ExcelApplicationBuilder` — multi-sheet workbook with dashboard, pipeline, and impact tables
- `PDFApplicationBuilder` — formatted PDF via ReportLab
- `MarkdownApplicationBuilder` — clean Markdown output for version control workflows
- Shared `styles.py` color palette and typography constants used across all renderers
- `Application.generate()` — produces all four formats in one call

**Week 3 — Intelligence Layer**
- `WinProbabilityModel` — 5-dimensional alignment scoring against CY2020–2024 winner patterns
- `HistoricalBenchmarks` — 9-metric tier comparison with methodology disclosure
- `RecommendationEngine` — quantified, prioritized improvement actions per dimension
- `PipelineOptimizer` — greedy construction + swap-based local search, no LP/MIP solver
- `OptimizationConstraints` — QEI budget, state diversity, sector, and eligibility constraints
- `analyze_winning_patterns()` and `compare_to_winners()` for pattern analysis
- Three executed example notebooks demonstrating full workflow

**Week 4 — Polish + Distribution**
- `nmtcapp.visualization` module — 5 publication-quality chart functions (300 DPI PNG)
  - `plot_pipeline_map` — project distribution on continental US map
  - `plot_distress_heatmap` — QEI by state with distress-level color coding
  - `plot_sector_distribution` — sector mix vs. winner patterns
  - `plot_readiness_radar` — 5-dimensional radar vs. competitive benchmark
  - `plot_winner_alignment` — pipeline metrics vs. winner p25/p50/p75
- `nmtcapp.cli` — `nmtcapp init`, `nmtcapp analyze`, `nmtcapp version` commands
- `templates/` — `pipeline_template.csv`, `pipeline_sample_strong.csv`,
  `pipeline_sample_weak.csv`, `cde_profile_template.yaml`, `cde_profile_sample.yaml`
- MkDocs documentation site with 13 pages deployed to GitHub Pages
- Streamlit interactive demo app (4 pages: Analyzer, Scorer, Optimizer, Methodology)
- Polished README with badges, architecture diagram, and honest limitations
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CITATION.cff`
- GitHub issue and PR templates
- Version bumped to 1.0.0; PyPI classifiers updated to Production/Stable

### Fixed

- `objectives.py` — distress scoring used wrong level strings (`"deep_distressed"` →
  `"deep"`, `"severely_distressed"` → `"severe"`), causing distress score to always be 0
- `sector_analysis.py` — `max_single_sector_pct` was missing from output dict, causing
  `win_probability._score_sector` to always apply a maximum concentration penalty (score = 0)
- `nmtc_mapper_adapter.py` — suppressed nmtcmapper's raw `print()` 404 messages using
  `contextlib.redirect_stdout`
- `pipeline_optimizer.py` — added no-regression guarantee: reverts to full pipeline if
  optimized subset scores lower than input
- `test_optimizer.py` — `test_eligible_only_filters` was mutating shared `_SAMPLE_PROJECTS`
  objects, causing cross-test `is_nmtc_eligible` contamination

---

## [0.2.0] — 2025-04-30

Weeks 1–3 development release (internal).

- Intelligence layer: `WinProbabilityModel`, `RecommendationEngine`, `PipelineOptimizer`
- Output renderers: Word, Excel, PDF, Markdown
- Core pipeline analysis and validation

## [0.1.0] — 2025-04-15

Initial development release (internal).

- Core `Application`, `Pipeline`, `CDEProfile` classes
- Basic validation and readiness scoring

---

[1.1.3]: https://github.com/Jaypatel1511/nmtc-application-builder/releases/tag/v1.1.3
[1.0.0]: https://github.com/Jaypatel1511/nmtc-application-builder/releases/tag/v1.0.0
[0.2.0]: https://github.com/Jaypatel1511/nmtc-application-builder/releases/tag/v0.2.0
[0.1.0]: https://github.com/Jaypatel1511/nmtc-application-builder/releases/tag/v0.1.0

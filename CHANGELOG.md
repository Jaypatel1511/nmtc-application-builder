# Changelog

All notable changes to `nmtc-application-builder` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
- 16 new tests; total suite: 618 passing (up from 602)

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

[1.0.0]: https://github.com/Jaypatel1511/nmtc-application-builder/releases/tag/v1.0.0
[0.2.0]: https://github.com/Jaypatel1511/nmtc-application-builder/releases/tag/v0.2.0
[0.1.0]: https://github.com/Jaypatel1511/nmtc-application-builder/releases/tag/v0.1.0

# Methodology

This page provides a complete technical description of the scoring approach used by NMTC Application Builder. It is intended for practitioners who need to understand how scores are computed, what assumptions are embedded, and where the analysis has meaningful limitations.

---

## Executive summary

NMTC Application Builder scores applications by comparing their pipeline metrics against patterns extracted from CDFI Fund NMTC award announcements (CY2020–CY2024). It does not compute a win probability — it computes an alignment score reflecting how closely a pipeline resembles historical winners on five measurable dimensions.

The five dimensions and their weights mirror the relative importance of scoring criteria in recent CDFI Fund NOFA documents:

| Dimension | Weight | Primary metric |
|-----------|--------|----------------|
| Distress concentration | 35% | % of QEI in deep/severe distressed tracts |
| Impact intensity | 25% | FTE jobs created per $1MM QEI |
| Geographic diversity | 20% | States served + HHI + rural % |
| Sector diversity | 15% | Sectors represented + concentration ceiling |
| Pipeline quality | 5% | Eligibility rate + project count + award size fit |

---

## Why we cannot compute true win probability

The CDFI Fund does not publish application-level microdata for non-winning applicants. What is publicly available:

- **Round-level aggregates:** total applications received, awards made, total dollars allocated
- **Winner-level data:** which CDEs received allocations and for what amounts (from award announcements)
- **Program-level impact statistics:** aggregate jobs, units, and outcomes across the funded portfolio (from annual reports)

What is not available:

- Application-level data for the ~65–70% of applicants who were not selected in any given round
- NOFA scores for any application
- Project-level pipeline data from any application (winner or non-winner)

Without the distribution of non-winner metrics, the standard conditional probability formula (P(win | metrics)) cannot be computed. We do not know whether applicants with 72% distress concentration are funded 40% of the time or 5% of the time — we only know that historical winners averaged 81% distress concentration.

This means any "win probability" generated from available data would be a classification score based on feature similarity to winners only, not a calibrated probability derived from the full applicant distribution. We report this explicitly as an alignment score to avoid misleading practitioners into treating it as a prediction.

---

## How each dimensional score is computed

### Distress concentration score (weight: 35%)

**Input:** `pct_deep_or_severe` — the fraction of total portfolio QEI deployed in census tracts classified as deep distress or severe distress by the CDFI Fund's NMTC Mapping Tool.

**Historical winner statistics (CY2020–CY2024):**

| Statistic | Value |
|-----------|-------|
| Mean | 81% |
| Standard deviation | 11% |
| P25 | 72% |
| P50 (median) | 82% |
| P75 | 91% |
| P90 | 95% |
| Floor (minimum observed) | 50% |
| Mean eligibility rate | 96% |

**Scoring formula:**

If `pct_deep_or_severe` < 50% (the historical floor):
```
score = (pct / 0.50) × 30
```

If `pct_deep_or_severe` ≥ 50%:
```
z = (pct - 0.81) / 0.11
score = Φ(z) × 100
```
where Φ is the standard normal CDF, approximated using `math.erfc`. The score is bounded [0, 100].

This formulation means a pipeline at the winner mean (81%) scores near 50 (50th percentile of the winner distribution), and a pipeline at the winner p75 (91%) scores near 75.

### Impact intensity score (weight: 25%)

**Input:** `jobs_per_million_qei` — total FTE jobs created (from project projections) divided by total QEI in millions.

**Historical winner statistics:**

| Statistic | Value |
|-----------|-------|
| Mean | 12.0 jobs/$MM |
| P25 | 6.0 jobs/$MM |
| P50 (median) | 10.0 jobs/$MM |
| P75 | 18.0 jobs/$MM |
| Top decile | 28.0 jobs/$MM |

**Scoring formula:**

```
if jpm <= 0: score = 0
if jpm >= 28 (top decile): score = 100
else: z = (jpm - 12.0) / 6.0; score = Φ(z) × 100
```

Score is bounded [0, 100].

### Geographic diversity score (weight: 20%)

**Input:** `states_count` (number of distinct states), `hhi` (Herfindahl-Hirschman Index of QEI concentration by state), `rural_pct` (fraction of QEI in rural tracts).

**Historical winner statistics:**

| Statistic | Value |
|-----------|-------|
| Mean states | 7.2 |
| Std states | 3.8 |
| P25 states | 4 |
| P50 states | 7 |
| P75 states | 10 |
| Mean HHI | 620 |
| Mean rural % | 18% |

**Scoring formula:**

```
states_score = Φ((states - 7.2) / 3.8) × 100

hhi_score = max(0, (2000 - hhi) / 2000 × 100)

rural_bonus = min(10, (rural_pct / 0.18) × 5)

score = min(100, states_score × 0.5 + hhi_score × 0.4 + rural_bonus)
```

The HHI score rewards lower concentration: an HHI of 0 (perfect equality) scores 100; an HHI ≥ 2000 scores 0. The rural bonus contributes up to 10 points and rewards reaching or exceeding the winner average rural allocation.

### Sector diversity score (weight: 15%)

**Input:** `sectors_represented` (count of distinct sectors), `max_single_sector_pct` (fraction of QEI in the most concentrated sector).

**Historical winner statistics:**

| Statistic | Value |
|-----------|-------|
| Mean sectors represented | 4.8 |
| Max single sector concentration | 35% |
| Healthcare share | 22% |
| Affordable housing share | 18% |
| Small business share | 17% |
| Education share | 14% |
| Community facility share | 12% |

**Scoring formula:**

```
sector_score = min(100, (sectors / 4.8) × 80)
conc_penalty = max(0, (max_single_pct - 0.35) × 200)
score = max(0, min(100, sector_score - conc_penalty))
```

A pipeline with 4.8 sectors (winner mean) and no sector exceeding 35% scores approximately 80. Each percentage point above the 35% ceiling subtracts 2 points from the sector score.

### Pipeline quality score (weight: 5%)

**Input:** `eligibility_pct` (fraction of projects in eligible tracts), `total_projects`, `requested_allocation`.

**Scoring formula:**

```
eligibility_score = min(100, (pct / 0.96) × 90)

count_score = min(100, (projects / 14.5) × 80)

size_score:
  $35M–$65M → 90
  $25M–$35M → 70
  >$65M     → 75
  <$25M     → 50

score = eligibility_score × 0.4 + count_score × 0.3 + size_score × 0.3
```

### Composite score

```
composite = (distress × 0.35) + (impact × 0.25) + (geographic × 0.20) + (sector × 0.15) + (pipeline × 0.05)
```

Bounded [0, 100] and rounded to one decimal place.

---

## How the readiness score differs from the alignment score

The **readiness score** (`ReadinessScore`) measures internal application quality and completeness:

- Is the pipeline NMTC-eligible?
- Does the pipeline meet minimum distress thresholds?
- Have all required fields been populated?
- Do internal numbers (QEI, QLICI, project cost) satisfy program rules?

The **alignment score** (`WinProbabilityScore`) measures external competitiveness:

- Does the pipeline look like historical winners?
- Is the distress concentration in the winner distribution?
- Does geographic diversity match winner patterns?

An application can have a high readiness score (everything is correctly filled out and eligible) but a low alignment score (distress concentration is only 55%, well below winner patterns). Both scores are necessary for a complete picture.

---

## The optimization objective function

The `PipelineOptimizer` maximizes the composite alignment score subject to constraints. The objective function is the same formula used in the alignment score, applied to the selected subset rather than the full pipeline.

```python
objective(selected) = composite_alignment_score(selected, requested_allocation, weights)
```

where `weights = {distress: 0.35, impact: 0.25, geographic: 0.20, sector: 0.15, pipeline: 0.05}`.

The optimizer uses no convexity assumptions — it is a heuristic (greedy + local search) and is not guaranteed to find the globally optimal subset. For pipelines of 15–25 projects with typical constraint sets, the heuristic converges to a near-optimal solution in fewer than 100 swap iterations. The `max_iterations` parameter (default 500) provides headroom for larger or more constrained problems.

---

## Validation methodology

Three validation checks run automatically in `analyze()`:

**Eligibility check:** Each project's `is_nmtc_eligible` field is verified. Projects with `is_nmtc_eligible = False` generate errors; projects with `is_nmtc_eligible = None` (not yet enriched) generate warnings.

**Completeness check:** All required `PipelineProject` fields (12 fields) and required `CDEProfile` fields are checked for presence and valid type. Optional fields with None values generate warnings, not errors.

**Consistency check:** Cross-field validation:
- `qei_request <= total_project_cost` (QEI cannot exceed total project cost)
- `qlici_amount <= qei_request` (QLICI is a component of QEI)
- `expected_jobs_created >= 0`

---

## Validation limitations

The scoring framework has several important limitations that practitioners should understand:

1. **No non-winner data.** Winner patterns are inferred from public award announcements and annual reports. The non-winner distribution is unknown. The scoring formulas are calibrated against winner data only.

2. **Aggregate inference.** Winner statistics (mean, standard deviation, percentiles) are inferred from program-level aggregates in annual reports, not computed from a microdata sample of individual applications. The inference introduces uncertainty, particularly for standard deviations and percentiles.

3. **NOFA changes.** The CDFI Fund revises NOFA criteria and scoring weights between rounds. The current library reflects the CY2024 NOFA structure. Scoring weights and dimensional definitions may not perfectly match future rounds.

4. **Impact projections are self-reported.** `expected_jobs_created` is entered by the CDE and not verified by the platform. Inflated job projections will improve the impact score without reflecting actual community outcomes.

5. **Geographic centroids.** The pipeline map uses state centroids, not exact project addresses. The geographic analysis itself uses census tract data (from `nmtc-mapper`), but the visualization is approximate.

---

## Acknowledgments

The scoring methodology was developed by reference to the following primary sources:

- CDFI Fund. *New Markets Tax Credit Program: Notice of Funds Availability (NOFA)*, various years (2020–2024). U.S. Department of the Treasury.
- CDFI Fund. *NMTC Program Award Book*, various years. U.S. Department of the Treasury.
- CDFI Fund. *Community Development Financial Institutions Fund Annual Report*, FY2018–FY2023. U.S. Department of the Treasury.
- U.S. Congress. *Consolidated Appropriations Act, 2023*, Pub. L. No. 117-328 (authorizing $5 billion in NMTC authority for CY2022).

The dimensional weighting structure is informed by but does not replicate the CDFI Fund's proprietary NOFA scoring rubric, which is not publicly disclosed at the question-level.

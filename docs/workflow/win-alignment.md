# Win Alignment Scoring

!!! danger "Critical Methodology Disclosure — Read This First"
    The score produced by `score_win_probability()` is an **alignment score**, not a win probability. The CDFI Fund publishes only winner-level award announcement data; application-level data for non-winners is not publicly available. Without the full distribution of both winning and non-winning applications, it is mathematically impossible to compute a true conditional probability of selection. The score tells you how closely your application resembles the pattern of historical winners — it does not tell you the probability that CDFI Fund reviewers will select your application. **A high alignment score improves competitive positioning; it does not guarantee an award.**

---

## Overview

```python
score = app.score_win_probability()
print(score.summary())
```

`score_win_probability()` runs `analyze()` internally (using the cached result if available), then passes the `PipelineAnalysisResult` to `WinProbabilityModel.score()`, which computes a composite 0–100 alignment score from five weighted dimensions.

---

## The five dimensions

### 1. Distress Concentration (weight: 35%)

The most heavily weighted dimension, reflecting the CDFI Fund's "Community Need" criterion, which accounts for the largest share of NOFA points.

The scoring compares your pipeline's `pct_deep_or_severe` (the fraction of total QEI deployed in deep or severely distressed census tracts) against the historical winner distribution:

| Statistic | Value |
|-----------|-------|
| Winner mean | 81% |
| Winner p25 | 72% |
| Winner median (p50) | 82% |
| Winner p75 | 91% |
| Floor (rarely funded below) | 50% |

If your pipeline's deep/severe concentration falls below the 50% floor, the distress dimension score is proportionally reduced. At the 50% mark you score approximately 30/100 on this dimension. At the winner median (82%), you score near 60/100. Exceeding the winner mean pushes you toward 80–100.

### 2. Impact Intensity (weight: 25%)

Measures jobs per million dollars of QEI, the primary impact metric in CDFI Fund annual reports and NOFA scoring. Operating business projects (manufacturing, healthcare clinics, small businesses) typically produce 20–40 jobs per $1MM QEI. Real estate projects typically produce 5–10. A pipeline with significant operating business exposure scores substantially higher on this dimension.

| Statistic | Value |
|-----------|-------|
| Winner mean | 12.0 jobs/$MM |
| Winner p25 | 6.0 jobs/$MM |
| Winner median (p50) | 10.0 jobs/$MM |
| Winner p75 | 18.0 jobs/$MM |
| Winner top decile | 28.0 jobs/$MM |

At 0 jobs/$MM the dimension score is 0. At or above the top decile (28 jobs/$MM) the score is 100.

### 3. Geographic Diversity (weight: 20%)

Evaluates two factors: the number of states served and the Herfindahl-Hirschman Index (HHI) of geographic concentration. Lower HHI means QEI is more evenly distributed across states. There is also a rural bonus — reaching the winner average of 18% rural QEI adds up to 10 points.

| Statistic | Value |
|-----------|-------|
| Winner mean states | 7.2 |
| Winner median states (p50) | 7 |
| Winner p25 states | 4 |
| Winner mean HHI | 620 |
| Winner mean rural % | 18% |

The dimension score is 50% from the states count, 40% from the HHI score, and 10% from the rural bonus.

### 4. Sector Diversity (weight: 15%)

Evaluates two factors: the number of distinct sectors represented and the concentration in any single sector. Historical winners average 4.8 sectors represented and rarely exceed 35% QEI concentration in any single sector.

- Sector score = `(sectors_represented / 4.8) × 80`, capped at 100
- Concentration penalty = `(max_single_sector_pct - 0.35) × 200`, subtracted if over the 35% ceiling

A pipeline with only healthcare projects (1 sector, 100% concentration) would score near 0 on this dimension even if the healthcare projects themselves are excellent. Diversifying into education, small business, and community facilities rapidly improves the sector score.

### 5. Pipeline Quality (weight: 5%)

A composite of three factors:

- **Eligibility rate** (40% of the sub-score): what fraction of projects are in NMTC-eligible census tracts. Winner average is 96%. Below 90% the score drops sharply.
- **Project count** (30%): normalized against the winner median of 13 projects. More projects demonstrate deployment certainty.
- **Award size fit** (30%): requests in the $35–65MM range score 90/100. Requests under $25MM score 50/100. The $35–65MM range represents ~60% of historical awards by volume.

---

## Composite score and competitive tiers

The five dimension scores are multiplied by their weights and summed:

```
composite = (distress × 0.35) + (impact × 0.25) + (geographic × 0.20) + (sector × 0.15) + (pipeline × 0.05)
```

The composite score is then classified into a competitive tier:

| Tier | Score Range | Interpretation |
|------|-------------|----------------|
| Strong | 75–100 | Well-aligned with historical winners across most dimensions |
| Competitive | 55–74 | Above threshold in key dimensions; targeted improvements recommended |
| Marginal | 35–54 | Significant gaps in one or more high-weight dimensions |
| Weak | 0–34 | Below typical winner patterns; substantial restructuring required |

---

## Reading the score output

```python
score = app.score_win_probability()

# Composite alignment score
print(score.composite_score)          # e.g. 71.4

# Per-dimension scores
print(score.dimensional_scores)
# {
#   "distress_concentration": 82.0,
#   "geographic_diversity":   65.0,
#   "impact_intensity":       74.0,
#   "sector_diversity":       71.0,
#   "pipeline_quality":       85.0,
# }

# Competitive tier
print(score.competitive_tier)         # "competitive"

# Historical acceptance rate baseline
print(score.acceptance_rate_baseline) # e.g. 0.345 (34.5%)

# Always-present disclosure
print(score.methodology_disclosure)

# Human-readable summary
print(score.summary())

# JSON-safe dict
data = score.to_dict()
```

---

## Using the score to prioritize improvements

The dimensional breakdown is the most actionable output. To identify where to focus:

```python
dims = score.dimensional_scores
# Find dimensions below 55 (marginal threshold)
gaps = {k: v for k, v in dims.items() if v < 55}
print(f"Priority gaps: {gaps}")
```

Then use `app.recommendations()` for specific, quantified actions tied to each gap. The recommendation engine directly maps to these same five dimensions — each recommendation includes a numeric improvement estimate tied to the relevant dimension score.

**Typical prioritization logic:**

1. **Fix any distress dimension score below 40** — this is the highest-weight dimension and the most direct signal to the CDFI Fund that your pipeline serves genuinely distressed communities.
2. **Ensure impact intensity is above the p25 threshold** (6 jobs/$MM) — below this the impact score contributes essentially nothing to the composite.
3. **Confirm geographic diversity**: single-state pipelines are very rarely funded. If you have fewer than 4 states, geographic is likely scoring near zero and dragging down the composite.
4. **Check sector concentration**: if one sector exceeds 35% of QEI, you are taking a penalty on the sector dimension.
5. **Pipeline quality** (5% weight) — meaningful for borderline applications but usually not the deciding factor.

---

## Acceptance rate baseline

`score.acceptance_rate_baseline` is the average acceptance rate across the four most recent NMTC allocation rounds (CY2020–CY2023). Recent round data:

| Round | Applications | Awards | Acceptance Rate |
|-------|-------------|--------|-----------------|
| CY2020 | 196 | 76 | 38.8% |
| CY2021 | 341 | 100 | 29.3% |
| CY2022 | 280 | 100 | 35.7% |
| CY2023 | 305 | 107 | 35.1% |

The overall acceptance rate matters for context — even a "strong" alignment score does not remove the inherent selectivity of the program. The acceptance rate tells you that roughly 30–39% of applicants receive awards in any given round, meaning competition is genuinely intense regardless of alignment score.

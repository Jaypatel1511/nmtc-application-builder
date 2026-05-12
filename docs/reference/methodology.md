# Methodology

This page documents the scoring framework used by NMTC Application Builder and its relationship to the CDFI Fund's published evaluation criteria. It is intended for practitioners who need to understand how scores are computed, what limitations apply, and what this tool is and is not.

---

## Source documents

This tool's scoring framework is derived from the following primary sources:

| Document | Notes |
|---|---|
| [CY 2024-2025 NMTC Allocation Application Review Process](https://www.cdfifund.gov/system/files/2025-12/CY_2024_25_NMTC_Program_Review_Process.pdf) | Primary source for scored sections, sub-criteria, gating thresholds |
| [CY 2024-2025 NMTC Allocation Application (NOAA)](https://www.cdfifund.gov/programs-training/programs/new-markets-tax-credit) | Application structure and narrative requirements |
| [CY 2024-2025 NMTC Application FAQ](https://www.cdfifund.gov/programs-training/programs/new-markets-tax-credit) | Clarifications on scoring intent and eligibility criteria |
| CDFI Fund NMTC Award Announcements, CY2020–CY2024 | Historical award statistics used in the benchmarks module |

---

## What this tool IS

A self-assessment tool for CDEs to evaluate how well their pipeline and organizational positioning align with the CDFI Fund's **published** CY 2024-2025 evaluation criteria. It translates the published scoring framework into quantitative scores so CDEs can identify gaps before submission.

## What this tool IS NOT

- **Not a win probability calculator.** The CDFI Fund does not publish scores or application data for non-winning applicants. A true probability of selection cannot be computed from available data.
- **Not a substitute for Phase 2 narrative review.** Phase 2 evaluates Management Capacity and Capitalization Strategy through qualitative reviewer judgment. This tool does not model those criteria.
- **Not authoritative.** The CDFI Fund's actual scoring rubric is proprietary. This tool's sub-score weights are best-effort interpretations of the published guidance; the CDFI Fund does not publish exact point values for individual sub-criteria.

---

## Scoring framework

The CDFI Fund evaluates applications on two scored sections plus optional Priority Points.

### Section 1 — Business Strategy (50 base points)

Evaluates the CDE's ability to deploy capital effectively and credibly.

| Sub-criterion | Max points | Key threshold |
|---|---|---|
| Product Flexibility | 10 | 50%+ below-market rate OR 5+ indicia of flexible terms |
| Pipeline Credibility | 15 | Identified, sized, and timed projects with LOIs |
| Track Record Strength | 15 | 5-year direct financing record; bonus for own capital at risk |
| Track Record Alignment | 10 | 70%+ pipeline supported by similar prior activity; 90%+ deployment rate |
| **Section total** | **50** | — |

**Disclosure:** Within Business Strategy, sub-point allocations (Product Flexibility 10 pts, Pipeline Credibility 15 pts, etc.) are this tool's interpretation of the Review Process document. The CDFI Fund does not publish exact point weights for each sub-criterion.

### Section 2 — Community Outcomes (50 base points)

Evaluates the depth of community impact and accountability.

| Sub-criterion | Max points | Key threshold |
|---|---|---|
| Higher Distress Targeting | 15 | 85%+ of QEI in severe distress or multi-indicia distress areas |
| Deep Distress Commitment | 10 | 20%+ of QEI in CDFI Fund-designated Deep Distress areas |
| Special Targeting | 5 | QEI in U.S. Territories, High Migration Rural Counties, NMTC Native Areas, or Persistent Poverty Counties (CY 2024-2025 priority) |
| Community Outcomes Quality | 10 | Quantified outcomes (jobs, units, sq ft) with third-party methodology |
| Community Accountability | 10 | LIC representation on board; community engagement track record |
| **Section total** | **50** | — |

### Priority Points (10 bonus points)

Bonus points that increase an application's ranking within the Highly Qualified pool.

| Criterion | Max points | Key threshold |
|---|---|---|
| DBC Track Record | 5 | 5+ years AND 70%+ of direct financing volume to Disadvantaged Businesses/Communities |
| Unrelated Entities Commitment | 5 | Substantially all (90%+) QEIs to entities unrelated to the CDE |

---

## Gating thresholds — Highly Qualified pool

The CDFI Fund uses a two-stage gating process to form the "Highly Qualified" pool that advances to Phase 2 review:

| Tier | Aggregate Base Score | Section Minimums |
|---|---|---|
| **Not Qualified** | < 85 | Either section < 40 |
| **Highly Qualified** | 85–94 | Both sections ≥ 40 |
| **Top Tier** | 95–100 | Both sections ≥ 45 |

Applications that fail either section minimum (< 40 in Business Strategy or Community Outcomes) do not advance to Phase 2, regardless of aggregate score.

**Award expectation by tier:**
- *Not Qualified:* Will not advance to Phase 2. No award expected.
- *Highly Qualified:* Phase 2 reviewed. Award depends on Phase 2 outcome and ranking within the pool.
- *Top Tier:* High probability of Phase 2 advancement; award amount may approach the maximum requested.

---

## Phase 2 considerations (not scored by this tool)

Phase 2 evaluates qualitative factors that cannot be quantified from pipeline data alone. These are reported as informational flags in the `phase2_flags` field of `WinProbabilityScore`.

| Factor | Notes |
|---|---|
| Management Capacity | Organizational capacity to deploy capital; staffing and systems |
| Capitalization Strategy | QEI-raising track record; investor relationships; capitalization feasibility |
| Non-Metro commitment | ≥ 20% non-metro required; ≥ 50% if applying as Rural CDE |
| Fee/compensation structure | Favorable fee structures to QALICBs viewed positively |
| Prior reporting compliance | Late or inaccurate prior-round reports may result in point deductions |

---

## Sub-score formulas (Business Strategy)

### Product Flexibility (0–10 pts)

```
score_below_mkt   = min(10, products_below_market_pct / 0.50 × 10)
score_indicia     = min(10, products_flexible_indicia_count / 5 × 10)
score             = max(score_below_mkt, score_indicia)
```

Full credit if either: ≥ 50% of products are offered below market rate, OR ≥ 5 indicia of flexible product terms are documented.

### Pipeline Credibility (0–15 pts)

```
Piecewise based on pipeline_pct_identified:
  ≥ 100%:  15 pts
  ≥  80%:  9 + (pct − 0.60) / 0.40 × 6
  ≥  60%:  6 + (pct − 0.40) / 0.20 × 3
  <  60%:  pct / 0.60 × 6

Adjusted for eligibility: penalty if eligibility_pct < 95%
```

### Track Record Strength (0–15 pts)

```
award_pts    = min(9, prior_award_count × 3)
year_pts     = min(3, years_in_operation / 5 × 3)
capital_bonus = 3 if has_own_capital_at_risk else 0
score         = min(15, award_pts + year_pts + capital_bonus)
```

### Track Record Alignment (0–10 pts)

```
align_score  = min(5, track_record_pipeline_alignment_pct / 0.70 × 5)
deploy_score = min(5, track_record_deployment_pct / 0.90 × 5)
score        = align_score + deploy_score
```

---

## Sub-score formulas (Community Outcomes)

### Higher Distress Targeting (0–15 pts)

```
score = min(15, pct_deep_or_severe / 0.85 × 15)
```

At 85%+ in severe or multi-indicia distress: full 15 pts. Proportional credit below.

### Deep Distress Commitment (0–10 pts)

```
score = min(10, pct_deep / 0.20 × 10)
```

At 20%+ in CDFI Fund Deep Distress areas: full 10 pts. Uses `pct_deep` from distress analysis; falls back to 50% of `pct_deep_or_severe` if not available separately.

### Special Targeting (0–5 pts)

```
partial = Σ min(1.25, category_pct / 0.10 × 1.25)  for each of 4 categories
score   = min(5, partial)
```

Categories: U.S. Territories, High Migration Rural Counties, NMTC Native Areas, Persistent Poverty Counties (each contributes up to 1.25 pts; 10%+ in a category = 1.25 pts).

### Community Outcomes Quality (0–10 pts)

| Condition | Score |
|---|---|
| Third-party validated outcomes | 9 |
| Quantified but self-reported | 6 |
| Not quantified | 2 |

### Community Accountability (0–10 pts)

```
board_pts        = min(8, lic_board_representation_pct / 0.33 × 8)
engagement_bonus = 2 if has_community_engagement_track_record else 0
score            = min(10, board_pts + engagement_bonus)
```

---

## Priority Points formulas

### DBC Track Record (0–5 pts)

```
year_score = min(2.5, dbc_focus_years / 5 × 2.5)
vol_score  = min(2.5, dbc_dollar_volume_pct / 0.70 × 2.5)
score      = year_score + vol_score
```

### Unrelated Entities (0–5 pts)

```
score = min(5, unrelated_entities_pct / 0.90 × 5)
```

---

## Readiness score vs. alignment score

This tool computes two separate scores:

**Readiness Score** (`ReadinessScore`) — internal application quality:
- Is the pipeline NMTC-eligible?
- Does the pipeline meet minimum distress thresholds?
- Are all required fields populated with valid values?
- Do internal numbers satisfy program rules (QEI ≤ project cost, etc.)?

**Alignment Score** (`WinProbabilityScore`) — external competitive position:
- Business Strategy: product terms, pipeline quality, track record
- Community Outcomes: distress targeting, community impact, accountability
- Priority Points: DBC focus, unrelated entities

An application can have a high readiness score but a low alignment score (eligible pipeline, but low distress concentration).

---

## What is not modeled

1. **Phase 2 qualitative review.** Management Capacity and Capitalization Strategy are evaluated by CDFI Fund staff through narrative review. This tool reports these as Phase 2 flags, not scores.
2. **Past reporting compliance deductions.** Late or inaccurate prior-round reporting can result in score deductions. This tool assumes clean compliance history; it is flagged in `phase2_flags.prior_reporting_compliance_risk`.
3. **Subjective reviewer judgment.** Phase 1 reviewers exercise judgment on the quality of narrative explanations. Narrative quality, internal consistency, and clarity cannot be quantified from pipeline data alone.
4. **Anomalous score resolution.** When two reviewers disagree by more than a threshold, a third reviewer resolves the discrepancy. This process is not modeled.
5. **Non-winner data.** The CDFI Fund does not publish application-level data for non-winning applicants. Historical benchmarks in `HistoricalBenchmarks` are derived from winner-level data only.

---

## Historical program statistics

| Stat | CY 2024-2025 (estimated) |
|---|---|
| Total applicants | 216 |
| Total QEI requested | $19.2B |
| Total authority available | $10.0B |
| Rural CDE award share (historical) | ~16.9% |

---

## Acknowledgments

Scoring methodology developed by reference to:

- CDFI Fund. *CY 2024-2025 NMTC Allocation Application Review Process.* U.S. Department of the Treasury.
- CDFI Fund. *New Markets Tax Credit Program: Notice of Allocation Availability (NOAA)*, CY 2024-2025. U.S. Department of the Treasury.
- CDFI Fund. *NMTC Program Award Book*, various years (CY2020–CY2024). U.S. Department of the Treasury.
- CDFI Fund. *Community Development Financial Institutions Fund Annual Report*, FY2020–FY2024. U.S. Department of the Treasury.

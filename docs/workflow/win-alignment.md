# Win Alignment Scoring

!!! danger "Methodology Disclosure — Read This First"
    The score produced by `score_win_probability()` is a **self-assessment alignment score**, not a win probability. See [Methodology](../reference/methodology.md) for a full disclosure of what this tool models, what it does not model, and the limitations of scoring against published criteria.

---

## Overview

`score_win_probability()` evaluates your application against the CDFI Fund's **published CY 2024-2025 Review Process** criteria. It returns a `WinProbabilityScore` with:

- Section scores for Business Strategy (0–50) and Community Outcomes (0–50)
- Priority Points bonus (0–10)
- An aggregate base score (0–100) and aggregate with priority (0–110)
- A tier classification: **Not Qualified**, **Highly Qualified**, or **Top Tier**
- Gating notes explaining any section minimums not met
- Phase 2 flags for qualitative factors outside the scope of this tool

For the canonical scoring framework — sub-score formulas, threshold tables, and methodology disclosure — see **[Methodology](../reference/methodology.md)**.

---

## Basic usage

```python
from nmtcapp import Application, CDEProfile, Pipeline

app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
app.add_pipeline(Pipeline.from_csv("pipeline.csv"))

score = app.score_win_probability()
print(score.summary())
```

`score_win_probability()` runs `analyze()` internally (or reuses the cached result if `analyze()` was already called). The `CDEProfile.extra` dict is automatically passed as `cde_attributes`, so any CDE-level scoring inputs in your YAML file are picked up without extra code.

---

## Reading the score output

```python
score = app.score_win_probability()

# Tier and aggregate
print(score.tier)                           # "Not Qualified" | "Highly Qualified" | "Top Tier"
print(score.aggregate_base_score)           # 0–100 (Business Strategy + Community Outcomes)
print(score.aggregate_with_priority)        # 0–110 (includes Priority Points bonus)

# Section totals
print(score.business_strategy["section_total"])    # 0–50
print(score.community_outcomes["section_total"])   # 0–50
print(score.priority_points["section_total"])      # 0–10

# Section scores normalized to 0–100 (for charts and comparisons)
print(score.dimensional_scores)
# {
#   "business_strategy":  86.0,   # 43/50 × 100
#   "community_outcomes": 94.0,   # 47/50 × 100
#   "priority_points":    90.0,   # 9/10 × 100
# }

# Gating notes (non-empty only when a section minimum is not met)
for note in score.tier_gating_notes:
    print(note)

# Phase 2 flags (informational — not scored by this tool)
print(score.phase2_flags)

# Backward-compatible fields (maintained for existing callers)
print(score.composite_score)    # float alias for aggregate_base_score
print(score.competitive_tier)   # legacy string: "strong" | "competitive" | "weak"

# JSON-safe dict
data = score.to_dict()
```

---

## Tier classification

The CDFI Fund uses section minimums to gate applications into the "Highly Qualified" pool that advances to Phase 2 review. It publishes **one** gate, in the first two rows. The third row is this tool's own label and is marked as such.

| Tier | Aggregate Base Score | Section Minimums | Phase 2? | Whose threshold |
|---|---|---|---|---|
| **Not Qualified** | < 85, or either section < 40 | — | No | CDFI Fund |
| **Highly Qualified** | 85–94 | Both sections ≥ 40/50 | Yes | CDFI Fund |
| **Top Tier** | ≥ 95 | Both sections ≥ 45/50 | Yes — same pool | **This tool** |

**"Top Tier" is not a CDFI Fund tier.** The Review Process (p.3, Step 2) publishes the Highly Qualified gate — 40 per section and an aggregate base score of 85 — and **nothing above it**; "Top Tier" returns zero hits across the Allocation Application (142 pp.), the Review Process (7 pp.) and the CY 2024-2025 NOAA (10 pp.). The 95/45 cut points are an unsourced house heuristic, and an application in this row is in the *same* Highly Qualified pool as the row above it, not a further one. See [Methodology](../reference/methodology.md#top-tier-is-not-a-cdfi-fund-tier).

**The section minimums are gating, not just weighted.** An application with 92 aggregate but 38 in Community Outcomes is Not Qualified — it does not advance to Phase 2 regardless of the aggregate.

```python
if score.tier == "Not Qualified":
    print("Does not advance to Phase 2.")
    for note in score.tier_gating_notes:
        print(f"  Gap: {note}")
elif score.tier == "Highly Qualified":
    print("Advances to Phase 2. Award depends on Phase 2 outcome and pool ranking.")
elif score.tier == "Top Tier":
    print("High probability of Phase 2 advancement.")
```

---

## Providing CDE-level attributes

Pipeline data alone is not sufficient to score all sub-criteria. Business Strategy and Community Accountability require CDE-level inputs (product terms, track record, governance) that are not derivable from a project CSV.

There are two ways to supply these inputs:

### Option A — YAML file (recommended)

Place scoring inputs under any key in your `cde_profile.yaml`. They are loaded into `CDEProfile.extra` and passed to the scoring model automatically:

```yaml
# cde_profile.yaml — scoring inputs (any top-level keys not in CDEProfile fields
# flow into CDEProfile.extra and are forwarded to WinProbabilityModel)
products_below_market_pct: 0.55
products_flexible_indicia_count: 6
prior_award_count: 4
years_in_operation: 8
has_own_capital_at_risk: true
pipeline_pct_identified: 0.92
track_record_pipeline_alignment_pct: 0.85
track_record_deployment_pct: 0.94
has_third_party_validation: true
lic_board_representation_pct: 0.44
has_community_engagement_track_record: true
unrelated_entities_pct: 0.95
dbc_focus_years: 6
dbc_dollar_volume_pct: 0.78
```

Then load and score normally — no extra code needed:

```python
cde = CDEProfile.from_yaml("cde_profile.yaml")
app = Application(cde=cde, requested_allocation=65_000_000)
app.add_pipeline(pipeline)
score = app.score_win_probability()   # cde.extra passed automatically
```

See [`nmtcapp/templates/cde_profile_sample.yaml`](https://github.com/Jaypatel1511/nmtc-application-builder/blob/main/nmtcapp/templates/cde_profile_sample.yaml) and [`nmtcapp/templates/pipeline_template.xlsx`](https://github.com/Jaypatel1511/nmtc-application-builder/blob/main/nmtcapp/templates/pipeline_template.xlsx) for the full field list.

### Option B — inline dict

Pass `cde_attributes` directly to `WinProbabilityModel().score()` when calling the model layer directly:

```python
from nmtcapp.intelligence.win_probability import WinProbabilityModel
from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalyzer

result = PipelineAnalyzer().analyze(pipeline)
score = WinProbabilityModel().score(
    result,
    requested_allocation=65_000_000,
    cde_attributes={
        "products_below_market_pct": 0.55,
        "prior_award_count": 4,
        "years_in_operation": 8,
        # ... other CDE-level inputs
    }
)
```

---

## Graceful degradation

When CDE-level inputs are absent, each affected sub-score defaults to 0 rather than raising an error. This means:

- Missing `products_below_market_pct` and `products_flexible_indicia_count` → Product Flexibility scores 0/10
- Missing track record fields → Track Record Strength and Alignment score 0/25
- Missing governance fields → Community Accountability scores 0/10

The aggregate score will be lower than the true CDE score, but the tool will not crash. The `score.tier_gating_notes` will explain which section minimums were not met.

**Pipeline-derived fallbacks:** Some CDE-level inputs can be inferred from pipeline flags when not supplied directly:

| CDE attribute | Pipeline fallback |
|---|---|
| `products_below_market_pct` | Fraction of QEI where `is_below_market_rate = True` |
| `unrelated_entities_pct` | Fraction of QEI where `is_unrelated_entity = True` |
| `pct_persistent_poverty` | From `distress_analysis` (requires `is_persistent_poverty` flag) |
| `pct_us_territories` | From `distress_analysis` (requires `is_us_territory` flag) |

---

## Using the score to prioritize improvements

The section breakdown is the most actionable output. To identify where to focus:

```python
bs = score.business_strategy
co = score.community_outcomes
pp = score.priority_points

print(f"Business Strategy:   {bs['section_total']}/50  (HQ minimum: 40)")
print(f"Community Outcomes:  {co['section_total']}/50  (HQ minimum: 40)")
print(f"Priority Points:     {pp['section_total']}/10")

# Sub-score drill-down: find the largest gaps
sub_scores = {
    "Product Flexibility (BS)":     (bs.get("product_flexibility", 0),    10),
    "Pipeline Credibility (BS)":    (bs.get("pipeline_credibility", 0),   15),
    "Track Record Strength (BS)":   (bs.get("track_record_strength", 0),  15),
    "Track Record Alignment (BS)":  (bs.get("track_record_alignment", 0), 10),
    "Higher Distress (CO)":         (co.get("higher_distress_targeting", 0), 15),
    "Deep Distress (CO)":           (co.get("deep_distress_commitment", 0),  10),
    "Special Targeting (CO)":       (co.get("special_targeting", 0),          5),
    "Outcomes Quality (CO)":        (co.get("community_outcomes_quality", 0), 10),
    "Accountability (CO)":          (co.get("community_accountability", 0),   10),
}
for name, (actual, max_pts) in sorted(sub_scores.items(), key=lambda x: x[1][0] / x[1][1]):
    gap = max_pts - actual
    print(f"  {name:<35} {actual:4.1f}/{max_pts}  (gap: {gap:.1f})")
```

Then use `app.recommendations()` for specific, quantified actions per gap. Each recommendation includes a `citation` field pointing to the relevant CDFI Fund Review Process section.

---

## Combining with recommendations and optimization

```python
# Get recommendations tied to the current score
recs = app.recommendations()
print(recs.summary())

for r in recs.recommendations:
    if r.priority in ("critical", "high"):
        print(f"[{r.priority.upper()}] {r.category}: {r.finding}")
        print(f"  Action:   {r.action}")
        print(f"  Estimate: {r.quantified_improvement}")
        if r.citation:
            print(f"  Citation: {r.citation}")

# Optimize project subset to maximize competitive alignment
from nmtcapp.optimizer import OptimizationConstraints
result = app.optimize_pipeline(
    constraints=OptimizationConstraints(max_total_qei=65_000_000, min_states=5)
)
print(f"Score: {result.alignment_score_before*100:.0f} → {result.alignment_score_after*100:.0f}")
```

---

## Phase 2 flags

`score.phase2_flags` is a dict of boolean flags for qualitative factors that cannot be scored from pipeline data. These are informational only — they do not affect the Phase 1 aggregate score.

```python
for flag, value in score.phase2_flags.items():
    status = "⚠️ " if value else "✓ "
    print(f"{status} {flag.replace('_', ' ')}: {value}")
```

Common flags: `non_metro_commitment_risk`, `fee_structure_risk`, `prior_reporting_compliance_risk`, `capitalization_risk`. See [Methodology — Phase 2 considerations](../reference/methodology.md#phase-2-considerations-not-scored-by-this-tool) for details.

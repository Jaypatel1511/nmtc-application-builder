# Recommendations

The recommendation engine translates the gap between your pipeline's current metrics and historical winner patterns into specific, quantified actions. Unlike generic advice ("improve distress concentration"), every recommendation includes a concrete action, a numeric improvement estimate, and a target threshold derived from the winner distribution.

---

## How recommendations are generated

```python
recs = app.recommendations()
print(recs.summary())
```

Internally, `app.recommendations()` runs three steps:

1. **Benchmarking** — `HistoricalBenchmarks().compare()` computes per-metric percentile positions against winner distributions
2. **Gap analysis** — `RecommendationEngine.recommend()` compares each metric against winner p25, p50, and p75 thresholds to identify gaps
3. **Prioritization** — gaps are classified as critical, high, or medium based on their distance from the minimum competitive threshold and the weight of the affected dimension

The resulting `RecommendationSet` sorts recommendations by priority (critical first) and groups them into `strategic_changes` (critical + high) and `quick_wins` (medium).

---

## Priority levels

| Priority | Meaning | When to expect it |
|----------|---------|-------------------|
| `critical` | Blocks competitive consideration | Eligibility rate <90%, only 1 state, distress <72% (p25 floor) |
| `high` | Meaningful score improvement available | Metric between p25 and p50 of winner distribution |
| `medium` | Incremental gains | Metric between p50 and p75; or bonus opportunity (native area, rural) |

Critical recommendations should be addressed before submission — they represent gaps that historically correlate with non-funding. High recommendations are important but not necessarily blocking; address as many as the pipeline timeline allows. Medium recommendations are refinements.

---

## Categories

Each recommendation is tagged with one of five categories:

| Category | Dimensions addressed |
|----------|---------------------|
| `distress` | Deep/severe concentration, native area and HMR bonus |
| `geographic` | States count, HHI, rural percentage |
| `impact` | Jobs per million QEI |
| `sector` | Sector diversity, concentration ceiling |
| `pipeline` | Eligibility rate, project count |

---

## Reading a recommendation object

```python
recs = app.recommendations()

for rec in recs.recommendations:
    print(f"[{rec.priority.upper()}] {rec.category}")
    print(f"  Finding: {rec.finding}")
    print(f"  Action:  {rec.action}")
    print(f"  Impact:  {rec.expected_impact}")
    print(f"  Estimate: {rec.quantified_improvement}")
    print()
```

A sample distress recommendation:

```
[HIGH] distress
  Finding: Deep/severe distress concentration (74%) is competitive but
           below the winner median of 82%.
  Action:  Substitute 8pp of LIC projects with deeper-distress
           alternatives to reach the winner median. Target projects in
           tracts with poverty rate ≥30% or median family income ≤60% AMI.
  Impact:  Reach median winner distress concentration; stronger NOFA score.
  Estimate: Estimated +8–15 distress alignment score points;
             advances from 'competitive' to 'strong' tier.
```

### `quantified_improvement`

This field is a **string**, not a number — `quantified_improvement: str` on `Recommendation`. It always contains a numeric estimate *stated in prose*, as the sample above shows (`Estimated +8–15 distress alignment score points; ...`); it is written for a reader, and parsing a figure back out of it is not supported. The estimate is based on the scoring formulas in `WinProbabilityModel` — specifically, the change in dimensional score from moving a metric from its current value to the target threshold. The estimates are ranges, not point predictions, because the actual improvement depends on which specific projects are modified. Use them as directional signals, not commitments.

---

## Working with the full RecommendationSet

```python
recs = app.recommendations()

# Overall assessment narrative
print(recs.overall_assessment)
# e.g. "Competitive alignment (71/100). Priority changes below could
#        improve your score by 10–20 points before submission."

# Strategic changes (critical + high priority) — address these first
for rec in recs.strategic_changes:
    print(f"[{rec.priority}] {rec.category}: {rec.action}")

# Quick wins (medium priority) — incremental improvements
for rec in recs.quick_wins:
    print(f"[medium] {rec.category}: {rec.action}")

# All recommendations as a list of dicts (JSON-safe)
import json
print(json.dumps(recs.to_dict(), indent=2))
```

---

## Acting on recommendations

### Distress recommendations

Distress gaps are addressed by substituting standard LIC projects with projects in deeper-distress census tracts. The CDFI Fund's NMTC Mapping Tool (https://www.cdfifund.gov/nmtc) allows you to identify qualifying tracts by address or census tract ID. Look for:

- Tracts with poverty rate ≥30% (often classified as "deep")
- Tracts with unemployment >1.5× the national average
- BIA-designated Native American areas (earn a bonus on the distress dimension)
- USDA high-migration rural counties

### Geographic recommendations

Geographic gaps are addressed by adding projects in additional states. If your HHI is high (concentrated in a small number of states), consider splitting a single large-state commitment into smaller projects in two or three states. The goal is to reach at least the winner p25 of 4 states, ideally 7+ states.

### Impact recommendations

The fastest way to improve jobs-per-million-QEI is to add operating business projects. Manufacturing facilities, healthcare clinics with significant staffing, and retail/service businesses in LICs typically generate 20–40 FTE jobs per $1MM QEI. Real estate projects typically generate 5–10. The difference compounds across the portfolio.

### Sector recommendations

If a single sector exceeds 35% of QEI, the sector concentration penalty reduces your sector dimension score. The fix is to add 1–2 projects in complementary sectors. Healthcare + education + community facility is a common winning combination. Affordable housing + small business also frequently appears in high-scoring applications.

### Pipeline recommendations

Low eligibility rate is the most urgent pipeline recommendation. Verify every project using the CDFI Fund NMTC Mapping Tool before submission. Projects that appear eligible based on zip code or neighborhood may not be in qualifying census tracts.

---

## Example: full recommendation workflow

```python
from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline

cde = CDEProfile.sample()
pipeline = Pipeline.from_csv("my_pipeline.csv")

app = Application(cde=cde, requested_allocation=55_000_000)
app.add_pipeline(pipeline)

# Score first to understand starting position
score = app.score_win_probability()
print(f"Starting score: {score.composite_score:.0f}/100 [{score.competitive_tier}]")

# Get recommendations
recs = app.recommendations()

# Print only critical and high priority items
for rec in recs.strategic_changes:
    print(f"\n[{rec.priority.upper()}] {rec.category.upper()}")
    print(f"  {rec.finding}")
    print(f"  Action: {rec.action}")
    print(f"  Expected: {rec.quantified_improvement}")
```

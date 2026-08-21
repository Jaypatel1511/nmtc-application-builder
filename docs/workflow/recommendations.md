# Recommendations

The recommendation engine translates the gap between your pipeline's current
metrics and the **published CY 2024-2025 Review Process criteria** into specific,
quantified actions. Every recommendation includes a concrete action, a numeric
estimate of the change in *this tool's own* sub-score, and a citation naming the
Review Process section behind it.

!!! warning "This page described a different engine, and was corrected in 1.5.1"

    Everything below the fold on this page — a `geographic` category, a
    `critical` priority triggered by "only 1 state", targets "derived from the
    winner distribution", advice to "reach at least the winner p25 of 4 states,
    ideally 7+ states" — described an engine that **does not exist and has not
    existed since 1.2.0**. It was published on this site while the code emitted
    nothing of the kind.

    Two separate defects, both corrected here:

    1. **It was a winner-population claim.** `p25`, `winner median`, "gaps that
       historically correlate with non-funding" — this package's attribution
       registry rules every `WINNER_*` key **HOUSE and unsourced**, and no score
       in this tool has ever been compared to a population of past Allocatees.
       It is the same class removed from `pipeline-analysis.md` and
       `about/why.md` in this release. "Blocks competitive consideration" is the
       same wrong-conclusion shape as the "Application not viable in current
       form" deleted from `pipeline-analysis.md`.
    2. **It was false about the code.** `RecommendationEngine` was executed at
       1, 2, 3, 4 and 5 states: it emits **zero geographic advice at any state
       count**. The page documented behaviour the engine does not have — and
       that page was, at the same time, the published defence for withdrawing
       the geographic advice from the *other* engine.

    The `benchmark_comparison` argument `recommend()` accepts is **never read**.
    No percentile is computed anywhere in this engine.

---

## How recommendations are generated

```python
recs = app.recommendations()
print(recs.summary())
```

Internally, `app.recommendations()` scores the pipeline with
`WinProbabilityModel` and then walks that score:

1. **Section scoring** — `WinProbabilityModel().score()` produces Business
   Strategy (/50), Community Outcomes (/50) and Priority Points (/10) against
   the Review Process's own sub-criteria
2. **Gap analysis** — `RecommendationEngine.recommend()` inspects each
   *sub-score* and emits a recommendation where it falls short of that
   sub-criterion's structural maximum, or of a threshold this tool marks as its
   own
3. **Gating** — if the score lands in `Not Qualified`, a `critical`
   recommendation is emitted for whichever published gate was missed

`recommend()` also takes a `benchmark_comparison` argument. **It is accepted and
never read** — the parameter is vestigial and no percentile is computed. It is
documented here rather than quietly omitted, because this page's previous
version described that argument as step 1 of the process.

The resulting `RecommendationSet` sorts recommendations by priority (critical
first) and groups them into `strategic_changes` (critical + high) and
`quick_wins` (medium).

---

## Priority levels

| Priority | Meaning | When it is emitted |
|----------|---------|--------------------|
| `critical` | A **published** gate is missed | The score is `Not Qualified` — a section total below the Highly Qualified section minimum, or an aggregate base score below the published aggregate minimum |
| `high` | A sub-score is well short of its maximum | A Review Process sub-criterion scores materially below its structural maximum |
| `medium` | A sub-score is one or two steps short | The same, nearer the top of the band; or an unclaimed Priority Points bonus |

`critical` means one thing only, and it is the one thing here with a federal
referent: **the CY 2024-2025 Review Process publishes a Highly Qualified gate**,
and the score did not clear it. An application that misses either section
minimum does not advance to Phase 2 — that is the Fund's rule, quoted in
`4_About_and_Methodology`, not this tool's judgement.

`critical` does **not** mean the application is not worth filing, and this table
previously said it "blocks competitive consideration". No output of this tool
blocks anything: the score is this tool's reading of published criteria, the
CDFI Fund scores the application itself, and a CDE deciding whether to file
should not take a `critical` here as an answer to that question.

The three trigger conditions this table used to list — "eligibility rate <90%,
only 1 state, distress <72% (p25 floor)" — trigger nothing. **No state count
raises any priority in this engine**, and there is no p25 floor anywhere in it.

---

## Categories

Each recommendation is tagged with one of **three** categories, and they are the
three scored sections of the Review Process:

| Category | Sub-criteria addressed |
|----------|------------------------|
| `business_strategy` | Product Flexibility, Pipeline Credibility, Track Record, unrelated-entity share |
| `community_outcomes` | Higher Distress Targeting, Deep Distress Commitment, jobs and community impact |
| `priority_points` | The two published priority-point categories |

**There is no `geographic` category, and there never was one in this engine.**
This table previously listed five categories — `distress`, `geographic`,
`impact`, `sector`, `pipeline` — and `RecommendationEngine` emits none of those
five strings. A reader filtering `rec.category == "geographic"` got an empty
list and no error.

To confirm on your own install:

```python
sorted({r.category for r in app.recommendations().recommendations})
# ['business_strategy', 'community_outcomes']   # 'priority_points' on some pipelines
```

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

A real recommendation, copied from `CDEProfile.sample()` +
`Pipeline.sample(n=20)` at a $65MM request. Note the `citation` field — every
item the engine emits names the Review Process section behind it:

```
[MEDIUM] business_strategy
  Finding:  Pipeline Credibility is 12/15. A few projects lack documented
            sizing or LOIs.
  Action:   Strengthen documentation for the remaining unsigned projects.
            Include project-level financial projections and realistic
            deployment timeline.
  Impact:   Incremental Pipeline Credibility improvement.
  Estimate: Estimated +3 points (Pipeline Credibility: 12/15 → 15/15).
  Citation: CY 2024-2025 Review Process, Section II.A — Business Strategy,
            Business Plan/Pipeline
```

The block that stood here was **fabricated**. It showed a `[HIGH] distress`
category the engine cannot emit, a "winner median of 82%" it does not hold, and
an estimate denominated in "distress alignment score points" — a unit no field
of `Recommendation` carries. Every figure in the block above is reproducible by
running the two lines under "How recommendations are generated".

### `quantified_improvement`

This field is a **string**, not a number — `quantified_improvement: str` on
`Recommendation`. It contains a numeric estimate *stated in prose*, as the
sample above shows (`Estimated +3 points (Pipeline Credibility: 12/15 →
15/15).`); it is written for a reader, and parsing a figure back out of it is
not supported.

**What the number is.** It is the arithmetic distance between the sub-score this
tool computed and that sub-criterion's structural maximum — that is, how many
points of *this tool's own* sub-score are unclaimed. It is **not** a prediction
of how the CDFI Fund would score the change, and it is not calibrated against
any outcome. Use it to rank which gaps are largest, not as a commitment.

---

## Working with the full RecommendationSet

```python
recs = app.recommendations()

# Overall assessment narrative
print(recs.overall_assessment)
# e.g. "Highly Qualified (90/100). Business Strategy: 43/50, Community
#        Outcomes: 47/50. Both sections meet the 40-point gating minimum.
#        Priority changes below can improve ranking within the Highly
#        Qualified pool."
#
# On a partial run (no eligibility data) this reads "NOT RATED" and gives
# no verdict at all. The "Competitive alignment (71/100)" example that
# stood here named a tier this engine does not have.

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

### Geographic recommendations — there are none, and the advice that was here is withdrawn

**This engine emits no geographic recommendation at any state count.** Executed
against the live scorer at 1, 2, 3, 4 and 5 states, it returns zero items
mentioning states, geography, footprint or HHI.

The paragraph that stood here read:

> The goal is to reach at least the winner p25 of 4 states, ideally 7+ states.

That is **withdrawn**, for the same reason the equivalent string was withdrawn
from `readiness_score._build_recommendations` in this release, and it is worth
stating plainly because this page was the published defence for that
withdrawal:

- **The CY 2024-2025 Review Process scores no state count at all.** The
  Allocation Application asks for a service area, not a minimum number of
  states. `MIN_GEOGRAPHIC_DIVERSITY` in `schema.py` records that ruling.
- **There is no "winner p25 of 4 states."** No distribution of past Allocatees'
  state counts is held anywhere in this package; the `WINNER_*` keys the phrase
  gestures at are all registered **HOUSE and unsourced**.
- **Following it can cost points on criteria the Fund does score.** Measured on
  1.5.0: a two-state pipeline at 100% deep/severe distress scores Community
  Outcomes 44/50, aggregate 94 — *Highly Qualified*. Spreading it to five
  states dilutes distress to 55% deep, the aggregate falls to 89, and the tier
  flips to *Not Qualified*.

**Suppression, not correction.** Writing the *right* geographic advice means
deriving what geographic breadth is worth, which is a methodology question this
release does not answer. Do not read the absence of geographic advice as a
finding that your footprint is fine, and do not read it as a finding that it is
not. This tool currently has nothing defensible to say about it.

If your HHI is high, `geographic_analysis` will still *label* the concentration
(`highly_concentrated` / `moderate` / `diverse`). That label is a measurement of
your own pipeline and is true. It is not a comparison to anyone else.

### Impact recommendations

The fastest way to improve jobs-per-million-QEI is to add operating business
projects, which generate more direct FTEs per dollar than real-estate projects.

The specific ranges that stood here — "20–40 FTE jobs per $1MM QEI" for
operating businesses, "5–10" for real estate — are **unsourced**. They are not
computed from award data, they are not constants this package holds, and they
should not be used to size a projection. The direction is the reliable part;
the numbers were not.

### Sector recommendations

If a single sector exceeds 35% of QEI, the sector concentration penalty reduces
this tool's own sector sub-score. The fix is to add 1–2 projects in
complementary sectors.

Two sentences were removed here in 1.5.1: that "healthcare + education +
community facility is a common winning combination", and that "affordable
housing + small business also frequently appears in high-scoring applications".
Both are claims about what past Allocatees did, this package holds no such
data, and the second is a claim about application *scores*, which the CDFI Fund
does not publish for any applicant.

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

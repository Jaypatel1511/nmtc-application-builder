# Quickstart

This guide walks through a complete first run — from install to generated application package — in under 60 seconds of reading. Every code block is runnable as-is.

---

## Step 1: Install

```bash
pip install "nmtc-application-builder[output,viz]"
```

This installs everything: core intelligence engine, Word/Excel/PDF renderers, and matplotlib visualizations.

---

## Step 2: Create a sample CDE and pipeline

`CDEProfile.sample()` returns a realistic Midwest/South CDE profile pre-populated with prior award history, governance structure, and contact details. `Pipeline.sample(n=20)` returns 20 realistic projects spanning multiple states, sectors, and distress levels — all eligibility fields pre-populated so no external API calls are needed.

```python
from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline

cde = CDEProfile.sample()
pipeline = Pipeline.sample(n=20)

print(cde.name)           # "Riverbend Community Capital CDE, LLC"
print(len(pipeline))      # 20
print(pipeline)           # Pipeline(projects=20, total_qei=$120,500,000)
```

To use your own data, load from a YAML file (CDE) and CSV (pipeline):

```python
cde = CDEProfile.from_yaml("my_cde.yaml")
pipeline = Pipeline.from_csv("my_pipeline.csv")
```

See `nmtcapp/templates/cde_profile_template.yaml` and `nmtcapp/templates/pipeline_template.csv` in the repository for the expected column structure.

---

## Step 3: Run analyze()

```python
app = Application(cde=cde, requested_allocation=65_000_000)
app.add_pipeline(pipeline)

analysis = app.analyze()
analysis.summary()
```

`analyze()` orchestrates five steps internally:

1. Enriches each project with NMTC eligibility and distress level via `nmtc-mapper`
2. Computes NMTC deal economics (credits, investor equity, CDE fees) via `nmtc-calc`
3. Runs distress concentration, geographic diversity, sector mix, and impact analyses
4. Runs eligibility, completeness, and consistency validation checks
5. Computes a readiness score (0–100, graded A–F)

Results are cached — calling `analyze()` again returns the same object without re-running.

---

## Step 4: Score win alignment

```python
score = app.score_win_probability()
print(score.summary())
```

Sample output:

```
====================================================================
  APPLICATION ALIGNMENT SCORE (vs. Historical NMTC Winners)
  Composite Score:    71.4 / 100
  Competitive Tier:   COMPETITIVE
  Acceptance Baseline:34.5% (recent 4-round average)
====================================================================

  Dimensional Scores:
  Distress Concentration         82.0  ████████████
  Geographic Diversity           65.0  ████████░░░░
  Impact Intensity               74.0  █████████░░░
  Sector Diversity               71.0  ████████░░░░
  Pipeline Quality               85.0  ██████████░░

  Assessment: Competitive alignment — above threshold in key dimensions.
====================================================================
```

!!! warning "This is not a win probability"
    The composite score measures alignment with historical winner patterns (CY2020–CY2024), not probability of funding. See [Win Alignment Scoring](workflow/win-alignment.md) for the full methodology explanation.

---

## Step 5: Get recommendations

```python
recs = app.recommendations()
print(recs.summary())
```

The recommendation engine scores each pipeline against the **published CY
2024-2025 Review Process criteria** and returns prioritized recommendations,
each citing the section behind it. A typical output includes:

- **Critical**: the score is `Not Qualified` — a published gate was missed
  (a section total below the Highly Qualified section minimum)
- **High**: a Review Process sub-criterion scores materially below its
  structural maximum
- **Medium**: a sub-criterion is one or two steps short, or a Priority Points
  bonus is unclaimed

Each recommendation includes a specific action and an estimate of the unclaimed
points in *this tool's own* sub-score (e.g., `"Estimated +3 points (Pipeline
Credibility: 12/15 → 15/15)."`).

!!! note "Corrected in 1.5.1"

    This passage said the engine "benchmarks each dimension against historical
    winners" and could recommend "lifting project count to winner median" or
    act on "geographic concentration". **Those phrases are withdrawn: the
    engine does none of these.** The engine
    was executed at 1–5 states and emits no geographic advice at any of them,
    no winner distribution is consulted, and no `winner median` is held. See
    [Recommendations](workflow/recommendations.md) for the full correction.

---

## Step 6: Optimize pipeline

```python
from nmtcapp.optimizer.constraints import OptimizationConstraints

constraints = OptimizationConstraints(
    max_total_qei=65_000_000,
    min_projects=10,
    min_states=5,
    min_distress_pct=0.70,
)

result = app.optimize_pipeline(constraints)
print(result.summary())
```

The optimizer selects a subset of your pipeline that maximizes alignment score subject to your constraints. It runs greedy construction followed by swap-based local search (default 500 iterations). The result shows which projects were selected and the dimensional improvement at each step.

---

## Step 7: Generate outputs

```python
paths = app.generate("./drafts/")
print(paths)
# {
#   "markdown": "./drafts/CDE-2018-0117_application.md",
#   "word":     "./drafts/CDE-2018-0117_application.docx",
#   "excel":    "./drafts/CDE-2018-0117_application.xlsx",
#   "pdf":      "./drafts/CDE-2018-0117_application.pdf"
# }
```

To generate only specific formats:

```python
paths = app.generate("./drafts/", formats=["word", "excel"])
```

The output directory is created automatically. File names are derived from the CDE's `cde_id` field.

---

## Visualizations

After generating outputs, create standalone charts:

```python
from nmtcapp.visualization import (
    plot_pipeline_map,
    plot_distress_heatmap,
    plot_sector_distribution,
    plot_readiness_radar,
    plot_winner_alignment,
)

plot_pipeline_map(app, "./charts/pipeline_map.png")
plot_distress_heatmap(app, "./charts/distress_heatmap.png")
plot_sector_distribution(app, "./charts/sector_mix.png")
plot_readiness_radar(app, "./charts/readiness_radar.png")
plot_winner_alignment(app, "./charts/winner_alignment.png")
```

Requires `matplotlib>=3.7` — install with `pip install "nmtc-application-builder[viz]"`.

---

## Next steps

- [Pipeline Analysis](workflow/pipeline-analysis.md) — what `analyze()` produces in detail
- [Win Alignment Scoring](workflow/win-alignment.md) — how the 5 dimensions are scored
- [Recommendations](workflow/recommendations.md) — how to act on the recommendation output
- [Pipeline Optimization](workflow/optimization.md) — constraint setup and result interpretation
- [API Reference](reference/api.md) — full method signatures

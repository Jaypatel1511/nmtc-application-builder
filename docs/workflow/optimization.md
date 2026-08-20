# Pipeline Optimization

The pipeline optimizer selects a subset of your pipeline that maximizes the composite alignment score subject to constraints you define — QEI budget, project count, minimum state count, required sectors, and more. It is designed to answer the question: "Given these 25 projects, which 12–15 should I put in the application to score as well as possible?"

!!! warning "Important framing"
    The optimizer maximizes alignment with historical winner patterns. It does not maximize the probability of winning an award (which cannot be computed from public data alone) and does not guarantee that the selected subset will receive funding. See [Win Alignment Scoring](win-alignment.md) for the full methodology disclosure.

---

## Algorithm

The optimizer uses two phases of a pure-Python heuristic — no LP or MIP solver is required.

### Phase 1: Greedy construction

Projects are ranked individually by their single-project alignment contribution (the composite score if only that project were selected). The algorithm adds projects in descending score order, skipping any that would push the total QEI above `max_total_qei` or the project count above `max_projects`. Required sectors (`required_sectors` constraint) are appended last using the cheapest available project from each missing sector.

### Phase 2: Swap-based local search

After greedy construction, the algorithm enters a swap loop: for each selected project, it tests every non-selected project as a replacement. If swapping out a selected project for an unselected one improves the composite alignment score, the swap is accepted. The process repeats until no improving swap can be found or `max_iterations` is reached.

A no-regression guarantee prevents the optimizer from returning a result worse than the original full pipeline: if the optimized subset scores lower than the full pipeline and the full pipeline satisfies all constraints, the full pipeline is returned unchanged.

---

## OptimizationConstraints fields

```python
from nmtcapp.optimizer.constraints import OptimizationConstraints

constraints = OptimizationConstraints(
    min_total_qei=40_000_000,      # minimum total QEI in selected set
    max_total_qei=65_000_000,      # maximum total QEI (typically = requested allocation)
    min_projects=10,                # minimum number of projects to select
    max_projects=20,                # maximum number of projects to select
    required_sectors=["healthcare", "education"],  # must include at least one of each
    excluded_states=["HI", "AK"],  # projects in these states are ineligible
    min_distress_pct=0.70,         # minimum fraction of QEI in deep/severe tracts
    min_states=5,                   # minimum distinct states in selected set
    max_single_sector_pct=0.40,    # maximum fraction of QEI in any one sector
    min_eligibility_pct=0.95,      # minimum fraction of projects that are NMTC-eligible
)
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `min_total_qei` | `float` | 0.0 | Minimum QEI sum in selected set (dollars) |
| `max_total_qei` | `float` | inf | Maximum QEI sum — set to your requested allocation |
| `min_projects` | `int` | 1 | Minimum projects to select |
| `max_projects` | `int` | 9999 | Maximum projects to select |
| `required_sectors` | `list[str]` | `[]` | Sectors that must have at least one project |
| `excluded_states` | `list[str]` | `[]` | States to exclude from selection |
| `min_distress_pct` | `float` | 0.0 | Minimum deep/severe distress fraction |
| `min_states` | `int` | 1 | Minimum distinct states in selected set |
| `max_single_sector_pct` | `float` | 1.0 | Maximum QEI share for any single sector |
| `min_eligibility_pct` | `float` | 0.0 | Minimum NMTC-eligible fraction |

All constraints are soft-checked: the optimizer tries its best to satisfy them. If the constraints are collectively infeasible (e.g., `min_states=10` when the pipeline only covers 6 states), the optimizer returns the best feasible result it can find and sets `constraints_satisfied=False` with an explanation in `infeasibility_reason`.

---

## Setting up constraints for a real application

For a typical $55MM application targeting strong alignment:

```python
from nmtcapp.optimizer.constraints import OptimizationConstraints

constraints = OptimizationConstraints(
    min_total_qei=45_000_000,       # don't underutilize the award
    max_total_qei=55_000_000,       # match your requested allocation
    min_projects=10,                 # winner median is 13; 10 is minimum competitive
    min_states=5,                    # above winner p25 of 4 states
    min_distress_pct=0.72,          # above the winner p25 floor
    required_sectors=["healthcare"], # must have at least one healthcare project
    max_single_sector_pct=0.40,     # enforce sector diversity ceiling
)

result = app.optimize_pipeline(constraints, max_iterations=500)
```

`max_iterations` (default 500) controls how many swap attempts the local search makes. For pipelines under 30 projects, 500 iterations is usually sufficient to converge. For larger pipelines you can increase to 1000+ with modest additional runtime.

---

## Reading the OptimizationResult

```python
result = app.optimize_pipeline(constraints)

# Summary to terminal
print(result.summary())

# Selected project list
for project in result.selected_projects:
    print(f"  {project.project_id}: {project.project_name} ({project.state})")

# Total QEI of selected set
total_qei = sum(p.qei_request for p in result.selected_projects)
print(f"Total selected QEI: ${total_qei:,.0f}")

# Alignment score improvement
print(f"Score: {result.alignment_score_before*100:.1f} → {result.alignment_score_after*100:.1f}")

# Per-dimension improvements
for dim, delta in result.dimensional_improvements.items():
    print(f"  {dim}: {delta*100:+.1f} pts")

# Were all constraints satisfied?
if not result.constraints_satisfied:
    print(f"Infeasibility: {result.infeasibility_reason}")

# Serialize to JSON
import json
print(json.dumps(result.to_dict(), indent=2))
```

### OptimizationResult fields

| Field | Type | Description |
|-------|------|-------------|
| `selected_projects` | `list[PipelineProject]` | Projects in the optimized subset |
| `objective_score` | `float` | Composite alignment score of selected set (0.0–1.0) |
| `alignment_score_before` | `float` | Score of the original full pipeline (0.0–1.0) |
| `alignment_score_after` | `float` | Score of the optimized subset (0.0–1.0) |
| `constraints_satisfied` | `bool` | True if all constraints were satisfied |
| `infeasibility_reason` | `str` | Description of the violated constraint if any |
| `dimensional_improvements` | `dict[str, float]` | Per-dimension score change (positive = improvement) |
| `iterations` | `int` | Number of accepted swaps in local search |
| `methodology_note` | `str` | Always-present disclosure about the optimizer objective |

Note: `objective_score`, `alignment_score_before`, and `alignment_score_after` are in the range [0.0, 1.0]. Multiply by 100 for the human-readable 0–100 scale shown in `summary()`.

---

## Full example workflow

```python
from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline
from nmtcapp.optimizer.constraints import OptimizationConstraints

# 1. Build application with a large candidate pool
cde = CDEProfile.from_yaml("my_cde.yaml")
pipeline = Pipeline.from_csv("candidate_pool.csv")   # e.g. 30 projects

app = Application(cde=cde, requested_allocation=55_000_000)
app.add_pipeline(pipeline)

# 2. Score the full pipeline first (optional, for comparison)
full_score = app.score_win_probability()
print(f"Full pipeline score: {full_score.composite_score:.1f}/100")

# 3. Define constraints matching your application parameters
constraints = OptimizationConstraints(
    max_total_qei=55_000_000,
    min_projects=10,
    min_states=5,
    min_distress_pct=0.72,
    max_single_sector_pct=0.40,
)

# 4. Run optimizer
result = app.optimize_pipeline(constraints, max_iterations=500)
print(result.summary())

# 5. Replace pipeline with optimized subset
from nmtcapp.core.pipeline import Pipeline
optimized_pipeline = Pipeline(projects=result.selected_projects)
app.add_pipeline(optimized_pipeline)   # clears cache, ready to re-analyze

# 6. Verify improvement
new_score = app.score_win_probability()
print(f"Optimized score: {new_score.composite_score:.1f}/100 [{new_score.competitive_tier}]")

# 7. Generate final outputs
paths = app.generate("./final_drafts/")
```

---

## Practical notes

**Candidate pool size matters.** The more projects you include in the initial pipeline, the more room the optimizer has to find a better subset. A pipeline of 15 projects targeting a $45MM application has limited optimization headroom. A pipeline of 30+ projects covering diverse states and sectors gives the optimizer meaningful choices.

**Constraints that are too tight reduce optimizer effectiveness.** If `min_total_qei` is close to `max_total_qei` and the pipeline has projects of varying sizes, the optimizer may be forced into configurations that are suboptimal on alignment metrics. Allow some slack — for example, if your requested allocation is $55MM, set `max_total_qei=55_000_000` but `min_total_qei=45_000_000`.

**The optimizer does not perform portfolio construction optimization** — it does not model leverage ratios, tax credit pricing, or investor requirements. These factors should be reviewed separately with your NMTC deal team.

# Visualizations

All five visualization functions produce 300 DPI PNG files suitable for embedding in presentations, Word documents, or reports. They require `matplotlib>=3.7`:

```bash
pip install "nmtc-application-builder[viz]"
```

Each function takes an `Application` instance and an output file path, runs `analyze()` internally (using the cache if available), and returns the output path.

---

## plot_pipeline_map

```python
from nmtcapp.visualization import plot_pipeline_map

plot_pipeline_map(app, "./charts/pipeline_map.png")
```

**What it shows:** A simplified US map (contiguous 48 states + DC) with pipeline projects plotted as scatter dots positioned at state centroids. Dot size is proportional to the project's QEI request — larger dots represent larger investments. Dots are color-coded by distress level: red (deep), yellow (severe), green (LIC), gray (unknown/other).

**Why it matters:** Reviewers and internal stakeholders immediately see geographic spread and distress depth without reading the data table. A map dominated by red dots across many states is the visual signature of a competitive application.

**Notes:**
- Alaska and Hawaii are excluded from the contiguous map view.
- Projects are positioned at state centroids, not exact addresses. Do not use this chart as a precise geographic map — it is a distribution visualization. See [Limitations](../about/limitations.md) for the geographic data note.
- Dot positions include a small random jitter so projects in the same state are visible as separate dots rather than stacked.

```python
# Full example
from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline
from nmtcapp.visualization import plot_pipeline_map

cde = CDEProfile.sample()
app = Application(cde=cde, requested_allocation=65_000_000)
app.add_pipeline(Pipeline.sample(n=20))

path = plot_pipeline_map(app, "./pipeline_map.png")
print(f"Saved to: {path}")
```

---

## plot_distress_heatmap

```python
from nmtcapp.visualization import plot_distress_heatmap

plot_distress_heatmap(app, "./charts/distress_heatmap.png")
```

**What it shows:** A horizontal bar chart with one bar per state (top 15 by QEI). Bar length represents total QEI in that state. Bar color represents the dominant distress level of projects in that state: red (deep), yellow (severe), green (LIC), gray (other). Dollar labels appear at the end of each bar.

**Why it matters:** Shows at a glance which states carry the most QEI and whether those states are in the high-distress range. A chart where the longest bars are red indicates both scale and community need alignment.

**Chart properties:**
- Sorted by QEI descending (highest-QEI state at top)
- Maximum 15 states shown
- X-axis formatted as "$XM"
- Professional styling: no top/right spines, light gray grid

```python
plot_distress_heatmap(app, "./distress_heatmap.png")
```

---

## plot_sector_distribution

```python
from nmtcapp.visualization import plot_sector_distribution

plot_sector_distribution(app, "./charts/sector_mix.png")
```

**What it shows:** A horizontal bar chart of QEI by sector, sorted by QEI descending. Bars are color-coded by CDFI Fund priority tier: deep blue (high priority: healthcare, affordable housing, education), medium blue (medium priority: small business, mixed use), light blue (other sectors). Each bar shows the sector's percentage of total QEI.

**Reference annotation:** The chart includes a note that "Winners typically have ≥50% in high-priority sectors (healthcare, affordable housing, education)."

**Why it matters:** Quick visual check on whether your sector mix aligns with CDFI Fund priority areas. A chart dominated by high-priority sectors (deep blue) is the target pattern.

```python
plot_sector_distribution(app, "./sector_mix.png")
```

---

## plot_readiness_radar

```python
from nmtcapp.visualization import plot_readiness_radar

plot_readiness_radar(app, "./charts/readiness_radar.png")
```

**What it shows:** A spider/radar chart with five axes — one for each win-alignment dimension (Distress, Geographic, Impact, Sector, Pipeline). Each axis runs from 0 to 100. The chart overlays two polygons:

- **Your Pipeline** (solid deep blue line, light fill) — your dimensional alignment scores
- **Winner Benchmark** (dashed amber line) — the competitive threshold of 75 on each dimension

**Why it matters:** Immediately shows which dimensions are strong (extending beyond the benchmark line) and which are weak (falling inside it). The radar chart is the most effective single visualization for communicating application strengths and gaps to a CDE board or investor.

**Title includes** the composite score and competitive tier (e.g., "Win Alignment Radar — 71/100 [COMPETITIVE]"). The title color reflects the tier: green (strong), blue (competitive), yellow (marginal), red (weak).

```python
plot_readiness_radar(app, "./readiness_radar.png")
```

---

## plot_winner_alignment

```python
from nmtcapp.visualization import plot_winner_alignment

plot_winner_alignment(app, "./charts/winner_alignment.png")
```

**What it shows:** A three-panel horizontal bar chart comparing your pipeline on three key metrics against historical winner distributions:

1. **Distress % (Deep + Severe)** — your value vs. winner P25, P50 (median), P75
2. **States Served** — your state count vs. winner P25, P50, P75
3. **Jobs per $MM QEI** — your jobs-per-million vs. winner P25, P50, P75

Each panel shows four bars: Winner P25, Winner P50 (Median), Winner P75, and Your Pipeline. A dashed amber vertical line marks the competitive threshold (P50). Your pipeline bar is dark blue; winner bars are light blue.

**Why it matters:** The most data-dense visualization — it places your pipeline
against this tool's own reference bands on three metrics. **The P25/P50/P75
bands are `HOUSE` values: unsourced round numbers this package chose, not a
distribution of past Allocatees and not percentiles of anything published.**
This paragraph used to say the chart "shows exactly where you stand relative to
the winner distribution" and that clearing P50 put a pipeline "in competitive
territory"; there is no such distribution, and clearing a house band predicts
no funding outcome. Read a bar that falls short as a prompt to look at that
metric, not as a measured gap against real applicants.

```python
plot_winner_alignment(app, "./winner_alignment.png")
```

---

## Charts are NOT put into any generated document

**No chart is placed into any output format.** Not into Word, not into PDF,
not into the workbook, not into markdown. `app.generate()` writes text and
tables only; the five visualization functions are yours to call, and what they
return is a PNG path.

This section previously said the opposite: it claimed `app.generate()` with
Word output enabled produced all five charts and put them into the document
sections automatically, described temporary files being removed afterwards,
and gave an install flag for making it happen. **None of that was ever true on
any release**, and it directly contradicted
[output-formats.md](output-formats.md#visualizations-are-not-embedded-in-any-generated-document),
which says so correctly in the same documentation set.

**The false version was not a harmless docs bug.** `plot_winner_alignment`
draws nine constants that are all `HOUSE` — unsourced round numbers this
package chose, not measurements of past Allocatees. A page telling a reader
those charts already go into the filed application is exactly what would
license someone to "fix" the code to match the page, and put nine invented
comparisons into a document a CDE files with the CDFI Fund. The mismatch
between page and code was the only thing standing between them.

If you want a chart in your application, place it yourself, and read
[output-formats.md](output-formats.md) first for why this package will not do
it for you.

---

## Customizing chart output

All five functions return the output path as a string. You can generate charts to any location:

```python
import os

chart_dir = "./charts/"
os.makedirs(chart_dir, exist_ok=True)

from nmtcapp.visualization import (
    plot_pipeline_map, plot_distress_heatmap, plot_sector_distribution,
    plot_readiness_radar, plot_winner_alignment,
)

charts = {
    "map":       plot_pipeline_map(app, f"{chart_dir}pipeline_map.png"),
    "distress":  plot_distress_heatmap(app, f"{chart_dir}distress_heatmap.png"),
    "sector":    plot_sector_distribution(app, f"{chart_dir}sector_mix.png"),
    "radar":     plot_readiness_radar(app, f"{chart_dir}readiness_radar.png"),
    "alignment": plot_winner_alignment(app, f"{chart_dir}winner_alignment.png"),
}

for name, path in charts.items():
    print(f"{name}: {path}")
```

All charts are saved at 300 DPI with white background (`facecolor="white"`), suitable for professional print use. The figure size and DPI are fixed — the library does not currently expose chart size as a parameter.

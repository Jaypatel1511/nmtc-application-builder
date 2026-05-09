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

**Why it matters:** The most data-dense visualization — shows exactly where you stand relative to the winner distribution on the three most important metrics. A pipeline bar that extends past the P50 line on all three panels is in competitive territory. A bar that falls short of P25 on any panel signals a critical gap.

```python
plot_winner_alignment(app, "./winner_alignment.png")
```

---

## Embedding in Word output

When you call `app.generate()` with Word output enabled, all five charts are automatically generated and embedded in the appropriate document sections. You do not need to call visualization functions separately — the `WordApplicationBuilder` handles this internally.

Charts are generated as temporary files during document construction and deleted after embedding. If `matplotlib` is not installed, the charts are omitted without error and the document is still generated.

To ensure charts are included in Word output:

```bash
pip install "nmtc-application-builder[output,viz]"
```

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

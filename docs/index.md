# NMTC Application Builder

**The open-source intelligence platform for competitive CDFI Fund applications.**

---

New Markets Tax Credit allocation applications are decided on margin. Two CDEs with comparable missions and track records can receive divergent outcomes because one pipeline had 82% deep-distress concentration and the other had 67%. One had projects in 9 states; the other had 4. NMTC Application Builder exists to close that information gap — giving every CDE the same benchmarking intelligence that previously required expensive consultants or years of pattern-recognition experience.

The library reads your project pipeline, enriches each project with NMTC eligibility and distress-level data, and scores your application against the CDFI Fund's **published CY 2024-2025 Review Process** criteria — Business Strategy (0–50), Community Outcomes (0–50), and Priority Points (0–10). It identifies exactly which section minimums you are and aren't meeting, generates prioritized recommendations with CDFI Fund citations, and produces a complete Word/Excel/PDF/Markdown application package. All in Python, all open source.

---

## What it does

!!! info "Pipeline Analysis"
    Enriches each project with NMTC eligibility (census tract lookup via `nmtc-mapper`) and deal economics (NMTC credit calculation via `nmtc-calc`). Produces distress concentration, geographic diversity, sector mix, and impact metrics in one call.

!!! info "Win Alignment Scoring"
    Scores your application against the CDFI Fund's published CY 2024-2025 criteria: Business Strategy (0–50), Community Outcomes (0–50), and Priority Points (0–10 bonus). Returns an aggregate base score (0–100) and tier classification: **Not Qualified** / **Highly Qualified** / **Top Tier**. **This is not a win probability — see the methodology note below.**

!!! info "Actionable Recommendations"
    Generates specific, quantified recommendations ranked by priority (critical / high / medium). Each recommendation includes a numeric improvement estimate, not just generic advice.

!!! info "Pipeline Optimization"
    Uses greedy construction + swap-based local search to find the subset of your pipeline that maximizes alignment score subject to QEI budget, project count, state diversity, and sector constraints.

!!! info "Document Generation"
    Renders a complete NMTC application package — CDFI Fund section structure (A through E), all required data tables, and supporting visualizations — in Word, Excel, PDF, and Markdown.

---

## 60-second quickstart

```python
from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline

cde = CDEProfile.sample()
pipeline = Pipeline.sample(n=20)
app = Application(cde=cde, requested_allocation=65_000_000)
app.add_pipeline(pipeline)
paths = app.generate("./drafts/")
```

That five-line block produces a complete application package (Word, Excel, PDF, Markdown) in `./drafts/`, runs all intelligence analyses, and writes the pipeline analysis summary to the terminal.

[Get started with Installation](installation.md){ .md-button .md-button--primary }
[Read the Quickstart](quickstart.md){ .md-button }
[View on GitHub](https://github.com/Jaypatel1511/nmtc-application-builder){ .md-button }

---

!!! warning "Methodology Disclosure"
    The score produced by `score_win_probability()` measures alignment with the CDFI Fund's **published** CY 2024-2025 evaluation criteria — it is **not** a probability of receiving an allocation. The CDFI Fund's actual scoring rubric is proprietary; sub-score weights are this tool's best-effort interpretation of the published guidance. A high score reflects strong self-assessed positioning; it does not guarantee funding. Always have a qualified CDFI/NMTC practitioner review your application before submission.

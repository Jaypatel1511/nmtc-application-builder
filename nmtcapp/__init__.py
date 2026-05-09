"""
nmtc-application-builder — Full Platform: Pipeline Intelligence, Output Renderers,
Win Alignment Scoring, Pipeline Optimization, and Visualization
===============================================================================
Flagship NMTC application intelligence platform for CDEs.

Covers:
- Week 1: Foundation — CDEProfile, Pipeline, PipelineProject, CSV/YAML loading
- Week 2: Output Renderers — Word, Excel, PDF, Markdown application documents
- Week 3: Intelligence — distress analysis, geographic diversity, sector mix,
  win alignment scoring, pipeline optimization, pattern analysis
- Week 4: Visualization — pipeline maps, distress heatmaps, sector charts,
  radar charts, winner alignment plots; CLI entry point

Quick start::

    from nmtcapp.core.application import Application
    from nmtcapp.core.cde import CDEProfile
    from nmtcapp.core.pipeline import Pipeline

    cde = CDEProfile.sample()
    pipeline = Pipeline.sample(n=20)

    app = Application(cde=cde, requested_allocation=65_000_000)
    app.add_pipeline(pipeline)
    analysis = app.analyze()
    analysis.summary()

    # Generate Word, Excel, PDF, and Markdown outputs
    paths = app.generate("./drafts/")

    # Score win alignment
    score = app.score_win_probability()
    print(score.summary())

    # Generate visualizations (requires matplotlib)
    from nmtcapp.visualization import plot_readiness_radar
    plot_readiness_radar(app, "./radar.png")
"""
__version__ = "1.0.0"
__author__ = "Jay Patel"

from nmtcapp.core.application import Application, ApplicationAnalysis
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.visualization import (
    plot_pipeline_map,
    plot_distress_heatmap,
    plot_sector_distribution,
    plot_readiness_radar,
    plot_winner_alignment,
)

__all__ = [
    "Application",
    "ApplicationAnalysis",
    "CDEProfile",
    "Pipeline",
    "PipelineProject",
    "plot_pipeline_map",
    "plot_distress_heatmap",
    "plot_sector_distribution",
    "plot_readiness_radar",
    "plot_winner_alignment",
    "__version__",
]

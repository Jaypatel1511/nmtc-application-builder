"""
nmtc-application-builder — Weeks 1–2: Foundation, Pipeline Intelligence & Output Renderers
===========================================================================================
Flagship NMTC application intelligence platform for CDEs.

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
"""
__version__ = "0.2.0"
__author__ = "Jay Patel"

from nmtcapp.core.application import Application, ApplicationAnalysis
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject

__all__ = [
    "Application",
    "ApplicationAnalysis",
    "CDEProfile",
    "Pipeline",
    "PipelineProject",
    "__version__",
]

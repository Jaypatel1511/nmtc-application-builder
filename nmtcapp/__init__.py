"""
nmtc-application-builder — Week 1: Foundation & Pipeline Intelligence
======================================================================
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
"""
__version__ = "0.1.0"
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

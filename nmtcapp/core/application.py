"""Master Application class — central entry point for all functionality."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from nmtcapp.intelligence.benchmarks import BenchmarkComparison
    from nmtcapp.intelligence.recommendations import RecommendationSet
    from nmtcapp.intelligence.win_probability import WinProbabilityScore
    from nmtcapp.optimizer.constraints import OptimizationConstraints
    from nmtcapp.optimizer.pipeline_optimizer import OptimizationResult

from nmtcapp.core.application_round import round_label
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalyzer, PipelineAnalysisResult
from nmtcapp.validation.completeness_check import check_completeness
from nmtcapp.validation.consistency_check import check_consistency
from nmtcapp.validation.eligibility_check import check_eligibility
from nmtcapp.validation.readiness_score import ReadinessScore, compute_readiness_score
from nmtcapp.data.schema import ValidationResult

logger = logging.getLogger(__name__)

#: The optional-dependency group that carries every renderer library. Named
#: here so the CLI, the scaffold and the skip message below say the same thing.
OUTPUT_EXTRA = "output"

#: The exact command that turns two output formats into four.
OUTPUT_EXTRA_INSTALL = f'pip install "nmtc-application-builder[{OUTPUT_EXTRA}]"'


def _skip_message(fmt: str, library: str) -> str:
    """The line a CDE sees when a renderer is skipped for a missing library.

    IT USED TO NAME THE LIBRARY AND NOTHING ELSE (1.3.1 F4)::

        python-docx not installed — skipping Word output

    ``pyproject.toml`` defines an ``output`` extra carrying exactly these three
    libraries, and NOTHING A CDE FOLLOWING THE ADVERTISED PATH EVER NAMED IT —
    not ``nmtcapp init``'s "Next steps", not the notebook the scaffold writes,
    and not this line, which is the only place the absence is ever mentioned.
    So a CDE pip-installs the package, generates, gets Markdown, and never
    learns that the PDF and Word renderers exist. Two of four output formats,
    invisible, on the surface whose whole job is to say what went wrong.

    "python-docx not installed" is also the wrong instruction to leave a reader
    with: installing python-docx alone fixes Word and leaves PDF missing, which
    is how someone arrives at three of four formats and stops.

    Example::

        _skip_message("PDF", "reportlab")[:40]   # -> 'PDF output skipped: reportlab is not in'
    """
    return (
        f"{fmt} output skipped: {library} is not installed. All four output "
        f"formats are available through the '{OUTPUT_EXTRA}' extra — install "
        f"it with:  {OUTPUT_EXTRA_INSTALL}"
    )


@dataclass
class ApplicationAnalysis:
    """Comprehensive result from Application.analyze().

    Contains all intelligence analyses, validation results, and readiness score.
    """
    cde_name: str
    requested_allocation: float
    application_round: Optional[str]
    pipeline_result: PipelineAnalysisResult
    distress_analysis: dict
    geographic_analysis: dict
    sector_analysis: dict
    impact_summary: dict
    deal_economics: dict
    validation_results: List[ValidationResult]
    readiness_score: ReadinessScore
    analyzed_at: str

    def summary(self) -> None:
        """Print a rich human-readable summary of the full analysis.

        Example::

            analysis = app.analyze()
            analysis.summary()
        """
        passed = sum(1 for v in self.validation_results if v.passed)
        total_val = len(self.validation_results)
        print("\n" + "=" * 70)
        print(f"  NMTC APPLICATION ANALYSIS")
        print(f"  CDE:   {self.cde_name}")
        print(f"  Round: {round_label(self.application_round)}  |  "
              f"Requested: ${self.requested_allocation:,.0f}")
        print(f"  Analyzed: {self.analyzed_at[:19]}")
        print("=" * 70)
        print(self.pipeline_result.summary())
        print()
        print("── Validation ──────────────────────────────────────────────────")
        for vr in self.validation_results:
            print(vr.summary())
        print(f"\n  {passed}/{total_val} checks passed")
        print()
        print(self.readiness_score.summary())

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dictionary.

        Example::

            import json
            data = analysis.to_dict()
            print(json.dumps(data, indent=2))
        """
        return {
            "cde_name": self.cde_name,
            "requested_allocation": self.requested_allocation,
            "application_round": self.application_round,
            "analyzed_at": self.analyzed_at,
            "pipeline_result": self.pipeline_result.to_dict(),
            "distress_analysis": self.distress_analysis,
            "geographic_analysis": self.geographic_analysis,
            "sector_analysis": self.sector_analysis,
            "impact_summary": self.impact_summary,
            "deal_economics": self.deal_economics,
            "validation_results": [
                {
                    "check_name": v.check_name,
                    "passed": v.passed,
                    "issues": v.issues,
                    "warnings": v.warnings,
                }
                for v in self.validation_results
            ],
            "readiness_score": self.readiness_score.to_dict(),
        }


class Application:
    """Master orchestration class — entry point for all NMTC application functionality.

    Combines a CDE profile and a project pipeline, then produces a comprehensive
    intelligence report via :meth:`analyze`.

    Example::

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

    def __init__(
        self,
        cde: CDEProfile,
        requested_allocation: float,
        application_round: Optional[str] = None,
    ) -> None:
        if not isinstance(cde, CDEProfile):
            raise TypeError("cde must be a CDEProfile instance")
        if requested_allocation <= 0:
            raise ValueError("requested_allocation must be > 0")

        self.cde = cde
        self.requested_allocation = requested_allocation
        self.application_round = application_round
        self._pipeline: Optional[Pipeline] = None
        self._analysis_cache: Optional[ApplicationAnalysis] = None

        # %,.0f IS NOT A FORMAT (1.5.0 S6). printf has no ',' flag, so this
        # raised ValueError inside logging on EVERY Application construction at
        # INFO or below -- swallowed by logging's own error handler, which
        # prints a traceback to stderr and returns, so nothing crashed and
        # nothing was logged either. The comma grouping belongs to str.format
        # and f-strings; the %-style equivalent is to format the number first.
        logger.info(
            "Application created for %s — round %s, allocation $%s",
            cde.name, application_round, f"{requested_allocation:,.0f}",
        )

    @property
    def pipeline(self) -> Optional[Pipeline]:
        return self._pipeline

    def add_pipeline(self, pipeline: Pipeline) -> None:
        """Set the project pipeline, replacing any existing pipeline.

        Example::

            app.add_pipeline(Pipeline.sample(n=20))
        """
        if not isinstance(pipeline, Pipeline):
            raise TypeError("pipeline must be a Pipeline instance")
        self._pipeline = pipeline
        self._analysis_cache = None
        logger.info("Pipeline set: %d projects", len(pipeline))

    def add_project(self, project: PipelineProject) -> None:
        """Add a single project to the pipeline.

        Creates a new Pipeline if none exists.

        Example::

            app.add_project(PipelineProject(...))
        """
        if not isinstance(project, PipelineProject):
            raise TypeError("project must be a PipelineProject instance")
        if self._pipeline is None:
            self._pipeline = Pipeline()
        self._pipeline.add(project)
        self._analysis_cache = None
        logger.info("Project added: %s", project.project_id)

    def analyze(self) -> ApplicationAnalysis:
        """Run comprehensive analysis and return an :class:`ApplicationAnalysis`.

        Orchestrates:
        1. Pipeline eligibility enrichment (nmtc-mapper)
        2. Deal economics computation (nmtc-calc)
        3. Distress, geographic, sector, and impact analyses
        4. Eligibility, completeness, and consistency validation
        5. Readiness score computation

        Results are cached — calling analyze() multiple times is safe and
        returns the same result unless the pipeline is modified.

        Example::

            analysis = app.analyze()
            analysis.summary()
        """
        if self._pipeline is None or len(self._pipeline) == 0:
            raise ValueError(
                "Cannot analyze — no pipeline projects. "
                "Call add_pipeline() or add_project() first."
            )

        if self._analysis_cache is not None:
            logger.debug("Returning cached analysis result")
            return self._analysis_cache

        logger.info("Running full application analysis for %s", self.cde.name)

        try:
            pipeline_result = PipelineAnalyzer().analyze(self._pipeline)
        except Exception as exc:
            raise RuntimeError(
                f"Pipeline analysis failed for {self.cde.name}: {exc}"
            ) from exc

        try:
            eligibility_val = check_eligibility(self._pipeline)
            completeness_val = check_completeness(self)
            # Hand the economics across rather than letting check_consistency
            # call back into analyze(): its cross-surface arithmetic check needs
            # the same deal_economics Section D renders, and this call site is
            # inside analyze(), before the cache is set.
            consistency_val = check_consistency(
                self, deal_economics=pipeline_result.deal_economics_summary
            )
            validation_results = [eligibility_val, completeness_val, consistency_val]
        except Exception as exc:
            raise RuntimeError(f"Validation failed for {self.cde.name}: {exc}") from exc

        try:
            readiness = compute_readiness_score(pipeline_result, validation_results)
        except Exception as exc:
            raise RuntimeError(f"Readiness scoring failed: {exc}") from exc

        analysis = ApplicationAnalysis(
            cde_name=self.cde.name,
            requested_allocation=self.requested_allocation,
            application_round=self.application_round,
            pipeline_result=pipeline_result,
            distress_analysis=pipeline_result.distress_breakdown,
            geographic_analysis=pipeline_result.geographic_diversity,
            sector_analysis=pipeline_result.sector_mix,
            impact_summary=pipeline_result.aggregate_impact,
            deal_economics=pipeline_result.deal_economics_summary,
            validation_results=validation_results,
            readiness_score=readiness,
            analyzed_at=datetime.now().isoformat(),
        )

        self._analysis_cache = analysis
        logger.info(
            "Analysis complete — readiness score: %.1f (%s)",
            readiness.overall_score, readiness.grade,
        )
        return analysis

    def summary(self) -> None:
        """Run analyze() and print a human-readable summary.

        Example::

            app.summary()
        """
        self.analyze().summary()

    def generate(self, output_dir: str = "./drafts", formats: list = None) -> dict:
        """Generate the full NMTC application document package.

        Runs analyze() then renders all requested output formats. Creates the
        output directory if it does not exist.

        Args:
            output_dir: Directory for generated files.
            formats: List of formats to generate. Defaults to all available
                     formats: ``["markdown", "word", "excel", "pdf"]``.

        Returns:
            Dict mapping format name to output path.

        Example::

            paths = app.generate("./drafts/")
            print(paths)
            # {"markdown": "./drafts/application.md",
            #  "word": "./drafts/application.docx",
            #  "excel": "./drafts/application.xlsx",
            #  "pdf": "./drafts/application.pdf"}
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        if formats is None:
            formats = ["markdown", "word", "excel", "pdf"]

        analysis = self.analyze()
        slug = self.cde.cde_id or "application"
        paths = {}

        if "markdown" in formats:
            from nmtcapp.renderers.markdown_builder import MarkdownApplicationBuilder
            path = os.path.join(output_dir, f"{slug}_application.md")
            MarkdownApplicationBuilder(self, analysis).save(path)
            paths["markdown"] = path

        if "word" in formats:
            try:
                from nmtcapp.renderers.word_builder import WordApplicationBuilder
                path = os.path.join(output_dir, f"{slug}_application.docx")
                WordApplicationBuilder(self, analysis).save(path)
                paths["word"] = path
            except ImportError:
                logger.warning(_skip_message("Word", "python-docx"))

        if "excel" in formats:
            try:
                from nmtcapp.renderers.excel_builder import ExcelApplicationBuilder
                path = os.path.join(output_dir, f"{slug}_application.xlsx")
                ExcelApplicationBuilder(self, analysis).save(path)
                paths["excel"] = path
            except ImportError:
                logger.warning(_skip_message("Excel", "openpyxl"))

        if "pdf" in formats:
            try:
                from nmtcapp.renderers.pdf_builder import PDFApplicationBuilder
                path = os.path.join(output_dir, f"{slug}_application.pdf")
                PDFApplicationBuilder(self, analysis).save(path)
                paths["pdf"] = path
            except ImportError:
                logger.warning(_skip_message("PDF", "reportlab"))

        logger.info(
            "generate() complete — %d files written to %s: %s",
            len(paths), output_dir, ", ".join(paths.keys()),
        )
        return paths

    def score_win_probability(self) -> "WinProbabilityScore":
        """Score this application against the CDFI Fund's CY 2024-2025 framework.

        Scores two sections (Business Strategy 50 pts, Community Outcomes 50 pts)
        plus Priority Points (10 pts). Returns a :class:`WinProbabilityScore` with
        tier classification (Not Qualified / Highly Qualified / Top Tier) and a
        mandatory methodology disclosure.

        Example::

            score = app.score_win_probability()
            print(score.summary())
        """
        from nmtcapp.intelligence.win_probability import WinProbabilityModel
        analysis = self.analyze()
        cde_attributes = dict(self.cde.extra) if self.cde.extra else {}
        # Derive prior award count from the awards list if not explicitly set
        if "prior_award_count" not in cde_attributes:
            cde_attributes["prior_award_count"] = len(self.cde.prior_awards)
        return WinProbabilityModel().score(
            analysis.pipeline_result,
            self.requested_allocation,
            self.application_round,
            cde_attributes=cde_attributes,
        )

    def benchmark(self) -> "BenchmarkComparison":
        """Compare this application against historical NMTC winner benchmarks.

        Example::

            bc = app.benchmark()
            print(bc.summary())
        """
        from nmtcapp.intelligence.benchmarks import HistoricalBenchmarks
        analysis = self.analyze()
        return HistoricalBenchmarks().compare(
            analysis.pipeline_result, self.requested_allocation
        )

    def recommendations(self) -> "RecommendationSet":
        """Generate actionable, quantified recommendations for improving competitiveness.

        Uses the same CDE attributes as :meth:`score_win_probability` so that
        the recommendation text is consistent with the displayed scores.

        Example::

            recs = app.recommendations()
            print(recs.summary())
        """
        from nmtcapp.intelligence.benchmarks import HistoricalBenchmarks
        from nmtcapp.intelligence.recommendations import RecommendationEngine
        from nmtcapp.intelligence.win_probability import WinProbabilityModel
        analysis = self.analyze()
        bc = HistoricalBenchmarks().compare(
            analysis.pipeline_result, self.requested_allocation
        )
        cde_attributes = dict(self.cde.extra) if self.cde.extra else {}
        if "prior_award_count" not in cde_attributes:
            cde_attributes["prior_award_count"] = len(self.cde.prior_awards)
        win_score = WinProbabilityModel().score(
            analysis.pipeline_result,
            self.requested_allocation,
            self.application_round,
            cde_attributes=cde_attributes,
        )
        return RecommendationEngine().recommend(
            analysis.pipeline_result, bc, win_score
        )

    def optimize_pipeline(
        self,
        constraints: Optional["OptimizationConstraints"] = None,
        max_iterations: int = 500,
    ) -> "OptimizationResult":
        """Optimize the pipeline to maximize alignment with historical winner patterns.

        Uses greedy construction + swap-based local search. Handles infeasible
        constraints gracefully — always returns a result.

        Args:
            constraints: Optional :class:`~nmtcapp.optimizer.constraints.OptimizationConstraints`.
                         Defaults to unconstrained (all projects eligible).
            max_iterations: Maximum local-search iterations (default 500).

        Example::

            from nmtcapp.optimizer import OptimizationConstraints
            constraints = OptimizationConstraints(
                max_total_qei=65_000_000,
                min_states=5,
            )
            result = app.optimize_pipeline(constraints)
            print(result.summary())
        """
        from nmtcapp.optimizer.constraints import OptimizationConstraints as OC
        from nmtcapp.optimizer.pipeline_optimizer import PipelineOptimizer
        if self._pipeline is None or len(self._pipeline) == 0:
            raise ValueError(
                "Cannot optimize — no pipeline projects. "
                "Call add_pipeline() or add_project() first."
            )
        c = constraints or OC()
        return PipelineOptimizer(max_iterations=max_iterations).optimize(
            self._pipeline, c, self.requested_allocation
        )

    def to_dict(self) -> dict:
        """Run analyze() and serialize to a JSON-safe dictionary.

        Example::

            import json
            data = app.to_dict()
            print(json.dumps(data, indent=2))
        """
        return self.analyze().to_dict()

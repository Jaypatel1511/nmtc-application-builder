"""Orchestrator that runs all intelligence analyses on a Pipeline."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from nmtcapp.intelligence.distress_analysis import analyze_distress_concentration
from nmtcapp.intelligence.geographic_analysis import analyze_geographic_diversity
from nmtcapp.intelligence.impact_aggregator import aggregate_impact
from nmtcapp.intelligence.sector_analysis import analyze_sector_mix
from nmtcapp.integrations.nmtc_calc_adapter import compute_pipeline_economics
from nmtcapp.integrations.nmtc_mapper_adapter import enrich_pipeline_eligibility

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)


@dataclass
class PipelineAnalysisResult:
    """Comprehensive result from analyzing a CDE's project pipeline.

    Example::

        result = PipelineAnalyzer().analyze(pipeline)
        print(result.summary())
    """
    total_projects: int
    total_qei_request: float
    total_project_cost: float
    eligibility_pct: float
    distress_breakdown: dict
    geographic_diversity: dict
    sector_mix: dict
    aggregate_impact: dict
    deal_economics_summary: dict

    def summary(self) -> str:
        """Return a formatted multi-section text summary.

        Example::

            print(result.summary())
        """
        d = self.distress_breakdown
        g = self.geographic_diversity
        s = self.sector_mix
        i = self.aggregate_impact
        e = self.deal_economics_summary

        lines = [
            "=" * 60,
            "PIPELINE ANALYSIS SUMMARY",
            "=" * 60,
            f"  Projects:        {self.total_projects}",
            f"  Total QEI:       ${self.total_qei_request:>14,.0f}",
            f"  Total Cost:      ${self.total_project_cost:>14,.0f}",
            f"  Eligible:        {self.eligibility_pct:.0%}",
            "",
            "── Distress Concentration ─────────────────────────────",
            f"  Deep/Severe:     {d.get('pct_deep_or_severe', 0):.0%}  "
            f"({'✓' if d.get('meets_target_threshold') else '✗'} target)",
            f"  LIC:             {d.get('pct_lic', 0):.0%}",
            f"  Non-LIC:         {d.get('pct_non_lic', 0):.0%}",
            f"  Native Area:     {d.get('pct_native_area', 0):.0%}",
            f"  Historical Rank: {d.get('vs_historical_winners', 'N/A')}",
            "",
            "── Geographic Diversity ────────────────────────────────",
            f"  States:          {g.get('states_count', 0)}",
            f"  MSAs:            {g.get('msa_count', 0)}",
            f"  Urban/Rural:     {g.get('urban_pct', 0):.0%} / {g.get('rural_pct', 0):.0%}",
            f"  HHI:             {g.get('hhi', 0):.0f}  "
            f"({g.get('geographic_concentration_label', 'N/A')})",
            "",
            "── Sector Mix ──────────────────────────────────────────",
            f"  Sectors:         {s.get('sectors_represented', 0)}",
            f"  Dominant:        {s.get('dominant_sector', 'N/A')}",
            f"  High Priority:   {s.get('high_priority_pct', 0):.0%}",
            f"  Diversity Score: {s.get('sector_diversity_score', 0):.1f}/100",
            "",
            "── Impact Projections ──────────────────────────────────",
            f"  Jobs Created:    {i.get('total_jobs_created', 0):,}",
            f"  Jobs Retained:   {i.get('total_jobs_retained', 0):,}",
            f"  Units Built:     {i.get('total_units_built', 0):,}",
            f"  Sq Ft:           {i.get('total_sq_ft', 0):,.0f}",
            f"  Jobs/$MM QEI:    {i.get('jobs_per_million_qei', 0):.1f}",
            f"  Benchmark:       {i.get('vs_historical_benchmarks', 'N/A')}",
            "",
            "── Deal Economics ──────────────────────────────────────",
            f"  Total NMTCs:     ${e.get('total_nmtcs', 0):>14,.0f}",
            f"  Investor Equity: ${e.get('total_investor_equity', 0):>14,.0f}",
            f"  CDE Fees:        ${e.get('total_cde_fees', 0):>14,.0f}",
            f"  Net Subsidy:     ${e.get('total_net_subsidy', 0):>14,.0f}",
            "=" * 60,
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dictionary."""
        return {
            "total_projects": self.total_projects,
            "total_qei_request": self.total_qei_request,
            "total_project_cost": self.total_project_cost,
            "eligibility_pct": self.eligibility_pct,
            "distress_breakdown": self.distress_breakdown,
            "geographic_diversity": self.geographic_diversity,
            "sector_mix": self.sector_mix,
            "aggregate_impact": self.aggregate_impact,
            "deal_economics_summary": self.deal_economics_summary,
        }


class PipelineAnalyzer:
    """Orchestrates all sub-analyses and eligibility enrichment for a pipeline.

    Example::

        analyzer = PipelineAnalyzer()
        result = analyzer.analyze(pipeline)
        print(result.summary())
    """

    def analyze(self, pipeline: "Pipeline") -> PipelineAnalysisResult:
        """Run all analyses and return a :class:`PipelineAnalysisResult`.

        Steps:
        1. Enrich each project with NMTC eligibility data via nmtc-mapper.
        2. Compute deal economics via nmtc-calc.
        3. Run distress, geographic, sector, and impact analyses.
        4. Assemble and return the result.

        Example::

            result = PipelineAnalyzer().analyze(Pipeline.sample())
        """
        if len(pipeline) == 0:
            logger.warning("PipelineAnalyzer.analyze called with empty pipeline")
            return self._empty_result()

        logger.info("Enriching pipeline (%d projects) with eligibility data", len(pipeline))
        enriched = enrich_pipeline_eligibility(pipeline)

        logger.info("Computing deal economics")
        economics = compute_pipeline_economics(enriched)

        logger.info("Running intelligence analyses")
        distress = analyze_distress_concentration(enriched)
        geographic = analyze_geographic_diversity(enriched)
        sector = analyze_sector_mix(enriched)
        impact = aggregate_impact(enriched)

        total_qei = sum(p.qei_request for p in enriched)
        total_cost = sum(p.total_project_cost for p in enriched)
        eligible_count = sum(1 for p in enriched if p.is_nmtc_eligible)
        eligibility_pct = eligible_count / len(enriched) if len(enriched) > 0 else 0.0

        return PipelineAnalysisResult(
            total_projects=len(enriched),
            total_qei_request=total_qei,
            total_project_cost=total_cost,
            eligibility_pct=eligibility_pct,
            distress_breakdown=distress,
            geographic_diversity=geographic,
            sector_mix=sector,
            aggregate_impact=impact,
            deal_economics_summary=economics,
        )

    def _empty_result(self) -> PipelineAnalysisResult:
        empty_dict: dict = {}
        return PipelineAnalysisResult(
            total_projects=0,
            total_qei_request=0.0,
            total_project_cost=0.0,
            eligibility_pct=0.0,
            distress_breakdown={},
            geographic_diversity={},
            sector_mix={},
            aggregate_impact={},
            deal_economics_summary={},
        )

"""Orchestrator that runs all intelligence analyses on a Pipeline."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from nmtcapp.data.schema import TARGET_DISTRESS_THRESHOLDS
from nmtcapp.intelligence.distress_analysis import analyze_distress_concentration
from nmtcapp.intelligence.geographic_analysis import analyze_geographic_diversity
from nmtcapp.intelligence.impact_aggregator import aggregate_impact
from nmtcapp.intelligence.sector_analysis import analyze_sector_mix
from nmtcapp.integrations.nmtc_calc_adapter import compute_pipeline_economics
from nmtcapp.integrations.nmtc_mapper_adapter import enrich_pipeline_eligibility
from nmtcapp.renderers._cell_format import supplied_total
from nmtcapp.renderers._disclosure import join_truncated
from nmtcapp.renderers._question_22 import Q22_QEI_BASIS_CLAUSE

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
    # "ok" when live CDFI Fund data enriched the pipeline; "unavailable" when
    # it could not be loaded — eligibility figures are then unverified and
    # scoring surfaces must exclude the eligibility component.
    eligibility_data_status: str = "ok"
    eligibility_data_error: Optional[str] = None
    unverified_project_ids: list = field(default_factory=list)

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

        lines = []
        if self.eligibility_data_status != "ok":
            lines.extend([
                "!" * 60,
                "  ELIGIBILITY DATA UNAVAILABLE",
                f"  {self.eligibility_data_error or 'reason unknown'}",
                "  Eligibility and distress figures below are UNVERIFIED and",
                "  excluded from scoring. Do not use for application content.",
                "!" * 60,
            ])
        elif self.unverified_project_ids:
            lines.extend([
                "!" * 60,
                f"  {len(self.unverified_project_ids)} project(s) could not be "
                "location-verified and remain",
                "  UNVERIFIED (no tract assigned): "
                + join_truncated(self.unverified_project_ids),
                "!" * 60,
            ])
        eligible_display = (
            "unverified" if self.eligibility_data_status != "ok"
            else f"{self.eligibility_pct:.0%}"
        )
        lines += [
            "=" * 60,
            "PIPELINE ANALYSIS SUMMARY",
            "=" * 60,
            f"  Projects:        {self.total_projects}",
            f"  Total QEI:       ${self.total_qei_request:>14,.0f}",
            f"  Total Cost:      ${self.total_project_cost:>14,.0f}",
            # "Eligible" is a share of PROJECT COUNT while every figure under
            # Distress Concentration below is a share of QEI. Two denominators
            # under one heading, neither stated. The label now states its own.
            f"  Eligible (by project count): {eligible_display}",
            "",
            "── Distress Concentration (share of pipeline QEI) ─────",
            # The "target" tick was TARGET_DISTRESS_THRESHOLDS' 0.75, which
            # data/schema.py labels a HOUSE HEURISTIC in capitals and warns must
            # not be presented as a Fund figure. Every rendered document got
            # that disclosure in 1.2.0. This block, the one `nmtcapp analyze`
            # prints, did not — it showed a bare "✗ target" against an
            # unattributed bar.
            f"  Deep/Severe:     {d.get('pct_deep_or_severe', 0):.0%}  "
            f"({'✓' if d.get('meets_target_threshold') else '✗'} this tool's own "
            f"≥{TARGET_DISTRESS_THRESHOLDS['target_deep_distress']:.0%} band — "
            "not a CDFI Fund threshold)",
            f"  LIC:             {d.get('pct_lic', 0):.0%}",
            # Non-LIC rolls the "unknown" bucket in with the "ineligible" one
            # (distress_analysis.py:77), so an unverified project is counted as
            # non-LIC. Deep/Severe and LIC are lower bounds and 1.2.0 disclosed
            # them as such; this is the same arithmetic pointing the other way,
            # and it was printed bare. It is an UPPER bound and now says so.
            f"  Non-LIC:         {d.get('pct_non_lic', 0):.0%}"
            + ("  (upper bound — includes unverified)"
               if self.unverified_project_ids else ""),
            # CDE-DECLARED, not tool-derived. See the provenance note on
            # NATIVE_AREA_BASIS in tables/distress_table.
            f"  Native Area:     {d.get('pct_native_area', 0):.0%}  "
            "(CDE-declared; not verified by this tool)",
            "",
            "── Geographic Diversity ────────────────────────────────",
            f"  States:          {g.get('states_count', 0)}",
            f"  MSAs:            {g.get('msa_count', 0)}",
            # THE THREE-WAY SPLIT (1.4.0 R2/R3). This line used to read
            # "Urban/Rural: 93% / 7%" — two figures summing to 100%, with no
            # denominator named and no third state possible, computed as
            # "rural = 1 − (QEI in states absent from a hard-coded list of
            # twelve)". All three parts of that were wrong: the word, the
            # basis, and the arithmetic.
            #
            # It now prints all three buckets. The undetermined one is printed
            # even when it is 0%, deliberately: a reader who only ever sees it
            # when it is non-zero has no way to know the category exists, and
            # would read a 0%-undetermined pipeline's two figures as the same
            # complement this change removed.
            f"  Non-metro:       {g.get('non_metro_pct', 0):.0%}  "
            f"({Q22_QEI_BASIS_CLAUSE})",
            f"  Metropolitan:    {g.get('metro_pct', 0):.0%}",
            f"  Not determined:  {g.get('metro_undetermined_pct', 0):.0%}"
            f"  ({g.get('metro_status_qei', {}).get('undetermined_projects', 0)}"
            " project(s) — counted as neither)",
            "  Question 22 asks what percentage of QLICIs the Applicant "
            "commits to deploy",
            "  in Non-Metropolitan Counties. This is a share of QEI in the "
            "current pipeline,",
            "  not that commitment, and Question 22 is not scored in Phase I.",
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
            # 1.2.1 B-2: an absent column is not a pipeline that builds zero
            # units. `nmtcapp analyze` is where a CDE first reads these back.
            f"  Units Built:     {supplied_total(i.get('total_units_built'))}",
            f"  Sq Ft:           {supplied_total(i.get('total_sq_ft'), '{:,.0f}')}",
            f"  Jobs/$MM QEI:    {i.get('jobs_per_million_qei', 0):.1f}",
            "",
            "── Deal Economics ──────────────────────────────────────",
            f"  Total NMTCs:     ${e.get('total_nmtcs', 0):>14,.0f}",
            f"  Investor Equity: ${e.get('total_investor_equity', 0):>14,.0f}",
            f"  Leverage Loans:  ${e.get('total_leverage_loans', 0):>14,.0f}",
            f"  CDE Fees:        ${e.get('total_cde_fees', 0):>14,.0f}",
            # Was "Net Subsidy". Same figure, honest label: this is QEI minus
            # the CDE fee, ~97.5% of QEI, and it contains the leverage loan the
            # QALICB repays. See section_d_capitalization for the full note.
            f"  QEI less fees:   ${e.get('total_net_subsidy', 0):>14,.0f}",
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
            "eligibility_data_status": self.eligibility_data_status,
            "eligibility_data_error": self.eligibility_data_error,
            "unverified_project_ids": self.unverified_project_ids,
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
        eligible_count = sum(1 for p in enriched if p.is_nmtc_eligible is True)
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
            eligibility_data_status=getattr(enriched, "eligibility_data_status", "ok"),
            eligibility_data_error=getattr(enriched, "eligibility_data_error", None),
            unverified_project_ids=[
                p.project_id for p in enriched if not p.is_enriched
            ],
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

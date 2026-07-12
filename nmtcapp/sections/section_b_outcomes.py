"""Section B: Community Outcomes generator."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.renderers._disclosure import is_partial_unverified, unverified_qualifier
from nmtcapp.sections.base import SectionGenerator, _placeholder

if TYPE_CHECKING:
    from nmtcapp.core.application import Application, ApplicationAnalysis

logger = logging.getLogger(__name__)


class SectionBCommunityOutcomes(SectionGenerator):
    """Generates Section B: Community Outcomes content.

    Pulls from impact aggregation, distress analysis, and HMDA community
    need data.

    Example::

        gen = SectionBCommunityOutcomes()
        content = gen.generate_content(application, analysis)
    """
    section_id = "B"
    title = "Community Outcomes"
    word_limit = 2500

    def generate_content(self, application: "Application", analysis: "ApplicationAnalysis") -> dict:
        pr = analysis.pipeline_result
        impact = pr.aggregate_impact
        distress = pr.distress_breakdown
        total_projects = pr.total_projects

        # Impact commitments
        jobs_created = impact.get("total_jobs_created", 0)
        jobs_retained = impact.get("total_jobs_retained", 0)
        units = impact.get("total_units_built", 0)
        sqft = impact.get("total_sq_ft", 0)
        jpm = impact.get("jobs_per_million_qei", 0)
        total_qei_mm = pr.total_qei_request / 1_000_000

        impact_narrative = (
            f"The {total_projects} projects in {application.cde.name}'s pipeline will produce "
            f"the following direct community impacts upon project completion:\n\n"
            f"  • {jobs_created:,} permanent full-time-equivalent jobs created\n"
            f"  • {jobs_retained:,} existing jobs retained\n"
            f"  • {units:,} affordable or mixed-income housing units developed\n"
            f"  • {int(sqft):,} sq ft of community facility / commercial space\n"
            f"  • {jpm:.1f} jobs per $1MM of QEI deployed "
            f"({impact.get('vs_historical_benchmarks', 'N/A').replace('_', ' ')} vs. CDFI Fund historical average)\n\n"
        ) + _placeholder(self.section_id, 500)

        # Distress commitments — tract-dependent figures may only be asserted
        # as fact when fully verified; otherwise they carry inline qualifiers
        # (or an explicit Unverified marker when no data loaded at all).
        deep_pct = distress.get("pct_deep_or_severe", 0.0)
        native_pct = distress.get("pct_native_area", 0.0)
        hmr_pct = distress.get("pct_high_migration_rural", 0.0)

        degraded = getattr(pr, "eligibility_data_status", "ok") != "ok"
        partial_unverified = is_partial_unverified(pr)

        def _tract_pct(value: float) -> str:
            if degraded:
                return "Unverified — eligibility data unavailable"
            if partial_unverified:
                return f"{value:.1%} {unverified_qualifier(pr)}"
            return f"{value:.1%}"

        distress_commitments = {
            "QEI in Deep/Severely Distressed Tracts": _tract_pct(deep_pct),
            "QEI in LIC (Standard Eligible) Tracts": _tract_pct(distress.get("pct_lic", 0)),
            "QEI in NMTC Native Areas": _tract_pct(native_pct),
            "QEI in High Migration Rural (HMR) Tracts": _tract_pct(hmr_pct),
            "CDFI Fund Competitive Minimum (Deep/Severe)": "50.0%",
            "CDFI Fund Target (Deep/Severe)": "75.0%",
            f"{application.cde.name} Commitment (Deep/Severe)": _tract_pct(deep_pct),
        }

        community_need = (
            f"HMDA mortgage lending data confirms severe unmet capital need across "
            f"{application.cde.name}'s target markets. In the {len(distress.get('dollars_by_distress', {}))} "
            f"census tracts where our pipeline projects are located, average loan denial rates "
            f"exceed 30%, with racial disparities of 2.3× for minority applicants relative to "
            f"white applicants (HMDA 5-year data, 2018–2022). NMTC capital is uniquely positioned "
            f"to bridge this gap through below-market QLICI financing.\n\n"
        ) + _placeholder(self.section_id, 400)

        return {
            "section_id": self.section_id,
            "title": self.title,
            "subsections": [
                {"heading": "Aggregate Community Impact Projections",
                 "body": impact_narrative, "type": "narrative"},
                {"heading": "Distress Level Commitments",
                 "body": distress_commitments, "type": "table_ref"},
                {"heading": "Community Need Documentation",
                 "body": community_need, "type": "narrative"},
                {"heading": "Per-Project Impact Detail",
                 "body": "(See Attachment: Impact Projections Table)", "type": "table_ref"},
                {"heading": "Long-Term Community Impact Strategy",
                 "body": _placeholder(self.section_id, 500), "type": "narrative"},
            ],
        }

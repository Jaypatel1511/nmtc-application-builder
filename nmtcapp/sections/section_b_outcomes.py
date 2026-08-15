"""Section B: Community Outcomes generator."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.data.benchmark_thresholds import (
    DEEP_DISTRESS_MIN_PCT, SEVERE_DISTRESS_MIN_PCT,
)
from nmtcapp.renderers._disclosure import is_partial_unverified, unverified_qualifier
from nmtcapp.sections.base import SectionGenerator, _cde_todo, _placeholder

if TYPE_CHECKING:
    from nmtcapp.core.application import Application, ApplicationAnalysis

logger = logging.getLogger(__name__)


class SectionBCommunityOutcomes(SectionGenerator):
    """Generates Section B: Community Outcomes content.

    Pulls from impact aggregation and distress analysis. Community need is
    not generated: it is emitted as a placeholder for the CDE to document.

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
            # The number, unranked. This line used to append
            # "(average vs. CDFI Fund historical average)" from a threshold
            # comparison that loaded no distribution — see the note in
            # intelligence/impact_aggregator.py.
            f"  • {jpm:.1f} jobs per $1MM of QEI deployed\n\n"
        ) + _placeholder()

        # Distress commitments — tract-dependent figures may only be asserted
        # as fact when fully verified; otherwise they carry inline qualifiers
        # (or an explicit Unverified marker when no data loaded at all).
        deep_pct = distress.get("pct_deep_or_severe", 0.0)
        # DEEP DISTRESS ALONE. The Fund's 20% bar is Deep Distress only, and
        # this figure was computed on every run and reported nowhere — the
        # document printed the 20% commitment directly above the CDE's COMBINED
        # deep+severe share, which is a larger number on a wider base. On the
        # audit's sample that read "20% Deep Distress" above "20.5%", inviting
        # the reader to conclude the bar was met when deep-only was 8.7%.
        deep_only_pct = distress.get("pct_deep", 0.0)
        severe_only_pct = distress.get("pct_severe", 0.0)
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
            # THE TWO BARS HAVE DIFFERENT BASES AND EACH NOW HAS ITS OWN ROW.
            # 85% is severe distress OR multiple indicia; 20% is Deep Distress
            # alone. One number must not be left to answer both, which is what
            # a single combined deep+severe row sitting under both bars did.
            "QEI in Deep Distress Tracts (the 20% bar's own basis)":
                _tract_pct(deep_only_pct),
            "QEI in Severely Distressed Tracts": _tract_pct(severe_only_pct),
            "QEI in Deep or Severely Distressed Tracts (combined)":
                _tract_pct(deep_pct),
            "QEI in LIC (Standard Eligible) Tracts": _tract_pct(distress.get("pct_lic", 0)),
            # CDE-declared. This tool cannot verify a Native Area: the Fund
            # publishes no tract-keyed resource and the determination is a
            # spatial intersection against its CIMS map, not a join. See
            # NATIVE_AREA_BASIS in tables/distress_table.
            "QEI in NMTC Native Areas (CDE-declared, not verified by this tool)":
                _tract_pct(native_pct),
            "QEI in High Migration Rural (HMR) Tracts": _tract_pct(hmr_pct),
            # Was labelled "CDFI Fund Severe Distress Threshold" and cited to
            # the Review Process generally (and, in the attribution allowlist,
            # to a "FAQ #79" that document does not contain). The Review
            # Process states the commitment under "Targeting Areas of Higher
            # Distress (Question 25)", it covers severe distress OR multiple
            # indicia rather than severe distress alone, and it carries a
            # SECOND figure this tool was not reporting at all.
            "CDFI Fund Higher-Distress Commitment (CY 2024-2025)":
                f"{SEVERE_DISTRESS_MIN_PCT:.0%} of QLICIs in areas of severe "
                "distress and/or multiple indicia of distress, and "
                f"{DEEP_DISTRESS_MIN_PCT:.0%} in Deep Distress areas "
                "(CY 2024-2025 NMTC Program Review Process, Targeting Areas of "
                "Higher Distress, Question 25; the CY 2026 NOAA is not yet "
                "published). THE TWO BARS HAVE DIFFERENT BASES: the "
                f"{SEVERE_DISTRESS_MIN_PCT:.0%} covers severe distress OR "
                f"multiple indicia, the {DEEP_DISTRESS_MIN_PCT:.0%} covers Deep "
                "Distress alone. Read each against its own row above; a "
                "combined deep-plus-severe share does not answer the "
                f"{DEEP_DISTRESS_MIN_PCT:.0%} bar.",
            f"{application.cde.name} — measured against the "
            f"{DEEP_DISTRESS_MIN_PCT:.0%} Deep Distress bar":
                _tract_pct(deep_only_pct),
            f"{application.cde.name} — deep or severe distress (combined)":
                _tract_pct(deep_pct),
        }

        # This tool does not retrieve, compute or verify any community-need
        # statistic. Every figure here must come from a source the CDE can
        # produce on request, so the whole subsection is the CDE's to write.
        community_need = (
            _cde_todo(
                "Document unmet capital need in the markets this pipeline serves. "
                "Supply the underlying evidence and cite each source by name, "
                "publisher and vintage — for example credit-access or lending "
                "data for your tracts, unemployment and poverty measures, "
                "business closures or disinvestment history, and community "
                "input gathered by your CDE. "
                "nmtc-application-builder does not compute, retrieve or verify "
                "community-need statistics of any kind, and supplies no figure "
                "for this subsection. No number may be entered here without a "
                "citation the CDE controls and can defend to the CDFI Fund."
            ) + "\n\n"
        ) + _placeholder()

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
                 "body": _placeholder(), "type": "narrative"},
            ],
        }

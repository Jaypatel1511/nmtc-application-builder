"""Section A: Business Strategy generator."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.sections.base import SectionGenerator, _placeholder

if TYPE_CHECKING:
    from nmtcapp.core.application import Application, ApplicationAnalysis

logger = logging.getLogger(__name__)


class SectionABusinessStrategy(SectionGenerator):
    """Generates Section A: Business Strategy content.

    Pulls from CDE mission, target markets, pipeline distress mix,
    geographic diversity, and sector strategy.

    Example::

        gen = SectionABusinessStrategy()
        content = gen.generate_content(application, analysis)
    """
    section_id = "A"
    title = "Business Strategy"
    word_limit = 3000

    def generate_content(self, application: "Application", analysis: "ApplicationAnalysis") -> dict:
        cde = application.cde
        pr = analysis.pipeline_result
        distress = pr.distress_breakdown
        geo = pr.geographic_diversity
        sector = pr.sector_mix

        states = geo.get("states", [])
        states_str = ", ".join(states[:5]) + (" and others" if len(states) > 5 else "")
        dominant_sector = sector.get("dominant_sector", "healthcare")
        deep_pct = distress.get("pct_deep_or_severe", 0.0)
        total_qei = pr.total_qei_request
        total_projects = pr.total_projects

        thesis = (
            f"{cde.name} will deploy ${application.requested_allocation / 1e6:.1f} million in "
            f"NMTC allocation across {total_projects} projects in {len(states)} states — "
            f"targeting {deep_pct:.0%} of QEI in deep and severely distressed census tracts. "
            f"Our pipeline focuses on {dominant_sector.replace('_', ' ')} and complementary "
            f"high-impact sectors in markets where conventional capital is systematically absent."
        ) + _placeholder(self.section_id, self.word_limit)

        target_markets_body = (
            f"Primary geographic targets: {states_str}.\n\n"
            f"{cde.name}'s mission — \"{cde.mission[:200]}...\" — guides our market selection "
            f"toward persistent-poverty counties and high-migration rural communities where "
            f"NMTC leverage is greatest.\n\n"
        ) + _placeholder(self.section_id, 500)

        pipeline_overview = {
            "Total Projects in Pipeline": total_projects,
            "Total QEI Requested ($)": f"${total_qei:,.0f}",
            "States Represented": len(states),
            "% QEI in Deep/Severe Distress": f"{deep_pct:.0%}",
            "Dominant Sector": dominant_sector.replace("_", " ").title(),
            "Total Jobs to Be Created": pr.aggregate_impact.get("total_jobs_created", "N/A"),
            "Sector Diversity Score": f"{sector.get('sector_diversity_score', 0):.1f}/100",
            "Historical Distress Rank": distress.get("vs_historical_winners", "N/A").replace("_", " ").title(),
        }

        deployment_strategy = (
            f"{cde.name} targets a {application.application_round} award and plans to close "
            f"the first tranche of transactions within 12 months of award announcement. "
            f"All {total_projects} projects have completed preliminary underwriting review.\n\n"
            f"QEI deployment strategy: {distress.get('pct_deep_or_severe', 0):.0%} of QEI "
            f"committed to deep/severe distress tracts (CDFI Fund target: ≥75%).\n\n"
        ) + _placeholder(self.section_id, 400)

        return {
            "section_id": self.section_id,
            "title": self.title,
            "subsections": [
                {"heading": "Investment Thesis and Strategy",
                 "body": thesis, "type": "narrative"},
                {"heading": "Target Markets — Geographic and Demographic",
                 "body": target_markets_body, "type": "narrative"},
                {"heading": "Pipeline Overview",
                 "body": pipeline_overview, "type": "table_ref"},
                {"heading": "QEI Deployment Strategy and Timeline",
                 "body": deployment_strategy, "type": "narrative"},
                {"heading": "Competitive Differentiation",
                 "body": _placeholder(self.section_id, 400), "type": "narrative"},
            ],
        }

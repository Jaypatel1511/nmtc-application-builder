"""Section E: Prior Awards generator (for prior allocatees only)."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.sections.base import SectionGenerator, _placeholder

if TYPE_CHECKING:
    from nmtcapp.core.application import Application, ApplicationAnalysis

logger = logging.getLogger(__name__)


class SectionEPriorAwards(SectionGenerator):
    """Generates Section E: Prior Awards content.

    Only relevant for CDEs with prior NMTC allocations. Returns an empty
    section if no prior awards exist.

    Example::

        gen = SectionEPriorAwards()
        content = gen.generate_content(application, analysis)
    """
    section_id = "E"
    title = "Prior Awards — Deployment History"
    word_limit = 1000

    def generate_content(self, application: "Application", analysis: "ApplicationAnalysis") -> dict:
        cde = application.cde
        awards = cde.prior_awards

        if not awards:
            return {
                "section_id": self.section_id,
                "title": self.title,
                "subsections": [{
                    "heading": "Prior Award Status",
                    "body": f"{cde.name} has not received prior NMTC allocations. "
                            "This is our first allocation application.",
                    "type": "narrative",
                }],
            }

        total_prior = cde.total_prior_allocation()
        fully_deployed = sum(
            1 for a in awards if a.get("deployment_status") == "fully_deployed"
        )

        summary = (
            f"{cde.name} has successfully deployed {fully_deployed} of {len(awards)} prior NMTC "
            f"allocation awards totaling ${total_prior:,.0f}. All compliance obligations have been "
            f"met; no compliance events or repayments have occurred.\n\n"
            f"The deployment history table below provides details on each prior award, including "
            f"states served, sectors financed, and outcomes achieved.\n\n"
        )

        award_details = []
        for i, award in enumerate(sorted(awards, key=lambda a: a.get("year", 0))):
            status = award.get("deployment_status", "").replace("_", " ").title()
            states = ", ".join(award.get("states", ["N/A"]))
            sectors = ", ".join(award.get("sectors", ["N/A"]))
            award_details.append(
                f"**Award {i+1} (FY{award.get('year', 'N/A')}):** "
                f"${award.get('amount', 0):,.0f} — {status}. "
                f"States: {states}. Sectors: {sectors}."
                + (" " + award.get("notes", "") if award.get("notes") else "")
            )

        outcomes = (
            f"Outcomes across all {len(awards)} prior awards:\n\n"
        ) + _placeholder(self.section_id, 400)

        return {
            "section_id": self.section_id,
            "title": self.title,
            "subsections": [
                {"heading": "Prior Allocation Summary",
                 "body": summary, "type": "narrative"},
                {"heading": "Award-by-Award Deployment History",
                 "body": award_details, "type": "list"},
                {"heading": "Compliance and Monitoring",
                 "body": "(See Attachment: Track Record Table)", "type": "table_ref"},
                {"heading": "Outcomes and Impact Achieved",
                 "body": outcomes, "type": "narrative"},
            ],
        }

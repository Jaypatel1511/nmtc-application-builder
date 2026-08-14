"""Section C: Management Capacity generator."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.sections.base import (
    SectionGenerator,
    _cde_todo,
    _compliance_statement,
    _placeholder,
)

if TYPE_CHECKING:
    from nmtcapp.core.application import Application, ApplicationAnalysis

logger = logging.getLogger(__name__)


class SectionCManagementCapacity(SectionGenerator):
    """Generates Section C: Management Capacity content.

    Pulls from CDEProfile.prior_awards, governance, and cdfidata track record.

    Example::

        gen = SectionCManagementCapacity()
        content = gen.generate_content(application, analysis)
    """
    section_id = "C"
    title = "Management Capacity"
    word_limit = 2000

    def generate_content(self, application: "Application", analysis: "ApplicationAnalysis") -> dict:
        cde = application.cde
        total_prior = cde.total_prior_allocation()
        fully_deployed = sum(
            1 for a in cde.prior_awards if a.get("deployment_status") == "fully_deployed"
        )
        board = cde.governance

        history_narrative = (
            f"{cde.name} was certified as a Community Development Entity by the CDFI Fund "
            f"on {cde.certification_date}. Since certification, the organization has received "
            f"{len(cde.prior_awards)} NMTC allocation awards totaling ${total_prior:,.0f}, "
            f"of which {fully_deployed} are recorded as fully deployed.\n\n"
            + _compliance_statement(cde) + "\n\n"
        ) + _placeholder(self.section_id, 400)

        governance_summary = {
            "Board Members": board.get("board_members", "N/A"),
            "Community Representatives": board.get("community_representatives", "N/A"),
            "Independent Directors": board.get("independent_directors", "N/A"),
            "Board Meeting Frequency": board.get("board_meeting_frequency", "Quarterly"),
            "CDE Certification Date": cde.certification_date,
            "Prior Allocations Received": len(cde.prior_awards),
            "Total Prior Allocation ($)": f"${total_prior:,.0f}",
            "Rounds Fully Deployed": fully_deployed,
        }

        underwriting = (
            f"{cde.name} maintains a rigorous underwriting process calibrated to NMTC compliance "
            f"requirements and community development mission:\n\n"
            f"  1. Initial Screening: NMTC eligibility verification via geocoding + ACS tract data\n"
            f"  2. Community Impact Assessment: Jobs/unit projections and HMDA disparity review\n"
            f"  3. Financial Underwriting: DSCR analysis, leverage review, sponsor capacity check\n"
            f"  4. Investment Committee Approval: "
            + _cde_todo(
                "State your investment committee's approval threshold "
                "(e.g. majority of members present, unanimous consent, or a "
                "named quorum). This tool has no such field — the CDE profile "
                "records a board headcount, which is not an approval rule."
            ) + "\n"
            f"  5. Compliance Monitoring: Annual site visits + CDFI Fund reporting throughout 7-year compliance period\n\n"
        ) + _placeholder(self.section_id, 300)

        return {
            "section_id": self.section_id,
            "title": self.title,
            "subsections": [
                {"heading": "CDE History and Certification",
                 "body": history_narrative, "type": "narrative"},
                {"heading": "Governance and Organizational Structure",
                 "body": governance_summary, "type": "table_ref"},
                {"heading": "Track Record — Prior NMTC Deployments",
                 "body": "(See Attachment: Track Record Table)", "type": "table_ref"},
                {"heading": "Underwriting Process and Internal Controls",
                 "body": underwriting, "type": "narrative"},
                {"heading": "Key Personnel and Qualifications",
                 "body": _placeholder(self.section_id, 400), "type": "narrative"},
            ],
        }

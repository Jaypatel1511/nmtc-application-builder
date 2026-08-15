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
        ) + _placeholder()

        governance_summary = {
            "Board Members": board.get("board_members", "N/A"),
            "Community Representatives": board.get("community_representatives", "N/A"),
            "Independent Directors": board.get("independent_directors", "N/A"),
            # Defaulted to "Quarterly" through 1.2.0-rc. That is not a fallback
            # string, it is an ANSWER to a governance question the CDE was asked
            # and did not answer, printed in a governance table in the section
            # where management capacity is scored — indistinguishable, to a
            # reader, from a value the CDE supplied. Every other row in this
            # dict defaults to "N/A"; this one now matches them.
            #
            # It survived every gate because "**Board Meeting Frequency:**
            # Quarterly" is four words and _is_prose requires five.
            "Board Meeting Frequency": board.get("board_meeting_frequency", "N/A"),
            "CDE Certification Date": cde.certification_date,
            "Prior Allocations Received": len(cde.prior_awards),
            "Total Prior Allocation ($)": f"${total_prior:,.0f}",
            "Rounds Fully Deployed": fully_deployed,
        }

        # The underwriting steps are the CDE's own internal controls. This tool
        # has no field for any of them, so it cannot describe them — and the
        # numbered list here previously asserted five specific ones for every
        # CDE, including step 2's "HMDA disparity review", a capability the
        # package removed with the HMDA adapter in this same release. A CDE
        # that submitted this told the Fund, in the subsection where management
        # capacity is scored, that it ran a review it does not run.
        #
        # Steps 1 and 5 are not safe either: this tool geocodes, the CDE may
        # not, and nothing here knows whether a CDE conducts annual site visits.
        underwriting = (
            _cde_todo(
                "Describe your CDE's underwriting process end to end — initial "
                "screening and how eligibility is established, impact "
                "assessment, financial underwriting and credit criteria, your "
                "investment committee's composition and approval threshold, "
                "and your compliance-monitoring practice over the seven-year "
                "period. This tool holds none of these: your CDE profile "
                "records a board headcount, which is not an approval rule, and "
                "nothing in it describes a control you actually operate."
            ) + "\n\n"
        ) + _placeholder()

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
                 "body": _placeholder(), "type": "narrative"},
            ],
        }

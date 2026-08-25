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

        # AN ABSENT DATE IS DISCLOSED, NOT PRINTED BLANK (1.6.0 T1c). This
        # was an unconditional f-string, so a profile with no certification
        # date rendered "certified as a Community Development Entity by the
        # CDFI Fund on ." into a federal filing draft -- a sentence whose
        # subject is a date and whose date is a full stop. Every xlsx upload
        # took that path before T1, because the identity strip removed the
        # cell the CDE had filled in.
        certification = str(cde.certification_date or "").strip()
        if certification:
            certified_clause = (
                f"{cde.name} was certified as a Community Development Entity "
                f"by the CDFI Fund on {certification}."
            )
        else:
            certified_clause = (
                f"{cde.name} is a certified Community Development Entity. "
                + _cde_todo(
                    "State the date the CDFI Fund certified this CDE. No "
                    "certification date was supplied in this CDE's profile, "
                    "and this tool will not print one it was not given."
                )
            )

        # THE COUNT AND THE LIST COME OFF DIFFERENT INPUTS (1.6.0 T1c).
        #
        # ``prior_awards`` is the detailed list this sentence narrates.
        # ``extra["prior_award_count"]`` is a SCORED attribute, and on the
        # xlsx path it is the only one of the two a CDE can supply -- the CDE
        # Profile sheet has a "Prior Award Count" cell and no award list at
        # all. So a CDE that declared 1 prior award was told, in the section
        # where management capacity is scored, that it had received 0
        # totalling $0.
        #
        # That was already the arithmetic at 9a2d584. What T1 changes is WHOSE
        # it is: the sentence used to be about "(your CDE)", a placeholder no
        # reader could mistake for an applicant, and is now about a named one.
        # A false quantitative claim about a named CDE is a different artifact
        # from the same words about a placeholder, so the disagreement is
        # disclosed rather than asserted.
        #
        # THE LIST STILL GOVERNS WHERE IT EXISTS. This does not adopt the
        # count as the answer -- the count carries no year, no amount and no
        # deployment status, so nothing here can narrate it. It says the two
        # disagree and names which input is missing.
        declared_count = cde.extra.get("prior_award_count") if cde.extra else None
        try:
            declared_count = int(declared_count) if declared_count is not None else None
        except (TypeError, ValueError):
            declared_count = None

        if declared_count is not None and declared_count != len(cde.prior_awards):
            awards_clause = (
                f"This CDE's profile declares {declared_count} prior NMTC "
                f"allocation award{'s' if declared_count != 1 else ''}, and "
                f"{len(cde.prior_awards)} "
                f"{'is' if len(cde.prior_awards) == 1 else 'are'} detailed in "
                "the profile this draft was generated from. "
                + _cde_todo(
                    "Supply the year, amount and deployment status of each "
                    "prior allocation. The declared count and the detailed "
                    "list disagree, so no total, no deployment count and no "
                    "since-certification narrative is stated here."
                )
            )
        else:
            awards_clause = (
                f"Since certification, the organization has received "
                f"{len(cde.prior_awards)} NMTC allocation awards totaling "
                f"${total_prior:,.0f}, of which {fully_deployed} are recorded "
                "as fully deployed."
            )

        history_narrative = (
            f"{certified_clause} {awards_clause}\n\n"
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
            # "N/A" LIKE EVERY OTHER ROW IN THIS DICT (1.6.0 T1c). This one
            # printed the raw attribute, so an absent date rendered as a
            # governance-table row with a label and nothing after it, in the
            # section where management capacity is scored. The rows around it
            # have disclosed with "N/A" since 1.2.0-rc.
            "CDE Certification Date": certification or "N/A",
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

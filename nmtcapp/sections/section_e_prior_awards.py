"""Section E: Prior Awards generator (for prior allocatees only)."""
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

# What an absent field prints. "N/A" is what this cell used to say, and "N/A"
# reads as a value the CDE supplied — "not applicable to this award" — when
# what is true is that nothing was ever collected. The distinction matters to a
# reviewer deciding whether a CDE served one state or declined to say.
_NOT_COLLECTED = "[CDE TO COMPLETE — not collected by this tool]"


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

        # THE SENTENCE DESCRIBES THE TABLE THAT EXISTS (1.2.1 L-5).
        #
        # It used to promise "details on each prior award, including states
        # served, sectors financed, and outcomes achieved" unconditionally, and
        # printed it directly above rows reading "States: N/A. Sectors: N/A."
        # whenever the CDE's profile carried an award without them — which is
        # every award loaded from the shipped scaffold, since neither field is
        # a template column. Outcomes are never in the table at all; they are a
        # [NARRATIVE PLACEHOLDER] two subsections below.
        #
        # Same class as the "Quarterly" governance default and the 0-affordable
        # -units cell: the tool asserting content it does not have. The sentence
        # now names only what the awards actually carry, and where nothing is
        # carried it says so and asks the CDE rather than promising detail the
        # reader will not find.
        detailed = [
            label for label, key in (("states served", "states"),
                                     ("sectors financed", "sectors"))
            if any(a.get(key) for a in awards)
        ]
        if detailed:
            table_note = (
                "The deployment history table below provides details on each "
                "prior award, including " + " and ".join(detailed) + "."
            )
        else:
            table_note = (
                "The deployment history table below lists each prior award's "
                "year, amount and deployment status. It does NOT record states "
                "served or sectors financed: neither is collected by this "
                "tool's CDE profile scaffold, so no value for them exists to "
                "print. " + _cde_todo(
                    "Add the states served and sectors financed for each prior "
                    "award directly to the table below. The CDFI Fund's Section "
                    "E asks for both and this tool does not hold them."
                )
            )

        summary = (
            f"{cde.name} has {len(awards)} prior NMTC allocation awards totaling "
            f"${total_prior:,.0f}, of which {fully_deployed} are recorded in the CDE "
            f"profile as fully deployed.\n\n"
            + _compliance_statement(cde) + "\n\n"
            + table_note + "\n\n"
        )

        award_details = []
        for i, award in enumerate(sorted(awards, key=lambda a: a.get("year", 0))):
            status = award.get("deployment_status", "").replace("_", " ").title()
            # "N/A" read as a value the CDE supplied. It is the absence of one.
            states = ", ".join(award.get("states") or []) or _NOT_COLLECTED
            sectors = ", ".join(award.get("sectors") or []) or _NOT_COLLECTED
            # `award.get("amount", 0)` printed "$0" for an award whose amount
            # the CDE left out — a statement that the round was worth nothing,
            # in the section the Fund reads to assess deployment history
            # (FIX-2 B-2 sweep, same fix as tables/track_record_table).
            amount = award.get("amount")
            amount_text = (
                f"${amount:,.0f}" if amount is not None
                else "[CDE TO COMPLETE: allocation amount]"
            )
            award_details.append(
                f"**Award {i+1} (FY{award.get('year', 'N/A')}):** "
                f"{amount_text} — {status}. "
                f"States: {states}. Sectors: {sectors}."
                + (" " + award.get("notes", "") if award.get("notes") else "")
            )

        outcomes = (
            f"Outcomes across all {len(awards)} prior awards:\n\n"
        ) + _placeholder()

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

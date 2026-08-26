"""Section E: Prior Awards generator (for prior allocatees only)."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.sections.base import (
    SectionGenerator,
    _cde_todo,
    _compliance_statement,
    _declared_prior_award_count,
    _placeholder,
    _prior_awards_disagree,
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

        # THE ONE RULING, READ FROM sections/base (1.6.1 T1). Both branches
        # below ask the SAME predicate the same way, because at 1.6.0 they did
        # not: the count was read inside ``if not awards:`` only, so a
        # NON-EMPTY list fell through to the summary with no comparison at
        # all, and one document carried Section C disclosing the disagreement
        # while Section E asserted the list as this CDE's complete history.
        #
        # The reasoning is stated once in ``sections/base``, beside the
        # predicate -- it used to be twenty lines here and twenty more in
        # section_c_management, which is the two-hand-maintained-copies shape
        # ``REQUIRED_CDE_FIELDS`` records the cost of.
        declared = _declared_prior_award_count(cde)
        disagrees = _prior_awards_disagree(cde)

        if not awards:
            # ``[]`` IS AN ANSWER. A genuine first-time applicant -- no
            # declared count, or a declared 0 -- reaches the unchanged
            # sentence below, because the predicate calls those two AGREEING.
            # "This is our first allocation application" is an affirmative
            # claim in the CDE's own voice about its own history, so it is
            # withheld only where the CDE's own profile contradicts it.
            if disagrees:
                body = (
                    f"{cde.name}'s profile declares {declared} prior NMTC "
                    f"allocation award{'s' if declared != 1 else ''}, and this "
                    "draft was generated from a profile carrying no details "
                    "for any of them. "
                    + _cde_todo(
                        "State each prior allocation's year, amount, states "
                        "served, sectors financed and deployment status. This "
                        "tool has the count and nothing else, and will not "
                        "state that this is a first application when the "
                        "profile says it is not."
                    )
                )
            else:
                body = (f"{cde.name} has not received prior NMTC allocations. "
                        "This is our first allocation application.")
            return {
                "section_id": self.section_id,
                "title": self.title,
                "subsections": [{
                    "heading": "Prior Award Status",
                    "body": body,
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

        # THE SAME RULING, ON THE BRANCH THAT NEVER ASKED (1.6.1 T1). This
        # sentence read "{name} has {n} prior NMTC allocation awards totaling
        # ${total}, of which {d} are recorded ... as fully deployed" in EVERY
        # case, which is a claim about the CDE's whole allocation history --
        # in the section the CDFI Fund reads for deployment history. Against a
        # profile declaring four and detailing one it was false, and Section C
        # said so in the same document.
        #
        # THE LIST STILL GOVERNS WHERE IT EXISTS, which is Section C's ruling
        # and is why the figures below are still the list's and the count is
        # still not adopted: the count carries no year, no amount and no
        # deployment status, so nothing here can narrate it. What changes is
        # that the figures are SCOPED to the awards they were computed from
        # instead of standing for the whole history, and the missing input is
        # named. Withholding the total the way Section C does would be theatre
        # here -- every award's amount prints in the table immediately below.
        if disagrees:
            prior_summary = (
                f"{cde.name}'s profile declares {declared} prior NMTC "
                f"allocation award{'s' if declared != 1 else ''}, and "
                f"{len(awards)} {'is' if len(awards) == 1 else 'are'} detailed "
                "in the profile this draft was generated from. The figures "
                f"below cover only {'that one' if len(awards) == 1 else 'those'}"
                f": ${total_prior:,.0f} allocated, of which {fully_deployed} "
                f"{'is' if fully_deployed == 1 else 'are'} recorded in the CDE "
                "profile as fully deployed. "
                + _cde_todo(
                    "Supply the year, amount, states served, sectors financed "
                    "and deployment status of every prior allocation. The "
                    "declared count and the detailed list disagree, so nothing "
                    "here states this CDE's full deployment history."
                )
            )
        else:
            prior_summary = (
                f"{cde.name} has {len(awards)} prior NMTC allocation awards "
                f"totaling ${total_prior:,.0f}, of which {fully_deployed} are "
                "recorded in the CDE profile as fully deployed."
            )

        summary = (
            prior_summary + "\n\n"
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

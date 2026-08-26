"""Abstract base class for NMTC application section generators."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nmtcapp.core.application import Application
    from nmtcapp.core.application import ApplicationAnalysis

logger = logging.getLogger(__name__)

# No length figure appears here, deliberately.
#
# Through 1.1.5 this string ended "Word limit for this section: {limit} words",
# with the limit passed per SUBSECTION — so Section A printed 3000, 500, 400
# and 400 as four different limits "for this section" against a declared
# word_limit of 3000, and the four sum to 4300. B printed 1400 against 2500,
# C 1100 against 2000. None of the numbers was sourced.
#
# They were also the wrong unit: the CY 2024-2025 application enforces a
# CHARACTER limit per question, not a word limit per section. This tool does
# not encode the real limits — the CY 2026 Application Materials are
# unpublished — so it must not state one. A CDE writing to an invented budget
# over-writes and is truncated at submission.
_PLACEHOLDER = (
    "\n\n[NARRATIVE PLACEHOLDER — Replace this text with your CDE's specific "
    "information. CDFI Fund reviewers score on specificity, evidence, and "
    "alignment with community need. Length is governed by the limit printed on "
    "the published application form for this question, which this tool does not "
    "encode — check the form, not this draft.]\n\n"
)

# Marker for any claim this tool cannot substantiate from the CDE's own inputs.
#
# Deliberately a visible bracketed placeholder rather than a softened sentence.
# A shortened but still-assertive paragraph reads as finished, so a reader gets
# no signal that anything is missing, and the next contributor who adds a
# sentence has no rule to violate. A bracketed placeholder makes an unfinished
# application LOOK unfinished.
_CDE_TODO = "[CDE TO COMPLETE: {what}]"


class SectionGenerator(ABC):
    """Base class for all NMTC application section generators.

    Each subclass generates one of the five CDE application sections (A–E).
    Content is returned as a structured dict so it can be rendered by any
    output format (Word, PDF, Markdown) without coupling to a specific renderer.

    Example::

        generator = SectionABusinessStrategy()
        content = generator.generate_content(application, analysis)
        md = generator.generate_markdown(application, analysis)
    """
    section_id: str = ""
    title: str = ""
    word_limit: int = 2000

    def generate_content(
        self,
        application: "Application",
        analysis: "ApplicationAnalysis",
    ) -> dict:
        """Return structured content dict for this section.

        The dict has the shape::

            {
                "section_id": "A",
                "title": "Business Strategy",
                "subsections": [
                    {
                        "heading": "Investment Thesis",
                        "body": "narrative text...",
                        "type": "narrative" | "list" | "table_ref"
                    },
                    ...
                ]
            }
        """
        raise NotImplementedError

    def generate_word(self, doc, application: "Application", analysis: "ApplicationAnalysis") -> None:
        """Write this section to an open python-docx Document.

        Callers pass the live ``Document`` object; this method appends
        headings, paragraphs, and tables to it in place.

        Example::

            generator.generate_word(doc, application, analysis)
        """
        from nmtcapp.renderers._word_helpers import write_section_to_doc
        content = self.generate_content(application, analysis)
        write_section_to_doc(doc, content)

    def generate_markdown(
        self,
        application: "Application",
        analysis: "ApplicationAnalysis",
    ) -> str:
        """Render this section as Markdown text.

        Example::

            md = generator.generate_markdown(application, analysis)
            print(md)
        """
        content = self.generate_content(application, analysis)
        return _content_to_markdown(content)


def _content_to_markdown(content: dict) -> str:
    """Convert structured content dict to Markdown."""
    lines = [f"## Section {content.get('section_id', '')}: {content.get('title', '')}", ""]
    for sub in content.get("subsections", []):
        lines.append(f"### {sub['heading']}")
        lines.append("")
        body = sub.get("body", "")
        if isinstance(body, list):
            for item in body:
                lines.append(f"- {item}")
        elif isinstance(body, str):
            lines.append(body)
        elif isinstance(body, dict):
            for k, v in body.items():
                lines.append(f"**{k}:** {v}")
        lines.append("")
    return "\n".join(lines)


def _placeholder() -> str:
    """The narrative placeholder text.

    Took ``(section_id, limit)`` through 1.1.5. ``section_id`` was never used —
    the format string said "this section" regardless of which section called
    it — and ``limit`` printed an unsourced word budget. Both are gone rather
    than left as ignored parameters, so a caller cannot pass a number that goes
    nowhere and read the call site as though it did something.
    """
    return _PLACEHOLDER


def _cde_todo(what: str) -> str:
    """Bracketed placeholder naming what the CDE must supply.

    Use wherever the tool would otherwise assert something it cannot derive
    from the CDE's own inputs. ``what`` should name the required evidence,
    not hedge the missing claim.

    Example::

        _cde_todo("State your compliance history over prior allocations.")
    """
    return _CDE_TODO.format(what=what)


#: THE ONE RULING ON THE PRIOR-AWARD COUNT (1.6.1 T1).
#:
#: Sections C and E BOTH narrate the same fact about the same CDE -- how many
#: prior NMTC allocations it has received -- off TWO DIFFERENT INPUTS:
#:
#:     cde.prior_awards              the detailed list: year, amount, states,
#:                                   sectors, deployment status
#:     cde.extra["prior_award_count"] a SCORED attribute, and on the xlsx path
#:                                   the ONLY one of the two a CDE can supply
#:                                   -- the CDE Profile sheet has a "Prior
#:                                   Award Count" cell and no award list.
#:
#: 1.6.0 taught ONE of the two sections to compare them. Section C compared in
#: every case; Section E read the count only inside its ``if not awards:``
#: branch, so a non-empty list fell straight through to the summary with no
#: comparison at all. Measured at fc34af5 (= v1.6.0), one detailed award and a
#: declared count of 4, in ONE generated document:
#:
#:   Section C  "declares 4 prior NMTC allocation awards, and 1 is detailed
#:               ... [CDE TO COMPLETE: ...]"            <- disclosed
#:   Section E  "has 1 prior NMTC allocation awards totaling $45,000,000, of
#:               which 1 are recorded ... as fully deployed."
#:                                                      <- asserted as complete
#:
#: At 9a2d584 neither section looked, so they agreed by not looking. This is
#: the same shape ``_compliance_statement`` below already exists to prevent:
#: two sections asserting the same thing about the same field out of two
#: hand-maintained copies of the reasoning. So the reasoning is stated ONCE,
#: here, and both sections read the predicate rather than re-deriving it.
#:
#: THE RULING IS SECTION C'S, UNCHANGED AND NOT RE-OPENED: **the list still
#: governs where it exists.** This does not adopt the count as the answer --
#: the count carries no year, no amount and no deployment status, so nothing
#: can narrate it. What each section does when they disagree is to say so and
#: name which input is missing. What each section SAYS around that fact stays
#: its own: C narrates certification history, E narrates the award table.
#:
#: ``[]`` IS AN ANSWER AND STAYS ONE. ``core.cde`` documents at length that an
#: empty ``prior_awards`` list is a CDE affirmatively stating it has no prior
#: allocations, and that 1.3.0 B3 fixed a validator that pressured a user
#: toward a false statement about its own history. A genuine first-time
#: applicant -- no declared count, or a declared 0 -- must reach the unchanged
#: first-application sentence, and ``_prior_awards_disagree`` returns False for
#: both. Over-hedging is a defect in the other direction.


def _declared_prior_award_count(cde) -> "int | None":
    """The prior-award count the CDE declared, or ``None`` if it declared none.

    ``None`` covers three cases that are all "the CDE did not state a count":
    the key is absent, the cell was left blank, and the cell holds something
    that is not a whole number. A blank cell is NOT a declared zero -- that
    distinction is the same one ``streamlit_app.utils._is_blank`` and
    ``CDEProfile.from_yaml`` draw, and it is why ``0`` and ``None`` are kept
    apart here rather than collapsed to a falsy test.

    Example::

        _declared_prior_award_count(cde)   # -> 4, or None
    """
    declared = getattr(cde, "extra", None)
    declared = declared.get("prior_award_count") if declared else None
    if declared is None:
        return None
    try:
        return int(declared)
    except (TypeError, ValueError):
        return None


def _prior_awards_disagree(cde) -> bool:
    """Do the CDE's declared prior-award count and its detailed list disagree?

    ``False`` when the CDE declared no count at all -- there is nothing to
    disagree with, and an absent count may not be read as a claim of zero.
    ``False`` when a declared ``0`` meets an empty list: those AGREE, and the
    CDE is a first-time applicant saying so.

    Read by Sections C and E. See the ruling above for why it is one predicate
    and not two copies of one.

    Example::

        _prior_awards_disagree(cde)   # -> True when 4 declared, 1 detailed
    """
    declared = _declared_prior_award_count(cde)
    return declared is not None and declared != len(cde.prior_awards)


def _compliance_statement(cde) -> str:
    """Compliance-history text derived only from what the CDE supplied.

    ``has_prior_reporting_issues`` is collected from the CDE's own profile
    (upload column "Prior Reporting Issues (Y/N)"). Three states, three
    outcomes — and note the field is NARROWER than a clean compliance
    history, so even a declared ``False`` does not license a blanket "zero
    violations or defaults" claim. That broader assertion is always the
    CDE's to make.

    Shared by Sections C and E, which both previously asserted a clean
    record unconditionally — including for a CDE that had declared the
    opposite in its own profile.

    Example::

        body = _compliance_statement(application.cde)
    """
    declared = getattr(cde, "extra", {}).get("has_prior_reporting_issues")

    if declared is True:
        # The CDE declared prior reporting issues. Emit no clean-history
        # claim of any kind — the earlier unconditional text asserted the
        # opposite of what the CDE told us.
        return _cde_todo(
            "Your CDE profile declares prior reporting issues. Describe them "
            "directly: what occurred, over which allocation(s), how each was "
            "resolved, and what controls now prevent recurrence. Do not omit "
            "this — the CDFI Fund holds prior compliance records, and an "
            "unexplained gap reads worse than a disclosed and remediated issue."
        )

    if declared is False:
        return (
            "Per this CDE's own profile declaration, no prior NMTC reporting "
            "issues have been recorded.\n\n"
            + _cde_todo(
                "State the CDE's full compliance and performance history over "
                "its prior allocations — recapture or reduction events, "
                "defaults, cures, and material findings. The profile field "
                "above covers reporting issues only and is not by itself a "
                "representation about defaults or compliance violations."
            )
        )

    return _cde_todo(
        "State the CDE's compliance and performance history over its prior "
        "allocations — reporting issues, recapture or reduction events, "
        "defaults, cures, and material findings. This tool has no compliance "
        "record for your CDE; supply 'has_prior_reporting_issues' in your CDE "
        "profile and document the full history here."
    )

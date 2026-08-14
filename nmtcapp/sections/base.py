"""Abstract base class for NMTC application section generators."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nmtcapp.core.application import Application
    from nmtcapp.core.application import ApplicationAnalysis

logger = logging.getLogger(__name__)

_PLACEHOLDER = (
    "\n\n[NARRATIVE PLACEHOLDER — Replace this text with your CDE's specific information. "
    "CDFI Fund reviewers score on specificity, evidence, and alignment with community need. "
    "Word limit for this section: {limit} words.]\n\n"
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


def _placeholder(section_id: str, limit: int) -> str:
    return _PLACEHOLDER.format(limit=limit)


def _cde_todo(what: str) -> str:
    """Bracketed placeholder naming what the CDE must supply.

    Use wherever the tool would otherwise assert something it cannot derive
    from the CDE's own inputs. ``what`` should name the required evidence,
    not hedge the missing claim.

    Example::

        _cde_todo("State your compliance history over prior allocations.")
    """
    return _CDE_TODO.format(what=what)


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

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

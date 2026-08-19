"""Professional PDF builder for NMTC applications using ReportLab."""
from __future__ import annotations

import logging
import os
from datetime import date
from typing import TYPE_CHECKING

from nmtcapp.renderers._disclosure import (
    is_partial_unverified, qlici_not_supplied_note, qualified_pct,
    unverified_banner, unverified_ids, unverified_qualifier,
)
from nmtcapp.renderers._cell_format import format_cell, supplied_total
from nmtcapp.renderers._frame_geometry import usable_width
from nmtcapp.renderers._methodology import (
    ACS_VINTAGE, deal_economics_note, distress_definitions, impact_bands_note,
    noaa_note, readiness_weights_note,
)
from nmtcapp.renderers.styles import COLORS, TYPOGRAPHY, PAGE_LAYOUT, rl_hex
from nmtcapp.sections import ALL_SECTIONS
from nmtcapp.tables.distress_table import build_distress_table, build_distress_summary_table
from nmtcapp.tables.geographic_table import build_geographic_table
from nmtcapp.tables.impact_table import build_impact_summary_table
from nmtcapp.tables.pipeline_table import build_pipeline_summary_table
from nmtcapp.tables.track_record_table import build_track_record_table

if TYPE_CHECKING:
    from nmtcapp.core.application import Application, ApplicationAnalysis

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import LETTER, landscape as rl_landscape
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
        Table, TableStyle, PageBreak, KeepTogether, HRFlowable, NextPageTemplate,
    )
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib import colors as rl_colors
    _REPORTLAB_AVAILABLE = True
except ImportError:
    _REPORTLAB_AVAILABLE = False

# Landscape letter dimensions (used even when reportlab not available for type checking)
_LETTER_LANDSCAPE = (11 * 72, 8.5 * 72)  # points: 792 × 612


def _rl_escape(text: str) -> str:
    """XML-escape plain text for a ReportLab Paragraph.

    ReportLab parses its Paragraph source as mini-HTML, so a bare '>' or '<'
    in shared text raises rather than rendering. The methodology strings live
    in renderers/_methodology as plain text — the same string Word and
    markdown receive — and are escaped here at the one place that needs it.
    Escaping at the boundary is what stops the PDF from becoming a second
    hand-maintained copy with its own entities baked in.
    """
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


# ---------------------------------------------------------------------------
# Style factory
# ---------------------------------------------------------------------------

def _build_styles():
    """Build the ReportLab paragraph style registry."""
    base = getSampleStyleSheet()
    primary = rl_hex("primary")
    secondary = rl_hex("secondary")
    accent = rl_hex("accent")
    body_color = rl_hex("text_body")
    muted = rl_hex("text_muted")

    styles = {
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22, textColor=rl_colors.white,
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle", parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14, textColor=rl_colors.white,
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "cover_detail": ParagraphStyle(
            "cover_detail", parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10, textColor=body_color,
            alignment=TA_CENTER, spaceAfter=2,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=TYPOGRAPHY["size_h1"],
            textColor=primary,
            spaceBefore=12, spaceAfter=6,
            borderPad=0,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=TYPOGRAPHY["size_h2"],
            textColor=secondary,
            spaceBefore=8, spaceAfter=4,
        ),
        "h3": ParagraphStyle(
            "h3", parent=base["Heading3"],
            fontName="Helvetica-BoldOblique",
            fontSize=TYPOGRAPHY["size_h3"],
            textColor=secondary,
            spaceBefore=6, spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontName="Helvetica",
            fontSize=TYPOGRAPHY["size_body"],
            textColor=body_color,
            leading=15, spaceBefore=3, spaceAfter=3,
            alignment=TA_JUSTIFY,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["Normal"],
            fontName="Helvetica",
            fontSize=TYPOGRAPHY["size_body"],
            textColor=body_color,
            leading=14, leftIndent=14, firstLineIndent=-10,
            spaceBefore=2, spaceAfter=2,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=TYPOGRAPHY["size_caption"],
            textColor=muted,
            spaceBefore=2, spaceAfter=4,
        ),
        "footer": ParagraphStyle(
            "footer", parent=base["Normal"],
            fontName="Helvetica",
            fontSize=TYPOGRAPHY["size_footnote"],
            textColor=muted,
            alignment=TA_CENTER,
        ),
    }
    return styles


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------

def _rl_table_style(n_data_rows: int, totals_last: bool = False) -> "TableStyle":
    """Build a ReportLab TableStyle matching the Word/Excel aesthetic."""
    primary_hex = COLORS["primary"]
    even_hex = COLORS["row_even"]
    total_hex = COLORS["row_total"]
    border_hex = COLORS["border"]

    cmds = [
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), rl_hex("primary")),
        ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), TYPOGRAPHY["size_table_header"]),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.4, rl_hex("border")),
        # Body text
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), TYPOGRAPHY["size_table_body"]),
        ("TEXTCOLOR", (0, 1), (-1, -1), rl_hex("text_body")),
        # Row padding
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]

    # Alternating row shading
    for i in range(1, n_data_rows + 1):
        if totals_last and i == n_data_rows:
            cmds.append(("BACKGROUND", (0, i), (-1, i), rl_hex("row_total")))
            cmds.append(("FONTNAME", (0, i), (-1, i), "Helvetica-Bold"))
        elif i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), rl_hex("row_even")))
        else:
            cmds.append(("BACKGROUND", (0, i), (-1, i), rl_hex("row_odd")))

    return TableStyle(cmds)


def _df_to_rl_table(df, styles, max_rows: int = 40, totals_last: bool = True,
                    col_widths=None, font_size: int = None) -> list:
    """Convert a DataFrame to a list of ReportLab flowables (table + optional caption).

    Uses Paragraph objects for text cells so long values wrap rather than overflow.
    """
    flowables = []
    if df is None or df.empty:
        flowables.append(Paragraph("No data available.", styles["caption"]))
        return flowables

    body_pt = font_size or TYPOGRAPHY["size_table_body"]
    header_pt = max(body_pt - 1, 6)

    # Build cell styles for wrapping
    cell_style = ParagraphStyle(
        "tbl_cell", parent=styles["body"],
        fontSize=body_pt, leading=body_pt + 2,
        spaceAfter=0, spaceBefore=0,
        textColor=rl_hex("text_body"),
    )
    header_style = ParagraphStyle(
        "tbl_hdr", parent=styles["body"],
        fontSize=header_pt, leading=header_pt + 2,
        spaceAfter=0, spaceBefore=0,
        textColor=rl_colors.white, fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )

    display = df.head(max_rows)
    header = [Paragraph(str(c), header_style) for c in display.columns]
    data = [header]
    for i, (_, row) in enumerate(display.iterrows()):
        is_last = (i == len(display) - 1)
        row_data = []
        # The COLUMN decides the format, not the magnitude — see
        # renderers/_cell_format. This branched on abs(v) > 1000, so a
        # non-currency float took a dollar sign and a fraction-valued share
        # printed as "0.33".
        for col_name, v in zip(display.columns, row):
            text = format_cell(col_name, v)
            # Truncate very long strings
            if len(text) > 80:
                text = text[:77] + "..."
            style = ParagraphStyle(
                "tbl_cell_bold" if is_last else "tbl_cell_row",
                parent=cell_style,
                fontName="Helvetica-Bold" if is_last else "Helvetica",
            )
            row_data.append(Paragraph(text, style))
        data.append(row_data)

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl_style = _rl_table_style(len(data) - 1, totals_last=totals_last)
    # Add word wrap support
    tbl_style.add("WORDWRAP", (0, 0), (-1, -1), "LTR")
    tbl_style.add("VALIGN", (0, 0), (-1, -1), "TOP")
    tbl.setStyle(tbl_style)
    flowables.append(tbl)

    if len(df) > max_rows:
        flowables.append(Paragraph(
            f"<i>Showing {max_rows} of {len(df)} rows. Full detail in Excel attachment.</i>",
            styles["caption"]
        ))
    return flowables


# ---------------------------------------------------------------------------
# Page templates
# ---------------------------------------------------------------------------

def _make_header_footer(app: "Application", styles):
    """Return on-page callback functions for header/footer on every page."""

    def _on_page(canvas, doc):
        canvas.saveState()
        w = canvas._pagesize[0]  # works for both portrait and landscape
        margin = inch
        canvas.setStrokeColor(rl_hex("border"))
        canvas.setLineWidth(0.5)
        canvas.line(margin, 0.65 * inch, w - margin, 0.65 * inch)
        canvas.setFont("Helvetica", TYPOGRAPHY["size_footnote"])
        canvas.setFillColor(rl_hex("text_muted"))
        footer_text = (
            f"{app.cde.name}  —  NMTC {app.application_round} Application  |  CONFIDENTIAL"
        )
        canvas.drawCentredString(w / 2, 0.45 * inch, footer_text)
        canvas.drawRightString(w - margin, 0.45 * inch, f"Page {doc.page}")
        canvas.restoreState()

    def _on_first_page(canvas, doc):
        pass  # cover page has no header/footer

    return _on_first_page, _on_page


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

class PDFApplicationBuilder:
    """Generates a professional PDF of the NMTC application using ReportLab.

    Produces a full application document with cover page, executive summary,
    all five sections, and appendices — suitable for board review or CDFI Fund
    submission (as a supplement to the online portal).

    Example::

        builder = PDFApplicationBuilder(application, analysis)
        builder.save("./drafts/application.pdf")
    """

    def __init__(self, application: "Application", analysis: "ApplicationAnalysis") -> None:
        if not _REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab is required for PDF output. Install with: pip install reportlab"
            )
        self.application = application
        self.analysis = analysis

    def save(self, path: str) -> None:
        """Build and save the PDF to *path*.

        Example::

            builder.save("./output/application.pdf")
        """
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        styles = _build_styles()
        on_first, on_later = _make_header_footer(self.application, styles)

        margin = inch * PAGE_LAYOUT["margin_left"]
        ls_margin = 0.75 * inch
        page_w, page_h = LETTER
        ls_w, ls_h = rl_landscape(LETTER)  # 792 × 612

        # Portrait body frame
        body_frame = Frame(
            margin, 0.9 * inch,
            page_w - 2 * margin,
            page_h - margin - 0.9 * inch,
            id="main",
        )
        cover_frame = Frame(margin, margin, page_w - 2 * margin, page_h - 2 * margin, id="cover")

        # Landscape frame for wide appendices
        ls_frame = Frame(
            ls_margin, 0.9 * inch,
            ls_w - 2 * ls_margin,
            ls_h - ls_margin - 0.9 * inch,
            id="landscape_main",
        )

        doc = BaseDocTemplate(
            path,
            pagesize=LETTER,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=0.9 * inch,
        )

        def _on_landscape(canvas, doc):
            canvas.saveState()
            w, h = rl_landscape(LETTER)
            canvas.setStrokeColor(rl_hex("border"))
            canvas.setLineWidth(0.5)
            canvas.line(ls_margin, 0.65 * inch, w - ls_margin, 0.65 * inch)
            canvas.setFont("Helvetica", TYPOGRAPHY["size_footnote"])
            canvas.setFillColor(rl_hex("text_muted"))
            footer = (
                f"{self.application.cde.name}  —  NMTC {self.application.application_round}  |  CONFIDENTIAL"
            )
            canvas.drawCentredString(w / 2, 0.45 * inch, footer)
            canvas.drawRightString(w - ls_margin, 0.45 * inch, f"Page {doc.page}")
            canvas.restoreState()

        doc.addPageTemplates([
            PageTemplate(id="Cover", frames=[cover_frame], onPage=on_first),
            PageTemplate(id="Body", frames=[body_frame], onPage=on_later),
            PageTemplate(id="Landscape", frames=[ls_frame], onPage=_on_landscape,
                         pagesize=rl_landscape(LETTER)),
        ])

        doc.build(self._build_story(styles))
        size_kb = os.path.getsize(path) // 1024
        logger.info("PDF saved: %s (%d KB)", path, size_kb)

    def _build_story(self, styles) -> list:
        """Return the flowable story ``save`` builds the document from.

        Split out of ``save`` so a gate can measure the story without writing
        a file: ``tests/test_render_frame_geometry`` walks it and asks every
        ``Table`` for the width it will draw at, which names the offending
        flowable instead of the coordinates of its debris. Nothing about the
        document changed when this moved — the rendered baseline is the proof.

        Example::

            story = builder._build_story(_build_styles())
        """
        story = []
        story += self._cover_page(styles)
        story.append(PageBreak())
        story.append(NextPageTemplate("Body"))
        story += self._executive_summary(styles)
        story.append(PageBreak())

        for section_gen in ALL_SECTIONS:
            content = section_gen.generate_content(self.application, self.analysis)
            story += _content_to_flowables(content, styles)
            story.append(PageBreak())

        # Appendix A — pipeline summary (portrait) + full distress (landscape)
        story += self._appendix_pipeline(styles)
        story.append(PageBreak())

        # Appendix B — distress table (landscape, 15 cols fits at 7pt)
        story += self._appendix_distress(styles)
        story.append(PageBreak())

        # Appendix C — geographic (portrait, 7 cols)
        story.append(NextPageTemplate("Body"))
        story += self._appendix("Appendix C: Geographic Targeting",
                                build_geographic_table(self.application.pipeline), styles)
        story.append(PageBreak())

        # Appendix D — impact summary (portrait, 7 cols)
        story += self._appendix("Appendix D: Impact Projections",
                                build_impact_summary_table(self.application.pipeline),
                                styles, max_rows=25,
                                excel_note="Full impact detail is in the Excel attachment.")
        story.append(PageBreak())

        # Appendix E — track record (portrait)
        story += self._appendix("Appendix E: CDE Track Record",
                                build_track_record_table(self.application.cde), styles)
        story.append(PageBreak())
        story += self._methodology(styles)
        return story

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _cover_page(self, styles) -> list:
        app = self.application
        score = self.analysis.readiness_score
        usable_w = usable_width()

        # Banner table
        banner_data = [
            [Paragraph("NEW MARKETS TAX CREDIT", styles["cover_title"])],
            [Paragraph("ALLOCATION APPLICATION", styles["cover_subtitle"])],
        ]
        banner = Table(banner_data, colWidths=[usable_w])
        banner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), rl_hex("primary")),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))

        # Gold accent rule
        accent_rule = HRFlowable(
            width="100%", thickness=6,
            color=rl_hex("accent"), spaceAfter=12,
        )

        # CDE name
        cde_para = Paragraph(
            f'<font color="{COLORS["primary"]}" size="18"><b>{app.cde.name}</b></font>',
            ParagraphStyle("cde_name", alignment=TA_CENTER, spaceAfter=12,
                           parent=styles["body"])
        )

        # Details table
        details = [
            ["Application Round:", app.application_round],
            ["Requested NMTC Allocation:", f"${app.requested_allocation:,.0f}"],
            ["Preparation Date:", date.today().strftime("%B %d, %Y")],
            ["Readiness Assessment:",
             f"Grade {score.grade} — {score.overall_score:.1f}/100"
             + (" (PARTIAL)" if getattr(score, "partial", False) else "")],
        ]
        col_w = [usable_w * 0.45, usable_w * 0.55]
        det_tbl = Table(details, colWidths=col_w)
        det_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), rl_hex("bg_light")),
            ("BACKGROUND", (1, 0), (1, -1), rl_hex("white")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (-1, -1), rl_hex("text_body")),
            ("GRID", (0, 0), (-1, -1), 0.5, rl_hex("border")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))

        contact = app.cde.contact
        contact_text = (
            f"Contact: {contact.get('name', '')}  |  {contact.get('email', '')}  |  "
            f"{contact.get('phone', '')}"
        )
        conf_text = (
            "CONFIDENTIAL — Prepared for CDFI Fund Review Only  |  "
            "Do Not Distribute Without CDE Authorization"
        )

        return [
            banner,
            Spacer(1, 8),
            accent_rule,
            Spacer(1, 12),
            cde_para,
            Spacer(1, 16),
            det_tbl,
            Spacer(1, 20),
            Paragraph(contact_text, styles["caption"]),
            Spacer(1, 8),
            Paragraph(f"<i>{conf_text}</i>", styles["caption"]),
        ]

    def _executive_summary(self, styles) -> list:
        app = self.application
        pr = self.analysis.pipeline_result
        score = self.analysis.readiness_score
        d = pr.distress_breakdown
        impact = pr.aggregate_impact

        flowables = [Paragraph("Executive Summary", styles["h1"])]

        degraded = getattr(pr, "eligibility_data_status", "ok") != "ok"
        partial_unverified = is_partial_unverified(pr)
        if degraded:
            flowables.append(Paragraph(
                '<font color="#B00000"><b>ELIGIBILITY DATA UNAVAILABLE — '
                f"{getattr(pr, 'eligibility_data_error', None) or 'reason unknown'}. "
                "Census tract eligibility and distress figures could not be "
                "verified and are excluded from this document. Do not submit "
                "until eligibility data has been restored and re-verified.</b></font>",
                styles["body"],
            ))
            flowables.append(Spacer(1, 8))
            summary_text = (
                f"{app.cde.name} respectfully requests ${app.requested_allocation/1e6:.1f} million in "
                f"New Markets Tax Credit allocation for {app.application_round}. Our "
                f"{pr.total_projects}-project pipeline spans "
                f"{pr.geographic_diversity.get('states_count', 0)} states. Census tract "
                "eligibility and distress concentration are unverified — eligibility "
                "data was unavailable when this draft was generated."
            )
        elif partial_unverified:
            flowables.append(Paragraph(
                '<font color="#B00000"><b>UNVERIFIED PROJECT LOCATIONS — '
                f"{unverified_banner(pr)}</b></font>",
                styles["body"],
            ))
            flowables.append(Spacer(1, 8))
            summary_text = (
                f"{app.cde.name} respectfully requests ${app.requested_allocation/1e6:.1f} million in "
                f"New Markets Tax Credit allocation for {app.application_round}. Our "
                f"{pr.total_projects}-project pipeline spans "
                f"{pr.geographic_diversity.get('states_count', 0)} states, with "
                f"{d.get('pct_deep_or_severe', 0):.0%} of QEI "
                f"{unverified_qualifier(pr)} committed to deep and severely "
                "distressed census tracts — figures reflect location-verified "
                "projects only."
            )
        else:
            summary_text = (
                f"{app.cde.name} respectfully requests ${app.requested_allocation/1e6:.1f} million in "
                f"New Markets Tax Credit allocation for {app.application_round}. Our "
                f"{pr.total_projects}-project pipeline spans "
                f"{pr.geographic_diversity.get('states_count', 0)} states, with "
                f"{d.get('pct_deep_or_severe', 0):.0%} of QEI committed to deep and severely "
                f"distressed census tracts."
            )
        flowables.append(Paragraph(summary_text, styles["body"]))
        flowables.append(Spacer(1, 10))

        # Key metrics table
        flowables.append(Paragraph("Key Metrics", styles["h2"]))
        def _elig_metric(value: float) -> str:
            if degraded:
                return "Unverified"
            if partial_unverified:
                return qualified_pct(value, pr)
            return f"{value:.0%}"

        metrics = [
            ["Metric", "Value"],
            ["Total Pipeline QEI", f"${pr.total_qei_request:,.0f}"],
            ["Total Project Cost", f"${pr.total_project_cost:,.0f}"],
            ["States Represented", str(pr.geographic_diversity.get("states_count", 0))],
            ["Deep/Severe Distress Concentration",
             _elig_metric(d.get("pct_deep_or_severe", 0))],
            ["NMTC Eligibility Rate", _elig_metric(pr.eligibility_pct)],
            ["Jobs to Be Created", f"{impact.get('total_jobs_created', 0):,}"],
            # 1.2.1 B-2: absent is not zero. See _cell_format.supplied_total.
            ["Affordable Units to Be Built",
             supplied_total(impact.get("total_units_built"))],
            ["Jobs per $1MM QEI", f"{impact.get('jobs_per_million_qei', 0):.1f}"],
        ]
        usable_w = usable_width()
        tbl = Table(metrics, colWidths=[usable_w * 0.65, usable_w * 0.35])
        tbl.setStyle(_rl_table_style(len(metrics) - 1))
        flowables += [tbl, Spacer(1, 12)]

        # Readiness score callout
        flowables.append(Paragraph("Application Readiness Assessment", styles["h2"]))
        score_data = [
            [
                Paragraph(
                    f'<font color="{COLORS["accent"]}"><b>Grade {score.grade}</b></font><br/>'
                    f'<font size="9">{score.overall_score:.1f}/100'
                    + (" (PARTIAL)" if getattr(score, "partial", False) else "")
                    + '</font>',
                    ParagraphStyle("grade", alignment=TA_CENTER, parent=styles["body"])
                ),
                Paragraph(
                    (
                        f'<font color="#B00000"><b>PARTIAL — {score.partial_note}</b></font><br/>'
                        if getattr(score, "partial", False) else ""
                    )
                    + "<br/>".join(
                        f"<b>{k.replace('_', ' ').title()}:</b> {v:.0f}/100"
                        for k, v in score.component_scores.items()
                    ),
                    styles["body"]
                ),
            ]
        ]
        score_tbl = Table(score_data, colWidths=[usable_w * 0.2, usable_w * 0.8])
        score_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), rl_hex("primary")),
            ("BACKGROUND", (1, 0), (1, 0), rl_hex("bg_light")),
            ("GRID", (0, 0), (-1, -1), 0.5, rl_hex("border")),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        flowables += [score_tbl, Spacer(1, 8)]
        return flowables

    def _appendix(self, title: str, df, styles, max_rows: int = 50,
                  excel_note: str = None) -> list:
        """Generic appendix builder — portrait, summary table."""
        flowables = [Paragraph(title, styles["h1"])]
        flowables += _df_to_rl_table(df, styles, max_rows=max_rows)
        if excel_note:
            flowables.append(Spacer(1, 6))
            flowables.append(Paragraph(f"<i>{excel_note}</i>", styles["caption"]))
        return flowables

    def _appendix_pipeline(self, styles) -> list:
        """Appendix A: 6-col summary portrait then full table landscape."""
        flowables = [Paragraph("Appendix A: Pipeline Detail", styles["h1"])]
        summary_df = build_pipeline_summary_table(self.application.pipeline)
        flowables += _df_to_rl_table(summary_df, styles, totals_last=True)
        flowables.append(Spacer(1, 6))
        flowables.append(Paragraph(
            "<i>Full 33-column pipeline detail (deal economics, QLICI structure, timeline) "
            "is provided in the accompanying Excel workbook, Pipeline Detail tab.</i>",
            styles["caption"],
        ))
        # 1.3.0 S3. The caption above sends the reader to the workbook for
        # "QLICI structure"; if the CDE never supplied one, say so here rather
        # than only in the workbook the caption points at.
        _qlici_note = qlici_not_supplied_note(self.application.pipeline)
        if _qlici_note:
            flowables.append(Spacer(1, 6))
            flowables.append(Paragraph(f"<b>{_qlici_note}</b>", styles["caption"]))
        return flowables

    def _appendix_distress(self, styles) -> list:
        """Appendix B: distress table in landscape orientation."""
        usable_w = usable_width(landscape=True)

        flowables = [
            NextPageTemplate("Landscape"),
            PageBreak(),
            Paragraph("Appendix B: Distress Documentation", styles["h1"]),
        ]
        df = build_distress_table(self.application.pipeline)
        if df is not None and not df.empty:
            n_cols = len(df.columns)
            col_w = usable_w / n_cols
            col_widths = [col_w] * n_cols
            flowables += _df_to_rl_table(df, styles, font_size=7, col_widths=col_widths)
        else:
            flowables.append(Paragraph("No distress data available.", styles["caption"]))

        # Switch back to portrait after this appendix
        flowables.append(NextPageTemplate("Body"))
        return flowables

    def _eligibility_source_line(self) -> str:
        """Cite the eligibility source only when it actually loaded.

        markdown_builder._methodology_note branched on this correctly; the
        Word and PDF methodology appendices asserted the citation
        unconditionally, so a run whose eligibility download failed still
        told a federal reviewer the CDFI Fund table had been used.
        """
        pr = self.analysis.pipeline_result
        if getattr(pr, "eligibility_data_status", "ok") != "ok":
            reason = getattr(pr, "eligibility_data_error", None) or "reason unknown"
            return (
                f"ELIGIBILITY: UNAVAILABLE — {reason}. No CDFI Fund eligibility "
                "data was loaded or used anywhere in this draft."
            )
        base = f"ELIGIBILITY: CDFI Fund NMTC Eligibility Table, {ACS_VINTAGE}."
        if is_partial_unverified(pr):
            ids = unverified_ids(pr)
            return (
                f"{base} {len(ids)} of {pr.total_projects} projects could not be "
                f"location-verified (no census tract assigned): {', '.join(ids)}."
            )
        return base

    def _methodology(self, styles) -> list:
        from nmtcapp import __version__
        flowables = [Paragraph("Appendix F: Methodology", styles["h1"])]
        text = (
            f"Generated by <b>nmtc-application-builder v{__version__}</b> on "
            f"{date.today().isoformat()}.<br/><br/>"
            f"{self._eligibility_source_line()}<br/><br/>"
            # Composed from nmtcapp/data/ by renderers/_methodology, and
            # XML-escaped for ReportLab here rather than kept as a second
            # hand-typed copy. This block and Word's used to disagree about
            # the names of the readiness components.
            f"{_rl_escape(distress_definitions())} {_rl_escape(noaa_note())}<br/><br/>"
            f"{_rl_escape(deal_economics_note())}<br/><br/>"
            f"{_rl_escape(impact_bands_note())}<br/><br/>"
            f"{_rl_escape(readiness_weights_note())}"
        )
        flowables.append(Paragraph(text, styles["body"]))
        return flowables


# ---------------------------------------------------------------------------
# Helper: content dict → ReportLab flowables
# ---------------------------------------------------------------------------


def _kv_table(body: dict, styles) -> "Table":
    """Build a section's key/value table so that it fits the page (FIX-2 B1).

    THIS CALL SITE USED TO BE ``Table(data)`` with bare ``str`` cells and no
    ``colWidths``. ReportLab cannot wrap a string cell, so it sized each column
    to the longest single line: Section D drew 691 pt into a 432 pt frame and
    cut the caveat on "QEI Less CDE Fees — $121,582,500" mid-word, and
    Section B drew 17,207 pt — the Q25 basis note as one unwrappable column —
    and rendered as a header bar over four empty striped rows. The words were
    right in the source and absent from the page.

    Three things make it fit, and all three are needed:

    ``colWidths``   45/55 off :func:`usable_width`, the same split the cover
                    page's details table uses. Without it ReportLab measures
                    the content instead of the frame.
    ``Paragraph``   a string cell is one line however wide it is. Only a
                    Paragraph wraps. Cells are XML-escaped on the way in
                    because a Paragraph parses its source as mini-HTML and the
                    section text is plain prose that may contain ``&`` or
                    ``<``; a string cell never parsed anything.
    ``splitInRow``  a ~4,000-character value wraps to roughly 1,000 pt, and no
                    portrait frame is 1,000 pt tall. ReportLab splits BETWEEN
                    rows by default and raises ``LayoutError`` on a single row
                    taller than the page, so ``colWidths`` alone converts a
                    silent overflow into a hard build failure. This lets the
                    row break across pages.

    AND NO ``repeatRows``, which ``_df_to_rl_table`` does set. A repeated
    "Item | Value" header above the continuation of a single wrapped cell
    announces a new row where there is none — the reader turns the page and is
    told the next sentence is a fresh item. It also interleaves those two words
    into the middle of any quoted list that spans the break, which is how
    ``tests/test_pinned_constants`` first saw this. Word's key/value tables do
    not repeat their header either (``_word_helpers.add_styled_table`` sets no
    ``tblHeader``), so this is the same decision on both paginated surfaces.

    WHY A TABLE AT ALL, given the note is 4,000 characters. Markdown renders
    the same dict as a ``**key:** value`` definition list and Word renders it
    as an autofit table whose rows break across pages (``_word_helpers.
    write_section_to_doc``). Both carry the note correctly today. Word is the
    surface to match: it and the PDF are the two PAGINATED renderings of this
    dict, they are the two a CDE prints, and a reader comparing the .docx and
    the .pdf of the same filing should not find one with a table and one with
    a run of prose. Markdown's divergence is not a third option to copy — it
    is what a format with no page does. So: same structure as Word, and
    ``splitInRow`` is what gives a ReportLab row the page-breaking behaviour a
    Word row already has.

    Example::

        flowables.append(_kv_table({"Item": "Value"}, _build_styles()))
    """
    body_pt = TYPOGRAPHY["size_table_body"]
    cell_style = ParagraphStyle(
        "kv_cell", parent=styles["body"],
        fontSize=body_pt, leading=body_pt + 2,
        spaceAfter=0, spaceBefore=0,
        textColor=rl_hex("text_body"),
    )
    header_style = ParagraphStyle(
        "kv_hdr", parent=styles["body"],
        fontSize=TYPOGRAPHY["size_table_header"],
        leading=TYPOGRAPHY["size_table_header"] + 2,
        spaceAfter=0, spaceBefore=0,
        textColor=rl_colors.white, fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )

    data = [[Paragraph("Item", header_style), Paragraph("Value", header_style)]]
    for key, value in body.items():
        data.append([
            Paragraph(_rl_escape(str(key)), cell_style),
            Paragraph(_rl_escape(str(value)), cell_style),
        ])

    usable_w = usable_width()
    tbl = Table(
        data,
        colWidths=[usable_w * 0.45, usable_w * 0.55],
        splitInRow=1,
    )
    style = _rl_table_style(len(data) - 1)
    style.add("WORDWRAP", (0, 0), (-1, -1), "LTR")
    style.add("VALIGN", (0, 0), (-1, -1), "TOP")
    tbl.setStyle(style)
    return tbl


def _content_to_flowables(content: dict, styles) -> list:
    """Convert a section content dict (from SectionGenerator) to ReportLab flowables."""
    flowables = []
    section_id = content.get("section_id", "")
    title = content.get("title", "")
    flowables.append(Paragraph(f"Section {section_id}: {title}", styles["h1"]))
    flowables.append(Spacer(1, 6))

    for sub in content.get("subsections", []):
        heading = sub.get("heading", "")
        body = sub.get("body", "")
        sub_type = sub.get("type", "narrative")

        flowables.append(Paragraph(heading, styles["h2"]))

        if sub_type == "list" and isinstance(body, list):
            for item in body:
                flowables.append(Paragraph(f"• {item}", styles["bullet"]))
        elif sub_type == "table_ref" and isinstance(body, dict):
            flowables.append(_kv_table(body, styles))
        elif sub_type == "table_ref" and isinstance(body, str):
            flowables.append(Paragraph(f"<i>{body}</i>", styles["caption"]))
        else:
            for para_text in str(body).split("\n\n"):
                para_text = para_text.strip()
                if para_text:
                    flowables.append(Paragraph(para_text, styles["body"]))

        flowables.append(Spacer(1, 6))

    return flowables

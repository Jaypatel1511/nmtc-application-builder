"""Professional PDF builder for NMTC applications using ReportLab."""
from __future__ import annotations

import logging
import os
from datetime import date
from typing import TYPE_CHECKING

from nmtcapp.renderers.styles import COLORS, TYPOGRAPHY, PAGE_LAYOUT, rl_hex
from nmtcapp.sections import ALL_SECTIONS
from nmtcapp.tables.distress_table import build_distress_table
from nmtcapp.tables.geographic_table import build_geographic_table
from nmtcapp.tables.impact_table import build_impact_table
from nmtcapp.tables.pipeline_table import build_pipeline_table
from nmtcapp.tables.track_record_table import build_track_record_table

if TYPE_CHECKING:
    from nmtcapp.core.application import Application, ApplicationAnalysis

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
        Table, TableStyle, PageBreak, KeepTogether, HRFlowable,
    )
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib import colors as rl_colors
    _REPORTLAB_AVAILABLE = True
except ImportError:
    _REPORTLAB_AVAILABLE = False


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
                    col_widths=None) -> list:
    """Convert a DataFrame to a list of ReportLab flowables (table + optional caption)."""
    flowables = []
    if df is None or df.empty:
        flowables.append(Paragraph("No data available.", styles["caption"]))
        return flowables

    display = df.head(max_rows)
    header = [str(c) for c in display.columns]
    data = [header]
    for _, row in display.iterrows():
        row_data = []
        for v in row:
            if isinstance(v, float) and abs(v) > 1000:
                row_data.append(f"${v:,.0f}")
            elif isinstance(v, float):
                row_data.append(f"{v:.2f}")
            elif v is None:
                row_data.append("")
            else:
                row_data.append(str(v))
        data.append(row_data)

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(_rl_table_style(len(data) - 1, totals_last=totals_last))
    flowables.append(tbl)

    if len(df) > max_rows:
        flowables.append(Paragraph(
            f"<i>Showing {max_rows} of {len(df)} rows.</i>", styles["caption"]
        ))
    return flowables


# ---------------------------------------------------------------------------
# Page templates
# ---------------------------------------------------------------------------

def _make_header_footer(app: "Application", styles):
    """Return on-page callback functions for header/footer on every page."""

    def _on_page(canvas, doc):
        canvas.saveState()
        w, h = LETTER
        # Footer line
        canvas.setStrokeColor(rl_hex("border"))
        canvas.setLineWidth(0.5)
        canvas.line(inch, 0.65 * inch, w - inch, 0.65 * inch)
        # Footer text
        canvas.setFont("Helvetica", TYPOGRAPHY["size_footnote"])
        canvas.setFillColor(rl_hex("text_muted"))
        footer_text = (
            f"{app.cde.name}  —  NMTC {app.application_round} Application  |  CONFIDENTIAL"
        )
        canvas.drawCentredString(w / 2, 0.45 * inch, footer_text)
        canvas.drawRightString(w - inch, 0.45 * inch, f"Page {doc.page}")
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
        page_w, page_h = LETTER
        frame = Frame(
            margin, 0.9 * inch,
            page_w - 2 * margin,
            page_h - margin - 0.9 * inch,
            id="main",
        )
        cover_frame = Frame(margin, margin, page_w - 2 * margin, page_h - 2 * margin, id="cover")

        doc = BaseDocTemplate(
            path,
            pagesize=LETTER,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=0.9 * inch,
        )
        doc.addPageTemplates([
            PageTemplate(id="Cover", frames=[cover_frame], onPage=on_first),
            PageTemplate(id="Body", frames=[frame], onPage=on_later),
        ])

        story = []
        story += self._cover_page(styles)
        story.append(PageBreak())
        story.append(Paragraph("", ParagraphStyle("switch", commands=[("NextPageTemplate", "Body")])))
        story += self._executive_summary(styles)
        story.append(PageBreak())

        for section_gen in ALL_SECTIONS:
            content = section_gen.generate_content(self.application, self.analysis)
            story += _content_to_flowables(content, styles)
            story.append(PageBreak())

        story += self._appendix("Appendix A: Pipeline Detail",
                                build_pipeline_table(self.application.pipeline, self.application.cde),
                                styles, max_rows=25)
        story.append(PageBreak())
        story += self._appendix("Appendix B: Distress Documentation",
                                build_distress_table(self.application.pipeline), styles)
        story.append(PageBreak())
        story += self._appendix("Appendix C: Geographic Targeting",
                                build_geographic_table(self.application.pipeline), styles)
        story.append(PageBreak())
        story += self._appendix("Appendix D: Impact Projections",
                                build_impact_table(self.application.pipeline), styles, max_rows=25)
        story.append(PageBreak())
        story += self._appendix("Appendix E: CDE Track Record",
                                build_track_record_table(self.application.cde), styles)
        story.append(PageBreak())
        story += self._methodology(styles)

        doc.build(story)
        size_kb = os.path.getsize(path) // 1024
        logger.info("PDF saved: %s (%d KB)", path, size_kb)

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _cover_page(self, styles) -> list:
        app = self.application
        score = self.analysis.readiness_score
        page_w, _ = LETTER
        margin = inch * PAGE_LAYOUT["margin_left"]
        usable_w = page_w - 2 * margin

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
            ["Readiness Assessment:", f"Grade {score.grade} — {score.overall_score:.1f}/100"],
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

        summary_text = (
            f"{app.cde.name} respectfully requests ${app.requested_allocation/1e6:.1f} million in "
            f"New Markets Tax Credit allocation for {app.application_round}. Our "
            f"{pr.total_projects}-project pipeline spans "
            f"{pr.geographic_diversity.get('states_count', 0)} states, with "
            f"{d.get('pct_deep_or_severe', 0):.0%} of QEI committed to deep and severely "
            f"distressed census tracts — placing us in the "
            f"{d.get('vs_historical_winners', 'competitive').replace('_', ' ')} tier of CDFI "
            f"Fund applicants historically."
        )
        flowables.append(Paragraph(summary_text, styles["body"]))
        flowables.append(Spacer(1, 10))

        # Key metrics table
        flowables.append(Paragraph("Key Metrics", styles["h2"]))
        metrics = [
            ["Metric", "Value"],
            ["Total QEI Requested", f"${pr.total_qei_request:,.0f}"],
            ["Total Project Cost", f"${pr.total_project_cost:,.0f}"],
            ["States Represented", str(pr.geographic_diversity.get("states_count", 0))],
            ["Deep/Severe Distress Concentration", f"{d.get('pct_deep_or_severe', 0):.0%}"],
            ["NMTC Eligibility Rate", f"{pr.eligibility_pct:.0%}"],
            ["Jobs to Be Created", f"{impact.get('total_jobs_created', 0):,}"],
            ["Affordable Units to Be Built", f"{impact.get('total_units_built', 0):,}"],
            ["Jobs per $1MM QEI", f"{impact.get('jobs_per_million_qei', 0):.1f}"],
        ]
        page_w, _ = LETTER
        margin = inch * PAGE_LAYOUT["margin_left"]
        usable_w = page_w - 2 * margin
        tbl = Table(metrics, colWidths=[usable_w * 0.65, usable_w * 0.35])
        tbl.setStyle(_rl_table_style(len(metrics) - 1))
        flowables += [tbl, Spacer(1, 12)]

        # Readiness score callout
        flowables.append(Paragraph("Application Readiness Assessment", styles["h2"]))
        score_data = [
            [
                Paragraph(
                    f'<font color="{COLORS["accent"]}"><b>Grade {score.grade}</b></font><br/>'
                    f'<font size="9">{score.overall_score:.1f}/100</font>',
                    ParagraphStyle("grade", alignment=TA_CENTER, parent=styles["body"])
                ),
                Paragraph(
                    "<br/>".join(
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

    def _appendix(self, title: str, df, styles, max_rows: int = 50) -> list:
        flowables = [Paragraph(title, styles["h1"])]
        flowables += _df_to_rl_table(df, styles, max_rows=max_rows)
        return flowables

    def _methodology(self, styles) -> list:
        from nmtcapp import __version__
        flowables = [Paragraph("Appendix F: Methodology", styles["h1"])]
        text = (
            f"Generated by <b>nmtc-application-builder v{__version__}</b> on "
            f"{date.today().isoformat()}.<br/><br/>"
            "ELIGIBILITY: CDFI Fund NMTC Eligibility Table, 2016–2020 ACS 5-Year Estimates.<br/><br/>"
            "DISTRESS LEVELS: Deep distress = poverty rate >30% or unemployment >1.5× national "
            "average. Severe distress = LIC plus additional qualifying factors.<br/><br/>"
            "DEAL ECONOMICS: nmtc-calc library, standard leveraged structure. "
            "Credit price $0.83/credit, CDE fee 2.5% of QEI, 7-year compliance period.<br/><br/>"
            "IMPACT BENCHMARKS: CDFI Fund Annual Reports, CY2018–CY2023. "
            "Average jobs per $1MM QEI: 12.0 FTE. Top quartile: ≥20.0 FTE per $1MM.<br/><br/>"
            "READINESS SCORE: Weighted model (eligibility 25%, distress 25%, geographic 15%, "
            "impact 20%, validation 10%, completeness 5%)."
        )
        flowables.append(Paragraph(text, styles["body"]))
        return flowables


# ---------------------------------------------------------------------------
# Helper: content dict → ReportLab flowables
# ---------------------------------------------------------------------------

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
            data = [["Item", "Value"]] + [[k, str(v)] for k, v in body.items()]
            tbl = Table(data)
            tbl.setStyle(_rl_table_style(len(data) - 1))
            flowables.append(tbl)
        elif sub_type == "table_ref" and isinstance(body, str):
            flowables.append(Paragraph(f"<i>{body}</i>", styles["caption"]))
        else:
            for para_text in str(body).split("\n\n"):
                para_text = para_text.strip()
                if para_text:
                    flowables.append(Paragraph(para_text, styles["body"]))

        flowables.append(Spacer(1, 6))

    return flowables

"""Professional Excel workbook builder for NMTC applications."""
from __future__ import annotations

import logging
import os
from datetime import date
from typing import TYPE_CHECKING

from nmtcapp.data.schema import READINESS_SCORING_WEIGHTS
from nmtcapp.renderers._disclosure import (
    is_partial_unverified, qualified_pct, unverified_banner,
)
from nmtcapp.renderers._methodology import readiness_weights_sheet_note
from nmtcapp.renderers.styles import COLORS, TYPOGRAPHY, TABLE_STYLES, xl_color
from nmtcapp.tables.distress_table import build_distress_table
from nmtcapp.tables.geographic_table import build_geographic_table
from nmtcapp.tables.impact_table import build_impact_table
from nmtcapp.tables.investor_table import build_investor_table
from nmtcapp.tables.investor_table import INVESTOR_TABLE_TITLE
from nmtcapp.tables.pipeline_table import build_pipeline_table
from nmtcapp.tables.track_record_table import build_track_record_table

if TYPE_CHECKING:
    from nmtcapp.core.application import Application, ApplicationAnalysis

logger = logging.getLogger(__name__)

try:
    from openpyxl import Workbook
    from openpyxl.styles import (
        Font, PatternFill, Alignment, Border, Side, numbers
    )
    from openpyxl.styles.differential import DifferentialStyle
    from openpyxl.formatting.rule import ColorScaleRule, CellIsRule, FormulaRule
    from openpyxl.chart import BarChart, Reference
    from openpyxl.chart.series import SeriesLabel
    from openpyxl.utils import get_column_letter
    _OPENPYXL_AVAILABLE = True
except ImportError:
    _OPENPYXL_AVAILABLE = False


# ---------------------------------------------------------------------------
# Style constants (openpyxl PatternFill / Font objects built on first use)
# ---------------------------------------------------------------------------

def _fill(hex_color: str) -> "PatternFill":
    return PatternFill(start_color=hex_color, end_color=hex_color, fill_type="solid")


def _font(bold=False, color="1A1A1A", size=10, name="Calibri", italic=False) -> "Font":
    return Font(name=name, bold=bold, color=color, size=size, italic=italic)


def _center() -> "Alignment":
    return Alignment(horizontal="center", vertical="center", wrap_text=True)


def _left() -> "Alignment":
    return Alignment(horizontal="left", vertical="center", wrap_text=True)


def _right() -> "Alignment":
    return Alignment(horizontal="right", vertical="center")


def _thin_border() -> "Border":
    thin = Side(style="thin", color=xl_color("border"))
    return Border(left=thin, right=thin, top=thin, bottom=thin)


# Number formats
FMT_CURRENCY = '"$"#,##0'
FMT_CURRENCY_DEC = '"$"#,##0.00'
FMT_PCT = "0.0%"
FMT_PCT0 = "0%"
FMT_NUMBER = "#,##0"
FMT_DECIMAL2 = "0.00"
FMT_TEXT = "@"


class ExcelApplicationBuilder:
    """Builds a professional Excel workbook for the NMTC application package.

    Produces 7 sheets: Pipeline Detail, Distress Documentation, Geographic
    Targeting, Impact Projections, Investor Commitments, Track Record, and a
    Summary Dashboard.

    Example::

        builder = ExcelApplicationBuilder(application, analysis)
        builder.save("./drafts/application.xlsx")
    """

    def __init__(self, application: "Application", analysis: "ApplicationAnalysis") -> None:
        if not _OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl is required for Excel output. Install with: pip install openpyxl")
        self.application = application
        self.analysis = analysis

    def build(self) -> "Workbook":
        """Build and return an openpyxl Workbook.

        Example::

            wb = builder.build()
        """
        wb = Workbook()
        wb.remove(wb.active)  # remove default empty sheet

        self._build_summary_dashboard(wb)
        self._build_pipeline_sheet(wb)
        self._build_distress_sheet(wb)
        self._build_geographic_sheet(wb)
        self._build_impact_sheet(wb)
        self._build_investor_sheet(wb)
        self._build_track_record_sheet(wb)

        return wb

    def save(self, path: str) -> None:
        """Save the workbook to an .xlsx file.

        Example::

            builder.save("./output/application.xlsx")
        """
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        wb = self.build()
        wb.save(path)
        size_kb = os.path.getsize(path) // 1024
        logger.info("Excel workbook saved: %s (%d KB)", path, size_kb)

    # ------------------------------------------------------------------
    # Sheet 1: Summary Dashboard
    # ------------------------------------------------------------------

    def _build_summary_dashboard(self, wb: "Workbook") -> None:
        ws = wb.create_sheet("Summary Dashboard")
        ws.sheet_view.showGridLines = False
        app = self.application
        analysis = self.analysis
        pr = analysis.pipeline_result
        score = analysis.readiness_score

        # Title block
        ws.merge_cells("A1:F1")
        ws["A1"] = "NEW MARKETS TAX CREDIT ALLOCATION APPLICATION"
        ws["A1"].font = _font(bold=True, color="FFFFFF", size=16)
        ws["A1"].fill = _fill(xl_color("primary"))
        ws["A1"].alignment = _center()
        ws.row_dimensions[1].height = 30

        ws.merge_cells("A2:F2")
        ws["A2"] = app.cde.name
        ws["A2"].font = _font(bold=True, color="FFFFFF", size=13)
        ws["A2"].fill = _fill(xl_color("secondary"))
        ws["A2"].alignment = _center()
        ws.row_dimensions[2].height = 22

        degraded = getattr(pr, "eligibility_data_status", "ok") != "ok"
        partial_unverified = is_partial_unverified(pr)
        ws.merge_cells("A3:F3")
        ws["A3"] = (
            f"{app.application_round}  |  Prepared: {date.today().strftime('%B %d, %Y')}  |  "
            f"Readiness Grade: {score.grade} ({score.overall_score:.1f}/100"
            + (" PARTIAL)" if getattr(score, "partial", False) else ")")
        )
        ws["A3"].font = _font(color="FFFFFF", size=9, italic=True)
        ws["A3"].fill = _fill(xl_color("accent"))
        ws["A3"].alignment = _center()
        ws.row_dimensions[3].height = 16

        if degraded:
            ws.merge_cells("A4:F4")
            ws["A4"] = (
                "ELIGIBILITY DATA UNAVAILABLE — "
                f"{getattr(pr, 'eligibility_data_error', None) or 'reason unknown'}. "
                "Eligibility/distress figures are unverified; readiness score is "
                "partial (computed without eligibility verification)."
            )
            ws["A4"].font = _font(bold=True, color="FFFFFF", size=10)
            ws["A4"].fill = _fill("B00000")
            ws["A4"].alignment = _center()
            ws.row_dimensions[4].height = 28
        elif partial_unverified:
            ws.merge_cells("A4:F4")
            ws["A4"] = "UNVERIFIED PROJECT LOCATIONS — " + unverified_banner(pr)
            ws["A4"].font = _font(bold=True, color="FFFFFF", size=10)
            ws["A4"].fill = _fill("B00000")
            ws["A4"].alignment = _center()
            ws.row_dimensions[4].height = 28

        # --- Key Metrics block (rows 5–14) ---
        ws["A5"] = "KEY APPLICATION METRICS"
        ws["A5"].font = _font(bold=True, color=xl_color("primary"), size=11)
        ws.merge_cells("A5:F5")

        distress = pr.distress_breakdown
        impact = pr.aggregate_impact
        metrics = [
            ("Total NMTC Allocation Requested", app.requested_allocation, FMT_CURRENCY, "primary"),
            ("Total QEI in Pipeline", pr.total_qei_request, FMT_CURRENCY, "secondary"),
            ("Total Project Cost", pr.total_project_cost, FMT_CURRENCY, "secondary"),
            ("Number of Projects", pr.total_projects, FMT_NUMBER, "secondary"),
            ("States Represented", pr.geographic_diversity.get("states_count", 0), FMT_NUMBER, "secondary"),
            ("NMTC Eligibility Rate",
             ("Unverified" if degraded
              else qualified_pct(pr.eligibility_pct, pr) if partial_unverified
              else pr.eligibility_pct),
             FMT_TEXT if (degraded or partial_unverified) else FMT_PCT, None),
            ("Deep/Severe Distress Concentration",
             ("Unverified" if degraded
              else qualified_pct(distress.get("pct_deep_or_severe", 0), pr)
              if partial_unverified
              else distress.get("pct_deep_or_severe", 0)),
             FMT_TEXT if (degraded or partial_unverified) else FMT_PCT, None),
            ("Total Jobs to Be Created", impact.get("total_jobs_created", 0), FMT_NUMBER, None),
            ("Jobs per $1MM QEI", impact.get("jobs_per_million_qei", 0), FMT_DECIMAL2, None),
        ]

        for i, (label, val, fmt, color_key) in enumerate(metrics):
            row = 6 + i
            ws.row_dimensions[row].height = 18
            label_cell = ws.cell(row=row, column=1, value=label)
            val_cell = ws.cell(row=row, column=3, value=val)
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
            ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=4)

            bg = xl_color("row_even") if i % 2 == 0 else xl_color("row_odd")
            label_cell.fill = _fill(bg)
            val_cell.fill = _fill(bg)
            label_cell.font = _font(size=10)
            label_cell.alignment = _left()
            label_cell.border = _thin_border()
            val_cell.number_format = fmt
            val_cell.font = _font(bold=True, size=10)
            val_cell.alignment = _right()
            val_cell.border = _thin_border()

        # --- Readiness Score block (rows 16–22) ---
        ws["A16"] = "READINESS SCORE BREAKDOWN"
        ws["A16"].font = _font(bold=True, color=xl_color("primary"), size=11)
        ws.merge_cells("A16:F16")

        ws.cell(row=17, column=1, value="Component").font = _font(bold=True, color="FFFFFF", size=10)
        ws.cell(row=17, column=3, value="Score").font = _font(bold=True, color="FFFFFF", size=10)
        ws.cell(row=17, column=4, value="Weight").font = _font(bold=True, color="FFFFFF", size=10)
        for col in (1, 2, 3, 4):
            ws.cell(row=17, column=col).fill = _fill(xl_color("primary"))
            ws.cell(row=17, column=col).alignment = _center()
            ws.cell(row=17, column=col).border = _thin_border()
        ws.merge_cells("A17:B17")
        ws.row_dimensions[17].height = 18

        # READ THE WEIGHTS, DO NOT RETYPE THEM. This was a hardcoded dict whose
        # keys were "eligibility" and "validation" while ReadinessScore's
        # component keys are "eligibility_quality" and "validation_pass_rate",
        # so weight_map.get(comp, 0) returned 0 for both. The workbook the Word
        # and PDF documents cross-reference as the authoritative attachment
        # printed Eligibility Quality 0.0% and Validation Pass Rate 0.0%, a
        # Weight column summing to 65%, and two components declared weightless
        # — against a methodology appendix in the same package stating 25% and
        # 10%. Reading the constant makes the two agree by construction and
        # removes the key-drift failure mode entirely.
        weight_map = READINESS_SCORING_WEIGHTS
        for i, (comp, val) in enumerate(score.component_scores.items()):
            row = 18 + i
            ws.row_dimensions[row].height = 17
            bg = xl_color("row_even") if i % 2 == 0 else xl_color("row_odd")

            label_cell = ws.cell(row=row, column=1, value=comp.replace("_", " ").title())
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
            score_cell = ws.cell(row=row, column=3, value=val)
            weight_cell = ws.cell(row=row, column=4, value=weight_map.get(comp, 0))

            for cell in (label_cell, score_cell, weight_cell):
                cell.fill = _fill(bg)
                cell.border = _thin_border()
            label_cell.font = _font(size=10)
            label_cell.alignment = _left()
            score_cell.number_format = "0.0"
            score_cell.font = _font(bold=True, size=10)
            score_cell.alignment = _right()
            weight_cell.number_format = FMT_PCT
            weight_cell.font = _font(size=10)
            weight_cell.alignment = _right()

            # Conditional color: ≥75 green, ≥50 yellow, <50 red
            if val >= 75:
                score_cell.font = _font(bold=True, color=xl_color("green"), size=10)
            elif val >= 50:
                score_cell.font = _font(bold=True, color=xl_color("yellow"), size=10)
            else:
                score_cell.font = _font(bold=True, color=xl_color("red"), size=10)

        # Overall score totals row
        tot_row = 18 + len(score.component_scores)
        ws.row_dimensions[tot_row].height = 20
        overall_label = ws.cell(row=tot_row, column=1, value="OVERALL SCORE")
        ws.merge_cells(start_row=tot_row, start_column=1, end_row=tot_row, end_column=2)
        overall_val = ws.cell(row=tot_row, column=3, value=score.overall_score)
        overall_grade = ws.cell(row=tot_row, column=4, value=f"Grade {score.grade}")
        for cell in (overall_label, overall_val, overall_grade):
            cell.fill = _fill(xl_color("row_total"))
            cell.font = _font(bold=True, size=11)
            cell.border = _thin_border()
        overall_label.alignment = _left()
        overall_val.number_format = "0.0"
        overall_val.alignment = _right()
        overall_grade.alignment = _center()

        # The workbook showed a Weight column with no statement of whose
        # weighting it was — the only one of the four artifacts to print the
        # readiness breakdown without the disclosure the other three carry, and
        # the one a reviewer opens to check the numbers.
        disclosure_row = tot_row + 1
        ws.merge_cells(start_row=disclosure_row, start_column=1,
                       end_row=disclosure_row, end_column=6)
        ws.row_dimensions[disclosure_row].height = 28
        note_cell = ws.cell(row=disclosure_row, column=1,
                            value=readiness_weights_sheet_note())
        note_cell.font = _font(italic=True, color=xl_color("text_muted"), size=8)
        note_cell.alignment = _left()

        # --- Bar chart: component scores ---
        try:
            score_start_row = 18
            score_end_row = 18 + len(score.component_scores) - 1
            chart = BarChart()
            chart.type = "bar"
            chart.title = "Readiness Score Components"
            chart.y_axis.title = "Score (0–100)"
            chart.style = 10
            chart.width = 14
            chart.height = 8

            data_ref = Reference(ws, min_col=3, min_row=score_start_row,
                                 max_row=score_end_row)
            cats_ref = Reference(ws, min_col=1, min_row=score_start_row,
                                 max_row=score_end_row)
            chart.add_data(data_ref)
            chart.set_categories(cats_ref)
            chart.series[0].title = SeriesLabel(v="Score")

            ws.add_chart(chart, "F5")
        except Exception:
            pass  # chart is optional — don't fail the build

        # Column widths
        ws.column_dimensions["A"].width = 22
        ws.column_dimensions["B"].width = 18
        ws.column_dimensions["C"].width = 18
        ws.column_dimensions["D"].width = 12
        ws.column_dimensions["E"].width = 12
        ws.column_dimensions["F"].width = 12

        # Footer
        footer_row = disclosure_row + 2
        ws.merge_cells(f"A{footer_row}:F{footer_row}")
        ws.cell(row=footer_row, column=1,
                value=f"CONFIDENTIAL — {app.cde.name} — NMTC {app.application_round} — "
                      f"Generated {date.today().isoformat()}")
        ws.cell(row=footer_row, column=1).font = _font(italic=True, color=xl_color("text_muted"), size=8)
        ws.cell(row=footer_row, column=1).alignment = _center()

    # ------------------------------------------------------------------
    # Generic DataFrame → worksheet writer
    # ------------------------------------------------------------------

    def _write_df_to_sheet(
        self,
        wb: "Workbook",
        sheet_name: str,
        df,
        title: str,
        currency_cols: list = None,
        pct_cols: list = None,
        number_cols: list = None,
        freeze_col: int = 2,
        max_rows: int = 200,
    ) -> None:
        """Write a DataFrame to a new worksheet with professional formatting."""
        ws = wb.create_sheet(sheet_name)
        ws.sheet_view.showGridLines = False

        if df is None or df.empty:
            ws["A1"] = "No data available."
            return

        display = df.head(max_rows)
        currency_cols = set(currency_cols or [])
        pct_cols = set(pct_cols or [])
        number_cols = set(number_cols or [])

        # FAIL LOUD ON A STALE CONFIG. Every one of these lists is a set of
        # column names typed at the call site, and five of the six sheets had
        # drifted: twenty names across Pipeline Detail, Distress Documentation,
        # Geographic Targeting, Impact Projections and Track Record referred to
        # columns that do not exist in the DataFrames they format. The columns
        # then fell through to the magnitude-based auto-detect below, which is
        # how Appendix C's share column ended up reading 0 0 0 0 0 0 1.
        #
        # A misconfigured column is silent by construction — the sheet still
        # renders, just wrong — so it has to be an exception rather than a
        # log line. The developer sees it on the first build; the CDE never
        # files it.
        named = currency_cols | pct_cols | number_cols
        missing = sorted(named - set(display.columns))
        if missing:
            raise ValueError(
                f"{sheet_name!r} formats column(s) that do not exist in its "
                f"table: {missing}. Available: {sorted(display.columns)}. "
                "A name that matches nothing formats nothing and falls through "
                "to magnitude-based auto-detection."
            )

        # Title row
        n_cols = len(display.columns)
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)
        title_cell = ws.cell(row=1, column=1, value=title)
        title_cell.font = _font(bold=True, color="FFFFFF", size=12)
        title_cell.fill = _fill(xl_color("primary"))
        title_cell.alignment = _center()
        ws.row_dimensions[1].height = 24

        # Sub-header: generation info
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=n_cols)
        sub_cell = ws.cell(row=2, column=1,
                           value=f"{self.application.cde.name}  |  {self.application.application_round}  "
                                 f"|  Generated {date.today().isoformat()}")
        sub_cell.font = _font(italic=True, color=xl_color("text_muted"), size=8)
        sub_cell.fill = _fill(xl_color("bg_light"))
        sub_cell.alignment = _center()
        ws.row_dimensions[2].height = 14

        # Header row (row 3)
        header_row = 3
        ws.row_dimensions[header_row].height = 20
        for j, col_name in enumerate(display.columns, start=1):
            cell = ws.cell(row=header_row, column=j, value=str(col_name))
            cell.font = _font(bold=True, color="FFFFFF", size=10)
            cell.fill = _fill(xl_color("primary"))
            cell.alignment = _center()
            cell.border = _thin_border()

        # Enable auto-filter on header row
        ws.auto_filter.ref = (
            f"A{header_row}:{get_column_letter(n_cols)}{header_row + len(display)}"
        )

        # Freeze: row 3 header + first freeze_col columns
        ws.freeze_panes = ws.cell(row=header_row + 1, column=freeze_col + 1)

        # Data rows
        is_last_row = False
        for i, (_, row_data) in enumerate(display.iterrows()):
            row_num = header_row + 1 + i
            is_last_row = (i == len(display) - 1)
            bg = xl_color("row_total") if is_last_row else (
                xl_color("row_even") if i % 2 == 0 else xl_color("row_odd")
            )
            ws.row_dimensions[row_num].height = 16

            for j, (col_name, val) in enumerate(zip(display.columns, row_data), start=1):
                cell = ws.cell(row=row_num, column=j)
                cell.fill = _fill(bg)
                cell.border = _thin_border()
                cell.alignment = _left()

                if is_last_row:
                    cell.font = _font(bold=True, size=10)
                else:
                    cell.font = _font(size=10)

                # Format by column type
                if col_name in currency_cols and isinstance(val, (int, float)):
                    cell.value = val
                    cell.number_format = FMT_CURRENCY
                    cell.alignment = _right()
                elif col_name in pct_cols and isinstance(val, (int, float)):
                    cell.value = val
                    cell.number_format = FMT_PCT
                    cell.alignment = _right()
                elif col_name in number_cols and isinstance(val, (int, float)):
                    cell.value = val
                    cell.number_format = FMT_NUMBER
                    cell.alignment = _right()
                else:
                    # Auto-detect currency by value size for unlabelled columns
                    if isinstance(val, float) and abs(val) > 10000:
                        cell.value = val
                        cell.number_format = FMT_CURRENCY
                        cell.alignment = _right()
                    elif isinstance(val, (int, float)):
                        cell.value = val
                        cell.number_format = FMT_NUMBER
                        cell.alignment = _right()
                    else:
                        cell.value = str(val) if val is not None else ""

        # Auto-size columns (cap at 40 chars)
        for j, col_name in enumerate(display.columns, start=1):
            col_letter = get_column_letter(j)
            max_len = max(
                len(str(col_name)),
                max((len(str(v)) for v in display.iloc[:, j - 1] if v is not None), default=0),
            )
            ws.column_dimensions[col_letter].width = min(max_len + 3, 40)

        if len(df) > max_rows:
            note_row = header_row + max_rows + 2
            ws.cell(row=note_row, column=1,
                    value=f"Showing {max_rows} of {len(df)} rows. See full data in source system.")
            ws.cell(row=note_row, column=1).font = _font(italic=True, color=xl_color("text_muted"), size=9)

    # ------------------------------------------------------------------
    # Individual sheet builders
    # ------------------------------------------------------------------

    def _build_pipeline_sheet(self, wb: "Workbook") -> None:
        df = build_pipeline_table(self.application.pipeline, self.application.cde)
        self._write_df_to_sheet(
            wb, "Pipeline Detail", df,
            title="Appendix A: Pipeline Detail",
            currency_cols=["Total Project Cost ($)", "QEI Request ($)",
                           "Total QLICI ($)", "Leverage Loan ($)",
                           "Total NMTCs ($)", "Estimated Investor Equity ($)",
                           "CDE Fee ($)"],
            number_cols=["Jobs Created", "Jobs Retained",
                         "Affordable Units Built", "Square Feet"],
            freeze_col=2,
            max_rows=100,
        )

        # Conditional formatting: Distress Level column
        ws = wb["Pipeline Detail"]
        try:
            # Find "Distress Level" column index
            header_row_vals = [ws.cell(row=3, column=j).value for j in range(1, 50)]
            if "Distress Level" in header_row_vals:
                col_idx = header_row_vals.index("Distress Level") + 1
                col_letter = get_column_letter(col_idx)
                last_row = 3 + min(len(df), 100)
                # Deep Distress → green background
                green_fill = PatternFill(start_color=xl_color("green_light"),
                                        end_color=xl_color("green_light"), fill_type="solid")
                yellow_fill = PatternFill(start_color=xl_color("yellow_light"),
                                         end_color=xl_color("yellow_light"), fill_type="solid")
                red_fill = PatternFill(start_color=xl_color("red_light"),
                                       end_color=xl_color("red_light"), fill_type="solid")
                rng = f"{col_letter}4:{col_letter}{last_row}"
                ws.conditional_formatting.add(
                    rng, CellIsRule(operator="equal", formula=['"Deep Distress"'],
                                   fill=green_fill))
                ws.conditional_formatting.add(
                    rng, CellIsRule(operator="equal", formula=['"Severely Distressed"'],
                                   fill=yellow_fill))
                ws.conditional_formatting.add(
                    rng, CellIsRule(operator="equal", formula=['"Non-LIC (Ineligible)"'],
                                   fill=red_fill))
        except Exception:
            pass

    def _build_distress_sheet(self, wb: "Workbook") -> None:
        df = build_distress_table(self.application.pipeline)
        self._write_df_to_sheet(
            wb, "Distress Documentation", df,
            title="Appendix B: Distress Documentation",
            # No numeric columns. "Poverty Rate (%)" and "Unemployment Rate
            # (%)" both render the string "See ACS" — tables/distress_table
            # refuses to infer an ACS statistic from a distress label. The
            # pct_cols this used to carry named "Poverty Rate (Est.)" and
            # "Unemployment Rate (Est.)", which have never existed here.
            freeze_col=2,
        )

    def _build_geographic_sheet(self, wb: "Workbook") -> None:
        df = build_geographic_table(self.application.pipeline)
        self._write_df_to_sheet(
            wb, "Geographic Targeting", df,
            title="Appendix C: Geographic Targeting",
            currency_cols=["QEI ($)"],
            # The real pct_cols entry the 1.2.0 note asked for once this
            # config was repaired. The column is a float again.
            pct_cols=["QEI (% of Total)"],
            number_cols=["Project Count", "Deep/Severe Projects",
                         "Native Area Projects (CDE-declared)",
                         "HMR Projects", "OZ Projects"],
            freeze_col=1,
        )

        # Color scale on Total QEI column
        ws = wb["Geographic Targeting"]
        try:
            header_vals = [ws.cell(row=3, column=j).value for j in range(1, 30)]
            if "QEI ($)" in header_vals:
                col_idx = header_vals.index("QEI ($)") + 1
                col_letter = get_column_letter(col_idx)
                last_row = 3 + min(len(df), 200) if df is not None and not df.empty else 10
                ws.conditional_formatting.add(
                    f"{col_letter}4:{col_letter}{last_row}",
                    ColorScaleRule(
                        start_type="min", start_color="FFFFFF",
                        mid_type="percentile", mid_value=50, mid_color=xl_color("row_even"),
                        end_type="max", end_color=xl_color("secondary"),
                    )
                )
        except Exception:
            pass

    def _build_impact_sheet(self, wb: "Workbook") -> None:
        df = build_impact_table(self.application.pipeline)
        self._write_df_to_sheet(
            wb, "Impact Projections", df,
            title="Appendix D: Impact Projections",
            currency_cols=["QEI ($)", "Total Project Cost ($)",
                           "Cost per Job ($)", "QEI per Job ($)"],
            number_cols=["Jobs Created", "Jobs Retained", "Total Jobs",
                         "Affordable Units", "Commercial Sq Ft"],
            freeze_col=2,
            max_rows=100,
        )

    def _build_investor_sheet(self, wb: "Workbook") -> None:
        df = build_investor_table(self.application)
        self._write_df_to_sheet(
            wb, "Investor Commitments", df,
            title=INVESTOR_TABLE_TITLE,
            currency_cols=["Commitment Amount ($)", "NMTCs Allocated ($)"],
            freeze_col=1,
        )

    def _build_track_record_sheet(self, wb: "Workbook") -> None:
        df = build_track_record_table(self.application.cde)
        self._write_df_to_sheet(
            wb, "Track Record", df,
            title="Appendix E: CDE Track Record",
            currency_cols=["Allocation ($)"],
            freeze_col=1,
        )

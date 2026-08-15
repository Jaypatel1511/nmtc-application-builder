"""Format a table cell by WHAT ITS COLUMN IS, not by what Python type it holds.

THE DEFECT THIS REPLACES

Every renderer decided currency by looking at the value::

    _word_helpers._fmt_cell   float and val > 1000        -> f"${val:,.0f}"
    pdf_builder._df_to_rl_table   float and abs(v) > 1000 -> f"${v:,.0f}"
    markdown_builder._df_to_md    float and v > 1000      -> f"{v:,.2f}"
    excel_builder._write_df_to_sheet  float and abs>10000 -> FMT_CURRENCY

A type-based rule standing in for a column-based one. It gets two things wrong
in opposite directions and both had live instances in 1.2.0:

  TOO EAGER   any non-currency float over the threshold takes a dollar sign it
              has not earned. A square footage, a ratio, an index, a rate.
  TOO TIMID   a share stored as a fraction (0.328) is under the threshold, so
              Word and PDF printed "0.33" for a state holding 32.8% of pipeline
              QEI, markdown printed "0.328", and Excel's auto-detect gave it
              "#,##0" and rendered it "0". Appendix C read 0 0 0 0 0 0 1 down
              the whole share column, in the workbook the Word and PDF
              documents cross-reference as the authoritative attachment.

1.2.0 worked around the second by pre-formatting that one column to a string in
tables/geographic_table, and said so in a comment that ends "If this sheet's
format config is repaired later, move this back to a float and give it a real
pct_cols entry." This module is that repair. The column knows what it is; the
value does not.

THE CONVENTION, which every table in this package already follows:

    header ends with "($)"          currency, whole dollars
    header ends with "($/credit)"   currency, cents
    header contains "(%"  or "%)"   a share stored as a FRACTION, shown as %
    anything else                   plain: thousands separator for integers,
                                    two decimals for floats, str() otherwise

Nothing infers from magnitude. A column that wants a dollar sign says so in its
own name, which is also what the reader of the header is told.
"""
from __future__ import annotations

import math

# What a cell prints when no value was supplied. Matches the tri-state flags
# elsewhere in the package rather than inventing a second convention.
NOT_SUPPLIED = "—"


def is_currency_column(header: str) -> bool:
    """True when the column header declares itself a dollar column."""
    h = str(header).strip()
    return h.endswith("($)") or h.endswith("($/credit)") or h.endswith("($/NMTC)")


def is_pct_column(header: str) -> bool:
    """True when the column holds a share stored as a fraction of one."""
    h = str(header).strip()
    return "(%" in h or h.endswith("(%)") or "% of Total" in h


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def format_cell(header: str, value) -> str:
    """Render one cell as text, deciding by the column's declared meaning.

    Example::

        format_cell("QEI ($)", 8500000.0)        # '$8,500,000'
        format_cell("QEI (% of Total)", 0.3284)  # '32.8%'
        format_cell("Square Feet", 24000.0)      # '24,000'
        format_cell("Jobs/$MM QEI", 7.13)        # '7.13'
    """
    # AN ABSENT VALUE IS NOT AN EMPTY ONE. A blank cell reads as an oversight
    # or as a zero somebody forgot to type; the em dash is what this package
    # already uses for "nobody told us" (tables/distress_table._flag,
    # tables/pipeline_table._yn_flag), so a reader who has seen one cell of it
    # knows what the next one means. It matters most where the column is
    # numeric: "0 affordable units" is a claim, "—" is not.
    if value is None:
        return NOT_SUPPLIED
    if _is_number(value) and isinstance(value, float) and math.isnan(value):
        return NOT_SUPPLIED

    if _is_number(value):
        if is_currency_column(header):
            if str(header).strip().endswith(("($/credit)", "($/NMTC)")):
                return f"${value:,.2f}"
            return f"${value:,.0f}"
        if is_pct_column(header):
            return f"{value:.1%}"
        if isinstance(value, float):
            # A whole-valued float in a plain column is a count that lost its
            # int somewhere (pandas promotes on a column with any NaN); show it
            # as the count it is rather than "24000.00".
            if value == int(value):
                return f"{int(value):,}"
            return f"{value:,.2f}"
        return f"{value:,}"

    return str(value)

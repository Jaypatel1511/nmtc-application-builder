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
    header names an IDENTIFIER      digits, exactly as given: no separator, no
                                    decimal point (see below)
    anything else                   plain: thousands separator for integers,
                                    two decimals for floats, str() otherwise

Nothing infers from magnitude. A column that wants a dollar sign says so in its
own name, which is also what the reader of the header is told.

IDENTIFIERS ARE NOT QUANTITIES (1.2.1 B-3)

The "anything else" arm above ends in ``f"{value:,}"``, and that is right for a
count and wrong for a label that happens to be made of digits. It shipped a
prior NMTC award year as **2,019** on all four surfaces — a year is an
identifier, not a quantity, and nothing is 2,019 of anything.

The consequence scales with the identifier. An 11-digit census tract GEOID
rendered ``17,031,838,200`` in a filing, in the column carrying a "CDFI Fund
NMTC Eligibility Table" citation, would be worse: unlike a stray comma in a
year it is not obviously a formatting fault, and a reviewer checking the tract
against the Fund's table finds nothing at that number.

So the class is declared rather than discovered. A column is an identifier when
its header names one — year, census tract, GEOID, FIPS, ZIP, or an ID — and an
identifier column never takes a separator whatever the magnitude of its value.
The GEOID columns reach this module as strings today (tables/distress_table
calls ``str()`` on them), so this rule is not what makes them correct now; it is
what keeps them correct the first time one arrives as an int.
"""
from __future__ import annotations

import math
import re

# What a cell prints when no value was supplied. Matches the tri-state flags
# elsewhere in the package rather than inventing a second convention.
NOT_SUPPLIED = "—"

# The same fact in a sentence. A narrative bullet cannot use a bare em dash —
# "• — affordable or mixed-income housing units developed" reads as a rendering
# fault — so the prose surfaces say it in words instead. Both come from here so
# a table cell and the paragraph above it cannot drift apart.
NOT_SUPPLIED_NARRATIVE = "Not reported"


def supplied_total(value, spec: str = "{:,}") -> str:
    """Format an aggregate that is ``None`` when no input was supplied.

    The counterpart of :data:`NOT_SUPPLIED` for figures that come out of
    :func:`~nmtcapp.intelligence.impact_aggregator.aggregate_impact` rather
    than out of a DataFrame column. Same rule, same reason: a supplied zero is
    a claim about the pipeline and an absent value is not, so they must not
    render alike.

    Example::

        supplied_total(142)         # '142'
        supplied_total(0)           # '0'      <- the CDE answered
        supplied_total(None)        # '—'      <- the CDE did not
    """
    if value is None:
        return NOT_SUPPLIED
    return spec.format(value)


def is_currency_column(header: str) -> bool:
    """True when the column header declares itself a dollar column."""
    h = str(header).strip()
    return h.endswith("($)") or h.endswith("($/credit)") or h.endswith("($/NMTC)")


def is_pct_column(header: str) -> bool:
    """True when the column holds a share stored as a fraction of one."""
    h = str(header).strip()
    return "(%" in h or h.endswith("(%)") or "% of Total" in h


# Word-bounded so "Sectors" does not match "Sector ID" logic and, more to the
# point, so "Total Jobs" never matches on a bare "ID" substring. Each term is a
# thing this package actually has a column for; add to the list rather than
# loosening a pattern.
_IDENTIFIER_TERMS = (
    r"year",          # Award Year
    r"census\s+tract",  # Census Tract (11-digit) / (GEOID)
    r"geoid",
    r"fips",
    r"zip(\s+code)?",
    r"tract",
    r"id",            # Project ID, CDE ID, QALICB ID
    r"identifier",
    r"number",        # Award Number, Application Number
    r"code",          # NAICS Code, State Code
)
_IDENTIFIER_RE = re.compile(
    r"(?<![A-Za-z])(" + "|".join(_IDENTIFIER_TERMS) + r")(?![A-Za-z])",
    re.IGNORECASE,
)


def is_identifier_column(header: str) -> bool:
    """True when the column names a label made of digits, not a quantity.

    An identifier column never takes a thousands separator: a year is not
    2,019 of anything and a census tract is not 17,031,838,200 of anything.

    A "($)" or "(%" header wins over this one — a column cannot be both, and
    a currency header is the more specific declaration. That ordering matters
    for a header like "Allocation ($)" sitting beside "Award Year".

    Example::

        is_identifier_column("Award Year")               # True
        is_identifier_column("Census Tract (11-digit)")  # True
        is_identifier_column("ZIP Code")                 # True
        is_identifier_column("Project ID")               # True
        is_identifier_column("Jobs Created")             # False
        is_identifier_column("Square Feet")              # False
    """
    h = str(header).strip()
    if is_currency_column(h) or is_pct_column(h):
        return False
    return bool(_IDENTIFIER_RE.search(h))


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def format_cell(header: str, value) -> str:
    """Render one cell as text, deciding by the column's declared meaning.

    Example::

        format_cell("QEI ($)", 8500000.0)        # '$8,500,000'
        format_cell("QEI (% of Total)", 0.3284)  # '32.8%'
        format_cell("Square Feet", 24000.0)      # '24,000'
        format_cell("Jobs/$MM QEI", 7.13)        # '7.13'
        format_cell("Award Year", 2019)          # '2019'   <- not '2,019'
        format_cell("Census Tract (GEOID)", 17031838200)  # '17031838200'
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
        # BEFORE the plain-number arm, which is where the separator lives.
        if is_identifier_column(header):
            if isinstance(value, float) and value == int(value):
                return str(int(value))
            return str(value)
        if isinstance(value, float):
            # A whole-valued float in a plain column is a count that lost its
            # int somewhere (pandas promotes on a column with any NaN); show it
            # as the count it is rather than "24000.00".
            if value == int(value):
                return f"{int(value):,}"
            return f"{value:,.2f}"
        return f"{value:,}"

    return str(value)

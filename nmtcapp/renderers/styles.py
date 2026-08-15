"""
Shared visual style definitions for all NMTC application output formats.

All renderers import from here to ensure consistency across Word, Excel, and PDF.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Color palette — cohesive identity across all formats
# ---------------------------------------------------------------------------
COLORS = {
    # Primary brand colors
    "primary":       "#1B438C",   # CDFI Fund-inspired deep blue
    "secondary":     "#2E6DA4",   # Medium blue (subheadings, borders)
    "accent":        "#F0A500",   # Gold — for grades, callouts, dividers
    # Table row colors
    "row_header":    "#1B438C",   # Table header background
    "row_even":      "#EBF0FA",   # Alternating row fill (light blue)
    "row_odd":       "#FFFFFF",   # Alternating row fill (white)
    "row_total":     "#D6E4F5",   # Summary/total row
    # Status / conditional formatting
    "green":         "#2D7D46",
    "green_light":   "#D6F0DF",
    "yellow":        "#C27C0E",
    "yellow_light":  "#FFF3CD",
    "red":           "#C0392B",
    "red_light":     "#FDECEA",
    # Neutral
    "text_dark":     "#1A1A1A",
    "text_body":     "#2C2C2C",
    "text_muted":    "#6B6B6B",
    "border":        "#BDC6D8",
    "bg_light":      "#F5F7FA",
    "white":         "#FFFFFF",
}

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
FONTS = {
    "heading":    "Calibri",
    "body":       "Calibri",
    "mono":       "Courier New",
}

# ---------------------------------------------------------------------------
# Typography — point sizes
# ---------------------------------------------------------------------------
TYPOGRAPHY = {
    "size_cover_title":  28,
    "size_h1":           18,
    "size_h2":           14,
    "size_h3":           12,
    "size_body":         11,
    "size_table_header": 10,
    "size_table_body":   10,
    "size_caption":       9,
    "size_footnote":       8,
}

# ---------------------------------------------------------------------------
# Page layout (in inches)
# ---------------------------------------------------------------------------
PAGE_LAYOUT = {
    "margin_top":    1.0,
    "margin_bottom": 1.0,
    "margin_left":   1.25,
    "margin_right":  1.25,
    "header_height": 0.5,
    "footer_height": 0.4,
}

# ---------------------------------------------------------------------------
# Table style settings
# ---------------------------------------------------------------------------
TABLE_STYLES = {
    "header_row_height":   0.35,   # inches
    "data_row_height":     0.25,   # inches
    "border_weight":       0.5,    # pt
    "header_text_color":   "FFFFFF",
    "header_bg_color":     "1B438C",
    "even_row_bg":         "EBF0FA",
    "odd_row_bg":          "FFFFFF",
    "total_row_bg":        "D6E4F5",
}

# ---------------------------------------------------------------------------
# openpyxl helpers (hex strings WITHOUT leading #)
# ---------------------------------------------------------------------------
def xl_color(key: str) -> str:
    """Return Excel-ready hex color (no #) for a COLORS key."""
    return COLORS[key].lstrip("#")


# ---------------------------------------------------------------------------
# ReportLab helpers
# ---------------------------------------------------------------------------
def rl_hex(key: str):
    """Return a ReportLab HexColor for a COLORS key."""
    try:
        from reportlab.lib.colors import HexColor
        return HexColor(COLORS[key])
    except ImportError:
        return COLORS[key]


# ---------------------------------------------------------------------------
# Distress level display labels (pipeline table)
# ---------------------------------------------------------------------------
DISTRESS_DISPLAY = {
    "deep":       "Deep Distress",
    "severe":     "Severely Distressed",
    "lic":        "Low Income Community",
    "ineligible": "Non-LIC (Ineligible)",
    None:         "Not Assessed",
    "unknown":    "Not Assessed",
}

# ---------------------------------------------------------------------------
# SECTOR_NAICS WAS DELETED IN 1.2.0. It mapped the CDE's coarse sector label to
# a NAICS code this tool invented, and printed the result in a column headed
# "Sector (NAICS)" in the pipeline table the CDE files. It read:
#
#     "healthcare":         "621 – Ambulatory Health Care Services"
#     "small_business":     "722/336 – Food Services / Manufacturing"
#     "community_facility": "624 – Social Assistance / Community Facilities"
#     "mixed_use":          "531 – Real Estate (Mixed Use)"
#     "clean_energy":       "221 – Utilities (Renewable Energy)"
#     ...
#
# Every one of those is a fabricated classification, for four separate reasons:
#
#   1. THERE IS NO NAICS INPUT. `PipelineProject` has no naics field and
#      pipeline_template.csv has no naics column, so no CDE has ever supplied
#      one. The code was derived entirely from `sector`.
#   2. A SECTOR LABEL DOES NOT DETERMINE A NAICS CODE. "small_business" is a
#      SIZE classification, not an industry; mapping every small-business
#      project to "722/336" asserts that each is either a restaurant or a
#      transportation-equipment manufacturer. 336 is Transportation Equipment
#      Manufacturing specifically, not manufacturing at large (31-33).
#   3. THE PARENTHETICALS ARE INVENTED. NAICS 531 is "Real Estate", not "Real
#      Estate (Mixed Use)" or "Real Estate (Residential)"; 221 is "Utilities",
#      not "Utilities (Renewable Energy)"; 624 is "Social Assistance", not
#      "Social Assistance / Community Facilities". Two different sectors were
#      also mapped to the same code, 531, distinguished only by the invented
#      parenthetical.
#   4. IT DEGRADED SILENTLY. The call site was
#      `SECTOR_NAICS.get(p.sector, p.sector)`, so a CDE writing `sector: retail`
#      got the literal string "retail" printed under a column headed
#      "Sector (NAICS)".
#
# A NAICS code identifies the QALICB's industry to the CDFI Fund and follows the
# allocation into CIIS/AMIS compliance reporting. Filing an invented one is a
# wrong number about the CDE's own project. The column now renders the CDE's own
# sector label under an honest heading; if a NAICS code is required, it is the
# CDE's to supply, and this tool does not have it.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Section metadata
# ---------------------------------------------------------------------------
SECTION_META = {
    "A": {"title": "Business Strategy",      "max_words": 3000},
    "B": {"title": "Community Outcomes",     "max_words": 2500},
    "C": {"title": "Management Capacity",    "max_words": 2000},
    "D": {"title": "Capitalization Strategy","max_words": 1500},
    "E": {"title": "Prior Awards",           "max_words": 1000},
}

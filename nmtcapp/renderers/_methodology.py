"""The methodology appendix's text, composed ONCE from the constants it describes.

WHY THIS MODULE EXISTS

Through 1.2.0 the methodology appendix — the paragraph in which the document
states its own provenance — was three separate hand-typed copies, one each in
word_builder, pdf_builder and markdown_builder, and every figure in all three
was a LITERAL. ``NMTC_PROGRAM_CONSTRAINTS["standard_credit_price"]`` could move
to 0.95 and Word would go on printing "credit price $0.83/credit" underneath a
Section D table computed at 0.95, because the two had no connection but a
coincidence of typing.

Two consequences were live at 1.2.0 and both are fixed here:

  1. THE THREE COPIES DISAGREED. Word's readiness-weight disclosure named the
     components "eligibility 25%, distress concentration 25%, geographic
     diversity 15%..."; the PDF's named them "eligibility 25%, distress 25%,
     geographic 15%..."; markdown's omitted the weights altogether and said
     only that they were a house heuristic. Three descriptions of one weighting
     in one package.
  2. A CONSTANT PIN WOULD HAVE BEEN A LIE. tests/test_pinned_constants.py
     asserts that each published constant renders as a specific string. Against
     a literal, that pin passes over a mutated constant — it pins the typing,
     not the value. Every figure below is interpolated so the pin bites.

RULE FOR ANYONE EDITING THIS FILE: no figure may be typed. If a number belongs
in this text it comes from nmtcapp/data/, or it does not appear.
"""
from __future__ import annotations

from nmtcapp.data.schema import (
    IMPACT_BENCHMARKS,
    NMTC_PROGRAM_CONSTRAINTS,
    READINESS_SCORING_WEIGHTS,
)

# The eligibility dataset's vintage, stated once. Also imported by
# tables/distress_table for its per-row ACS Vintage column, so the appendix and
# the table cells cannot disagree about which ACS release classified the tracts.
ACS_VINTAGE = "2016–2020 ACS 5-Year Estimates"

# The CDFI Fund's own column letters for the two distress definitions, from the
# NOTES sheet of NMTC_LIC_Eligibility_2016_2020.xlsb, which reads:
#
#     Column O. Severe Distress | Severe distress=LIC AND (Poverty>30%; MFI<=60%;Unemployment>=1.5)
#     Column P. Deep Distress   | Deep distress=LIC AND (Poverty>40%; MFI<=40%;Unemployment>=2.5)
#
# 1.2.0 cited "columns 14 and 15". Those are the 0-based positional indices of
# the same two columns in the data sheet's header row — correct as array
# offsets, and not what the Fund calls them. A reader opening the workbook to
# check the quotation would look at columns N and O and find the unemployment
# ratio and severe distress. A citation-precision defect inside the text that
# round nine added to fix a citation defect; the docs page carried it too.
DISTRESS_COLUMN_LETTERS = "columns O and P"

_CREDIT_RATE = NMTC_PROGRAM_CONSTRAINTS["credit_rate"]
_CREDIT_PRICE = NMTC_PROGRAM_CONSTRAINTS["standard_credit_price"]
_CDE_FEE_RATE = NMTC_PROGRAM_CONSTRAINTS["cde_fee_rate_typical"]
_COMPLIANCE_YEARS = NMTC_PROGRAM_CONSTRAINTS["compliance_period_years"]


def distress_definitions() -> str:
    """The two tier definitions, quoted from the workbook this tool loads.

    Not interpolated from a constant, because the package HAS no constant for
    them: the thresholds live in the CDFI Fund's workbook and reach the code as
    a classification (``distress_level``), never as numbers. The string below is
    a quotation, and tests/pinned_constants.txt pins it against the workbook's
    own cells.

    NOT BYTE-IDENTICAL, AND IT NO LONGER SAYS IT IS. The workbook's NOTES sheet
    holds ``Severe distress=LIC AND (Poverty>30%; MFI<=60%;Unemployment>=1.5)``;
    this renders it with a space either side of the ``=`` and after the second
    semicolon — three insertions per line, six across both. Every threshold,
    operator and separator is the workbook's. The word in the rendered sentence
    was "verbatim" until FIX-4, which is a fidelity claim the text does not meet,
    inside the one paragraph whose whole job is fidelity.
    """
    return (
        "DISTRESS LEVELS (quoted from the CDFI Fund NMTC LIC Eligibility "
        f"workbook, {ACS_VINTAGE.replace(' 5-Year Estimates', '')}, "
        f"{DISTRESS_COLUMN_LETTERS} — the file this tool loads to classify "
        "every tract; the criteria are the workbook's own, with spacing "
        "normalised for legibility): Severe distress = LIC AND (Poverty>30%; "
        "MFI<=60%; Unemployment>=1.5). Deep distress = LIC AND (Poverty>40%; "
        "MFI<=40%; "
        "Unemployment>=2.5). The semicolons are ORs; both tiers additionally "
        "require the tract to be a Low-Income Community."
    )


def noaa_note() -> str:
    """The round-availability caveat that travels with the distress note."""
    return (
        "NMTC rounds are announced by a NOAA — Notice of Allocation "
        "Availability — and the CY 2026 NOAA is not yet published."
    )


def deal_economics_note() -> str:
    """Names the library and every parameter it was given.

    The credit RATE was absent from this note through 1.2.0. Section D printed
    "Total NMTCs Generated ($)" — 39% of QEI — with no statement anywhere in the
    document of where 39% comes from, while the credit price and the fee rate
    beside it both carried their disclaimers. It is the one figure in the deal
    economics block that IS statutory, and it was the only one unattributed.
    """
    return (
        "DEAL ECONOMICS: computed using the nmtc-calc library, standard "
        f"leveraged NMTC structure. Statutory credit rate {_CREDIT_RATE:.0%} of "
        f"QEI over {_COMPLIANCE_YEARS} years (IRC §45D(a)(2): 5% of the QEI on "
        "each of the first three credit allowance dates and 6% on each of the "
        f"remaining four). Assumed credit price ${_CREDIT_PRICE:.2f}/credit and "
        f"CDE fee {_CDE_FEE_RATE:.1%} of QEI are market assumptions of this "
        "model, not CDFI Fund parameters. The leverage loan is the residual of "
        "QEI less investor equity, so leverage plus equity equals QEI in every "
        "surface of this document."
    )


def impact_bands_note() -> str:
    """Declares the impact screening bands this tool's own."""
    low = IMPACT_BENCHMARKS["jobs_per_million_qei_low"]
    avg = IMPACT_BENCHMARKS["jobs_per_million_qei_avg"]
    high = IMPACT_BENCHMARKS["jobs_per_million_qei_high"]
    return (
        "IMPACT SCREENING BANDS: THIS TOOL'S OWN BANDS "
        f"({low:.0f} / {avg:.0f} / {high:.0f} FTE per $1MM QEI). The CDFI Fund "
        "publishes no jobs-per-QEI benchmark in any denominator: it reports job "
        "counts and dollar counts separately and never divides them, and it "
        "publishes no distribution, so no band here is a percentile. These are "
        "not a federal figure and must not be cited as one."
    )


def _weights_clause() -> str:
    """'eligibility 25%, distress concentration 25%, ...' from the weights dict."""
    labels = {
        "eligibility_quality": "eligibility",
        "distress_concentration": "distress concentration",
        "geographic_diversity": "geographic diversity",
        "impact_metrics": "impact metrics",
        "validation_pass_rate": "validation",
        "completeness": "completeness",
    }
    return ", ".join(
        f"{labels.get(key, key.replace('_', ' '))} {value:.0%}"
        for key, value in READINESS_SCORING_WEIGHTS.items()
    )


def readiness_weights_note() -> str:
    """Declares the readiness weighting unsourced, and lists it."""
    return (
        "READINESS SCORE: An UNSOURCED HOUSE HEURISTIC of this tool "
        f"({_weights_clause()}). The weights are this tool's own judgement; "
        "they are not calibrated against award data, the CDFI Fund publishes no "
        "such weighting, and the score does not predict an award outcome."
    )


def readiness_weights_sheet_note() -> str:
    """The same disclosure, sized for a spreadsheet cell.

    The Excel workbook rendered a READINESS SCORE BREAKDOWN table with a Weight
    column and NO disclosure of any kind — the only one of the four artifacts
    that showed the weighting without saying whose it was. It is also the
    artifact the Word and PDF documents cross-reference by name as the
    authoritative attachment.
    """
    labels = {
        "eligibility_quality": "eligibility quality",
        "distress_concentration": "distress concentration",
        "geographic_diversity": "geographic diversity",
        "impact_metrics": "impact metrics",
        "validation_pass_rate": "validation pass rate",
        "completeness": "completeness",
    }
    clause = "; ".join(
        f"{labels.get(key, key.replace('_', ' '))} {value:.0%}"
        for key, value in READINESS_SCORING_WEIGHTS.items()
    )
    return (
        "READINESS SCORE BREAKDOWN — weights are this tool's own unsourced "
        f"judgement ({clause}); the CDFI Fund publishes no such weighting and "
        "this score does not predict an award outcome."
    )

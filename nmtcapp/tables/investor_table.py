"""Section D investor commitments table."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from nmtcapp.core.application import Application

logger = logging.getLogger(__name__)

# Blank investor rows — a FORM for the CDE to complete, not a roster.
#
# Through 1.1.5 this list asserted two investors with a type, a CRA
# obligation of "Yes", a "Prospective" commitment status, a credit price, and
# the note "Primary CRA-motivated investor; term sheet pending" — while
# Section D's own narrative said, in the same document, that this tool
# "cannot attest to any relationship, to investor motivation, or to how many
# investors will participate". The dollar columns were computed off the CDE's
# real pipeline QEI, so they read as real commitments. "Term sheet pending" is
# a representation to a federal agency about financing that does not exist.
#
# Every cell the tool cannot substantiate is now a bracketed placeholder. Two
# rows are kept only so the form has the shape a reviewer expects; the row
# count is not a claim either, which is what INVESTOR_TABLE_NOTE says.
_TODO = "[CDE TO COMPLETE]"

_PLACEHOLDER_INVESTORS = [
    {
        "Investor Name": "[CDE TO COMPLETE: investor name]",
        "Investor Type": _TODO,
        "CRA Obligation": _TODO,
        "Commitment Amount ($)": _TODO,
        "Commitment Status": _TODO,
        "Credit Price ($/credit)": _TODO,
        "Notes": _TODO,
    },
    {
        "Investor Name": "[CDE TO COMPLETE: investor name]",
        "Investor Type": _TODO,
        "CRA Obligation": _TODO,
        "Commitment Amount ($)": _TODO,
        "Commitment Status": _TODO,
        "Credit Price ($/credit)": _TODO,
        "Notes": _TODO,
    },
]

# Rendered on every surface that shows this table, so the four output formats
# describe it identically. 1.1.5 titled the Excel sheet "(Scaffold)", gave the
# Word heading no qualifier at all, and had Markdown and PDF omit the table and
# print "(See Attachment: Investor Commitments Table)" — three behaviours
# across four surfaces for the same content.
INVESTOR_TABLE_TITLE = "Section D: Investor Commitments"

INVESTOR_TABLE_NOTE = (
    "[CDE TO COMPLETE: This table is a blank form. nmtc-application-builder "
    "holds no investor data for your CDE and supplies no figure in it — not a "
    "name, a type, a CRA obligation, a commitment amount, a credit price or a "
    "status, and not the number of rows. Add one row per investor you can "
    "name and defend to the CDFI Fund, and delete any row you cannot.]"
)


def build_investor_identification_table(application: "Application") -> pd.DataFrame:
    """Investor identification: name, type, CRA status, commitment status (4 cols).

    Example::

        df = build_investor_identification_table(application)
    """
    pipeline = application.pipeline
    if pipeline is None:
        return pd.DataFrame()
    rows = []
    for tmpl in _PLACEHOLDER_INVESTORS:
        rows.append({
            "Investor Name":      tmpl["Investor Name"],
            "Investor Type":      tmpl["Investor Type"],
            "CRA Obligation":     tmpl["CRA Obligation"],
            "Commitment Status":  tmpl["Commitment Status"],
        })
    return pd.DataFrame(rows)


def build_investor_commitment_table(application: "Application") -> pd.DataFrame:
    """Investor commitment amounts and pricing (5 cols).

    Example::

        df = build_investor_commitment_table(application)
    """
    pipeline = application.pipeline
    if pipeline is None:
        return pd.DataFrame()
    # No dollar column is derived from pipeline QEI here. A 70/30 split across
    # two invented investors at $0.83/credit produced figures that looked like
    # commitments because they were computed off the CDE's real numbers.
    rows = [
        {
            "Investor Name":           tmpl["Investor Name"],
            "Commitment Amount ($)":   tmpl["Commitment Amount ($)"],
            "NMTCs Allocated ($)":     _TODO,
            "Credit Price ($/credit)": tmpl["Credit Price ($/credit)"],
            "Notes":                   tmpl["Notes"],
        }
        for tmpl in _PLACEHOLDER_INVESTORS
    ]
    rows.append({
        "Investor Name":           "TOTALS",
        "Commitment Amount ($)":   _TODO,
        "NMTCs Allocated ($)":     _TODO,
        "Credit Price ($/credit)": "",
        "Notes":                   INVESTOR_TABLE_NOTE,
    })
    return pd.DataFrame(rows)


def build_investor_table(application: "Application") -> pd.DataFrame:
    """Build the Section D investor commitments form.

    Every cell is a bracketed placeholder. This tool holds no investor data
    and derives no commitment amount from pipeline QEI — see the module
    comment for what this used to assert.

    Example::

        df = build_investor_table(application)
    """
    pipeline = application.pipeline
    if pipeline is None:
        return pd.DataFrame()

    rows = []
    for tmpl in _PLACEHOLDER_INVESTORS:
        row = dict(tmpl)
        row["NMTCs Allocated ($)"] = _TODO
        rows.append(row)

    rows.append({
        "Investor Name": "TOTALS",
        "Investor Type": "",
        "CRA Obligation": "",
        "Commitment Amount ($)": _TODO,
        "NMTCs Allocated ($)": _TODO,
        "Commitment Status": "",
        "Credit Price ($/credit)": "",
        "Notes": INVESTOR_TABLE_NOTE,
    })

    return pd.DataFrame(rows)

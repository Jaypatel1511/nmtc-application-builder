"""Section D investor commitments table."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from nmtcapp.core.application import Application

logger = logging.getLogger(__name__)

# Placeholder investor roster — a real application would populate this from
# the CDE's investor pipeline. This scaffold shows the expected structure.
_PLACEHOLDER_INVESTORS = [
    {
        "Investor Name": "[Lead Bank Investor — TBD]",
        "Investor Type": "Commercial Bank (CRA)",
        "CRA Obligation": "Yes",
        "Commitment Amount ($)": None,  # populated from QEI split
        "Commitment Status": "Prospective",
        "Credit Price ($/credit)": 0.83,
        "Notes": "Primary CRA-motivated investor; term sheet pending",
    },
    {
        "Investor Name": "[Insurance Company Investor — TBD]",
        "Investor Type": "Insurance Company",
        "CRA Obligation": "No",
        "Commitment Amount ($)": None,
        "Commitment Status": "Prospective",
        "Credit Price ($/credit)": 0.82,
        "Notes": "Non-CRA motivated; relationship investor",
    },
]


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
    total_qei = sum(p.qei_request for p in pipeline)
    total_nmtcs = total_qei * 0.39
    total_equity = total_nmtcs * 0.83
    splits = [0.70, 0.30]
    rows = []
    for i, tmpl in enumerate(_PLACEHOLDER_INVESTORS):
        rows.append({
            "Investor Name":          tmpl["Investor Name"],
            "Commitment Amount ($)":  round(total_equity * splits[i]),
            "NMTCs Allocated ($)":    round(total_nmtcs * splits[i]),
            "Credit Price ($/credit)": tmpl["Credit Price ($/credit)"],
            "Notes":                  tmpl["Notes"],
        })
    rows.append({
        "Investor Name":         "TOTALS",
        "Commitment Amount ($)": round(total_equity),
        "NMTCs Allocated ($)":   round(total_nmtcs),
        "Credit Price ($/credit)": "",
        "Notes":                 f"Based on ${total_qei:,.0f} QEI at $0.83/credit",
    })
    return pd.DataFrame(rows)


def build_investor_table(application: "Application") -> pd.DataFrame:
    """Build the Section D investor commitments table.

    Provides a scaffold for the CDE's investor lineup with estimated
    commitment amounts based on total QEI requested.

    Example::

        df = build_investor_table(application)
    """
    pipeline = application.pipeline
    if pipeline is None:
        return pd.DataFrame()

    total_qei = sum(p.qei_request for p in pipeline)
    total_nmtcs = total_qei * 0.39
    total_equity = total_nmtcs * 0.83

    # Estimate split: 70% lead bank, 30% second investor
    rows = []
    splits = [0.70, 0.30]
    for i, tmpl in enumerate(_PLACEHOLDER_INVESTORS):
        row = dict(tmpl)
        row["Commitment Amount ($)"] = round(total_equity * splits[i])
        row["NMTCs Allocated ($)"] = round(total_nmtcs * splits[i])
        rows.append(row)

    # Totals row
    rows.append({
        "Investor Name": "TOTALS",
        "Investor Type": "",
        "CRA Obligation": "",
        "Commitment Amount ($)": round(total_equity),
        "NMTCs Allocated ($)": round(total_nmtcs),
        "Commitment Status": "",
        "Credit Price ($/credit)": "",
        "Notes": f"Based on ${total_qei:,.0f} total QEI at $0.83/credit",
    })

    return pd.DataFrame(rows)

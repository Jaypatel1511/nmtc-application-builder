"""Section D: Capitalization Strategy generator."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.data.schema import NMTC_PROGRAM_CONSTRAINTS
from nmtcapp.sections.base import SectionGenerator, _cde_todo, _placeholder

if TYPE_CHECKING:
    from nmtcapp.core.application import Application, ApplicationAnalysis

logger = logging.getLogger(__name__)


class SectionDCapitalizationStrategy(SectionGenerator):
    """Generates Section D: Capitalization Strategy content.

    Pulls from pipeline economics (QEI/NMTC/equity) and CRA investor analysis.

    Example::

        gen = SectionDCapitalizationStrategy()
        content = gen.generate_content(application, analysis)
    """
    section_id = "D"
    title = "Capitalization Strategy"
    word_limit = 1500

    def generate_content(self, application: "Application", analysis: "ApplicationAnalysis") -> dict:
        econ = analysis.deal_economics
        # econ["total_qei"] is the PIPELINE total, which is not the amount the
        # CDE requested. Rendering it in a row labelled "Requested" put a
        # different number in Section D than on the cover page of the same
        # document. The two are now separate, differently-labelled rows.
        requested = application.requested_allocation
        total_qei = econ.get("total_qei", requested)

        # Market assumptions, sourced from the single constant rather than
        # duplicated as display strings. These are this tool's modelling
        # defaults for a standard leveraged structure — the CDFI Fund does
        # not set a credit price or a CDE fee rate.
        credit_price = NMTC_PROGRAM_CONSTRAINTS["standard_credit_price"]
        cde_fee_rate = NMTC_PROGRAM_CONSTRAINTS["cde_fee_rate_typical"]
        compliance_years = NMTC_PROGRAM_CONSTRAINTS["compliance_period_years"]
        total_nmtcs = econ.get(
            "total_nmtcs", total_qei * NMTC_PROGRAM_CONSTRAINTS["credit_rate"]
        )
        investor_equity = econ.get("total_investor_equity", total_nmtcs * credit_price)
        cde_fees = econ.get("total_cde_fees", total_qei * cde_fee_rate)
        net_subsidy = econ.get("total_net_subsidy", total_qei - cde_fees)
        leverage = econ.get(
            "total_leverage_loans",
            total_qei * NMTC_PROGRAM_CONSTRAINTS["leverage_ratio_typical"],
        )

        economics_summary = {
            "Allocation Requested ($)":       f"${requested:,.0f}",
            "Total Pipeline QEI ($)":         f"${total_qei:,.0f}",
            "Total NMTCs Generated ($)":      f"${total_nmtcs:,.0f}",
            "Estimated Investor Equity ($)":  f"${investor_equity:,.0f}",
            "Assumed Credit Price ($/NMTC)":
                f"${credit_price:.2f} (market assumption, not a CDFI Fund parameter)",
            "Total Leverage Loans ($)":       f"${leverage:,.0f}",
            "CDE Fee Income ($)":             f"${cde_fees:,.0f}",
            "Assumed CDE Fee Rate":
                f"{cde_fee_rate:.1%} of QEI (market assumption, not a CDFI Fund parameter)",
            "Net Subsidy to QALICBs ($)":     f"${net_subsidy:,.0f}",
            "Compliance Period":              f"{compliance_years} years (IRC §45D)",
        }

        investor_narrative = (
            _cde_todo(
                "Describe your actual investor relationships and their current "
                "status — named institutions where you have them, whether each "
                "is a term sheet, a letter of intent, a prior-round investor or "
                "a prospect, and who is expected to lead. This tool has no "
                "investor data for your CDE and cannot attest to any "
                "relationship, to investor motivation, or to how many investors "
                "will participate."
            ) + "\n\n"
            f"Modelled on ${total_qei/1e6:.1f}MM of pipeline QEI at an assumed credit "
            f"price of ${credit_price:.2f}/NMTC credit, the structure implies "
            f"${investor_equity/1e6:.1f}MM of investor equity. The credit price is a "
            f"market assumption of this model, not a quoted or committed price.\n\n"
            f"Pipeline footprint: "
            f"{len(list({p.state for p in application.pipeline}))} states.\n\n"
        ) + _placeholder(self.section_id, 400)

        leverage_narrative = (
            f"Each transaction will utilize a standard leveraged NMTC structure:\n\n"
            f"  1. Leverage Lender provides senior debt (approx. ${leverage/1e6:.1f}MM total)\n"
            f"  2. Tax Credit Investor contributes equity (${investor_equity/1e6:.1f}MM)\n"
            f"  3. Combined proceeds flow through CDE as QLICI loans at below-market rates\n"
            f"  4. Net subsidy to QALICBs: ${net_subsidy/1e6:.1f}MM in below-market capital\n\n"
            f"Assumed CDE fee rate: {cde_fee_rate:.1%} of QEI (${cde_fees/1e6:.1f}MM) — a market "
            f"assumption of this model, not a CDFI Fund parameter. "
            f"Fees cover origination, compliance monitoring, and asset management over the "
            f"{compliance_years}-year compliance period.\n\n"
        ) + _placeholder(self.section_id, 200)

        return {
            "section_id": self.section_id,
            "title": self.title,
            "subsections": [
                {"heading": "Deal Economics Summary",
                 "body": economics_summary, "type": "table_ref"},
                {"heading": "Investor Strategy and Relationships",
                 "body": investor_narrative, "type": "narrative"},
                {"heading": "Leverage Structure",
                 "body": leverage_narrative, "type": "narrative"},
                {"heading": "Investor Commitments",
                 "body": "(See Attachment: Investor Commitments Table)", "type": "table_ref"},
                {"heading": "Leverage Loan Sources",
                 "body": _placeholder(self.section_id, 200), "type": "narrative"},
            ],
        }

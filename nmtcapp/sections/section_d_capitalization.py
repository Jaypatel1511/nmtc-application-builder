"""Section D: Capitalization Strategy generator."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.sections.base import SectionGenerator, _placeholder

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
        total_qei = econ.get("total_qei", application.requested_allocation)
        total_nmtcs = econ.get("total_nmtcs", total_qei * 0.39)
        investor_equity = econ.get("total_investor_equity", total_nmtcs * 0.83)
        cde_fees = econ.get("total_cde_fees", total_qei * 0.025)
        net_subsidy = econ.get("total_net_subsidy", total_qei - cde_fees)
        leverage = econ.get("total_leverage_loans", total_qei * 0.80)

        economics_summary = {
            "Total QEI Requested ($)":        f"${total_qei:,.0f}",
            "Total NMTCs Generated ($)":      f"${total_nmtcs:,.0f}",
            "Estimated Investor Equity ($)":  f"${investor_equity:,.0f}",
            "Assumed Credit Price ($/NMTC)":  "$0.83",
            "Total Leverage Loans ($)":       f"${leverage:,.0f}",
            "CDE Fee Income ($)":             f"${cde_fees:,.0f}",
            "Net Subsidy to QALICBs ($)":     f"${net_subsidy:,.0f}",
            "Compliance Period":              "7 years (standard)",
        }

        investor_narrative = (
            f"{application.cde.name} has established relationships with CRA-motivated bank "
            f"investors in our primary markets. Based on ${total_qei/1e6:.1f}MM of requested QEI "
            f"at a standard credit price of $0.83/NMTC credit, we anticipate raising "
            f"${investor_equity/1e6:.1f}MM in investor equity from one or two lead investors.\n\n"
            f"Primary investor profile: CRA-rated commercial banks with Community Development "
            f"obligations in {len(list({p.state for p in application.pipeline}))} target states.\n\n"
        ) + _placeholder(self.section_id, 400)

        leverage_narrative = (
            f"Each transaction will utilize a standard leveraged NMTC structure:\n\n"
            f"  1. Leverage Lender provides senior debt (approx. ${leverage/1e6:.1f}MM total)\n"
            f"  2. Tax Credit Investor contributes equity (${investor_equity/1e6:.1f}MM)\n"
            f"  3. Combined proceeds flow through CDE as QLICI loans at below-market rates\n"
            f"  4. Net subsidy to QALICBs: ${net_subsidy/1e6:.1f}MM in below-market capital\n\n"
            f"CDE fee rate: 2.5% of QEI (${cde_fees/1e6:.1f}MM). "
            f"Fees cover origination, compliance monitoring, and asset management over the 7-year period.\n\n"
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

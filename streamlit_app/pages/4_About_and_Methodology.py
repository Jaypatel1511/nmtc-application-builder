"""About & Methodology — documentation, data sources, and limitations."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import streamlit as st

from nmtcapp.data.historical_awards import NMTC_AWARD_ROUNDS, APPLICATION_VOLUME_TRENDS
from nmtcapp.data.benchmark_thresholds import (
    HIGHLY_QUALIFIED_AGGREGATE_MIN, HIGHLY_QUALIFIED_SECTION_MIN,
    TOP_TIER_AGGREGATE_MIN, TOP_TIER_SECTION_MIN,
    SEVERE_DISTRESS_MIN_PCT, DEEP_DISTRESS_MIN_PCT,
    DBC_PRIORITY_YEARS_MIN, DBC_VOLUME_PCT_MIN, UNRELATED_ENTITIES_MIN_PCT,
    TOTAL_APPLICANTS_CY2024_25, TOTAL_REQUEST_CY2024_25_B, TOTAL_AVAILABLE_CY2024_25_B,
)
from utils import apply_theme

apply_theme()
st.title("📖 About & Methodology")
st.markdown(
    "Documentation for NMTC Application Builder — source documents, scoring framework, "
    "gating logic, and known limitations."
)
st.markdown("---")

# ---------------------------------------------------------------------------
# What this tool is / is not
# ---------------------------------------------------------------------------
st.markdown(
    """
## What this tool IS — and IS NOT

**NMTC Application Builder** is an open-source Python library and Streamlit demo
that helps Community Development Entities (CDEs) self-assess their NMTC applications
against the CDFI Fund's **published** CY 2024-2025 Review Process criteria.

### This tool IS:
- A self-assessment framework aligned to the **CDFI Fund's published CY 2024-2025
  scoring structure** (Business Strategy + Community Outcomes + Priority Points)
- A diagnostic tool to identify scoring gaps before submission
- A calculator for the published gating thresholds (85/100 aggregate, 40/50 per section)

### This tool IS NOT:
- A win probability calculator (the CDFI Fund does not publish non-winner data,
  so a true probability of selection cannot be computed)
- A substitute for Phase 2 narrative review (Management Capacity and Capitalization
  Strategy are evaluated through qualitative reviewer judgment)
- An authoritative replication of the CDFI Fund's proprietary scoring rubric
  (sub-score weights within sections are best-effort interpretations)
"""
)

st.info(
    "**Source document:** "
    "[CY 2024-2025 NMTC Allocation Application Review Process]"
    "(https://www.cdfifund.gov/system/files/2025-12/CY_2024_25_NMTC_Program_Review_Process.pdf)"
    " — U.S. Department of the Treasury, CDFI Fund"
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Scoring framework overview
# ---------------------------------------------------------------------------
st.markdown("## Scoring Framework (CY 2024-2025)")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Business Strategy", "50 pts", "Section 1")
with col2:
    st.metric("Community Outcomes", "50 pts", "Section 2")
with col3:
    st.metric("Priority Points", "10 pts", "Bonus")

st.markdown("---")

# Business Strategy
st.markdown(
    """
### Section 1 — Business Strategy (50 base points)

| Sub-criterion | Max | Key threshold |
|---|---|---|
| **Product Flexibility** | 10 | ≥ 50% below-market rate OR ≥ 5 indicia of flexible terms |
| **Pipeline Credibility** | 15 | Pipeline projects identified, sized, and timed credibly |
| **Track Record Strength** | 15 | 5-year direct financing record; bonus for own capital at risk |
| **Track Record Alignment** | 10 | ≥ 70% pipeline supported by similar prior activity; ≥ 90% deployment rate |

> **Sub-score disclosure:** Weights within Business Strategy (e.g., Product Flexibility 10 pts)
> are this tool's interpretation of the Review Process document. The CDFI Fund does not
> publish exact point values for individual sub-criteria.
"""
)

# Community Outcomes
st.markdown(
    f"""
### Section 2 — Community Outcomes (50 base points)

| Sub-criterion | Max | Key threshold |
|---|---|---|
| **Higher Distress Targeting** | 15 | ≥ {SEVERE_DISTRESS_MIN_PCT:.0%} of QEI in severe distress or multi-indicia distress |
| **Deep Distress Commitment** | 10 | ≥ {DEEP_DISTRESS_MIN_PCT:.0%} of QEI in Deep Distress areas |
| **Special Targeting** | 5 | QEI in U.S. Territories, High Migration Rural, NMTC Native Areas, Persistent Poverty Counties |
| **Community Outcomes Quality** | 10 | Quantified outcomes (jobs, units, sq ft) with third-party methodology |
| **Community Accountability** | 10 | LIC board representation + community engagement track record |
"""
)

# Priority Points
st.markdown(
    f"""
### Priority Points (10 bonus points)

Priority Points increase an application's ranking within the Highly Qualified pool
but do not affect gating.

| Criterion | Max | Key threshold |
|---|---|---|
| **DBC Track Record** | 5 | ≥ {DBC_PRIORITY_YEARS_MIN} years AND ≥ {DBC_VOLUME_PCT_MIN:.0%} of financing volume to Disadvantaged Businesses/Communities |
| **Unrelated Entities Commitment** | 5 | ≥ {UNRELATED_ENTITIES_MIN_PCT:.0%} of QEIs to unrelated entities |
"""
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Gating logic
# ---------------------------------------------------------------------------
st.markdown("## Highly Qualified Gating Logic")

st.markdown(
    f"""
The CDFI Fund uses a **two-stage gating process** to form the Highly Qualified pool
that advances to Phase 2 review.

| Tier | Aggregate Base Score | Section Minimums | Outcome |
|---|---|---|---|
| **Not Qualified** | < {HIGHLY_QUALIFIED_AGGREGATE_MIN} | Either section < {HIGHLY_QUALIFIED_SECTION_MIN} | Does not advance to Phase 2 |
| **Highly Qualified** | {HIGHLY_QUALIFIED_AGGREGATE_MIN}–{TOP_TIER_AGGREGATE_MIN - 1} | Both sections ≥ {HIGHLY_QUALIFIED_SECTION_MIN} | Phase 2 reviewed; award depends on ranking |
| **Top Tier** | {TOP_TIER_AGGREGATE_MIN}–100 | Both sections ≥ {TOP_TIER_SECTION_MIN} | High probability of award at or near maximum requested |

**Critical rule:** An application that scores below {HIGHLY_QUALIFIED_SECTION_MIN} points in
*either* section does not advance to Phase 2, regardless of aggregate score.
"""
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Phase 2 considerations
# ---------------------------------------------------------------------------
st.markdown(
    """
## Phase 2 Considerations (Not Scored by This Tool)

Phase 2 evaluates qualitative factors through CDFI Fund staff review.
This tool reports these as informational flags (`phase2_flags`) but does not score them.

| Factor | What Reviewers Look For |
|---|---|
| **Management Capacity** | Staffing, systems, organizational capability to deploy capital |
| **Capitalization Strategy** | QEI-raising track record; investor relationships; feasibility |
| **Non-Metro Commitment** | ≥ 20% non-metro required; ≥ 50% for Rural CDE designation |
| **Fee / Compensation Structure** | Fee levels favorable to QALICBs |
| **Prior Reporting Compliance** | Late or inaccurate prior-round reports → potential point deductions |
"""
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Historical round statistics
# ---------------------------------------------------------------------------
st.markdown("## Historical NMTC Round Statistics")
st.markdown(
    "Source: CDFI Fund NMTC Award Announcements (public disclosures)."
)

rows = []
for round_name, data in NMTC_AWARD_ROUNDS.items():
    rows.append({
        "Round": round_name,
        "Applications": data["applications"],
        "Awards": data["awards"],
        "Total Allocated ($B)": f"${data['total_allocated'] / 1e9:.1f}B",
        "Avg Award ($M)": f"${data['avg_award'] / 1e6:.1f}M",
        "Acceptance Rate": f"{data['acceptance_rate']:.1%}",
        "Announced": data["announcement_year"],
    })

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
st.markdown(f"> **Trend note:** {APPLICATION_VOLUME_TRENDS['trend_note']}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Limitations
# ---------------------------------------------------------------------------
st.markdown(
    """
## Known Limitations

### 1. Phase 2 not modeled
Phase 2 evaluates Management Capacity and Capitalization Strategy through narrative
review. These are the subjective factors that distinguish applicants within the
Highly Qualified pool. This tool does not score Phase 2.

### 2. Sub-score weights are interpretive
The CDFI Fund publishes section totals (50 pts each) and criterion descriptions,
but does not publish exact point values for individual sub-criteria. This tool's
sub-point allocations (e.g., Product Flexibility 10 pts) are best-effort
interpretations.

### 3. Non-winner data is not available
The CDFI Fund publishes only winner-level data. Application data for non-winning
applicants is not publicly disclosed. The `HistoricalBenchmarks` module uses
winner patterns only.

### 4. Past reporting compliance not modeled
Prior-round reporting issues can result in score deductions. This tool assumes
a clean compliance record unless explicitly flagged in `cde_attributes`.

### 5. Pipeline data quality matters
Scores are only as good as the data provided. Inaccurate distress classifications,
job estimates, or sector assignments will produce misleading results.

### 6. Sample data is illustrative only
The sample pipeline (20 projects, Riverbend Community Capital CDE) is fictional.
Do not use sample output to benchmark a real application.
"""
)

# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("## Links & Resources")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        **Project**
        - [GitHub repository](https://github.com/Jaypatel1511/nmtc-application-builder)
        - [PyPI package](https://pypi.org/project/nmtc-application-builder/)
        - MIT License
        """
    )

with col2:
    st.markdown(
        """
        **CDFI Fund resources**
        - [NMTC Program](https://www.cdfifund.gov/programs-training/programs/new-markets-tax-credit)
        - [CY 2024-2025 Review Process (PDF)](https://www.cdfifund.gov/system/files/2025-12/CY_2024_25_NMTC_Program_Review_Process.pdf)
        - [NMTC Mapping Tool](https://www.cdfifund.gov/programs-training/programs/nmtc/nmtc-mapping-tool)
        """
    )

with col3:
    st.markdown(
        """
        **Getting help**
        - Open an issue on GitHub for bugs or feature requests
        - Pull requests welcome
        - Python 3.9+, MIT License
        """
    )

st.markdown("---")
st.caption(
    "NMTC Application Builder is an independent open-source tool and is not affiliated "
    "with or endorsed by the CDFI Fund or any government agency."
)

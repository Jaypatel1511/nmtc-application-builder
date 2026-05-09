"""About & Methodology — documentation, data sources, and limitations."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pandas as pd
import streamlit as st

from nmtcapp.data.historical_awards import NMTC_AWARD_ROUNDS, APPLICATION_VOLUME_TRENDS

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.title("📖 About & Methodology")
st.markdown(
    "Documentation for the NMTC Application Builder — data sources, scoring methodology, "
    "known limitations, and historical program statistics."
)
st.markdown("---")

# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
st.markdown(
    """
## Overview

**NMTC Application Builder** is an open-source Python library and Streamlit demo
that helps Community Development Entities (CDEs) analyze, score, and optimize their
New Markets Tax Credit (NMTC) applications before submission to the CDFI Fund.

The library provides:

- **Pipeline analysis** — distress concentration, geographic diversity, sector mix,
  and impact projections derived from a CDE's project pipeline.
- **Win alignment scoring** — a composite score (0–100) measuring how closely an
  application matches patterns observed in historical NMTC award winners.
- **Pipeline optimization** — greedy construction + swap-based local search to
  select the highest-scoring project subset given budget and diversity constraints.
- **Document generation** — full NMTC application package in Markdown, Word,
  Excel, and PDF formats (not shown in this demo).

### What this tool is — and is not

This tool provides **analytical assistance**, not predictions. NMTC allocation
decisions involve subjective reviewer judgement, relationship factors, and policy
priorities that no quantitative model can fully capture.

"""
)

# ---------------------------------------------------------------------------
# The 5 dimensions
# ---------------------------------------------------------------------------
st.markdown(
    """
## The Five Scoring Dimensions

The win alignment score is a weighted composite of five dimensions, each scored 0–100:

| Dimension | Weight | What it measures |
|---|---|---|
| **Distress Concentration** | 35% | Percentage of QEI in deep- or severely-distressed census tracts |
| **Impact Intensity** | 25% | Jobs created per $1MM QEI vs. historical winner distribution |
| **Geographic Diversity** | 20% | Number of states, geographic HHI, and rural share |
| **Sector Diversity** | 15% | Number of sectors represented and concentration risk |
| **Pipeline Quality** | 5% | NMTC eligibility rate, project count, and award size fit |

**Competitive threshold:** 55 points (composite). Applications scoring 55+ are broadly
aligned with historical winners on the measured dimensions. **Strong alignment:** 75+.

### Distress scoring detail

Distress concentration is the most heavily weighted dimension (35%) because NOFA scoring
criteria place the greatest emphasis on community need. The scorer benchmarks against the
winner distribution:

- Winner p25: **72%** deep/severe
- Winner median: **82%** deep/severe
- Winner p75: **91%** deep/severe

Pipelines below the 50% floor (rarely funded) score near 0 on this dimension.

### Geographic scoring detail

Geographic diversity is scored on three sub-factors:
1. **State count** — normalized against the winner distribution (mean 7.2 states, std 3.8)
2. **HHI (Herfindahl-Hirschman Index)** — lower HHI = more evenly distributed pipeline
3. **Rural bonus** — pipelines near or above the winner rural mean (18%) receive a bonus

### Impact scoring detail

Impact intensity uses jobs-per-$1MM-QEI as the primary metric:
- Winner p25: **6 jobs/$MM**
- Winner median: **10 jobs/$MM**
- Winner p75: **18 jobs/$MM**
- Winner top 10%: **28 jobs/$MM**

Operating business projects (manufacturing, healthcare, small business) typically
generate more jobs per dollar than pure real-estate plays.

"""
)

# ---------------------------------------------------------------------------
# Historical winner data
# ---------------------------------------------------------------------------
st.markdown("## Historical NMTC Round Statistics")
st.markdown(
    "Source: CDFI Fund NMTC Award Announcements (public disclosures). "
    "CY2024 figures are estimates based on prior-round trends."
)

rows = []
for round_name, data in NMTC_AWARD_ROUNDS.items():
    rows.append(
        {
            "Round": round_name,
            "Applications": data["applications"],
            "Awards": data["awards"],
            "Total Allocated ($B)": f"${data['total_allocated'] / 1e9:.1f}B",
            "Avg Award ($M)": f"${data['avg_award'] / 1e6:.1f}M",
            "Median Award ($M)": f"${data['median_award'] / 1e6:.1f}M",
            "Acceptance Rate": f"{data['acceptance_rate']:.1%}",
            "Announced": data["announcement_year"],
        }
    )

hist_df = pd.DataFrame(rows)
st.dataframe(hist_df, use_container_width=True, hide_index=True)

st.markdown(
    f"> **Trend note:** {APPLICATION_VOLUME_TRENDS['trend_note']}"
)

# ---------------------------------------------------------------------------
# Limitations
# ---------------------------------------------------------------------------
st.markdown(
    """
## Known Limitations

### 1. Non-winner data is not available

The CDFI Fund publishes only winner-level data. Application microdata for
non-winning applicants is not publicly disclosed. This means the scoring model
is trained only on winners — it cannot identify what distinguishes winners from
near-misses on application quality dimensions. All benchmarks are derived from
winner characteristics, not from a winner-vs-loser comparison.

**Implication:** A high alignment score means your application looks like a
historical winner. It does not mean you will win.

### 2. Subjective reviewer factors are not modelled

NMTC allocation involves human review of narrative sections, CDE track record,
organizational capacity, and policy alignment that cannot be quantified from
pipeline data alone. The scores in this tool cover only the quantitative pipeline
dimensions.

### 3. NOFA criteria change year to year

The scoring weights in this tool are derived from historical NOFA guidance and
award patterns (CY2020–CY2024). The CDFI Fund publishes a new NOFA for each
round — always verify current criteria before submission.

### 4. Pipeline data quality matters

The analysis is only as good as the pipeline data you provide. Projects with
missing or inaccurate distress classifications, job estimates, or sector
assignments will produce misleading scores.

### 5. Sample data is illustrative only

The sample pipeline (20 projects, Heartland Impact CDE) is fictional. All
distress levels, census tracts, and job estimates are illustrative. Do not use
sample output to benchmark a real application.

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
        - [NMTC Mapping Tool](https://www.cdfifund.gov/programs-training/programs/nmtc/nmtc-mapping-tool)
        - [Annual Reports](https://www.cdfifund.gov/research/reports)
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

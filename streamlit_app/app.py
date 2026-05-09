"""NMTC Application Builder — Streamlit demo entry point."""
import streamlit as st

st.set_page_config(
    page_title="NMTC Application Builder",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Header */
    .nmtc-header {
        background: linear-gradient(135deg, #1B438C 0%, #0d2757 100%);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    .nmtc-header h1 {
        margin: 0;
        font-size: 2.4rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .nmtc-header p {
        margin: 0.4rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.85;
    }

    /* Metric font sizing */
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #1B438C !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #6C757D !important;
        font-weight: 500 !important;
    }

    /* Feature cards */
    .feature-card {
        background: #f8f9fc;
        border: 1px solid #dde3f0;
        border-left: 4px solid #1B438C;
        border-radius: 8px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        height: 100%;
    }
    .feature-card h3 {
        color: #1B438C;
        margin: 0 0 0.5rem 0;
        font-size: 1.05rem;
        font-weight: 600;
    }
    .feature-card p {
        color: #495057;
        margin: 0;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .feature-card .icon {
        font-size: 1.6rem;
        margin-bottom: 0.4rem;
    }

    /* Quick stats bar */
    .stats-bar {
        background: #F0A500;
        color: white;
        padding: 0.6rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        text-align: center;
        letter-spacing: 0.03em;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #f0f4fb;
    }

    /* Competitive tier badge */
    .tier-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.06em;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="nmtc-header">
        <h1>🏗️ NMTC Application Builder</h1>
        <p>Intelligence-powered analysis, scoring, and optimization for CDFI Fund NMTC applications</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Quick stats bar
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="stats-bar">'
    "📊 Trained on CY2020–2024 winner data &nbsp;|&nbsp; "
    "✅ 500+ tests &nbsp;|&nbsp; "
    "🔓 MIT License"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Feature cards
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

cards = [
    (
        col1,
        "📋",
        "Pipeline Analyzer",
        "Upload your CSV or use sample data to run a full pipeline intelligence report — "
        "distress concentration, geographic diversity, sector mix, and impact projections.",
    ),
    (
        col2,
        "🎯",
        "Win Alignment Scorer",
        "Score your application's alignment with patterns in historical NMTC winners across "
        "five dimensions: distress, geographic, impact, sector, and pipeline quality.",
    ),
    (
        col3,
        "⚙️",
        "Pipeline Optimizer",
        "Automatically select the highest-scoring project subset given your QEI budget, "
        "state diversity, and sector constraints using greedy + local-search optimization.",
    ),
    (
        col4,
        "📖",
        "Methodology",
        "Full documentation of data sources, scoring methodology, limitations, and "
        "historical NMTC round statistics. Required reading before relying on scores.",
    ),
]

for col, icon, title, desc in cards:
    with col:
        st.markdown(
            f"""
            <div class="feature-card">
                <div class="icon">{icon}</div>
                <h3>{title}</h3>
                <p>{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Navigation instructions
# ---------------------------------------------------------------------------
st.markdown("---")

left, right = st.columns([2, 1])

with left:
    st.subheader("Getting started")
    st.markdown(
        """
        Use the **sidebar** on the left to navigate between pages:

        1. **Pipeline Analyzer** — start here. Load sample data or upload your own
           pipeline CSV to see a full analysis report.
        2. **Win Alignment Scorer** — after analyzing, score your application against
           historical winner patterns.
        3. **Pipeline Optimizer** — set budget and diversity constraints, then let the
           optimizer select the highest-scoring project subset.
        4. **About & Methodology** — review data sources, limitations, and historical
           round statistics before drawing conclusions.

        > **Tip:** All pages share the same pipeline session. Running the analyzer
        > first populates the session for subsequent pages.
        """
    )

with right:
    st.subheader("Sample CDE profile")
    st.markdown(
        """
        The demo uses **Heartland Impact CDE, LLC** — a realistic sample profile
        with three prior NMTC award rounds and a 20-project pipeline spanning
        12 states across healthcare, education, affordable housing, and small
        business sectors.

        No external API calls are needed — all sample data is pre-enriched with
        NMTC eligibility and distress classification.
        """
    )
    st.info(
        "**Requested allocation:** $65,000,000 | **Round:** CY2025"
    )

# ---------------------------------------------------------------------------
# Methodology disclosure
# ---------------------------------------------------------------------------
st.markdown("---")
st.info(
    "⚠️ **Methodology Disclosure:** Alignment scores measure similarity to patterns "
    "observed in historical NMTC award winners (CY2020–CY2024). They are **not** "
    "win probabilities. The CDFI Fund does not publish non-winner application data, "
    "so a true probability of selection cannot be computed. Scores are intended to "
    "guide pipeline improvement, not predict award outcomes."
)

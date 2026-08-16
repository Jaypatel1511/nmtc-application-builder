"""Shared helpers for the NMTC Application Builder Streamlit demo."""
from __future__ import annotations

import sys
import os

# Ensure project root is on the path so nmtcapp imports work from any working directory.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import streamlit as st

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline

# ---------------------------------------------------------------------------
# Brand colours
# ---------------------------------------------------------------------------
PRIMARY = "#1B438C"
ACCENT = "#F0A500"
SUCCESS = "#28A745"
WARNING = "#FFC107"
DANGER = "#DC3545"
MUTED = "#6C757D"

# ---------------------------------------------------------------------------
# Tier badge colours
# ---------------------------------------------------------------------------
TIER_COLORS = {
    "strong": SUCCESS,
    "competitive": PRIMARY,
    "marginal": WARNING,
    "weak": DANGER,
}

# ---------------------------------------------------------------------------
# Valid sectors — NOW ACTUALLY FROM SCHEMA (FIX-2 G-5 sweep)
#
# The comment above this list said "(from schema)" and the list was hand-typed.
# It happened to agree. A sector added to nmtcapp.data.schema.TARGET_SECTORS
# would not have appeared here, so the Streamlit uploader would have rejected
# a sector the package itself recognises, with a message naming a vocabulary
# nothing else in the repo holds.
# ---------------------------------------------------------------------------
from nmtcapp.data.schema import VALID_SECTORS  # noqa: F401  (re-exported)


# Identity keys parsed off an uploaded "CDE Profile" sheet. These describe WHO
# the CDE is; they must never reach a CDEProfile built for someone else's
# upload, and none of them feeds a score.
_IDENTITY_KEYS = frozenset({
    "cde_name", "cde_id", "ein", "headquarters_state", "certification_date",
    "mission", "website", "organization_type", "target_markets",
    "requested_allocation_millions", "application_round",
})


def _scoring_attrs_only(cde_extra: dict, is_demo: bool) -> dict:
    """Strip identity keys and blanks from a parsed CDE Profile sheet.

    Refuses outright if the sheet carries the shipped sample CDE's identity —
    an unedited template upload — because everything else on that sheet is
    then the sample's too. Demo mode is exempt: it is running the sample on
    purpose and labels every screen as fictional.

    Example::

        _scoring_attrs_only({"cde_name": "X", "dbc_focus_years": 4}, False)
        # -> {"dbc_focus_years": 4}
    """
    if not is_demo:
        from nmtcapp.core.sample_identity import assert_not_sample_identity
        assert_not_sample_identity(
            name=cde_extra.get("cde_name"),
            cde_id=cde_extra.get("cde_id"),
            ein=cde_extra.get("ein"),
            source="the uploaded CDE Profile sheet",
        )
    return {
        k: v for k, v in cde_extra.items()
        if k not in _IDENTITY_KEYS and v not in ("", [], {}, None)
    }


def get_or_create_app(
    pipeline: Pipeline | None = None,
    is_demo: bool | None = None,
    cde_extra: dict | None = None,
) -> Application:
    """Return the shared Application object from session_state, creating if needed.

    Args:
        pipeline: If provided, create a new Application using this pipeline.
        is_demo: Explicitly set demo mode. Pass ``False`` when the user has
            supplied their own pipeline so the demo banner is suppressed.
            Defaults to ``True`` whenever no pipeline is provided (i.e., the
            sample pipeline is being used).
        cde_extra: Optional dict of CDE-level scoring attributes (from the
            CDE Profile sheet in an uploaded xlsx). Merged into CDEProfile.extra
            so the Win Alignment Scorer automatically picks them up.
    """
    creating_new = "app" not in st.session_state or pipeline is not None
    if creating_new:
        effective_demo = is_demo if is_demo is not None else pipeline is None
        if effective_demo:
            cde = CDEProfile.sample()
        else:
            # User-supplied pipeline: NEUTRAL profile. The sample CDE's
            # scoring attributes (3 prior awards, 76% track-record alignment,
            # third-party validation, ...) must never influence an upload's
            # framework score — page 1 discloses missing CDE fields as
            # "defaulted to 0/False", and that must be literally true.
            cde = CDEProfile(
                name="(your CDE)",
                cde_id="user-upload",
                certification_date="",
                mission="",
                target_markets=[],
                prior_awards=[],
                contact={},
                governance={},
                extra={},
            )
        if cde_extra:
            # IDENTITY NEVER MERGES. The neutral profile above exists so an
            # upload's framework score cannot inherit the sample CDE's
            # attributes — and through 1.1.5 this merge handed them straight
            # back, because the shipped "blank template" carried Riverbend's
            # identity and all eighteen scoring attributes in its CDE Profile
            # sheet. A CDE that filled in only the Pipeline sheet was scored as
            # Riverbend, and Riverbend's has_prior_reporting_issues=False
            # rendered as "Per this CDE's own profile declaration, no prior
            # NMTC reporting issues have been recorded."
            #
            # Only genuinely-supplied SCORING attributes may merge. Identity
            # keys are dropped, and anything blank is dropped too so an
            # untouched cell cannot register as an answer.
            cde_extra = _scoring_attrs_only(cde_extra, effective_demo)
            cde.extra = {**cde.extra, **cde_extra}
        p = pipeline if pipeline is not None else Pipeline.sample(n=20)
        app = Application(cde=cde, requested_allocation=65_000_000, application_round="CY2025")
        app.add_pipeline(p)
        st.session_state["app"] = app
        st.session_state["is_demo_data"] = effective_demo
    elif cde_extra and "app" in st.session_state:
        # User re-supplied CDE data without re-uploading the pipeline — patch extra in place
        st.session_state["app"].cde.extra = {
            **st.session_state["app"].cde.extra,
            **_scoring_attrs_only(cde_extra, st.session_state.get("is_demo_data", True)),
        }
        if "is_demo_data" not in st.session_state:
            st.session_state["is_demo_data"] = True
    elif "is_demo_data" not in st.session_state:
        st.session_state["is_demo_data"] = True
    return st.session_state["app"]


def get_app() -> Application | None:
    """Return the Application from session_state, or None if not yet created."""
    return st.session_state.get("app")


def fmt_millions(value: float) -> str:
    """Format a dollar value in millions with one decimal place."""
    return f"${value / 1_000_000:.1f}M"


def fmt_pct(value: float) -> str:
    """Format a fraction (0–1) as percentage."""
    return f"{value * 100:.1f}%"


def tier_badge_html(tier: str) -> str:
    """Return an HTML span styled as a coloured tier badge."""
    color = TIER_COLORS.get(tier.lower(), MUTED)
    label = tier.upper()
    return (
        f'<span style="background-color:{color};color:white;'
        f'padding:4px 12px;border-radius:12px;font-weight:600;'
        f'font-size:0.9rem;letter-spacing:0.05em;">{label}</span>'
    )


def priority_color(priority: str) -> str:
    """Map recommendation priority to a display colour."""
    return {
        "critical": DANGER,
        "high": ACCENT,
        "medium": SUCCESS,
    }.get(priority.lower(), MUTED)


def apply_theme() -> None:
    """Inject shared dark-mode CSS.

    IMPORTANT: call this BEFORE injecting page-level CSS in the same function,
    so page-level !important rules with equal specificity win (last-wins rule).
    """
    st.markdown(
        """
        <style>
        [data-testid="stMain"] {
            background-color: #0E1117;
        }
        [data-testid="stSidebar"] {
            background-color: #1A1F2E;
        }
        h1, h2, h3, h4 {
            color: #E5E7EB !important;
            font-weight: 600 !important;
        }
        p, li {
            color: #E5E7EB;
        }
        .stMetricLabel { color: #9CA3AF !important; font-size: 0.85rem !important; }
        .stMetricValue { color: #F3F4F6 !important; font-weight: 600 !important; }
        [data-testid="stRadio"] label,
        [data-testid="stCheckbox"] label { color: #E5E7EB !important; }
        [data-baseweb="tab"] { color: #9CA3AF; }
        [data-baseweb="tab"][aria-selected="true"] { color: #F3F4F6; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_methodology_warning() -> None:
    """Display the mandatory win-alignment methodology disclosure."""
    st.warning(
        "**Methodology Notice:** The alignment score measures how closely this "
        "application matches patterns observed in historical NMTC award winners "
        "(CY2020–CY2024). It is **not** a win probability. The CDFI Fund does not "
        "publish non-winner application data, so a true probability of selection "
        "cannot be computed. A high alignment score improves competitiveness but "
        "does **not** guarantee an award."
    )

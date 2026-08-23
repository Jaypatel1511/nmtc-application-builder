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
from nmtcapp.core.application_round import (  # noqa: F401  (round_label re-exported)
    is_round_specified,
    round_label,
)
from nmtcapp.renderers._round_provenance import UPCOMING_ROUND

#: The round the FICTIONAL sample CDE is filing into.
#:
#: A DEFAULT MAY NOT INVENT THE USER'S FACT; A FIXTURE MAY STATE ITS OWN
#: (1.5.5 T1). ``Application`` no longer defaults the round, because the round
#: a real CDE files into is that CDE's fact. The demo is not a real CDE — it
#: is a complete worked example of a filled-in application, and a worked
#: example with the field left blank teaches the wrong thing.
#:
#: Read from ``_round_provenance.UPCOMING_ROUND`` rather than typed, so this
#: cannot become the next "CY2025": a literal here would drift the moment the
#: Fund opens a round, and drift is how a demo ends up naming a round nobody
#: ran. What it names today is CY 2026 — announced 12 Aug 2026, not yet open,
#: and the round a CDE using this tool would in fact enter.
SAMPLE_APPLICATION_ROUND = UPCOMING_ROUND

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


# ---------------------------------------------------------------------------
# THE DOLLAR SIGNS WERE BEING EATEN (1.5.5 T3)
# ---------------------------------------------------------------------------
def md(text: str) -> str:
    """Make ``text`` safe to hand to a Streamlit markdown surface.

    STREAMLIT'S MARKDOWN IS NOT COMMONMARK. It carries
    ``micromark-extension-math`` with ``singleDollarTextMath`` left at its
    default of TRUE, so ONE ``$`` opens an inline-math span and the next
    matching ``$`` closes it. Both delimiters are consumed and the run
    between them is re-typeset.

    That is not hypothetical. Through 1.5.4 the round-provenance note --
    which contains "$10 billion" and "$5 billion" in ONE paragraph -- rendered
    on three pages as "awarded 23 Dec 2025 with 10 billion in allocation
    authority ... CY 2026 will make 5 billion available". Ten billion WHAT.
    In a federal-allocation disclosure the unit is not decoration, and the
    package's own gates could not see it because they read the SOURCE string,
    which was correct the whole time.

    WHY THE ESCAPE LIVES HERE AND NOT IN THE NOTE. The note is ONE STRING
    READ EVERYWHERE (``renderers/_round_provenance``) -- Word, PDF, Excel and
    Markdown render the same object. A ``\\$`` baked into it would put a
    literal backslash into a generated Word document. The mangling is
    Streamlit's, so the repair belongs at Streamlit's boundary.

    Escaping is safe even where it is not yet needed: a lone ``$`` is
    currently harmless (micromark's unterminated-math branch emits no span),
    but "currently" is doing load-bearing work in that sentence -- add a
    second amount to the same body later and the first one silently loses its
    unit. Verified in Chrome against the pinned Streamlit on 2026-08-22:
    ``\\$`` renders as ``$`` and produces no math node, on ``st.markdown``,
    ``st.info`` and ``st.caption`` alike.

    Gated by ``tests/test_streamlit_markdown_survival.py``, which asserts the
    RENDERED text rather than this source.

    Example::

        st.info(md(round_provenance_paragraphs()[0]))
    """
    return text.replace("$", r"\$")


# Identity keys parsed off an uploaded "CDE Profile" sheet. These describe WHO
# the CDE is; they must never reach a CDEProfile built for someone else's
# upload, and none of them feeds a score.
_IDENTITY_KEYS = frozenset({
    "cde_name", "cde_id", "ein", "headquarters_state", "certification_date",
    "mission", "website", "organization_type", "target_markets",
    "requested_allocation_millions", "application_round",
})


def _supplied_round(cde_extra: dict | None) -> str | None:
    """The round off an uploaded CDE Profile sheet, or None if it was blank.

    WHY THIS EXISTS SEPARATELY FROM ``_scoring_attrs_only`` (1.5.5 audit B4).
    ``application_round`` is correctly stripped from the dict that merges into
    ``cde.extra`` — that dict is a SCORING-ATTRIBUTE bag and a round is not a
    scoring attribute; it moves no score. The defect was that stripping it
    from the wrong destination was mistaken for discarding it, so a round the
    CDE typed into the template's own "Application Round" cell was replaced by
    the tool's assertion. It has a right destination: ``Application``.

    A blank or whitespace cell is NOT an answer. ``is_round_specified`` is the
    same predicate the renderers use, so an untouched cell reaches the same
    disclosure as an omitted argument rather than rendering an empty round.

    Example::

        _supplied_round({"application_round": "CY 2027"})   # -> 'CY 2027'
        _supplied_round({"application_round": "  "})        # -> None
    """
    value = (cde_extra or {}).get("application_round")
    return value.strip() if is_round_specified(value) else None


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
    # Read before _scoring_attrs_only() below rebinds cde_extra without it.
    supplied_round = _supplied_round(cde_extra)
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
        # THE ROUND IS GATED ON effective_demo (1.5.5 audit B4). This line
        # applied SAMPLE_APPLICATION_ROUND unconditionally, so a real upload
        # got "CY 2026" asserted onto every generated document. That is the
        # trade core/application_round rules out in as many words: it swaps a
        # false claim for an unverified one. The demo is a fictional worked
        # example and may state its own round; an upload's round is the
        # uploader's fact, honoured when supplied and DISCLOSED when not.
        app = Application(cde=cde, requested_allocation=65_000_000,
                          application_round=(
                              SAMPLE_APPLICATION_ROUND if effective_demo
                              else supplied_round))
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
        # A CDE that uploads its pipeline first and its CDE Profile second
        # arrives here. The round on that second sheet is the same fact off
        # the same cell and is honoured the same way -- except on the demo,
        # whose round is the fixture's own and is not user-overridable
        # through this side door.
        if supplied_round and not st.session_state.get("is_demo_data", True):
            st.session_state["app"].application_round = supplied_round
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


# ---------------------------------------------------------------------------
# metric_classification -- a classification is not a movement (1.5.1 audit, F1)
#
# T4 FIXED HALF OF THIS AND SHIPPED A CLAIM THAT IT WAS WHOLE. The round found
# that ``st.metric(delta="Grade F")`` rendered a GREEN UP ARROW, because
# streamlit.elements.metric._determine_delta_color_and_direction treats a delta
# as negative only when ``str(delta)`` starts with "-" and as zero only when it
# is exactly "0"; a grade letter falls through to UP. It fixed that by passing
# ``delta_color="off"``, and both 1_Pipeline_Analyzer.py and CHANGELOG.md then
# stated the result was GRAY/NONE.
#
# IT IS NOT. Executed against the pinned Streamlit (1.61.1), for every grade:
#
#     _determine_delta_color_and_direction("off", "Grade F")
#         -> color=GRAY  direction=UP
#
# Read the function and the reason is structural: DIRECTION is computed from the
# delta's sign BEFORE the colour mode is consulted, and ``delta_color`` only
# ever selects a COLOUR. There is no value of ``delta_color`` that removes the
# arrow. "off" greys it; the F still points up.
#
# So the round shipped a partial fix AND a false statement that it was complete
# -- and the false statement is the part that stops anyone looking again. The
# arrow was still there for anyone who opened the page.
#
# THE FIX IS TO STOP USING THE DELTA SLOT FOR CLASSIFICATIONS. ``delta`` means
# "this value moved, in this direction". A grade, a section label, a
# meets/below verdict and a denominator are none of them movements, and no
# argument to st.metric makes the slot mean something else. They are rendered
# below the metric as their own element, where they carry no direction at all.
#
# SEVEN SITES, NOT TWO. The round found the grade and the three About-page
# section labels. Executing every delta string in the app found four more:
# "Meets/Below this tool's own >=X% band" (RED/GREEN + UP), "of 20" (GREEN +
# UP -- a denominator rendered as favourable movement) and the two
# "check/cross meets min" verdicts on the scorer.

#: Tone -> the colour Streamlit's own caption markdown accepts. ``None`` leaves
#: the caption in the theme's muted grey, which is what a neutral label wants.
_CLASSIFICATION_TONES = {"good": "green", "bad": "red", None: None}


def metric_classification(
    container,
    label: str,
    value,
    classification: str,
    tone: str | None = None,
    help: str | None = None,
) -> None:
    """Render a metric whose sidecar text CLASSIFIES rather than moves.

    Args:
        container: the ``st`` module or a column returned by ``st.columns``.
        label: the metric label.
        value: the metric value.
        classification: the grade / verdict / label. Rendered UNDER the metric
            as a caption, never as ``delta``, so Streamlit draws no arrow.
        tone: ``"good"``, ``"bad"`` or ``None``. Colours the caption text only.
            A colour is a colour; it is not a direction.
        help: forwarded to ``st.metric``.

    Deliberately does NOT accept a ``delta``. A caller with a real signed
    movement should call ``st.metric`` directly -- that is what the slot is
    for, and the optimizer's "+3.0 pts" still uses it.
    """
    if tone not in _CLASSIFICATION_TONES:
        raise ValueError(
            f"tone must be one of {sorted(k for k in _CLASSIFICATION_TONES if k)} "
            f"or None, got {tone!r}"
        )
    container.metric(label, value, help=help)
    colour = _CLASSIFICATION_TONES[tone]
    text = classification if colour is None else f":{colour}[{classification}]"
    container.caption(text)

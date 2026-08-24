"""Shared helpers for the NMTC Application Builder Streamlit demo."""
from __future__ import annotations

import sys
import os
from dataclasses import dataclass

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
from nmtcapp.renderers._cell_format import NOT_SUPPLIED_INPUT
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


#: The largest figure the "Requested Allocation ($M)" cell can hold, IN MILLIONS.
#:
#: NOT an invented plausibility band. ``data/historical_awards`` records that
#: "CY 2026 is a $5 billion single round" -- $5B is the national allocation
#: authority competed in one round, across every applicant. A single CDE
#: cannot request more than the entire country's round, so a cell above this
#: is not an ambitious request; it is a unit error. ``AWARD_SIZE_TIERS``
#: deliberately leaves its top tier unbounded ("over_65MM" -> inf) and is
#: therefore no help here: it describes what winners got, not what the cell
#: can mean.
_MAX_ALLOCATION_MILLIONS = 5_000

#: What ``Application`` is given when an upload states no allocation.
#:
#: THIS IS A PLACEHOLDER AND NOT A CLAIM, AND THE DISTINCTION IS LOAD-BEARING.
#: ``Application.__init__`` raises on ``requested_allocation <= 0``; the
#: library has no "unstated allocation" the way it has an unstated round, and
#: giving it one means an Optional float through eight renderers, two
#: sections and the validators -- a library API change, and not this patch.
#: So the Streamlit layer still hands it a number.
#:
#: WHAT MAKES IT NOT A CLAIM IS THAT NOTHING RENDERS IT. The only surface in
#: this app that shows the figure is page 1, and it now shows
#: ``NOT_SUPPLIED_INPUT`` instead whenever the CDE did not state one. There is
#: no document export in the Streamlit app -- the Word/PDF/Excel/Markdown
#: builders are library and CLI surfaces, reached with an allocation the
#: caller passed in.
#:
#: IT IS 65_000_000 RATHER THAN SOMETHING NEUTRAL-LOOKING ON PURPOSE. It is
#: what this line already held, so an upload that states no allocation
#: computes exactly what it computed at e4c6586 and this change moves nothing
#: for it. A "more obviously fake" number would move the optimizer's size-fit
#: sub-score for every such upload, which is a real behavioural change made
#: for cosmetic reasons.
#:
#: AND IT IS NOT FULLY INERT, WHICH IS RECORDED RATHER THAN GLOSSED:
#: ``optimizer/objectives.score_pipeline_quality`` reads the allocation for a
#: size-fit band, so page 3 scores an unstated allocation as though it were
#: $65MM. That is pre-existing, it is unchanged here, and it is the reason
#: _IDENTITY_KEYS' "none of them feeds a score" is false -- see the audit note
#: on that frozenset. Making page 3 disclose it is its own change.
_UNSTATED_ALLOCATION_PLACEHOLDER = 65_000_000


def _supplied_allocation(cde_extra: dict | None) -> float | None:
    """The requested allocation off an uploaded CDE Profile sheet, in DOLLARS.

    Returns ``None`` when the cell cannot be read as a request, which is
    DISCLOSED by the caller rather than replaced with a guess.

    WHY THIS EXISTS, AND WHY IT MIRRORS ``_supplied_round`` (1.5.5 audit B6).
    ``requested_allocation_millions`` is correctly stripped from the dict that
    merges into ``cde.extra`` -- that dict is a SCORING-ATTRIBUTE bag and a
    request is not a scoring attribute. The defect was, exactly as with the
    round, that nothing then routed it to its real destination,
    ``Application``, so a CDE that filled the template's own "Requested
    Allocation ($M)" cell had a different money figure asserted in its place
    on every surface that shows one.

    THE UNITS, RULED FROM WHAT THE TEMPLATE ASKS. The blank template's CDE
    Profile sheet labels column 10 ``Requested Allocation ($M)``; the shipped
    ``pipeline_sample.xlsx`` states ``65`` in it; and the Pipeline sheet's
    ``QEI ($M)`` and ``Total Cost ($M)`` use the same convention and are
    already multiplied by 1_000_000 in ``_XLSX_MILLIONS_COLS``. Three
    independent readings of the same workbook agree, so the cell is MILLIONS
    and the conversion is unambiguous.

    WHAT IS REFUSED, AND WHY NOTHING IS COERCED OR CLAMPED:

      * blank / whitespace / absent -- not an answer, same as a blank round.
      * zero or negative -- not a request, and ``Application`` forbids it.
      * non-numeric -- a typo is not a licence to guess what was meant.
      * above ``_MAX_ALLOCATION_MILLIONS`` -- the unit trap. A user who types
        ``65000000`` into a ($M) cell means $65MM and would otherwise get $65
        TRILLION. "They obviously meant 65" is a guess about which unit they
        used, and clamping to the ceiling invents a request they never made.
        A wrong allocation is worse than a disclosed absent one, so it
        discloses.

    Note the cell arrives as a STRING: ``_parse_cde_profile_from_wb`` sends
    every unrecognised key through ``str(val).strip()``, so ``65`` is
    ``"65"``. Numbers are accepted too, for callers that pass a parsed dict.

    Example::

        _supplied_allocation({"requested_allocation_millions": "42"})   # -> 42000000.0
        _supplied_allocation({"requested_allocation_millions": "  "})   # -> None
        _supplied_allocation({"requested_allocation_millions": 65000000})  # -> None
    """
    raw = (cde_extra or {}).get("requested_allocation_millions")
    if raw is None:
        return None
    text = str(raw).strip().lstrip("$").strip()
    if not text:
        return None
    try:
        millions = float(text)
    except (TypeError, ValueError):
        return None
    if millions != millions or millions in (float("inf"), float("-inf")):
        return None
    if millions <= 0 or millions > _MAX_ALLOCATION_MILLIONS:
        return None
    return millions * 1_000_000


def requested_allocation_label(value: float) -> str:
    """Render the requested allocation, or disclose that the CDE never stated one.

    The counterpart of ``round_label`` for the figure on the adjacent line of
    page 1. ``NOT_SUPPLIED_INPUT`` is the library's own vocabulary for "a
    REQUIRED field was absent from the input and the tool put a number there
    anyway" -- written for the QLICI defect, which is the same shape -- so
    this invents no new string and renders as text that cannot be mistaken
    for a figure.

    Defaults to showing the figure: every path that does not go through an
    upload (the demo, and any Application built directly) states its own.
    """
    if not st.session_state.get("allocation_is_stated", True):
        return NOT_SUPPLIED_INPUT
    return fmt_millions(value)


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


@dataclass(frozen=True)
class UploadedCDEProfile:
    """A parsed CDE Profile sheet, split into the two destinations it serves.

    THE TYPE EXISTS BECAUSE THE ORDER OF TWO CALLS WAS LOAD-BEARING AND
    NOTHING ENFORCED IT (1.5.7 T1). ``load_uploaded_pipeline`` returns ONE
    dict that feeds TWO destinations: the scoring-attribute bag that merges
    into ``CDEProfile.extra``, and two facts -- the round and the requested
    allocation -- whose destination is ``Application``. ``_scoring_attrs_only``
    correctly removes the second from the first. ``get_or_create_app``
    correctly read them before doing so.

    The defect was that page 1 ALSO called ``_scoring_attrs_only``, one line
    earlier, and rebound the name. ``get_or_create_app`` then read a dict the
    caller had already emptied, found nothing, and fell back to
    ``_UNSTATED_ALLOCATION_PLACEHOLDER`` -- telling a CDE that had filled in
    both cells that it had supplied neither, and then computing with
    \\$65,000,000. Its defence was a comment naming its OWN strip; it could not
    see the caller's.

    WHY A TYPE AND NOT "READ EARLIER". Reading earlier fixes this caller and
    leaves the trap armed for the next one: the hazard is that a
    SCORING-ATTRIBUTE BAG and TWO IDENTITY FACTS travel in one dict, so
    stripping the bag silently discards the facts. A dict cannot carry the
    distinction; this can. Once the facts are on their own fields, no caller
    can strip them by forgetting, because the strip does not reach them --
    and a caller who hands ``get_or_create_app`` one of these hands over
    both destinations at once or neither.

    ``scoring_attrs`` is already stripped and blank-filtered: it is exactly
    what may merge into ``CDEProfile.extra``.

    Example::

        parsed = read_uploaded_cde_profile({"application_round": "CY 2027",
                                            "dbc_focus_years": 4},
                                           is_demo=False)
        parsed.scoring_attrs      # -> {'dbc_focus_years': 4}
        parsed.supplied_round     # -> 'CY 2027'
    """

    scoring_attrs: dict
    supplied_round: str | None
    supplied_allocation: float | None


def read_uploaded_cde_profile(
    cde_extra: dict | None, *, is_demo: bool
) -> UploadedCDEProfile:
    """Split a parsed CDE Profile sheet into scoring attrs + the two facts.

    THE ONLY CORRECT ORDER, WRITTEN ONCE. Both reads happen before the strip,
    here, in the one place that performs the strip for callers. There is no
    second ordering for a caller to get wrong.

    Example::

        read_uploaded_cde_profile({"requested_allocation_millions": "42"},
                                  is_demo=False).supplied_allocation
        # -> 42000000.0
    """
    cde_extra = cde_extra or {}
    return UploadedCDEProfile(
        scoring_attrs=_scoring_attrs_only(cde_extra, is_demo),
        supplied_round=_supplied_round(cde_extra),
        supplied_allocation=_supplied_allocation(cde_extra),
    )


def get_or_create_app(
    pipeline: Pipeline | None = None,
    is_demo: bool | None = None,
    cde_extra: dict | UploadedCDEProfile | None = None,
) -> Application:
    """Return the shared Application object from session_state, creating if needed.

    Args:
        pipeline: If provided, create a new Application using this pipeline.
        is_demo: Explicitly set demo mode. Pass ``False`` when the user has
            supplied their own pipeline so the demo banner is suppressed.
            Defaults to ``True`` whenever no pipeline is provided (i.e., the
            sample pipeline is being used).
        cde_extra: The parsed CDE Profile sheet from an uploaded xlsx, as
            either an ``UploadedCDEProfile`` (preferred -- see below) or the
            raw dict ``load_uploaded_pipeline`` returns. Scoring attributes
            merge into ``CDEProfile.extra`` so the Win Alignment Scorer picks
            them up; the round and requested allocation go to ``Application``.

            EITHER SHAPE IS SAFE, WHICH IS THE POINT (1.5.7 T1). Handed a raw
            dict, this function does the read-then-strip itself, in that
            order. Handed an ``UploadedCDEProfile``, the facts arrive on their
            own fields and no strip can have reached them. What is no longer
            possible is the shape that shipped in 1.5.6: a caller stripping
            first and handing over a dict whose facts are already gone, which
            this function could not distinguish from a sheet that stated
            neither.
    """
    creating_new = "app" not in st.session_state or pipeline is not None
    # THE READ HAPPENS BEFORE ANY STRIP AND NO CALLER CAN REORDER IT.
    #
    # Through 1.5.6 these two lines were the whole defence, and the comment
    # here said "Read before _scoring_attrs_only() below rebinds cde_extra
    # without them." It named THIS function's strip. Page 1 ran its own strip
    # one line before the call, so by the time these ran there was nothing
    # left to read -- and the 18 tests over this behaviour all passed, because
    # every one of them hand-wrote a dict that still contained the keys.
    # See UploadedCDEProfile for why the fix is a type and not "read earlier".
    if isinstance(cde_extra, UploadedCDEProfile):
        _parsed, _raw_extra = cde_extra, None
        supplied_round = _parsed.supplied_round
        supplied_allocation = _parsed.supplied_allocation
        _has_extra = bool(_parsed.scoring_attrs)
    else:
        _parsed, _raw_extra = None, cde_extra
        supplied_round = _supplied_round(_raw_extra)
        supplied_allocation = _supplied_allocation(_raw_extra)
        _has_extra = bool(_raw_extra)
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
        if _has_extra:
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
            # Already stripped when the caller handed over a parsed
            # profile; the identity guard ran at read time in that case.
            _attrs = (
                _parsed.scoring_attrs if _parsed is not None
                else _scoring_attrs_only(_raw_extra, effective_demo)
            )
            cde.extra = {**cde.extra, **_attrs}
        p = pipeline if pipeline is not None else Pipeline.sample(n=20)
        # THE ROUND IS GATED ON effective_demo (1.5.5 audit B4). This line
        # applied SAMPLE_APPLICATION_ROUND unconditionally, so a real upload
        # got "CY 2026" asserted onto every generated document. That is the
        # trade core/application_round rules out in as many words: it swaps a
        # false claim for an unverified one. The demo is a fictional worked
        # example and may state its own round; an upload's round is the
        # uploader's fact, honoured when supplied and DISCLOSED when not.
        # THE ALLOCATION IS GATED ON effective_demo TOO (1.5.5 audit B6), for
        # the reason directly above and on the same line of the same
        # frozenset. This read ``requested_allocation=65_000_000``
        # unconditionally, so a CDE that stated its own request in the
        # template's "Requested Allocation ($M)" cell had $65,000,000
        # asserted over it -- rendered on page 1 and fed to page 3's
        # optimizer. The demo is a fictional worked example and states its
        # own $65MM; an upload's request is the uploader's fact, honoured
        # when supplied and DISCLOSED when not.
        allocation_is_stated = effective_demo or supplied_allocation is not None
        if effective_demo:
            requested = 65_000_000
        elif supplied_allocation is not None:
            requested = supplied_allocation
        else:
            requested = _UNSTATED_ALLOCATION_PLACEHOLDER
        app = Application(cde=cde, requested_allocation=requested,
                          application_round=(
                              SAMPLE_APPLICATION_ROUND if effective_demo
                              else supplied_round))
        app.add_pipeline(p)
        st.session_state["app"] = app
        st.session_state["is_demo_data"] = effective_demo
        st.session_state["allocation_is_stated"] = allocation_is_stated
    elif _has_extra and "app" in st.session_state:
        # User re-supplied CDE data without re-uploading the pipeline — patch extra in place
        _side_attrs = (
            _parsed.scoring_attrs if _parsed is not None
            else _scoring_attrs_only(
                _raw_extra, st.session_state.get("is_demo_data", True)
            )
        )
        st.session_state["app"].cde.extra = {
            **st.session_state["app"].cde.extra,
            **_side_attrs,
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
        # The request on that second sheet is the same fact off the same cell
        # and is honoured the same way -- and, like the round, not through
        # this side door on the demo, whose $65MM is the fixture's own.
        if (supplied_allocation is not None
                and not st.session_state.get("is_demo_data", True)):
            st.session_state["app"].requested_allocation = supplied_allocation
            st.session_state["allocation_is_stated"] = True
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

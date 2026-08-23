"""C2: uploaded pipelines must never score against the sample CDE's attributes.

Before this fix, ``get_or_create_app`` gave EVERY pipeline — including user
uploads — ``CDEProfile.sample()``, whose ``extra`` dict carries strong scoring
attributes (3 prior awards, 76% track-record alignment, third-party
validation, ...). Uploads therefore scored against a fictional CDE's track
record while page 1 claimed missing fields were "defaulted to 0/False".

The fix: uploads get a NEUTRAL profile (no prior awards, empty extra);
``CDEProfile.sample()`` remains only for the demo path.
"""
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STREAMLIT_APP = os.path.join(_REPO_ROOT, "streamlit_app")
for p in (_REPO_ROOT, _STREAMLIT_APP):
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st

from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline

from utils import get_or_create_app

# Signature values of the sample CDE that must never influence an upload score
SAMPLE_SIGNATURES = {
    "prior_award_count": 3,
    "track_record_pipeline_alignment_pct": 0.76,
    "has_third_party_validation": True,
    "products_below_market_pct": 0.42,
    "unrelated_entities_pct": 0.82,
}


@pytest.fixture(autouse=True)
def _fresh_session():
    st.session_state.clear()
    yield
    st.session_state.clear()


def _uploaded_pipeline() -> Pipeline:
    # Simulates a user upload: same shape as a from_csv result. Sample
    # projects reused as pre-enriched rows so scoring runs without API calls.
    return Pipeline.sample(n=6)


def test_upload_gets_neutral_profile():
    app = get_or_create_app(pipeline=_uploaded_pipeline(), is_demo=False)
    assert app.cde.name == "(your CDE)"
    assert app.cde.cde_id == "user-upload"
    assert app.cde.prior_awards == []
    assert app.cde.extra == {}
    assert st.session_state["is_demo_data"] is False


def test_upload_cde_extra_from_upload_is_kept():
    app = get_or_create_app(
        pipeline=_uploaded_pipeline(), is_demo=False,
        cde_extra={"prior_award_count": 1, "years_in_operation": 2},
    )
    assert app.cde.extra == {"prior_award_count": 1, "years_in_operation": 2}


def test_upload_score_free_of_sample_signature_values():
    app = get_or_create_app(pipeline=_uploaded_pipeline(), is_demo=False)
    score = app.score_win_probability()
    # No prior awards, no alignment/deployment history, no capital at risk:
    # every track-record sub-score must be at its zero default.
    assert score.business_strategy["track_record_strength"] == 0
    assert score.business_strategy["track_record_alignment"] == 0
    # None of the sample-CDE signature attributes may be present.
    for key in SAMPLE_SIGNATURES:
        assert key not in app.cde.extra


def test_upload_score_differs_from_sample_profile_score():
    """Proves the leak is closed: same pipeline, different profile basis."""
    pipeline = _uploaded_pipeline()

    st.session_state.clear()
    upload_app = get_or_create_app(pipeline=pipeline, is_demo=False)
    upload_score = upload_app.score_win_probability()

    st.session_state.clear()
    demo_app = get_or_create_app(pipeline=Pipeline.sample(n=6), is_demo=True)
    demo_score = demo_app.score_win_probability()

    assert demo_app.cde.name == CDEProfile.sample().name
    assert upload_score.aggregate_with_priority != demo_score.aggregate_with_priority


def test_demo_path_still_gets_sample_profile_and_demo_banner():
    app = get_or_create_app()  # no pipeline → demo
    assert app.cde.name == CDEProfile.sample().name
    assert app.cde.extra.get("prior_award_count") == 3
    assert st.session_state["is_demo_data"] is True


def test_page1_zero_default_disclosure_is_true_for_uploads():
    """Page 1 tells upload users that missing CDE fields default to 0/False.
    With the neutral profile those effective values must actually be 0/False —
    in particular prior_award_count derives from an EMPTY awards list."""
    app = get_or_create_app(pipeline=_uploaded_pipeline(), is_demo=False)
    # Mirror Application.score_win_probability's attribute assembly
    cde_attributes = dict(app.cde.extra) if app.cde.extra else {}
    if "prior_award_count" not in cde_attributes:
        cde_attributes["prior_award_count"] = len(app.cde.prior_awards)
    assert cde_attributes == {"prior_award_count": 0}


# ---------------------------------------------------------------------------
# THE ROUND A CDE FILES INTO IS THE CDE'S FACT — AT THE STREAMLIT BOUNDARY TOO
# (1.5.5 audit B4)
# ---------------------------------------------------------------------------
#
# THE DEFECT. 1.5.5 T1 removed ``application_round="CY2025"`` as a default
# because the round a CDE files into is that CDE's fact and a library may not
# supply one. ``core/application_round`` states the ruling in as many words:
#
#     "Replacing 'CY2025' with 'CY 2026' would swap a false claim for an
#      unverified one."
#
# ``streamlit_app/utils.get_or_create_app`` did exactly that trade, on the
# release's own surface. ``application_round=SAMPLE_APPLICATION_ROUND`` sat
# OUTSIDE the ``if effective_demo:`` branch, so it applied to a real upload as
# well as to the demo, and every generated document asserted "CY 2026" to a
# CDE who never said so. ``SAMPLE_APPLICATION_ROUND``'s own docstring scopes
# itself to "the FICTIONAL sample CDE". The code did not.
#
# AND THE SECOND HALF, WHICH IS WORSE. ``upload_handler._CDE_FIELD_MAP`` maps
# the CDE Profile sheet's "Application Round" cell to ``application_round``,
# so the template ASKS the user for the round. ``_scoring_attrs_only`` then
# strips it as an identity key and the tool renders its own assertion in its
# place. A CDE who filled that cell had their value discarded silently.
#
# THE RULING ON THAT CELL, AND WHY IT IS "HONOUR" RATHER THAN "DISCLOSE":
#
#   * It is NOT deliberately an identity field. ``_IDENTITY_KEYS`` says its
#     members "describe WHO the CDE is"; a round is what the CDE is filing
#     INTO, not who they are. The strip is right for the DESTINATION it
#     guards — ``cde.extra`` is a scoring-attribute bag and a round is not a
#     scoring attribute, which is also why the round moves no score — and the
#     defect is that nothing then routed it to the ``Application``.
#   * ``tests/test_application_round.py``'s header already states the
#     intended contract: ``core/upload_handler`` "maps a user-supplied
#     'Application Round' column onto it. It is unambiguously the round the
#     CDE is filing INTO, which is the user's fact about their own
#     submission."
#   * Disclosing "this cell is not read" while the template goes on asking
#     for it would be a worse design than either honouring or removing it:
#     it asks a CDE for a fact about their own filing and then announces it
#     was ignored.
#
# So: supplied → rendered verbatim. Absent → the disclosure, never a guess.
# The demo is unchanged and still names CY 2026, because the demo is a
# fictional worked example stating its own fact, not a default inventing a
# user's.
#
# NOT FIXED HERE, AND REPORTED RATHER THAN QUIETLY LEFT: the same sheet's
# "Requested Allocation ($M)" is discarded by the identical mechanism —
# parsed to ``requested_allocation_millions``, stripped by
# ``_scoring_attrs_only``, and then ``get_or_create_app`` hard-codes
# ``requested_allocation=65_000_000`` for uploads as well as for the demo. It
# is the same defect class. It is left for its own change because it moves a
# money figure on every rendered surface, which is a behavioural change that
# deserves its own review rather than a ride on a round fix.

from nmtcapp.core.application_round import (  # noqa: E402
    ROUND_UNSPECIFIED_VALUE,
    round_label,
)
from utils import SAMPLE_APPLICATION_ROUND  # noqa: E402


def test_an_upload_is_not_given_a_round_the_cde_never_stated():
    """The T1 ruling, applied at the Streamlit boundary."""
    app = get_or_create_app(pipeline=_uploaded_pipeline(), is_demo=False)
    assert app.application_round is None, (
        f"an uploaded pipeline was given application_round="
        f"{app.application_round!r}. The round a CDE files into is the CDE's "
        "fact; this surface may not supply one any more than Application's "
        "default could."
    )
    assert round_label(app.application_round) == ROUND_UNSPECIFIED_VALUE


def test_an_upload_that_states_its_round_has_it_honoured():
    """A fact the CDE supplied about its own filing is not overwritten."""
    app = get_or_create_app(
        pipeline=_uploaded_pipeline(),
        is_demo=False,
        cde_extra={"application_round": "CY 2027", "dbc_focus_years": 4},
    )
    assert app.application_round == "CY 2027", (
        f"the CDE Profile sheet said 'CY 2027' and the tool rendered "
        f"{app.application_round!r} instead. Silently discarding a user's "
        "stated fact about their own filing is the defect class this release "
        "exists to remove."
    )
    # ...and it still must not reach the scoring bag.
    assert "application_round" not in app.cde.extra
    assert app.cde.extra["dbc_focus_years"] == 4


@pytest.mark.parametrize("blank", ["", "   ", None])
def test_a_blank_round_cell_discloses_rather_than_defaulting(blank):
    """An untouched cell is not an answer — and not a licence to guess."""
    app = get_or_create_app(
        pipeline=_uploaded_pipeline(),
        is_demo=False,
        cde_extra={"application_round": blank},
    )
    assert app.application_round is None
    assert round_label(app.application_round) == ROUND_UNSPECIFIED_VALUE


def test_the_demo_still_states_its_own_round():
    """The fixture may state its own fact; only the DEFAULT was the defect."""
    app = get_or_create_app()  # no pipeline -> demo
    assert app.application_round == SAMPLE_APPLICATION_ROUND
    assert st.session_state["is_demo_data"] is True


def test_a_round_supplied_on_a_later_cde_upload_is_honoured_too():
    """The re-supply branch reads the same fact off the same sheet.

    A CDE that uploads a pipeline first and its CDE Profile second reaches
    ``get_or_create_app``'s ``elif`` branch, which patched ``cde.extra`` and
    left the round alone.
    """
    get_or_create_app(pipeline=_uploaded_pipeline(), is_demo=False)
    app = get_or_create_app(cde_extra={"application_round": "CY 2027"})
    assert app.application_round == "CY 2027"


def test_a_later_cde_upload_cannot_put_a_round_on_the_demo():
    """The demo's own round is not user-overridable through the side door."""
    get_or_create_app()  # demo
    app = get_or_create_app(cde_extra={"application_round": "CY 2027"})
    assert app.application_round == SAMPLE_APPLICATION_ROUND

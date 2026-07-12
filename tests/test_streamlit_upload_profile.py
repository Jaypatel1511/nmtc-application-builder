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

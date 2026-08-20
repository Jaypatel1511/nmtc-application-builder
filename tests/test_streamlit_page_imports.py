"""Smoke tests: a hand-written sample of the Streamlit pages' nmtcapp imports.

SUPERSEDED BY tests/test_streamlit_deployment_pin.py. Kept because these are
cheap and named per page, but READ THE CORRECTION BELOW BEFORE TRUSTING THEM.

THIS FILE PREVIOUSLY CLAIMED TO CATCH "a PyPI-installed
nmtc-application-builder shadowing the local repo version". IT DOES NOT, AND
IT DID NOT. When the deployed app broke on `join_truncated` at 1.3.1, every
test here was green, for two independent reasons:

  1. THE LIST IS TYPED, NOT DERIVED, so it drifts silently. `test_page1_imports`
     below mirrors three of page 1's nine imported names. It does not mention
     join_truncated, LIC_ROW_LABEL, NATIVE_AREA_ROW_LABEL, Q25_QEI_BASIS_CLAUSE
     or q25_basis_note --- the five that a stale pin actually fails on. That is
     rule 4 of tests/test_pinned_constants.py (THE LIST IS DERIVED, NOT
     INHERITED) violated in the one place it most mattered.

  2. CI INSTALLS THIS TREE (`pip install ".[dev]"`), so `nmtcapp` here is always
     the repository, never the pinned PyPI copy. A test that only ever resolves
     against the tree cannot detect the tree being shadowed by something else.
     No amount of adding names to the lists below would fix that half.

test_streamlit_deployment_pin.py addresses (1) by walking the AST instead of
mirroring by hand, and addresses (2) by forcing the pin to equal this tree's
version so that "resolves against the tree" and "resolves against the pinned
version" are the same statement.
"""


def test_page1_imports():
    from nmtcapp.core.application import Application  # noqa: F401
    from nmtcapp.core.cde import CDEProfile  # noqa: F401
    from nmtcapp.core.pipeline import Pipeline  # noqa: F401


def test_page2_imports():
    from nmtcapp.core.pipeline import Pipeline  # noqa: F401
    from nmtcapp.data.benchmark_thresholds import (  # noqa: F401
        HIGHLY_QUALIFIED_AGGREGATE_MIN,
        HIGHLY_QUALIFIED_SECTION_MIN,
        HOUSE_TOP_TIER_AGGREGATE_MIN,
        HOUSE_TOP_TIER_SECTION_MIN,
    )


def test_page3_imports():
    from nmtcapp.optimizer.constraints import OptimizationConstraints  # noqa: F401


def test_page4_imports():
    from nmtcapp.data.historical_awards import (  # noqa: F401
        NMTC_AWARD_ROUNDS,
        APPLICATION_VOLUME_TRENDS,
    )
    from nmtcapp.data.benchmark_thresholds import (  # noqa: F401
        HIGHLY_QUALIFIED_AGGREGATE_MIN,
        HIGHLY_QUALIFIED_SECTION_MIN,
        HOUSE_TOP_TIER_AGGREGATE_MIN,
        HOUSE_TOP_TIER_SECTION_MIN,
        SEVERE_DISTRESS_MIN_PCT,
        DEEP_DISTRESS_MIN_PCT,
        DBC_PRIORITY_YEARS_MIN,
        DBC_VOLUME_PCT_MIN,
        HOUSE_UNRELATED_ENTITIES_MIN_PCT,
        TOTAL_APPLICANTS_CY2024_25,
        TOTAL_REQUEST_CY2024_25_B,
        TOTAL_AVAILABLE_CY2024_25_B,
    )


def test_utils_imports():
    """utils.py is imported by app.py before any page sys.path.insert runs."""
    from nmtcapp.core.application import Application  # noqa: F401
    from nmtcapp.core.cde import CDEProfile  # noqa: F401
    from nmtcapp.core.pipeline import Pipeline  # noqa: F401

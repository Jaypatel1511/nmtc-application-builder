"""Smoke tests: verify every Streamlit page's nmtcapp imports resolve correctly.

These tests fail in CI before the app crashes on Streamlit Cloud, catching:
  - Missing names after a module is renamed or refactored
  - A PyPI-installed nmtc-application-builder shadowing the local repo version
  - Any import-time NameError or AttributeError in the imported modules

Each test mirrors the exact `from nmtcapp...` import lines at the top of the
corresponding Streamlit page file, so a breakage here maps 1-to-1 to a page crash.
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

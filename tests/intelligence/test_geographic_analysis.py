"""Tests for geographic diversity analysis."""
import pytest

from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.intelligence.geographic_analysis import analyze_geographic_diversity


def _make_project(project_id: str, state: str, qei: float) -> PipelineProject:
    return PipelineProject(
        project_id=project_id, project_name=f"Project {project_id}",
        qalicb_name="Test QALICB", address="100 Main", city="Chicago", state=state,
        sector="healthcare", project_type="real_estate",
        total_project_cost=qei * 1.5, qei_request=qei, qlici_amount=qei,
        expected_jobs_created=10, expected_jobs_retained=2,
        is_nmtc_eligible=True, distress_level="deep",
        census_tract="17031010100", is_native_area=False,
        is_high_migration_rural=False, is_opportunity_zone=False,
    )


def test_analyze_geographic_empty_pipeline():
    result = analyze_geographic_diversity(Pipeline())
    assert result["states_count"] == 0
    assert result["meets_diversity_minimum"] is False


def test_states_count():
    projects = [
        _make_project("P1", "IL", 5_000_000),
        _make_project("P2", "OH", 5_000_000),
        _make_project("P3", "TX", 5_000_000),
    ]
    result = analyze_geographic_diversity(Pipeline(projects))
    assert result["states_count"] == 3


def test_single_state_pipeline():
    projects = [_make_project(f"P{i}", "IL", 1_000_000) for i in range(5)]
    result = analyze_geographic_diversity(Pipeline(projects))
    assert result["states_count"] == 1
    assert result["meets_diversity_minimum"] is False
    assert result["geographic_concentration_label"] == "highly_concentrated"


def test_diverse_pipeline_meets_minimum():
    projects = [
        _make_project("P1", "IL", 2_000_000),
        _make_project("P2", "TX", 2_000_000),
        _make_project("P3", "NY", 2_000_000),
        _make_project("P4", "GA", 2_000_000),
    ]
    result = analyze_geographic_diversity(Pipeline(projects))
    assert result["meets_diversity_minimum"] is True


def test_hhi_single_state():
    projects = [_make_project(f"P{i}", "IL", 1_000_000) for i in range(5)]
    result = analyze_geographic_diversity(Pipeline(projects))
    assert result["hhi"] == pytest.approx(10_000, abs=1)


def test_hhi_diverse_states():
    projects = [_make_project(f"P{i}", ["IL", "TX", "NY", "GA", "FL"][i], 1_000_000)
                for i in range(5)]
    result = analyze_geographic_diversity(Pipeline(projects))
    assert result["hhi"] < 5_000


def test_state_breakdown_table():
    projects = [
        _make_project("P1", "IL", 6_000_000),
        _make_project("P2", "TX", 4_000_000),
    ]
    result = analyze_geographic_diversity(Pipeline(projects))
    breakdown = result["state_breakdown"]
    assert "IL" in breakdown
    assert breakdown["IL"]["qei_dollars"] == 6_000_000
    assert breakdown["IL"]["project_count"] == 1
    assert breakdown["TX"]["pct_of_total_qei"] == pytest.approx(0.40)


def test_sample_pipeline_diversity(sample_pipeline):
    result = analyze_geographic_diversity(sample_pipeline)
    assert result["states_count"] >= 10
    assert result["meets_diversity_minimum"] is True


# ===========================================================================
# 1.4.0 R2 — the Non-Metropolitan County split
#
# WHAT THESE FIXTURES ADD THAT NOTHING IN THE TREE HAD. Not one fixture in
# this repository set is_non_metro before 1.4.0, because the field did not
# exist and the share it replaced was computed from `state` — so the whole
# metric was exercised only through the two-letter state codes above, and its
# indeterminate case could not be expressed at all.
#
# Four projects, one per reachable input state, all at equal QEI so every
# expected share is an exact quarter and no assertion needs a tolerance.
# ===========================================================================

def _metro_project(project_id: str, state: str, qei: float,
                   is_non_metro=None, geocode_success=True) -> PipelineProject:
    project = _make_project(project_id, state, qei)
    project.is_non_metro = is_non_metro
    project.geocode_success = geocode_success
    return project


def _four_way_pipeline() -> Pipeline:
    """One project of each kind, $1MM each.

    NOTE THE STATES. The determined-metro project sits in MT and the
    determined-non-metro one in IL — deliberately the OPPOSITE of what the
    deleted twelve-state list would have said. MT was one of the twelve
    "rural" states and IL was the archetypal urban one. If anything ever
    reintroduces a state-based fallback, these two assertions inverted are the
    signature.
    """
    return Pipeline([
        _metro_project("P-NONMETRO", "IL", 1_000_000, is_non_metro=True),
        _metro_project("P-METRO", "MT", 1_000_000, is_non_metro=False),
        _metro_project("P-NONE", "TX", 1_000_000, is_non_metro=None),
        _metro_project("P-UNGEOCODED", "GA", 1_000_000,
                       is_non_metro=None, geocode_success=False),
    ])


def test_the_four_input_states_land_in_three_buckets():
    """True → non-metro, False → metro, None and ungeocoded → neither."""
    result = analyze_geographic_diversity(_four_way_pipeline())

    assert result["non_metro_pct"] == pytest.approx(0.25)
    assert result["metro_pct"] == pytest.approx(0.25)
    # BOTH undetermined projects, not one: the ungeocoded project is not a
    # fourth category and is not metropolitan.
    assert result["metro_undetermined_pct"] == pytest.approx(0.50)


def test_the_three_shares_account_for_every_dollar():
    result = analyze_geographic_diversity(_four_way_pipeline())
    total = (result["non_metro_pct"] + result["metro_pct"]
             + result["metro_undetermined_pct"])
    assert total == pytest.approx(1.0), (
        "the three county-status shares do not sum to 1.0, so some pipeline "
        "QEI is in no bucket at all"
    )


def test_project_counts_and_dollars_travel_with_the_shares():
    """Question 22(f) asks for "the number and dollar amount of transactions"."""
    qei = analyze_geographic_diversity(_four_way_pipeline())["metro_status_qei"]

    assert qei["non_metro_projects"] == 1
    assert qei["metro_projects"] == 1
    assert qei["undetermined_projects"] == 2
    assert qei["non_metro"] == 1_000_000
    assert qei["metro"] == 1_000_000
    assert qei["undetermined"] == 2_000_000


def test_none_never_collapses_into_the_metropolitan_bucket():
    """The single most important property of the replacement.

    A pipeline in which NOTHING was determined must report 0% metropolitan.
    The metric this replaces reported 93% urban for exactly this pipeline,
    because "urban" meant "state absent from a list of twelve" and every one
    of these states is absent from it.
    """
    pipeline = Pipeline([
        _metro_project(f"P{i}", state, 1_000_000, is_non_metro=None)
        for i, state in enumerate(("IL", "TX", "NY", "CA", "OH"))
    ])
    result = analyze_geographic_diversity(pipeline)

    assert result["metro_pct"] == 0.0, (
        "an entirely undetermined pipeline reports a non-zero METROPOLITAN "
        "share — the twelve-state complement is back"
    )
    assert result["non_metro_pct"] == 0.0
    assert result["metro_undetermined_pct"] == pytest.approx(1.0)


def test_the_share_is_weighted_by_qei_not_by_project_count():
    """One large non-metro project outweighs three small metro ones."""
    pipeline = Pipeline([
        _metro_project("BIG", "IL", 9_000_000, is_non_metro=True),
        _metro_project("S1", "TX", 1_000_000, is_non_metro=False),
        _metro_project("S2", "NY", 1_000_000, is_non_metro=False),
        _metro_project("S3", "CA", 1_000_000, is_non_metro=False),
    ])
    result = analyze_geographic_diversity(pipeline)

    assert result["non_metro_pct"] == pytest.approx(0.75)
    assert result["metro_status_qei"]["non_metro_projects"] == 1
    assert result["metro_status_qei"]["metro_projects"] == 3


def test_the_deleted_keys_do_not_come_back():
    """`rural_pct` and `urban_pct` are gone, and gone by the right name.

    Keeping either as an alias would leave two names for a figure whose whole
    defect was that its name described a different concept from its basis.
    "Rural" is this package's own word; "Non-Metropolitan County" is the OMB
    designation Question 22 is written in, and neither the Application nor the
    NOAA uses the word "rural" for it outside the Rural CDE designation.
    """
    for result in (analyze_geographic_diversity(_four_way_pipeline()),
                   analyze_geographic_diversity(Pipeline())):
        assert "rural_pct" not in result
        assert "urban_pct" not in result


def test_the_empty_pipeline_asserts_nothing_about_any_dollar():
    """Zero QEI: all three shares 0.0, and deliberately NOT summing to 1.0."""
    result = analyze_geographic_diversity(Pipeline())

    assert result["non_metro_pct"] == 0.0
    assert result["metro_pct"] == 0.0
    assert result["metro_undetermined_pct"] == 0.0, (
        "an empty pipeline reports undetermined dollars. There are no dollars "
        "— a full ring of 'not determined' asserts that some quantity of QEI "
        "is of unknown status, which is a different claim from 'no QEI'."
    )
    assert result["metro_status_qei"]["undetermined_projects"] == 0


def test_the_twelve_state_list_is_gone_from_the_module():
    """Deleted, not merely unused — an unused set gets re-wired.

    Three of its twelve members (MS, KS, NM) were simultaneously assigned
    MSAs by _STATE_MSA_MAP in the same file, so the module counted the same
    dollars both ways forty lines apart.
    """
    import nmtcapp.intelligence.geographic_analysis as geo

    assert not hasattr(geo, "_RURAL_STATES"), (
        "_RURAL_STATES is back in intelligence/geographic_analysis"
    )
    # _STATE_MSA_MAP is a SEPARATE ruling and is deliberately kept: it feeds
    # msa_count and the per-state MSA label, never the county determination.
    assert hasattr(geo, "_STATE_MSA_MAP"), (
        "_STATE_MSA_MAP was deleted as collateral. It feeds msa_count on three "
        "surfaces and has nothing to do with the non-metropolitan share; "
        "removing it is a user-visible removal ruled against in 1.4.0 R2."
    )

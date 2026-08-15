"""H4 + M3: tables never fabricate figures or downgrade unverified to "No".

- The distress table's Poverty Rate column previously printed ">30%"/">20%"
  inferred from the distress LABEL while citing the CDFI Fund table as its
  per-row Data Source — a fabricated ACS figure. It must say "See ACS"
  unconditionally.
- None flags (native area / HMR / OZ / severely-distressed) are UNVERIFIED,
  not "No"/"N" — rendering them as negatives asserts a fact nobody checked.
"""
import pytest

from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.tables.distress_table import (
    build_distress_summary_table,
    build_distress_table,
)
from nmtcapp.tables.pipeline_table import build_pipeline_table


def _verified_project() -> PipelineProject:
    return PipelineProject(
        project_id="VER-01", project_name="Verified Deep",
        qalicb_name="VER QALICB LLC", address="1 Main St", city="Chicago",
        state="IL", sector="healthcare", project_type="real_estate",
        total_project_cost=7_000_000, qei_request=5_000_000,
        qlici_amount=5_000_000, expected_jobs_created=40,
        census_tract="17031000100", is_nmtc_eligible=True,
        distress_level="deep", is_native_area=False,
        is_high_migration_rural=False, is_opportunity_zone=True,
    )


def _unverified_project() -> PipelineProject:
    p = PipelineProject(
        project_id="UNV-01", project_name="Unverified",
        qalicb_name="UNV QALICB LLC", address="9 Lost Rd", city="Nowhere",
        state="MT", sector="education", project_type="real_estate",
        total_project_cost=4_000_000, qei_request=3_000_000,
        qlici_amount=3_000_000, expected_jobs_created=12,
    )
    p.geocode_success = False
    return p


@pytest.fixture()
def mixed_pipeline() -> Pipeline:
    return Pipeline([_verified_project(), _unverified_project()])


# ---------------------------------------------------------------------------
# Distress table: no label-inferred poverty figures — ever
# ---------------------------------------------------------------------------

def test_poverty_rate_is_see_acs_for_every_row(mixed_pipeline):
    df = build_distress_table(mixed_pipeline)
    data_rows = df[df["Project ID"] != "SUMMARY"]
    assert (data_rows["Poverty Rate (%)"] == "See ACS").all(), (
        f"fabricated poverty figures: {data_rows['Poverty Rate (%)'].tolist()}"
    )


# ---------------------------------------------------------------------------
# Distress table: unverified flags are "—"/"Unverified", never "No"
# ---------------------------------------------------------------------------

def test_distress_table_unverified_flags_not_rendered_as_no(mixed_pipeline):
    df = build_distress_table(mixed_pipeline)
    unv = df[df["Project ID"] == "UNV-01"].iloc[0]
    assert unv["NMTC Native Area (CDE-declared)"] == "—"
    assert unv["High Migration Rural (HMR)"] == "—"
    assert unv["Opportunity Zone"] == "—"
    assert unv["Severely Distressed Flag"] == "Unverified"
    assert unv["NMTC Eligible"] == "Unverified"


def test_distress_table_verified_flags_still_yes_no(mixed_pipeline):
    df = build_distress_table(mixed_pipeline)
    ver = df[df["Project ID"] == "VER-01"].iloc[0]
    assert ver["NMTC Native Area (CDE-declared)"] == "No"
    assert ver["High Migration Rural (HMR)"] == "No"
    assert ver["Opportunity Zone"] == "Yes"
    assert ver["Severely Distressed Flag"] == "Yes"
    assert ver["NMTC Eligible"] == "Yes"


def test_distress_summary_table_unverified_flags(mixed_pipeline):
    df = build_distress_summary_table(mixed_pipeline)
    unv = df[df["Project ID"] == "UNV-01"].iloc[0]
    assert unv["Severely Distressed"] == "Unverified"
    assert unv["Native Area (CDE-declared)"] == "—"


def test_summary_row_counts_only_verified_yes(mixed_pipeline):
    df = build_distress_table(mixed_pipeline)
    summary = df[df["Project ID"] == "SUMMARY"].iloc[0]
    # 1 of 2 severely distressed (the verified deep project); the unverified
    # project is neither a Yes nor silently absorbed as a No.
    assert summary["Severely Distressed Flag"].startswith("1/2")
    assert summary["NMTC Eligible"].startswith("1/2")


# ---------------------------------------------------------------------------
# Pipeline table: same rules in the CDFI Fund CY2025 template format
# ---------------------------------------------------------------------------

def test_pipeline_table_unverified_flags_not_rendered_as_n(mixed_pipeline):
    df = build_pipeline_table(mixed_pipeline)
    unv = df[df["Project ID"] == "UNV-01"].iloc[0]
    assert unv["NMTC Native Area (CDE-declared, Y/N)"] == "—"
    assert unv["High Migration Rural (Y/N)"] == "—"
    assert unv["Opportunity Zone (Y/N)"] == "—"
    assert unv["NMTC Eligible (Y/N)"] == "Unverified"


def test_pipeline_table_verified_flags_still_y_n(mixed_pipeline):
    df = build_pipeline_table(mixed_pipeline)
    ver = df[df["Project ID"] == "VER-01"].iloc[0]
    assert ver["NMTC Native Area (CDE-declared, Y/N)"] == "N"
    assert ver["High Migration Rural (Y/N)"] == "N"
    assert ver["Opportunity Zone (Y/N)"] == "Y"
    assert ver["NMTC Eligible (Y/N)"] == "Y"

"""Crash-safety tests for Pipeline.from_csv().

Covers three categories of user error that must produce friendly error messages
rather than raw tracebacks:
  1. Blank required numeric fields (expected_jobs_created, total_project_cost, etc.)
  2. Blank required string fields (project_id, state, etc.)
  3. Comment rows and empty-template CSV files
"""
from __future__ import annotations

import io
import os
import sys
import tempfile

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from nmtcapp.core.pipeline import Pipeline

# ---------------------------------------------------------------------------
# CSV builder helpers
# ---------------------------------------------------------------------------

_HEADER = (
    "project_id,project_name,qalicb_name,address,city,state,"
    "sector,project_type,total_project_cost,qei_request,qlici_amount,"
    "expected_jobs_created,expected_jobs_retained"
)

_GOOD_ROW = (
    "PRJ-001,Test Project,Test QALICB LLC,123 Main St,Chicago,IL,"
    "healthcare,real_estate,5000000,3500000,3500000,25,5"
)


def _write_csv(rows: list[str]) -> str:
    """Write rows to a temp CSV file and return its path."""
    content = "\n".join([_HEADER] + rows)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline=""
    ) as f:
        f.write(content)
        return f.name


# ---------------------------------------------------------------------------
# Tests: blank required numeric fields
# ---------------------------------------------------------------------------


class TestBlankRequiredNumericFields:
    def test_blank_expected_jobs_created_raises_friendly_error(self):
        """Blank expected_jobs_created must raise a friendly ValueError, not a raw int(nan) crash."""
        row = (
            "PRJ-001,Test Project,Test QALICB LLC,123 Main St,Chicago,IL,"
            "healthcare,real_estate,5000000,3500000,3500000,,5"
        )
        path = _write_csv([row])
        with pytest.raises(ValueError) as exc_info:
            Pipeline.from_csv(path)
        msg = str(exc_info.value)
        assert "expected_jobs_created" in msg
        assert "blank" in msg.lower() or "required" in msg.lower()
        # Must NOT expose the raw Python internals
        assert "cannot convert float NaN" not in msg

    def test_blank_total_project_cost_raises_friendly_error(self):
        """Blank total_project_cost must raise a friendly error, not silently pass NaN."""
        row = (
            "PRJ-001,Test Project,Test QALICB LLC,123 Main St,Chicago,IL,"
            "healthcare,real_estate,,3500000,3500000,25,5"
        )
        path = _write_csv([row])
        with pytest.raises(ValueError) as exc_info:
            Pipeline.from_csv(path)
        msg = str(exc_info.value)
        assert "total_project_cost" in msg
        assert "blank" in msg.lower() or "required" in msg.lower()

    def test_blank_qei_request_raises_friendly_error(self):
        """Blank qei_request must raise a friendly error."""
        row = (
            "PRJ-001,Test Project,Test QALICB LLC,123 Main St,Chicago,IL,"
            "healthcare,real_estate,5000000,,3500000,25,5"
        )
        path = _write_csv([row])
        with pytest.raises(ValueError) as exc_info:
            Pipeline.from_csv(path)
        msg = str(exc_info.value)
        assert "qei_request" in msg

    def test_blank_qlici_amount_raises_friendly_error(self):
        """Blank qlici_amount must raise a friendly error."""
        row = (
            "PRJ-001,Test Project,Test QALICB LLC,123 Main St,Chicago,IL,"
            "healthcare,real_estate,5000000,3500000,,25,5"
        )
        path = _write_csv([row])
        with pytest.raises(ValueError) as exc_info:
            Pipeline.from_csv(path)
        msg = str(exc_info.value)
        assert "qlici_amount" in msg

    def test_blank_expected_jobs_retained_defaults_to_zero(self):
        """Blank expected_jobs_retained must default to 0, not crash."""
        row = (
            "PRJ-001,Test Project,Test QALICB LLC,123 Main St,Chicago,IL,"
            "healthcare,real_estate,5000000,3500000,3500000,25,"
        )
        path = _write_csv([row])
        pipeline = Pipeline.from_csv(path)
        assert len(pipeline) == 1
        project = list(pipeline)[0]
        assert project.expected_jobs_retained == 0

    def test_missing_expected_jobs_retained_column_defaults_to_zero(self):
        """Absent expected_jobs_retained column must default to 0."""
        header = (
            "project_id,project_name,qalicb_name,address,city,state,"
            "sector,project_type,total_project_cost,qei_request,qlici_amount,"
            "expected_jobs_created"
        )
        row = (
            "PRJ-001,Test Project,Test QALICB LLC,123 Main St,Chicago,IL,"
            "healthcare,real_estate,5000000,3500000,3500000,25"
        )
        content = "\n".join([header, row])
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            f.write(content)
            path = f.name
        pipeline = Pipeline.from_csv(path)
        assert list(pipeline)[0].expected_jobs_retained == 0


# ---------------------------------------------------------------------------
# Tests: blank required string fields
# ---------------------------------------------------------------------------


class TestBlankRequiredStringFields:
    def test_blank_project_id_raises_friendly_error(self):
        """Blank project_id must raise a friendly error, not produce 'nan' silently."""
        row = (
            ",Test Project,Test QALICB LLC,123 Main St,Chicago,IL,"
            "healthcare,real_estate,5000000,3500000,3500000,25,5"
        )
        path = _write_csv([row])
        with pytest.raises(ValueError) as exc_info:
            Pipeline.from_csv(path)
        msg = str(exc_info.value)
        assert "project_id" in msg

    def test_blank_state_raises_friendly_error(self):
        """Blank state must raise a friendly error."""
        row = (
            "PRJ-001,Test Project,Test QALICB LLC,123 Main St,Chicago,,"
            "healthcare,real_estate,5000000,3500000,3500000,25,5"
        )
        path = _write_csv([row])
        with pytest.raises(ValueError) as exc_info:
            Pipeline.from_csv(path)
        msg = str(exc_info.value)
        assert "state" in msg

    def test_error_message_includes_project_id(self):
        """The error message must identify the offending row by project_id."""
        row = (
            "PRJ-BAD-ROW,Test Project,Test QALICB LLC,123 Main St,Chicago,IL,"
            "healthcare,real_estate,,3500000,3500000,25,5"
        )
        path = _write_csv([row])
        with pytest.raises(ValueError) as exc_info:
            Pipeline.from_csv(path)
        assert "PRJ-BAD-ROW" in str(exc_info.value)

    def test_valid_row_after_bad_row_still_fails(self):
        """A single bad row should fail even if other rows are good."""
        bad_row = (
            "PRJ-BAD,Test,QALICB LLC,123 Main,Chicago,IL,"
            "healthcare,real_estate,,3500000,3500000,25,5"
        )
        path = _write_csv([_GOOD_ROW, bad_row])
        with pytest.raises(ValueError):
            Pipeline.from_csv(path)


# ---------------------------------------------------------------------------
# Tests: comment rows and empty templates
# ---------------------------------------------------------------------------


class TestCommentRowsAndEmptyTemplates:
    def test_comment_rows_are_skipped(self):
        """Rows where project_id starts with '#' must be skipped silently."""
        comment = "# VALID SECTORS: healthcare | affordable_housing | education"
        path = _write_csv([comment, _GOOD_ROW])
        pipeline = Pipeline.from_csv(path)
        assert len(pipeline) == 1
        assert list(pipeline)[0].project_id == "PRJ-001"

    def test_multiple_comment_rows_skipped(self):
        """Multiple comment rows must all be skipped."""
        comments = [
            "# VALID SECTORS: healthcare | affordable_housing",
            "# VALID PROJECT TYPES: real_estate | operating_business",
            "# closing_target_date format: YYYY-MM-DD",
            "# v1.1 flags (Y/N, optional):",
        ]
        path = _write_csv(comments + [_GOOD_ROW])
        pipeline = Pipeline.from_csv(path)
        assert len(pipeline) == 1

    def test_only_comment_rows_raises_no_data_error(self):
        """A CSV with only comment rows (no data) must raise a friendly 'no rows found' error."""
        comments = [
            "# VALID SECTORS: healthcare | affordable_housing | education",
            "# VALID PROJECT TYPES: real_estate | operating_business",
        ]
        path = _write_csv(comments)
        with pytest.raises(ValueError) as exc_info:
            Pipeline.from_csv(path)
        msg = str(exc_info.value).lower()
        assert "no project rows" in msg or "no data" in msg

    def test_empty_csv_no_data_rows_raises_friendly_error(self):
        """A CSV with only a header row (no data rows) must raise a friendly error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            f.write(_HEADER + "\n")
            path = f.name
        with pytest.raises(ValueError) as exc_info:
            Pipeline.from_csv(path)
        msg = str(exc_info.value).lower()
        assert "no project rows" in msg or "no data" in msg

    def test_template_csv_file_skips_comments_and_parses_ok(self):
        """The actual pipeline_template.csv (comments-only) raises a friendly no-data error."""
        template_path = os.path.join(_REPO_ROOT, "templates", "pipeline_template.csv")
        if not os.path.exists(template_path):
            pytest.skip("pipeline_template.csv not found")
        with pytest.raises(ValueError) as exc_info:
            Pipeline.from_csv(template_path)
        msg = str(exc_info.value).lower()
        # Must NOT be a raw int(nan)/KeyError traceback — must be our friendly message
        assert "cannot convert float nan" not in msg
        assert "no project rows" in msg or "no data" in msg


# ---------------------------------------------------------------------------
# Tests: valid CSV still parses correctly after the fixes
# ---------------------------------------------------------------------------


class TestValidCsvStillParses:
    def test_good_row_parses_correctly(self):
        """A well-formed CSV must still parse without errors."""
        path = _write_csv([_GOOD_ROW])
        pipeline = Pipeline.from_csv(path)
        assert len(pipeline) == 1
        p = list(pipeline)[0]
        assert p.project_id == "PRJ-001"
        assert p.total_project_cost == 5_000_000
        assert p.expected_jobs_created == 25
        assert p.expected_jobs_retained == 5

    def test_sample_strong_csv_parses(self):
        """pipeline_sample_strong.csv must parse without errors after the fix."""
        path = os.path.join(_REPO_ROOT, "templates", "pipeline_sample_strong.csv")
        if not os.path.exists(path):
            pytest.skip("pipeline_sample_strong.csv not found")
        pipeline = Pipeline.from_csv(path)
        assert len(pipeline) > 0

    def test_sample_weak_csv_parses(self):
        """pipeline_sample_weak.csv must parse without errors after the fix."""
        path = os.path.join(_REPO_ROOT, "templates", "pipeline_sample_weak.csv")
        if not os.path.exists(path):
            pytest.skip("pipeline_sample_weak.csv not found")
        pipeline = Pipeline.from_csv(path)
        assert len(pipeline) > 0

    def test_optional_flag_columns_absent_parses_ok(self):
        """A CSV without the v1.1 flag columns must still parse (flags default to None)."""
        header = (
            "project_id,project_name,qalicb_name,address,city,state,"
            "sector,project_type,total_project_cost,qei_request,qlici_amount,"
            "expected_jobs_created"
        )
        row = (
            "PRJ-001,Test Project,Test QALICB LLC,123 Main St,Chicago,IL,"
            "healthcare,real_estate,5000000,3500000,3500000,25"
        )
        content = "\n".join([header, row])
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            f.write(content)
            path = f.name
        pipeline = Pipeline.from_csv(path)
        p = list(pipeline)[0]
        assert p.is_native_area is None
        assert p.is_us_territory is None
        assert p.is_below_market_rate is None

"""Tests for CSV encoding fallback in load_uploaded_pipeline.

Covers: cp1252 / Windows-1252 (default Excel export encoding), smart quotes,
accented characters, byte 0xd2 (the specific byte from the bug report), and
verification that UTF-8 and UTF-8-with-BOM files still parse correctly.
"""
from __future__ import annotations

import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from nmtcapp.core.upload_handler import load_uploaded_pipeline

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HEADER = (
    "project_id,project_name,qalicb_name,address,city,state,"
    "sector,project_type,total_project_cost,qei_request,qlici_amount,"
    "expected_jobs_created"
)

_GOOD_ROW = (
    'PRJ-E001,"{name}","Test QALICB LLC","{address}",'
    "Chicago,IL,healthcare,real_estate,5000000,3500000,3500000,25"
)


def _csv_bytes(name: str, address: str, encoding: str = "cp1252") -> bytes:
    """Build a one-row CSV encoded with the given encoding."""
    content = f"{_HEADER}\n{_GOOD_ROW.format(name=name, address=address)}\n"
    return content.encode(encoding)


def _csv_bytes_raw(header: bytes, row: bytes) -> bytes:
    """Build a CSV from raw bytes (for injecting specific byte values)."""
    return header + b"\n" + row + b"\n"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCsvEncodingFallback:
    """CSV files with non-UTF-8 encoding must be decoded and parsed correctly."""

    def test_cp1252_smart_right_single_quote(self):
        """0x92 (cp1252 right single quotation mark ') must parse without error."""
        csv_bytes = _csv_bytes("St’s Health Center", "100 Main St")
        pipeline, _ = load_uploaded_pipeline(csv_bytes, "pipeline.csv")
        assert len(pipeline) == 1

    def test_cp1252_accented_character(self):
        """0xe9 (cp1252 é) must parse without error."""
        csv_bytes = _csv_bytes("Caf\xe9 Community Center", "200 Broadway")
        pipeline, _ = load_uploaded_pipeline(csv_bytes, "pipeline.csv")
        assert len(pipeline) == 1
        assert list(pipeline)[0].project_id == "PRJ-E001"

    def test_cp1252_byte_0xd2(self):
        """Byte 0xd2 (the byte from the bug report) must not crash the reader."""
        # 0xd2 is Ò in cp1252 (capital O with grave); invalid as a lone UTF-8 byte
        header = _HEADER.encode("ascii")
        row = b'PRJ-E001,"S\xd2rensen HC","Test QALICB LLC","123 Main",Chicago,IL,healthcare,real_estate,5000000,3500000,3500000,25'
        csv_bytes = _csv_bytes_raw(header, row)
        pipeline, _ = load_uploaded_pipeline(csv_bytes, "pipeline.csv")
        assert len(pipeline) == 1

    def test_cp1252_smart_double_quotes(self):
        """0x93/0x94 (cp1252 curly double quotes) must parse without error."""
        csv_bytes = _csv_bytes("Test “Project”", "300 Oak Ave")
        pipeline, _ = load_uploaded_pipeline(csv_bytes, "pipeline.csv")
        assert len(pipeline) == 1

    def test_utf8_csv_still_works(self):
        """Standard UTF-8 CSV must parse as before."""
        csv_bytes = (
            f"{_HEADER}\n"
            "PRJ-U001,UTF8 Project,UTF8 QALICB LLC,123 Main,Chicago,IL,"
            "healthcare,real_estate,5000000,3500000,3500000,25\n"
        ).encode("utf-8")
        pipeline, _ = load_uploaded_pipeline(csv_bytes, "pipeline.csv")
        assert len(pipeline) == 1
        assert list(pipeline)[0].project_id == "PRJ-U001"

    def test_utf8_bom_csv(self):
        """UTF-8 with BOM (common Excel 'CSV UTF-8' export) must parse correctly."""
        csv_bytes = (
            f"{_HEADER}\n"
            "PRJ-B001,BOM Project,BOM QALICB LLC,123 Main,Chicago,IL,"
            "healthcare,real_estate,5000000,3500000,3500000,25\n"
        ).encode("utf-8-sig")
        pipeline, _ = load_uploaded_pipeline(csv_bytes, "pipeline.csv")
        assert len(pipeline) == 1
        assert list(pipeline)[0].project_id == "PRJ-B001"

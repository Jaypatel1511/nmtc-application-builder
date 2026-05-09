"""Tests for Application.generate() method."""
import os
import pytest
from unittest.mock import patch, MagicMock

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline


class TestApplicationGenerate:
    def test_generate_returns_dict(self, sample_application, tmp_path):
        paths = sample_application.generate(output_dir=str(tmp_path), formats=["markdown"])
        assert isinstance(paths, dict)

    def test_generate_markdown_creates_file(self, sample_application, tmp_path):
        paths = sample_application.generate(output_dir=str(tmp_path), formats=["markdown"])
        assert "markdown" in paths
        assert os.path.exists(paths["markdown"])

    def test_generated_markdown_not_empty(self, sample_application, tmp_path):
        paths = sample_application.generate(output_dir=str(tmp_path), formats=["markdown"])
        assert os.path.getsize(paths["markdown"]) > 500

    def test_generate_creates_output_dir(self, sample_application, tmp_path):
        output_dir = str(tmp_path / "new_output_dir")
        sample_application.generate(output_dir=output_dir, formats=["markdown"])
        assert os.path.isdir(output_dir)

    def test_generate_word_creates_docx(self, sample_application, tmp_path):
        pytest.importorskip("docx")
        paths = sample_application.generate(output_dir=str(tmp_path), formats=["word"])
        assert "word" in paths
        assert paths["word"].endswith(".docx")
        assert os.path.exists(paths["word"])

    def test_generate_excel_creates_xlsx(self, sample_application, tmp_path):
        pytest.importorskip("openpyxl")
        paths = sample_application.generate(output_dir=str(tmp_path), formats=["excel"])
        assert "excel" in paths
        assert paths["excel"].endswith(".xlsx")
        assert os.path.exists(paths["excel"])

    def test_generate_pdf_creates_pdf(self, sample_application, tmp_path):
        pytest.importorskip("reportlab")
        paths = sample_application.generate(output_dir=str(tmp_path), formats=["pdf"])
        assert "pdf" in paths
        assert paths["pdf"].endswith(".pdf")
        assert os.path.exists(paths["pdf"])

    def test_generate_default_formats_produces_multiple_files(self, sample_application, tmp_path):
        pytest.importorskip("docx")
        pytest.importorskip("openpyxl")
        pytest.importorskip("reportlab")
        paths = sample_application.generate(output_dir=str(tmp_path))
        assert len(paths) >= 2

    def test_generate_filename_uses_cde_id(self, sample_application, tmp_path):
        paths = sample_application.generate(output_dir=str(tmp_path), formats=["markdown"])
        cde_id = sample_application.cde.cde_id
        assert cde_id in os.path.basename(paths["markdown"])

    def test_generate_skips_unavailable_word(self, sample_application, tmp_path):
        with patch.dict("sys.modules", {"docx": None}):
            # Should not raise, just skip Word
            paths = sample_application.generate(
                output_dir=str(tmp_path), formats=["markdown", "word"]
            )
            assert "markdown" in paths

    def test_generate_empty_formats_list(self, sample_application, tmp_path):
        paths = sample_application.generate(output_dir=str(tmp_path), formats=[])
        assert paths == {}

    def test_generate_unknown_format_ignored(self, sample_application, tmp_path):
        paths = sample_application.generate(
            output_dir=str(tmp_path), formats=["markdown", "unknown_format"]
        )
        assert "markdown" in paths
        assert "unknown_format" not in paths

    def test_generate_reuses_analysis_cache(self, sample_application, tmp_path):
        # First call — primes cache
        _ = sample_application.analyze()
        with patch.object(sample_application, "analyze", wraps=sample_application.analyze) as mock_analyze:
            sample_application.generate(output_dir=str(tmp_path), formats=["markdown"])
            # analyze() should be called once (returns from cache immediately)
            mock_analyze.assert_called_once()

"""Tests for PDFApplicationBuilder."""
import pytest

pytest.importorskip("reportlab", reason="reportlab not installed")

from nmtcapp.renderers.pdf_builder import PDFApplicationBuilder, _df_to_rl_table, _build_styles


class TestPDFBuilder:
    @pytest.fixture
    def builder(self, sample_application, application_analysis):
        return PDFApplicationBuilder(sample_application, application_analysis)

    # ---- Build and save ----

    def test_save_creates_pdf(self, builder, tmp_path):
        import os
        path = str(tmp_path / "application.pdf")
        builder.save(path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 1000

    def test_saved_pdf_starts_with_magic_bytes(self, builder, tmp_path):
        path = str(tmp_path / "application.pdf")
        builder.save(path)
        with open(path, "rb") as f:
            header = f.read(4)
        assert header == b"%PDF"

    def test_save_creates_parent_directory(self, builder, tmp_path):
        import os
        path = str(tmp_path / "subdir" / "application.pdf")
        builder.save(path)
        assert os.path.exists(path)

    # ---- Cover page flowables ----

    def test_cover_page_returns_flowables(self, builder):
        styles = _build_styles()
        flowables = builder._cover_page(styles)
        assert isinstance(flowables, list)
        assert len(flowables) > 3

    # ---- Executive summary flowables ----

    def test_executive_summary_returns_flowables(self, builder):
        styles = _build_styles()
        flowables = builder._executive_summary(styles)
        assert isinstance(flowables, list)
        assert len(flowables) > 2

    # ---- Appendix flowables ----

    def test_appendix_returns_flowables(self, builder):
        import pandas as pd
        styles = _build_styles()
        df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
        flowables = builder._appendix("Appendix A: Test", df, styles)
        assert len(flowables) >= 2  # heading + table

    def test_appendix_empty_df_does_not_crash(self, builder):
        import pandas as pd
        styles = _build_styles()
        flowables = builder._appendix("Appendix X", pd.DataFrame(), styles)
        assert isinstance(flowables, list)

    # ---- Methodology flowables ----

    def test_methodology_returns_flowables(self, builder):
        styles = _build_styles()
        flowables = builder._methodology(styles)
        assert len(flowables) >= 2

    def test_methodology_mentions_eligibility(self, builder):
        from reportlab.platypus import Paragraph
        styles = _build_styles()
        flowables = builder._methodology(styles)
        texts = " ".join(
            f.text if hasattr(f, "text") else ""
            for f in flowables
        )
        assert "ELIGIBILITY" in texts or "eligib" in texts.lower()


class TestPDFImportError:
    def test_raises_if_reportlab_missing(self, sample_application, application_analysis,
                                          monkeypatch):
        import nmtcapp.renderers.pdf_builder as mod
        monkeypatch.setattr(mod, "_REPORTLAB_AVAILABLE", False)
        with pytest.raises(ImportError, match="reportlab"):
            PDFApplicationBuilder(sample_application, application_analysis)


class TestBuildStyles:
    def test_returns_dict(self):
        styles = _build_styles()
        assert isinstance(styles, dict)

    def test_has_required_keys(self):
        styles = _build_styles()
        for key in ("h1", "h2", "body", "caption", "footer"):
            assert key in styles


class TestDfToRlTable:
    def test_empty_df_returns_caption(self):
        import pandas as pd
        styles = _build_styles()
        flowables = _df_to_rl_table(pd.DataFrame(), styles)
        assert len(flowables) == 1

    def test_none_returns_caption(self):
        styles = _build_styles()
        flowables = _df_to_rl_table(None, styles)
        assert len(flowables) == 1

    def test_df_returns_table_flowable(self):
        import pandas as pd
        from reportlab.platypus import Table
        styles = _build_styles()
        df = pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})
        flowables = _df_to_rl_table(df, styles)
        assert any(isinstance(f, Table) for f in flowables)

    def test_max_rows_adds_caption(self):
        import pandas as pd
        styles = _build_styles()
        df = pd.DataFrame({"A": range(50)})
        flowables = _df_to_rl_table(df, styles, max_rows=5)
        # Caption should mention row count
        from reportlab.platypus import Paragraph
        captions = [f for f in flowables if isinstance(f, Paragraph)]
        assert any("5 of 50" in (f.text or "") for f in captions)

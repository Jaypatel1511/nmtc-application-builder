"""Tests for MarkdownApplicationBuilder."""
import pytest

from nmtcapp.renderers.markdown_builder import MarkdownApplicationBuilder, _df_to_md


class TestMarkdownBuilder:
    @pytest.fixture
    def builder(self, sample_application, application_analysis):
        return MarkdownApplicationBuilder(sample_application, application_analysis)

    @pytest.fixture
    def md(self, builder):
        return builder.build()

    # ---- Structural checks ----

    def test_build_returns_string(self, md):
        assert isinstance(md, str)

    def test_build_is_nonempty(self, md):
        assert len(md) > 500

    def test_contains_cover_title(self, md):
        assert "NEW MARKETS TAX CREDIT" in md

    def test_contains_cde_name(self, md, sample_application):
        assert sample_application.cde.name in md

    def test_contains_executive_summary(self, md):
        assert "Executive Summary" in md

    def test_contains_table_of_contents(self, md):
        assert "Table of Contents" in md

    def test_contains_all_section_headers(self, md):
        for letter in ("A", "B", "C", "D", "E"):
            assert f"Section {letter}" in md

    def test_contains_all_appendices(self, md):
        for label in ("Appendix A", "Appendix B", "Appendix C", "Appendix D", "Appendix E"):
            assert label in md

    def test_contains_methodology_note(self, md):
        assert "Methodology" in md

    def test_contains_readiness_grade(self, md, application_analysis):
        assert f"Grade {application_analysis.readiness_score.grade}" in md

    def test_sections_separated_by_horizontal_rule(self, md):
        assert "---" in md

    # ---- TOC links ----

    def test_toc_has_all_sections(self, builder):
        toc = builder._toc()
        for letter in ("A", "B", "C", "D", "E"):
            assert f"Section {letter}" in toc

    def test_toc_has_appendix_links(self, builder):
        toc = builder._toc()
        assert "Appendix A" in toc

    # ---- Cover ----

    def test_cover_contains_allocation(self, builder, sample_application):
        cover = builder._cover()
        assert f"${sample_application.requested_allocation:,.0f}" in cover

    def test_cover_contains_round(self, builder, sample_application):
        # THE COVER STATES THE ROUND FIELD, WHATEVER IT HOLDS (1.5.5 T1).
        # This asserted `sample_application.application_round in cover`, and
        # sample_application takes the default -- which used to be the string
        # "CY2025", a round the CDFI Fund has never run. The assertion passed
        # BECAUSE the defect was there. With no default to invent one the
        # cover renders the disclosure instead, and that is what a cover
        # generated from an Application with no round must carry.
        from nmtcapp.core.application_round import round_label
        cover = builder._cover()
        assert sample_application.application_round is None
        assert round_label(sample_application.application_round) in cover

    # ---- Executive summary ----

    def test_executive_summary_has_distress_pct(self, builder):
        es = builder._executive_summary()
        assert "%" in es

    def test_executive_summary_has_strengths_section(self, builder):
        es = builder._executive_summary()
        assert "Strengths" in es or "strength" in es.lower()

    # ---- Save to file ----

    def test_save_creates_file(self, builder, tmp_path):
        path = str(tmp_path / "application.md")
        builder.save(path)
        import os
        assert os.path.exists(path)
        assert os.path.getsize(path) > 100

    def test_save_content_matches_build(self, builder, tmp_path):
        path = str(tmp_path / "application.md")
        builder.save(path)
        with open(path) as f:
            content = f.read()
        assert content == builder.build()


class TestDfToMd:
    def test_empty_df_returns_placeholder(self):
        import pandas as pd
        result = _df_to_md(pd.DataFrame())
        assert "No data" in result or "_" in result

    def test_none_returns_placeholder(self):
        result = _df_to_md(None)
        assert "No data" in result or "_" in result

    def test_header_row_present(self):
        import pandas as pd
        df = pd.DataFrame({"Col A": [1, 2], "Col B": ["x", "y"]})
        md = _df_to_md(df)
        assert "Col A" in md
        assert "Col B" in md

    def test_separator_row_present(self):
        import pandas as pd
        df = pd.DataFrame({"A": [1]})
        md = _df_to_md(df)
        assert "---" in md

    def test_max_rows_respected(self):
        import pandas as pd
        df = pd.DataFrame({"A": range(100)})
        md = _df_to_md(df, max_rows=5)
        assert "Showing 5 of 100 rows" in md

    def test_pipe_chars_escaped(self):
        import pandas as pd
        df = pd.DataFrame({"A": ["foo|bar"]})
        md = _df_to_md(df)
        assert "foo\\|bar" in md

    def test_float_formatting(self):
        import pandas as pd
        df = pd.DataFrame({"Val": [1234567.89]})
        md = _df_to_md(df)
        assert "1,234,567.89" in md or "1234567" in md

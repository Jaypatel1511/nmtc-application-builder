"""Tests for Section A–E content generators."""
import pytest

from nmtcapp.sections import ALL_SECTIONS
from nmtcapp.sections.base import SectionGenerator
from nmtcapp.sections.section_a_business import SectionABusinessStrategy
from nmtcapp.sections.section_b_outcomes import SectionBCommunityOutcomes
from nmtcapp.sections.section_c_management import SectionCManagementCapacity
from nmtcapp.sections.section_d_capitalization import SectionDCapitalizationStrategy
from nmtcapp.sections.section_e_prior_awards import SectionEPriorAwards


# ---------------------------------------------------------------------------
# ALL_SECTIONS registry
# ---------------------------------------------------------------------------

class TestAllSections:
    def test_has_five_sections(self):
        assert len(ALL_SECTIONS) == 5

    def test_all_sections_are_generators(self):
        for s in ALL_SECTIONS:
            assert isinstance(s, SectionGenerator)

    def test_section_ids_are_unique(self):
        ids = [s.section_id for s in ALL_SECTIONS]
        assert len(set(ids)) == 5

    def test_section_ids_are_a_through_e(self):
        ids = {s.section_id for s in ALL_SECTIONS}
        assert ids == {"A", "B", "C", "D", "E"}


# ---------------------------------------------------------------------------
# Section A
# ---------------------------------------------------------------------------

class TestSectionA:
    @pytest.fixture
    def content(self, sample_application, application_analysis):
        return SectionABusinessStrategy().generate_content(sample_application, application_analysis)

    def test_section_id(self, content):
        assert content["section_id"] == "A"

    def test_has_subsections(self, content):
        assert len(content["subsections"]) >= 4

    def test_investment_thesis_is_narrative(self, content):
        thesis = next(s for s in content["subsections"] if "thesis" in s["heading"].lower())
        assert thesis["type"] == "narrative"
        assert len(thesis["body"]) > 50

    def test_pipeline_overview_is_dict(self, content):
        overview = next(s for s in content["subsections"] if "pipeline" in s["heading"].lower())
        assert isinstance(overview["body"], dict)
        assert len(overview["body"]) >= 4

    def test_pipeline_overview_contains_project_count(self, content):
        overview = next(s for s in content["subsections"] if "pipeline" in s["heading"].lower())
        combined = " ".join(str(v) for v in overview["body"].values())
        assert any(c.isdigit() for c in combined)

    def test_target_markets_mentions_states(self, content):
        target = next(s for s in content["subsections"] if "target" in s["heading"].lower())
        assert len(str(target["body"])) > 20

    def test_markdown_generation(self, sample_application, application_analysis):
        md = SectionABusinessStrategy().generate_markdown(sample_application, application_analysis)
        assert "Section A" in md
        assert "Business Strategy" in md

    def test_word_generation_does_not_raise(self, sample_application, application_analysis):
        from docx import Document
        doc = Document()
        SectionABusinessStrategy().generate_word(doc, sample_application, application_analysis)
        # Verify content was added
        assert len(doc.paragraphs) > 0


# ---------------------------------------------------------------------------
# Section B
# ---------------------------------------------------------------------------

class TestSectionB:
    @pytest.fixture
    def content(self, sample_application, application_analysis):
        return SectionBCommunityOutcomes().generate_content(sample_application, application_analysis)

    def test_section_id(self, content):
        assert content["section_id"] == "B"

    def test_impact_subsection_exists(self, content):
        headings = [s["heading"] for s in content["subsections"]]
        assert any("impact" in h.lower() or "outcome" in h.lower() or "community" in h.lower()
                   for h in headings)

    def test_distress_commitment_is_table_ref(self, content):
        distress = next(
            (s for s in content["subsections"] if "distress" in s["heading"].lower()), None
        )
        assert distress is not None
        assert distress["type"] in ("table_ref", "narrative")

    def test_body_text_not_empty(self, content):
        for sub in content["subsections"]:
            assert sub.get("body") is not None


# ---------------------------------------------------------------------------
# Section C
# ---------------------------------------------------------------------------

class TestSectionC:
    @pytest.fixture
    def content(self, sample_application, application_analysis):
        return SectionCManagementCapacity().generate_content(sample_application, application_analysis)

    def test_section_id(self, content):
        assert content["section_id"] == "C"

    def test_governance_subsection_has_dict(self, content):
        gov = next(
            (s for s in content["subsections"] if "governance" in s["heading"].lower()), None
        )
        assert gov is not None
        assert isinstance(gov["body"], dict)

    def test_underwriting_subsection_exists(self, content):
        headings = [s["heading"].lower() for s in content["subsections"]]
        assert any("underwrite" in h or "due diligence" in h or "process" in h for h in headings)


# ---------------------------------------------------------------------------
# Section D
# ---------------------------------------------------------------------------

class TestSectionD:
    @pytest.fixture
    def content(self, sample_application, application_analysis):
        return SectionDCapitalizationStrategy().generate_content(sample_application, application_analysis)

    def test_section_id(self, content):
        assert content["section_id"] == "D"

    def test_deal_economics_is_dict(self, content):
        econ = next(
            (s for s in content["subsections"] if "economics" in s["heading"].lower() or
             "deal" in s["heading"].lower()), None
        )
        assert econ is not None
        assert isinstance(econ["body"], dict)

    def test_deal_economics_has_qei(self, content):
        econ = next(
            s for s in content["subsections"]
            if isinstance(s["body"], dict) and any("qei" in k.lower() for k in s["body"])
        )
        assert any("qei" in k.lower() for k in econ["body"])


# ---------------------------------------------------------------------------
# Section E — with and without prior awards
# ---------------------------------------------------------------------------

class TestSectionE:
    @pytest.fixture
    def content_no_awards(self, sample_application, application_analysis):
        from nmtcapp.core.cde import CDEProfile
        from nmtcapp.core.application import Application
        cde_no_awards = CDEProfile(
            name="No Awards CDE", cde_id="no-awards", certification_date="2020-01-01",
            mission="test", contact={}, target_markets=["IL"], prior_awards=[], governance={},
        )
        app = Application(cde=cde_no_awards, requested_allocation=10_000_000)
        app.add_pipeline(sample_application.pipeline)
        return SectionEPriorAwards().generate_content(app, application_analysis)

    def test_section_id(self, content_no_awards):
        assert content_no_awards["section_id"] == "E"

    def test_no_awards_message(self, content_no_awards):
        body = content_no_awards["subsections"][0]["body"]
        assert "first" in body.lower() or "not received" in body.lower() or "no prior" in body.lower()

    def test_with_prior_awards(self, sample_application, application_analysis):
        content = SectionEPriorAwards().generate_content(sample_application, application_analysis)
        assert content["section_id"] == "E"
        # sample CDE has prior_awards in CDEProfile.sample()
        headings = [s["heading"] for s in content["subsections"]]
        assert len(headings) >= 1


# ---------------------------------------------------------------------------
# Base class / interface
# ---------------------------------------------------------------------------

class TestSectionGeneratorBase:
    def test_word_limit_is_positive(self):
        for s in ALL_SECTIONS:
            assert s.word_limit > 0

    def test_title_is_nonempty(self):
        for s in ALL_SECTIONS:
            assert s.title and len(s.title) > 3

    def test_generate_content_returns_required_keys(self, sample_application, application_analysis):
        for s in ALL_SECTIONS:
            content = s.generate_content(sample_application, application_analysis)
            assert "section_id" in content
            assert "title" in content
            assert "subsections" in content
            assert isinstance(content["subsections"], list)

    def test_generate_markdown_returns_string(self, sample_application, application_analysis):
        for s in ALL_SECTIONS:
            md = s.generate_markdown(sample_application, application_analysis)
            assert isinstance(md, str)
            assert len(md) > 100

    def test_generate_markdown_contains_section_header(self, sample_application, application_analysis):
        for s in ALL_SECTIONS:
            md = s.generate_markdown(sample_application, application_analysis)
            assert f"Section {s.section_id}" in md

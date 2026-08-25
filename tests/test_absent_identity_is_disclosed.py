"""T1c (1.6.0): an absent identity value is DISCLOSED, never rendered blank.

THE PACKAGE'S ESTABLISHED PATTERN, APPLIED WHERE IT WAS NOT.

``sections/base`` ships ``_cde_todo`` for exactly this: "wherever the tool
would otherwise assert something it cannot derive from the CDE's own inputs".
``section_c_management`` already uses ``"N/A"`` for every governance row it
lacks, and ``_compliance_statement`` already refuses to claim a clean record
it was not told about. Three renders did not follow it, and on an xlsx upload
-- where those fields were guaranteed absent before T1 -- they produced this,
in a federal filing draft, measured at 9a2d584::

    (your CDE) was certified as a Community Development Entity by the CDFI
    Fund on . Since certification, ...

    (your CDE)'s stated mission is: ""

    **CDE Certification Date:**

CHECKED, NOT ASSUMED (this round's own hypothesis 3). A fourth candidate --
``Primary geographic targets:`` -- reads from the PIPELINE's states, not from
``cde.target_markets``, and rendered ``NC, SC, TN, VA, WV`` correctly on the
same document. It is not a symptom of the strip and is not changed here.

T1 REMOVES THE COMMON CASE AND NOT THE DEFECT. After T1 an xlsx upload
supplies all three, so the shipped path stops producing them. A CDE may still
leave any single cell blank, and the YAML path has always been able to reach
here with a blank one, so these are fixed on their own terms rather than
declared solved by T1.

AND T1 ESCALATES A FOURTH ONE. "the organization has received 0 NMTC
allocation awards totaling $0" was, at 9a2d584, a sentence about ``(your
CDE)`` -- a placeholder nobody could mistake for an applicant. After T1 it is
a sentence about a NAMED CDE, and the xlsx path has no ``prior_awards``
column, so it says $0 to a CDE that typed ``Prior Award Count: 1`` two cells
away. A false quantitative claim about a named applicant is a different thing
from the same words about a placeholder, so it is disclosed here.
"""
from __future__ import annotations

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline
from nmtcapp.sections.section_a_business import SectionABusinessStrategy
from nmtcapp.sections.section_c_management import SectionCManagementCapacity


def _cde(**overrides) -> CDEProfile:
    base = dict(
        name="Cardinal Ridge Community Capital, LLC",
        cde_id="CDE-2020-0431",
        certification_date="2020-09-14",
        mission="Deploy NMTC capital into persistently distressed rural communities.",
        target_markets=["North Carolina"],
        prior_awards=[],
        contact={"name": "A. Reyes", "email": "areyes@cardinalridgecapital.org"},
        governance={"board_members": 7, "community_representatives": 3},
    )
    base.update(overrides)
    return CDEProfile(**base)


def _analysis(cde: CDEProfile):
    app = Application(cde=cde, requested_allocation=55_000_000)
    app.add_pipeline(Pipeline.sample(n=6))
    return app, app.analyze()


def _text(content) -> str:
    """Flatten a section's content dict to one searchable string."""
    out = []

    def walk(value):
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, dict):
            for k, v in value.items():
                out.append(str(k))
                walk(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                walk(v)
        else:
            out.append(str(value))

    walk(content)
    return "\n".join(out)


class TestAnAbsentCertificationDate:
    def test_the_history_narrative_does_not_render_an_empty_date(self):
        cde = _cde(certification_date="")
        app, analysis = _analysis(cde)
        text = _text(SectionCManagementCapacity().generate_content(app, analysis))
        assert "by the CDFI Fund on ." not in text, (
            "Section C rendered 'certified ... by the CDFI Fund on .' -- an "
            "empty value printed mid-sentence. The package's pattern is to "
            "DISCLOSE an absent value, never to render it blank."
        )

    def test_the_history_narrative_names_what_is_missing(self):
        cde = _cde(certification_date="")
        app, analysis = _analysis(cde)
        text = _text(SectionCManagementCapacity().generate_content(app, analysis))
        assert "State the date the CDFI Fund certified this CDE" in text, (
            "the absence was not named. A generic placeholder elsewhere in "
            "the section is not a disclosure OF THIS FIELD."
        )

    def test_a_supplied_date_still_renders(self):
        app, analysis = _analysis(_cde())
        text = _text(SectionCManagementCapacity().generate_content(app, analysis))
        assert "by the CDFI Fund on 2020-09-14." in text

    def test_the_governance_table_row_is_not_blank(self):
        cde = _cde(certification_date="")
        app, analysis = _analysis(cde)
        content = SectionCManagementCapacity().generate_content(app, analysis)
        table = next(sub["body"] for sub in content["subsections"]
                     if sub["heading"].startswith("Governance"))
        row = table["CDE Certification Date"]
        assert row and str(row).strip(), (
            "the governance table's certification-date row rendered empty. "
            "Every other row in that dict discloses with 'N/A'."
        )


class TestAnAbsentMission:
    def test_no_empty_quoted_mission_is_rendered(self):
        cde = _cde(mission="")
        app, analysis = _analysis(cde)
        text = _text(SectionABusinessStrategy().generate_content(app, analysis))
        assert 'stated mission is: ""' not in text, (
            "Section A rendered an empty quoted mission. A pair of quotation "
            "marks around nothing is not a disclosure."
        )

    def test_the_absence_is_named(self):
        cde = _cde(mission="")
        app, analysis = _analysis(cde)
        text = _text(SectionABusinessStrategy().generate_content(app, analysis))
        assert "State this CDE's mission" in text, (
            "the absence was not named. A generic placeholder elsewhere in "
            "the section is not a disclosure OF THIS FIELD."
        )

    def test_a_supplied_mission_still_renders_quoted(self):
        app, analysis = _analysis(_cde())
        text = _text(SectionABusinessStrategy().generate_content(app, analysis))
        assert 'stated mission is: "Deploy NMTC capital' in text


class TestPriorAwardsThatWereDeclaredButNotDetailed:
    """The xlsx path collects a COUNT and no award list.

    ``Prior Award Count`` is a scoring attr; ``prior_awards`` is the list
    Section C narrates. A CDE that states the count still has an empty list,
    and Section C asserted the list's arithmetic as fact about a named CDE.
    """

    def test_a_declared_count_is_not_contradicted_by_the_narrative(self):
        cde = _cde()
        cde.extra = {"prior_award_count": 1}
        app, analysis = _analysis(cde)
        text = _text(SectionCManagementCapacity().generate_content(app, analysis))
        assert "received 0 NMTC allocation awards totaling $0" not in text, (
            "Section C told a CDE that declared 1 prior award that it had "
            "received 0, totalling $0. The count and the list come off "
            "different inputs and the section may not assert the list's "
            "arithmetic over the CDE's own declaration."
        )

    def test_the_disagreement_is_disclosed(self):
        cde = _cde()
        cde.extra = {"prior_award_count": 1}
        app, analysis = _analysis(cde)
        text = _text(SectionCManagementCapacity().generate_content(app, analysis))
        assert "Supply the year, amount and deployment status" in text, (
            "the disagreement was not named. A generic placeholder elsewhere "
            "in the section is not a disclosure OF THIS ONE."
        )

    def test_a_first_time_applicant_is_unaffected(self):
        """No declared count and no list: [] is a complete answer."""
        app, analysis = _analysis(_cde())
        text = _text(SectionCManagementCapacity().generate_content(app, analysis))
        assert "received 0 NMTC allocation awards totaling $0" in text

    def test_a_detailed_list_still_narrates_its_own_arithmetic(self):
        cde = _cde(prior_awards=[
            {"year": 2021, "amount": 40_000_000, "deployment_status": "fully_deployed"},
        ])
        cde.extra = {"prior_award_count": 1}
        app, analysis = _analysis(cde)
        text = _text(SectionCManagementCapacity().generate_content(app, analysis))
        assert "received 1 NMTC allocation awards totaling $40,000,000" in text

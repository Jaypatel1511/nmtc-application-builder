"""T1 (1.6.1): Sections C and E must implement ONE ruling on the prior-award count.

THE DEFECT, MEASURED AT fc34af5 (= v1.6.0).

A CDE's prior NMTC allocation history reaches the generated application from
TWO inputs that can disagree:

    cde.prior_awards               the detailed list
    cde.extra["prior_award_count"] a SCORED attribute, and on the xlsx path
                                   the ONLY one of the two a CDE can supply

1.6.0 taught ONE of the two sections that narrate it to compare them.
``section_c_management`` compares in every case. ``section_e_prior_awards``
read the count INSIDE its ``if not awards:`` branch only, so a non-empty list
fell straight through to ``total_prior = cde.total_prior_allocation()`` and
narrated the list with no comparison at all. Executed, one detailed award
against a declared count of 4, in ONE document::

    Section C  "This CDE's profile declares 4 prior NMTC allocation awards,
                and 1 is detailed ... [CDE TO COMPLETE: ...]"      <- discloses
    Section E  "... has 1 prior NMTC allocation awards totaling $45,000,000,
                of which 1 are recorded as fully deployed."    <- asserts as
                                                                  the whole
                                                                  history

At 9a2d584 NEITHER section looked, so they agreed by not looking. 1.6.0 taught
one of them to look, and that is what put a contradiction about a named CDE's
federal award history inside one document.

WHAT IS ASSERTED HERE, AND WHY IT IS THE CROSS-SECTION SHAPE.

The load-bearing test is not "Section E says X". It is that the two sections
REACH THE SAME VERDICT on the same input -- because a per-section assertion is
exactly what 1.6.0 had, and it passed while the two disagreed. Each section
still says its own thing around that verdict: C narrates certification
history, E narrates the award table.

``[]`` IS AN ANSWER AND MUST STAY ONE. ``core.cde`` documents at length that
an empty ``prior_awards`` list is a CDE affirmatively stating it has no prior
allocation, and that 1.3.0 B3 fixed a validator that pressured a user toward a
false statement about its own history. Over-hedging is a defect in the other
direction, so the first-time-applicant cases are asserted POSITIVELY here, not
merely left alone.

THE EIGHT PAIRS are the ones the 1.6.1 audit executed. Seven of them render
byte-identically to fc34af5; ``1 award + 4`` is the one that moves.
"""
from __future__ import annotations

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline
from nmtcapp.sections.base import (
    _declared_prior_award_count,
    _prior_awards_disagree,
)
from nmtcapp.sections.section_c_management import SectionCManagementCapacity
from nmtcapp.sections.section_e_prior_awards import SectionEPriorAwards

#: One fully-deployed award. The amount is the audit's, so the rendered strings
#: below are the ones it read.
ONE_AWARD = [{"year": 2021, "amount": 45_000_000,
              "deployment_status": "fully_deployed"}]

#: "the CDE declared no count", distinct from a declared 0. Not None, because
#: ``{"prior_award_count": None}`` is a different input from an absent key and
#: both must reach the same answer.
ABSENT = "<<absent>>"

#: (label, prior_awards, declared count, do the two disagree?)
#:
#: ``[] + blank`` is a cell the CDE left empty, which is NOT a declared zero
#: and NOT a declared anything -- it agrees with an empty list because there is
#: nothing to disagree with, not because it was read as 0.
PAIRS = [
    ("[] + absent",      [],        ABSENT, False),
    ("[] + 0",           [],        0,      False),
    ("[] + blank",       [],        "",     False),
    ("[] + 1",           [],        1,      True),
    ("[] + 3",           [],        3,      True),
    ("1 award + absent", ONE_AWARD, ABSENT, False),
    ("1 award + 1",      ONE_AWARD, 1,      False),
    ("1 award + 4",      ONE_AWARD, 4,      True),
]

_IDS = [p[0] for p in PAIRS]

#: The pairs where the two inputs disagree, as their own list.
#:
#: NOT a ``pytest.skip`` inside the full sweep. SKIP HEADROOM IN THIS PACKAGE
#: IS EXACTLY ZERO -- 57 measured against ``MAX_SDIST_SKIPS = 57`` in
#: tests/test_release_floor.py -- so a test module that adds a skipping case
#: breaches a ceiling this repository has declined to raise four times. A
#: filtered parametrize asserts the same thing and skips nothing.
DISAGREEING = [p for p in PAIRS if p[3]]
_DISAGREEING_IDS = [p[0] for p in DISAGREEING]


def _cde(awards, declared) -> CDEProfile:
    cde = CDEProfile(
        name="Cardinal Ridge Community Capital, LLC",
        cde_id="CDE-2020-0431",
        certification_date="2020-09-14",
        mission="Deploy NMTC capital into persistently distressed rural communities.",
        target_markets=["North Carolina"],
        prior_awards=[dict(a) for a in awards],
        contact={"name": "A. Reyes", "email": "areyes@cardinalridgecapital.org"},
        governance={"board_members": 7, "community_representatives": 3},
    )
    cde.extra = {} if declared is ABSENT else {"prior_award_count": declared}
    return cde


def _render(cde):
    """Both sections' narrative text, from one Application, as (section_c, section_e)."""
    app = Application(cde=cde, requested_allocation=55_000_000)
    app.add_pipeline(Pipeline.sample(n=6))
    analysis = app.analyze()

    def narrative(content):
        return "\n".join(
            sub["body"] for sub in content["subsections"]
            if sub["type"] == "narrative" and isinstance(sub["body"], str)
        )

    return (
        narrative(SectionCManagementCapacity().generate_content(app, analysis)),
        narrative(SectionEPriorAwards().generate_content(app, analysis)),
    )


#: The phrase each section prints when it has ruled that the two inputs
#: disagree. Both are ``_cde_todo`` blocks; neither section may go quiet.
_C_DISCLOSES = "The declared count and the detailed list disagree"
_E_DISCLOSES_EMPTY = "will not state that this is a first application"
_E_DISCLOSES_DETAILED = "nothing here states this CDE's full deployment history"


class TestThePredicate:
    """The one predicate, on its own, before either section is involved."""

    @pytest.mark.parametrize("label,awards,declared,disagrees", PAIRS, ids=_IDS)
    def test_the_predicate_answers_the_pair(self, label, awards, declared, disagrees):
        assert _prior_awards_disagree(_cde(awards, declared)) is disagrees

    def test_an_absent_count_is_not_a_declared_zero(self):
        """Both reach 'no disagreement', and they must do so for different reasons."""
        assert _declared_prior_award_count(_cde([], ABSENT)) is None
        assert _declared_prior_award_count(_cde([], 0)) == 0

    @pytest.mark.parametrize("junk", ["", "   ", "four", None, [], {}])
    def test_a_count_that_is_not_a_whole_number_is_not_a_declaration(self, junk):
        """A cell that cannot be read as a count may not be read as a claim."""
        assert _declared_prior_award_count(_cde([], junk)) is None
        assert _prior_awards_disagree(_cde([], junk)) is False

    def test_a_numeric_string_is_a_declaration(self):
        """The xlsx path can deliver '3'; that is the CDE answering."""
        assert _declared_prior_award_count(_cde([], "3")) == 3
        assert _prior_awards_disagree(_cde([], "3")) is True


class TestTheTwoSectionsImplementOneRuling:
    """THE LOAD-BEARING GATE. Per-section assertions are what 1.6.0 already had.

    Both sections may say different things; neither may reach a different
    VERDICT about the same CDE's award history in the same document.
    """

    @pytest.mark.parametrize("label,awards,declared,disagrees", PAIRS, ids=_IDS)
    def test_both_sections_reach_the_same_verdict(
        self, label, awards, declared, disagrees
    ):
        section_c, section_e = _render(_cde(awards, declared))
        c_disclosed = _C_DISCLOSES in section_c
        e_disclosed = (
            _E_DISCLOSES_EMPTY in section_e or _E_DISCLOSES_DETAILED in section_e
        )
        assert c_disclosed == e_disclosed == disagrees, (
            f"pair {label!r}: Section C {'discloses' if c_disclosed else 'does not'}, "
            f"Section E {'discloses' if e_disclosed else 'does not'}, and the "
            f"two inputs {'do' if disagrees else 'do not'} disagree.\n\n"
            "These two sections narrate ONE fact about ONE named CDE's federal "
            "award history and ship in ONE document. Whatever each says around "
            "it, they may not rule differently on whether the CDE's own profile "
            "contradicts itself.\n\n"
            f"--- SECTION C ---\n{section_c[:600]}\n\n"
            f"--- SECTION E ---\n{section_e[:600]}"
        )

    @pytest.mark.parametrize("label,awards,declared,disagrees", DISAGREEING,
                             ids=_DISAGREEING_IDS)
    def test_neither_section_adopts_the_count_as_the_answer(
        self, label, awards, declared, disagrees
    ):
        """THE LIST STILL GOVERNS WHERE IT EXISTS -- Section C's ruling, both places.

        The count carries no year, no amount and no deployment status, so
        neither section may narrate a total or a deployment count derived from
        it. With one award of $45,000,000 detailed and four declared, no
        section may print a figure for the other three.

        Parametrised over the DISAGREEING pairs only -- the agreeing ones have
        nothing to adopt, and filtering the list is how that is said without
        adding a skip. See DISAGREEING above.
        """
        section_c, section_e = _render(_cde(awards, declared))
        expected_total = sum(a["amount"] for a in awards)
        for name, text in (("C", section_c), ("E", section_e)):
            assert f"{declared} NMTC allocation awards totaling" not in text, (
                f"Section {name} narrated the DECLARED count as though the "
                "list backed it. The count carries no amount."
            )
            if awards:
                assert f"${expected_total:,.0f}" in text or name == "C", (
                    f"Section {name} dropped the figure the list does support"
                )


class TestTheDisagreementOnANonEmptyList:
    """The pair the ruling was missing. 1 detailed award, 4 declared."""

    @pytest.fixture
    def rendered(self):
        return _render(_cde(ONE_AWARD, 4))

    def test_section_e_no_longer_asserts_the_list_as_the_whole_history(self, rendered):
        _, section_e = rendered
        assert "has 1 prior NMTC allocation awards totaling $45,000,000" not in section_e, (
            "Section E stated the detailed list as this CDE's complete "
            "allocation history, in the section the CDFI Fund reads for "
            "deployment history, against a profile declaring four. Section C "
            "disclosed the same disagreement in the same document."
        )

    def test_section_e_names_the_disagreement_and_what_is_missing(self, rendered):
        _, section_e = rendered
        assert "declares 4 prior NMTC allocation awards" in section_e
        assert "1 is detailed" in section_e
        assert _E_DISCLOSES_DETAILED in section_e

    def test_the_figures_that_survive_are_scoped_to_the_awards_they_came_from(
        self, rendered
    ):
        """The list governs where it exists: its own arithmetic still prints,
        as the subtotal it is rather than as the history it is not."""
        _, section_e = rendered
        assert "The figures below cover only that one: $45,000,000 allocated" in section_e

    def test_the_award_table_still_renders(self):
        """Disclosing the disagreement may not delete the detail that exists."""
        cde = _cde(ONE_AWARD, 4)
        app = Application(cde=cde, requested_allocation=55_000_000)
        app.add_pipeline(Pipeline.sample(n=6))
        content = SectionEPriorAwards().generate_content(app, app.analyze())
        rows = next(s["body"] for s in content["subsections"] if s["type"] == "list")
        assert len(rows) == 1
        assert "$45,000,000" in rows[0]


class TestEmptyListIsStillAnAnswer:
    """1.3.0 B3's ruling, asserted positively so the fix cannot over-hedge."""

    @pytest.mark.parametrize("declared", [ABSENT, 0, "", "   ", "0"],
                             ids=["absent", "zero", "blank", "whitespace", "zero-string"])
    def test_a_genuine_first_time_applicant_still_says_so(self, declared):
        section_c, section_e = _render(_cde([], declared))
        assert "This is our first allocation application" in section_e, (
            "a CDE with no prior allocation and no contradicting declaration "
            "was hedged out of saying so. An empty prior_awards list IS the "
            "answer -- see CDE_FIELDS_WHERE_EMPTY_IS_AN_ANSWER."
        )
        assert "received 0 NMTC allocation awards totaling $0" in section_c

    @pytest.mark.parametrize("declared", [1, 3])
    def test_a_contradicted_first_application_is_withheld(self, declared):
        _, section_e = _render(_cde([], declared))
        assert "This is our first allocation application" not in section_e
        assert _E_DISCLOSES_EMPTY in section_e


class TestTheRulingIsStatedOnce:
    """No third position, and no fourth hand-maintained copy of the reasoning."""

    def test_both_sections_import_the_shared_predicate(self):
        import nmtcapp.sections.section_c_management as sec_c
        import nmtcapp.sections.section_e_prior_awards as sec_e
        for module in (sec_c, sec_e):
            assert module._prior_awards_disagree is _prior_awards_disagree, (
                f"{module.__name__} does not read the shared predicate. Two "
                "copies of this reasoning is what put a contradiction in one "
                "document; see REQUIRED_CDE_FIELDS for what the third copy of "
                "a list cost."
            )

    def test_neither_section_re_derives_the_count_from_extra(self):
        """The literal key may appear nowhere but in the one predicate."""
        import inspect
        import nmtcapp.sections.section_c_management as sec_c
        import nmtcapp.sections.section_e_prior_awards as sec_e
        for module in (sec_c, sec_e):
            code = "".join(
                line for line in inspect.getsource(module).splitlines(keepends=True)
                if not line.lstrip().startswith("#")
            )
            assert 'extra.get("prior_award_count")' not in code, (
                f"{module.__name__} reads the raw attribute again. The "
                "normalisation lives in sections/base._declared_prior_award_"
                "count and there is exactly one of it."
            )

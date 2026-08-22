"""UNSUPPLIED IS NOT ZERO, AND THE TOOL MAY NOT INSTRUCT ON AN UNSUPPLIED INPUT.

THE DEFECT (1.5.4 T2)

``WinProbabilityModel`` reads seventeen CDE-level scoring inputs out of
``CDEProfile.extra``. Every one of them is read with a default:

    attrs.get("lic_board_representation_pct", 0.0)      win_probability.py:544

A CDE that never supplied the field and a CDE that supplied 0.0 are therefore
indistinguishable to the model, and were indistinguishable to everything
downstream of it.

THE ADVERTISED PATH SUPPLIES NONE OF THEM. The shipped
``cde_profile_template.yaml`` had its whole scoring block commented out, and the
Streamlit upload path builds a NEUTRAL profile with ``extra={}`` on purpose
(``streamlit_app/utils.py:115``) so an upload cannot inherit the sample CDE's
attributes. Both are correct decisions. What was not correct is what the
recommendation engine then said about the resulting zeros:

    Finding:  Community Accountability is 0/10. The CDFI Fund values LIC
              resident representation on the board AND documented community
              engagement history.
    Action:   Increase LIC resident or community representative board seats to
              at least 33% of total board members.

measured against a CDE whose REQUIRED ``governance`` block declares
``board_members: 9, community_representatives: 4`` -- 44%. The tool told a CDE
already at 44% to climb to 33%, in an action field, over a score of 0/10 that
measured nothing.

WHAT THIS MODULE ASSERTS, AND WHY IT IS TWO RULES AND NOT ONE

  1. An unsupplied input is not a zero. It must not render as ``0/10``.
  2. The tool may not INSTRUCT on an unsupplied input. It may DISCLOSE -- the
     field was not supplied, the Fund does score the underlying criterion, and
     here is where to supply it. That disclosure has a basis (the Fund's own
     scoring), so it survives the adopted principle, and it is more useful than
     either the false instruction or silence.

Rule 1 alone would leave the instruction standing over a blank. Rule 2 alone
would leave the fabricated zero standing under a disclosure. Both, or neither
is fixed.

WHAT IS DELIBERATELY NOT ASSERTED. That ``CDEProfile.governance`` may be read
as a substitute for the scored field. A declared field standing in for a scored
one is the ``declared_census_tract`` provenance question again and needs its own
ruling; 1.5.4 marks the field unscored and does not substitute. The 44% above is
evidence that the instruction is false, NOT a value this package may score.
"""
from __future__ import annotations

import re

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline


#: The neutral profile the Streamlit upload path builds, with the governance
#: block a CDE is REQUIRED to fill in. 4 of 9 is 44%.
def _neutral_cde(**overrides) -> CDEProfile:
    kwargs = dict(
        name="Testbench CDE, LLC",
        cde_id="TEST-CDE-0001",
        certification_date="2019-04-01",
        mission="Testbench.",
        target_markets=["Illinois"],
        prior_awards=[],
        contact={"name": "A B", "title": "CEO", "email": "a@b.org"},
        governance={"board_members": 9, "community_representatives": 4},
        extra={},
    )
    kwargs.update(overrides)
    return CDEProfile(**kwargs)


def _recommendations(cde=None, pipeline=None):
    app = Application(
        cde=cde or _neutral_cde(),
        requested_allocation=65_000_000,
        application_round="CY2025",
    )
    app.add_pipeline(pipeline or Pipeline.sample(n=20))
    return app.recommendations()


def _item(recs, needle):
    """The item ABOUT ``needle``, not merely one that mentions it.

    THE DEFECT THIS SIGNATURE FIXES (1.5.4 audit close, B1). This read
    ``needle in r.finding`` and returned ``hits[0]``, and the test below was
    DEAD FROM BIRTH because the same commit that added it added
    ``RecommendationEngine._gating_unscored_clause``. That clause appends
    EVERY ``SUBSCORE_LABELS`` value into the gating item's ``finding``, and the
    gating item is ``critical`` and sorts first -- so for all seven labels it
    names, the substring search matched ``[0, 1, <the real item>]`` and
    ``hits[0]`` returned the GATING item, whose text contains neither ``0/10``
    nor the board instruction. Measured: the exact shipped instruction was
    re-inserted into the Community Accountability disclosure and this module
    stayed green, 13 passed.

    ``startswith`` is what distinguishes the two: the disclosure item's finding
    OPENS with its label (``f"{label} — NOT SCORED. ..."``,
    recommendations.py:399), while the gating item only mentions the label
    mid-sentence inside the NOTE clause. Verified against every one of the nine
    ``SUBSCORE_LABELS`` values on the shipped tree: ``in`` resolves seven of
    them to the gating item, ``startswith`` resolves all nine to the item that
    is actually about them.

    NARROWING A MATCH CANNOT SILENTLY DISARM THIS. The ``assert hits`` below
    fires when nothing matches, so a finding that stops leading with its label
    fails loudly here rather than passing vacuously -- which is the direction
    of error a tighter needle would otherwise risk.
    """
    hits = [r for r in recs.recommendations if r.finding.startswith(needle)]
    assert hits, (
        f"no recommendation whose finding BEGINS with {needle!r}; findings were:\n"
        + "\n".join(f"  - {r.finding[:90]}" for r in recs.recommendations)
    )
    return hits[0]


def _text(rec) -> str:
    return " ".join(
        f"{rec.finding} {rec.action} {rec.expected_impact} "
        f"{rec.quantified_improvement} {rec.citation}".split()
    )


# ---------------------------------------------------------------------------
# The measured case, in full
# ---------------------------------------------------------------------------

def test_a_board_at_44_percent_is_not_told_to_reach_33_percent():
    """The exact false instruction, asserted as a whole rather than in parts.

    This is the finding in its shipped form: a score of 0/10 the CDE never
    supplied an input for, and an action telling it to reach a share it is
    already above. Both halves are named here because fixing either one alone
    still ships the other.
    """
    recs = _recommendations()
    item = _item(recs, "Community Accountability")
    text = _text(item)

    # SELECTED ITEM FIRST, THEN THE WHOLE SURFACE. The corpus assertions below
    # are what make this gate independent of _item's needle altogether: B1 was
    # not a wrong assertion, it was an assertion pointed at the wrong item, and
    # a gate that can be disarmed by a change in item ORDER is the shape this
    # module exists to close. Measured on the shipped tree: neither string
    # appears anywhere in the rendered corpus, so neither assertion is
    # vacuous.
    corpus = " ".join(_text(r) for r in recs.recommendations)

    assert "0/10" not in text, (
        "Community Accountability renders as 0/10 for a CDE that supplied no "
        "lic_board_representation_pct and no "
        "has_community_engagement_track_record. An unsupplied input is not a "
        f"zero.\n\n{text}"
    )
    assert "33% of total board members" not in text, (
        "the action instructs a CDE whose own required governance block "
        "declares 4 of 9 community representatives (44%) to raise its board to "
        f"33%. The tool may not instruct on an input it was never given.\n\n{text}"
    )
    assert "33% of total board members" not in corpus, (
        "the false board instruction is absent from the Community "
        "Accountability item but present SOMEWHERE ELSE on the recommendations "
        "surface. A CDE reads the surface, not the item this test selected."
        f"\n\n{corpus}"
    )
    assert not re.search(r"\b\d+/10\b", corpus), (
        "a x/10 sub-score renders somewhere on the surface for a CDE that "
        "supplied none of its inputs. Selecting a different item is not a fix; "
        f"the number is still on the page.\n\n{corpus}"
    )


# ---------------------------------------------------------------------------
# The class, not the instance
# ---------------------------------------------------------------------------

#: Sub-scores whose EVERY input is a CDE declaration read from
#: ``CDEProfile.extra`` with no measured substitute anywhere in the pipeline.
#: When ``extra`` is empty these five are built entirely out of ``.get``
#: defaults, so the number they produce describes nothing.
#:
#: Written out here rather than imported so that a sub-score quietly losing its
#: registry entry cannot quietly shrink what this gate checks. The companion
#: gate ``test_cde_scoring_inputs.py`` asserts the registry itself still
#: matches what the model reads.
_DECLARED_ONLY_SUBSCORES = (
    ("pipeline_credibility", 15, "Pipeline Credibility"),
    ("track_record_alignment", 10, "Track Record Alignment"),
    ("community_outcomes_quality", 10, "Community Outcomes Quality"),
    ("community_accountability", 10, "Community Accountability"),
    ("dbc_track_record", 5, "DBC Track Record"),
)


@pytest.mark.parametrize("key,maximum,label", _DECLARED_ONLY_SUBSCORES)
def test_a_subscore_with_no_supplied_input_renders_no_score(key, maximum, label):
    """Rule 1, on every sub-score built only out of CDE declarations.

    ``x/15``, ``x/10``, ``x/5`` are all forbidden here for the same reason: the
    numerator is a ``.get`` default and the denominator makes it read as a
    measurement. What must render instead is that the input was not supplied.
    """
    recs = _recommendations()
    matching = [r for r in recs.recommendations if label in _text(r)]
    assert matching, f"no recommendation mentions {label!r}"
    for rec in matching:
        text = _text(rec)
        assert not re.search(rf"\b\d+/{maximum}\b", text), (
            f"{label} renders a score out of {maximum} for a CDE that supplied "
            f"none of its inputs. That number is a .get default, not a "
            f"measurement.\n\n{text}"
        )


@pytest.mark.parametrize("key,maximum,label", _DECLARED_ONLY_SUBSCORES)
def test_a_subscore_with_no_supplied_input_says_so(key, maximum, label):
    """Rule 2's affirmative half: silence is not the fix either.

    A sub-score that simply stopped rendering would leave a CDE unaware that
    the Fund scores the underlying criterion at all. The item must name the
    input it did not get.
    """
    recs = _recommendations()
    matching = [r for r in recs.recommendations if label in _text(r)]
    assert matching, f"no recommendation mentions {label!r}"
    disclosing = [r for r in matching if "not supplied" in _text(r)]
    assert disclosing, (
        f"{label} is built entirely from inputs this CDE never supplied and no "
        "item says so. The CDE cannot tell a scored zero from a blank "
        "field.\n\n" + "\n\n".join(_text(r) for r in matching)
    )
    for rec in disclosing:
        text = _text(rec)
        assert re.search(r"\bextra\b|CDE Profile|cde_profile", text), (
            f"{label}'s disclosure does not tell the CDE WHERE to supply the "
            f"field. A disclosure a reader cannot act on is silence with extra "
            f"words.\n\n{text}"
        )


def test_every_unsupplied_input_is_named_by_the_item_that_relies_on_it():
    """The input's own key, verbatim, because that is what the CDE must type."""
    recs = _recommendations()
    corpus = " ".join(_text(r) for r in recs.recommendations)
    for key in (
        "pipeline_pct_identified",
        "track_record_pipeline_alignment_pct",
        "track_record_deployment_pct",
        "has_quantified_outcomes",
        "has_third_party_validation",
        "lic_board_representation_pct",
        "has_community_engagement_track_record",
        "dbc_focus_years",
        "dbc_dollar_volume_pct",
    ):
        assert key in corpus, (
            f"{key!r} was never supplied and drives a rendered recommendation, "
            "and no item names it. The CDE has no way to know which field to "
            "fill in."
        )


def test_a_cde_that_supplies_everything_is_still_given_scores():
    """THE OTHER DIRECTION OF ERROR, and it is the one a fix like this drops.

    Suppressing a score whenever it is low, rather than whenever its inputs are
    absent, would convert a truthfulness fix into a tool that has stopped
    scoring. The shipped sample CDE supplies all seventeen inputs, so every
    sub-score it triggers must still render as a fraction and must NOT claim
    anything was unsupplied.
    """
    recs = _recommendations(cde=CDEProfile.sample())
    corpus = " ".join(_text(r) for r in recs.recommendations)
    assert "not supplied" not in corpus, (
        "the sample CDE supplies every scoring input and an item still says "
        f"something was not supplied:\n\n{corpus}"
    )
    assert re.search(r"\b\d+/\d+\b", corpus), (
        "a fully-supplied CDE was given no scored figure at all — the fix has "
        "withdrawn scoring rather than withdrawing fabrication."
    )

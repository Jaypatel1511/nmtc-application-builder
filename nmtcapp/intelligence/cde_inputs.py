"""THE SEVENTEEN CDE-DECLARED SCORING INPUTS, IN ONE PLACE, READ FROM THE MODEL.

WHY THIS MODULE EXISTS (1.5.4 T2/T3)

``WinProbabilityModel`` reads CDE-level scoring inputs out of
``CDEProfile.extra``. Until 1.5.4 the list of those inputs existed THREE TIMES,
hand-maintained, in three files that could not see each other:

    nmtcapp/intelligence/win_probability.py      the reads themselves
    nmtcapp/templates/cde_profile_template.yaml  a commented-out block
    streamlit_app/pages/1_Pipeline_Analyzer.py   _CDE_DEFAULTS_DISCLOSURE

and they did not agree. The template offered ``has_favorable_fee_structure``
and ``has_prior_reporting_issues``, which are Phase-2 flags and score nothing,
alongside fifteen that do; and NONE of the three offered
``pct_persistent_poverty``, ``pct_us_territories`` or
``non_metro_commitment_pct``, all of which the model reads. A scaffold that
promises a field the model does not read, and withholds one it does, is the
same defect as a display literal beside a comparison that reads the constant --
two copies of one fact, joined by nothing.

So the list is DEFINED here and the other three READ it. A field added to the
model and not to this registry fails ``tests/test_cde_scoring_inputs.py``,
which re-derives the model's reads from its source.

WHAT ``measured_substitute`` MEANS, AND WHY IT IS THE HINGE OF T2

Some of these inputs have a pipeline-derived stand-in: if the CDE does not
declare ``products_below_market_pct``, the model uses the QEI-weighted share of
the pipeline priced below market, which is a MEASUREMENT of the CDE's own data.
Absence there is not ignorance.

The rest have nothing behind them. ``lic_board_representation_pct`` absent is
read as ``0.0`` (``win_probability.py:544``) and scores 0/10, and through 1.5.3
the recommendation engine then told the CDE to raise its board to 33% -- a CDE
whose own REQUIRED ``governance`` block declared 4 of 9, which is 44%.

That is the distinction this registry encodes and everything downstream reads:

    a measured substitute        -> absence is fine, the number means something
    no measured substitute       -> absence is UNKNOWN, and unknown is not zero

WHAT ``absent_default`` IS FOR. It is the value the model actually uses when the
key is missing, quoted so a reader can see that three of them are not zero at
all: ``pipeline_pct_identified`` defaults to 0.65 and ``has_quantified_outcomes``
to True, both of which are invented positions, one moderate and one favourable.
Naming them is the point -- an unstated favourable default is the harder half to
notice.

WHAT THIS MODULE DOES NOT DO. It does not read ``CDEProfile.governance`` as a
substitute for ``lic_board_representation_pct``. A declared field standing in
for a scored one is the ``declared_census_tract`` provenance question again and
needs its own ruling; 1.5.4 marks the field unscored and substitutes nothing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class CDEScoringInput:
    """One key ``WinProbabilityModel`` reads from ``CDEProfile.extra``."""

    #: The key, exactly as the CDE types it into the YAML or the workbook sheet.
    key: str
    #: The sub-score it feeds, keyed as it appears in the section dicts.
    subscore: str
    #: What the model uses when the key is absent, in the model's own terms.
    absent_default: str
    #: The pipeline-derived quantity used instead when the key is absent, or ""
    #: when there is none. "" is what makes absence UNKNOWN rather than zero.
    measured_substitute: str = ""
    #: Human-readable description, for the scaffold's comment.
    describes: str = ""

    @property
    def has_measured_substitute(self) -> bool:
        return bool(self.measured_substitute)


#: Sub-score keys to the label the recommendation engine prints.
SUBSCORE_LABELS: Dict[str, str] = {
    "product_flexibility": "Product Flexibility",
    "pipeline_credibility": "Pipeline Credibility",
    "track_record_strength": "Track Record Strength",
    "track_record_alignment": "Track Record Alignment",
    "special_targeting": "Special Targeting",
    "community_outcomes_quality": "Community Outcomes Quality",
    "community_accountability": "Community Accountability",
    "dbc_track_record": "DBC Track Record",
    "unrelated_entities": "Unrelated Entities",
}

#: EVERY SCORING INPUT THE MODEL READS. Ordered by sub-score, which is the
#: order the scaffold offers them in.
CDE_SCORING_INPUTS: Tuple[CDEScoringInput, ...] = (
    CDEScoringInput(
        key="products_below_market_pct",
        subscore="product_flexibility",
        absent_default="the pipeline's measured below-market share, else 0.0",
        measured_substitute="distress_breakdown['pct_below_market_rate']",
        describes="QEI-weighted share of products priced below market, 0-1",
    ),
    CDEScoringInput(
        key="products_flexible_indicia_count",
        subscore="product_flexibility",
        absent_default="0",
        describes="count of documented flexible-terms indicia",
    ),
    CDEScoringInput(
        key="pipeline_pct_identified",
        subscore="pipeline_credibility",
        absent_default="0.65 — an invented moderate position, not a measurement",
        describes="share of pipeline projects identified with LOIs or "
                  "commitment letters, 0-1",
    ),
    CDEScoringInput(
        key="prior_award_count",
        subscore="track_record_strength",
        absent_default="0",
        describes="number of prior NMTC allocations. Application.recommendations() "
                  "and .score_win_probability() inject len(prior_awards) when it "
                  "is omitted, so on those paths it is always supplied; a direct "
                  "WinProbabilityModel.score() call gets no such help",
    ),
    CDEScoringInput(
        key="years_in_operation",
        subscore="track_record_strength",
        absent_default="0",
        describes="years of direct-financing operation",
    ),
    CDEScoringInput(
        key="has_own_capital_at_risk",
        subscore="track_record_strength",
        absent_default="False",
        describes="has the CDE or its parent co-invested balance-sheet capital",
    ),
    CDEScoringInput(
        key="track_record_pipeline_alignment_pct",
        subscore="track_record_alignment",
        absent_default="0.0",
        describes="share of the NMTC pipeline supported by similar prior "
                  "activity, 0-1",
    ),
    CDEScoringInput(
        key="track_record_deployment_pct",
        subscore="track_record_alignment",
        absent_default="0.0",
        describes="share of prior allocation deployed, 0-1",
    ),
    CDEScoringInput(
        key="pct_persistent_poverty",
        subscore="special_targeting",
        absent_default="the pipeline's measured persistent-poverty share",
        measured_substitute="distress_breakdown['pct_persistent_poverty']",
        describes="QEI share in Persistent Poverty Counties, 0-1",
    ),
    CDEScoringInput(
        key="pct_us_territories",
        subscore="special_targeting",
        absent_default="the pipeline's measured U.S. territories share",
        measured_substitute="distress_breakdown['pct_us_territories']",
        describes="QEI share in U.S. Island Areas / territories, 0-1",
    ),
    CDEScoringInput(
        key="has_quantified_outcomes",
        subscore="community_outcomes_quality",
        absent_default="True — a FAVOURABLE assumption, not a measurement",
        describes="are outcome projections quantified (jobs, units, sq ft)",
    ),
    CDEScoringInput(
        key="has_third_party_validation",
        subscore="community_outcomes_quality",
        absent_default="False",
        describes="is there a documented third-party impact methodology",
    ),
    CDEScoringInput(
        key="lic_board_representation_pct",
        subscore="community_accountability",
        absent_default="0.0",
        describes="share of board seats held by LIC residents or community "
                  "representatives, 0-1",
    ),
    CDEScoringInput(
        key="has_community_engagement_track_record",
        subscore="community_accountability",
        absent_default="False",
        describes="is there a documented community engagement history",
    ),
    CDEScoringInput(
        key="dbc_focus_years",
        subscore="dbc_track_record",
        absent_default="0",
        describes="years of Disadvantaged Business/Community focus",
    ),
    CDEScoringInput(
        key="dbc_dollar_volume_pct",
        subscore="dbc_track_record",
        absent_default="0.0",
        describes="share of direct financing volume to DBCs, 0-1",
    ),
    CDEScoringInput(
        key="unrelated_entities_pct",
        subscore="unrelated_entities",
        absent_default="the pipeline's measured unrelated-entity share, else 0.0",
        measured_substitute="distress_breakdown['pct_unrelated_entity']",
        describes="QEI share to entities unrelated to the CDE, 0-1",
    ),
)

#: Read from ``extra`` but NOT scored — Phase 2 / compliance flags. Kept here so
#: the scaffold gate can tell "offered and unread" from "offered and unscored",
#: which are different defects: the first is a promise the model does not keep,
#: the second is a field that legitimately does not move a score.
CDE_UNSCORED_INPUTS: Tuple[CDEScoringInput, ...] = (
    CDEScoringInput(
        key="non_metro_commitment_pct",
        subscore="",
        absent_default="None — reported as not declared",
        describes="the CDE's OWN declared Question 22(c) minimum "
                  "Non-Metropolitan QLICI commitment, 0-1. Reported "
                  "unchanged; never computed from the pipeline",
    ),
    CDEScoringInput(
        key="has_favorable_fee_structure",
        subscore="",
        absent_default="None",
        describes="informational Phase 2 flag",
    ),
    CDEScoringInput(
        key="has_prior_reporting_issues",
        subscore="",
        absent_default="False",
        describes="Y/N. Drives a COMPLIANCE STATEMENT in Sections C and E of "
                  "the generated application. Set it only from your own record",
    ),
)

#: Every key the scaffold offers, scored and unscored, in scaffold order.
ALL_CDE_INPUT_KEYS: Tuple[str, ...] = tuple(
    item.key for item in CDE_SCORING_INPUTS + CDE_UNSCORED_INPUTS
)


def _is_supplied(attrs: dict, key: str) -> bool:
    """A key present but blank is NOT an answer.

    Mirrors ``CDEProfile.from_yaml``'s blank rule and
    ``streamlit_app.utils._scoring_attrs_only``'s: an untouched scaffold line
    and an untouched spreadsheet cell must not register as a declaration.
    ``False``, ``0`` and ``0.0`` ARE answers and are kept -- the membership test
    below compares by equality, and none of them equals ``""``, ``[]``, ``{}``
    or ``None``.
    """
    if key not in attrs:
        return False
    value = attrs[key]
    return not any(value is blank or value == blank for blank in ("", [], {}, None))


def inputs_for(subscore: str) -> Tuple[CDEScoringInput, ...]:
    """Every scoring input feeding one sub-score."""
    return tuple(i for i in CDE_SCORING_INPUTS if i.subscore == subscore)


def unsupplied_inputs(attrs: dict) -> Dict[str, Tuple[str, ...]]:
    """Sub-score -> the input keys it needs that this CDE did not supply.

    An input with a measured substitute is never reported here: the model used
    a measurement of the CDE's own pipeline rather than a default, so nothing
    about the resulting number is unknown.

    A sub-score that appears here MUST NOT RENDER AS A FRACTION anywhere. The
    arithmetic still runs and ``WinProbabilityScore`` is unchanged -- no score
    moves in 1.5.4 -- but part of the number is a ``.get`` default, and a
    fraction is how a reader is told a thing was measured.

    THE RULE IS UNIFORM ON PURPOSE. An earlier draft exempted sub-scores that
    had ANY measured substitute among their inputs, which would have kept
    ``Track Record Strength is 0/15`` printable for a CDE that declared no
    prior awards (a real answer) and supplied neither ``years_in_operation``
    nor ``has_own_capital_at_risk`` (two blanks). Two of three components
    unknown is not a score, and a rule with an exemption in it is a rule whose
    exemption is where the next instance hides.

    Example::

        unsupplied_inputs({})["community_accountability"]
        # -> ('lic_board_representation_pct',
        #     'has_community_engagement_track_record')
    """
    out: Dict[str, Tuple[str, ...]] = {}
    for item in CDE_SCORING_INPUTS:
        if item.has_measured_substitute or _is_supplied(attrs, item.key):
            continue
        out[item.subscore] = out.get(item.subscore, ()) + (item.key,)
    return out

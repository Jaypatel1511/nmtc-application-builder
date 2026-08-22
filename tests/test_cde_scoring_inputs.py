"""THE SCAFFOLD MUST OFFER EXACTLY WHAT THE MODEL READS. IT OFFERED NEITHER HALF.

THE DEFECT (1.5.4 T3)

``nmtcapp init`` writes ``cde_profile_template.yaml`` and the documented path is
"fill it in, then run". Through 1.5.3 the file's entire scoring block was
COMMENTED OUT, so the advertised path produced ``CDEProfile.extra == {}`` and
every one of the model's seventeen scoring inputs fell to its ``.get`` default.
That is what made 1.5.4 T2 reachable through the public API.

Uncommenting it is NOT the fix on its own, and this module is why. The list of
inputs existed three times, hand-maintained, in three files that could not see
each other:

    nmtcapp/intelligence/win_probability.py      the reads themselves
    nmtcapp/templates/cde_profile_template.yaml  the commented block
    streamlit_app/pages/1_Pipeline_Analyzer.py   _CDE_DEFAULTS_DISCLOSURE

and MEASURED, they disagreed in both directions:

  * the template offered ``has_favorable_fee_structure`` and
    ``has_prior_reporting_issues``, which the model reads as Phase-2 flags and
    scores nothing, mixed into a block headed "Win Alignment scoring inputs";
  * NONE of the three offered ``pct_persistent_poverty``, ``pct_us_territories``
    or ``non_metro_commitment_pct``, all of which the model reads.

A scaffold that promises a field the model does not read is the same defect one
layer out; a scaffold that withholds one it does read is the defect that
produced T2. So the registry in ``nmtcapp/intelligence/cde_inputs`` is the one
copy, the other two are derived from it, and the first test below re-derives it
from the MODEL'S OWN SOURCE so the registry cannot drift from the reads either.

AND A BLANK IS NOT AN ANSWER. Uncommenting the block with its ``0.0`` and
``false`` placeholders would have MOVED SCORES: ``pipeline_pct_identified``
defaults to 0.65 when absent and would have become 0.0, and
``has_quantified_outcomes`` defaults to True and would have become False. An
untouched scaffold would have scored WORSE than no scaffold at all, and 1.5.4
is a patch. So the keys are offered with EMPTY values and ``from_yaml`` drops
blanks out of ``extra``, which is the rule ``streamlit_app.utils
._scoring_attrs_only`` has always applied to the workbook path. Absent and
blank now mean the same thing on both paths, and that thing is "not supplied".
"""
from __future__ import annotations

import ast
import os
import re

import pytest
import yaml

from nmtcapp.core.cde import CDEProfile
from nmtcapp.intelligence import cde_inputs

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#: streamlit_app/ IS copied out of the tarball by release.yml's sdist job, so
#: the repo-relative path below resolves there. ``nmtcapp/`` deliberately is
#: NOT -- a bare nmtcapp/ directory in the working directory shadows the
#: installed package as a namespace package, which is the exact failure that
#: job's own comment guards against. So the MODEL is resolved through the
#: INSTALLED package, the way tests/conftest.templates_dir resolves the
#: scaffold.
#:
#: FOUND BY RUNNING THE SDIST JOB, NOT BY READING (1.5.4). The first draft of
#: this module built the model path from _REPO_ROOT: green here, red in the
#: tarball with FileNotFoundError. A new gate that would have failed
#: release.yml on a tree whose CI was green.
_PAGE1 = os.path.join(
    _REPO_ROOT, "streamlit_app", "pages", "1_Pipeline_Analyzer.py"
)


def _model_path() -> str:
    import nmtcapp.intelligence.win_probability as model
    return os.path.abspath(model.__file__)


def _template_path() -> str:
    import nmtcapp
    return os.path.join(
        os.path.dirname(nmtcapp.__file__), "templates", "cde_profile_template.yaml"
    )


def _model_attr_reads() -> set:
    """Every literal key the model pulls out of its ``attrs`` dict.

    Parsed from the model's SOURCE rather than exercised, because a read on a
    branch no fixture takes is still a read the scaffold has to offer -- and
    "no fixture takes it" is how a field goes unoffered for nine releases.
    """
    with open(_model_path(), encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    keys = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "get":
            continue
        if not (isinstance(func.value, ast.Name) and func.value.id == "attrs"):
            continue
        if node.args and isinstance(node.args[0], ast.Constant):
            if isinstance(node.args[0].value, str):
                keys.add(node.args[0].value)
    return keys


def _scaffold_keys() -> list:
    """Every key the scaffold offers in its scoring block, commented or not."""
    with open(_template_path(), encoding="utf-8") as handle:
        body = handle.read()
    marker = "OPTIONAL — Win Alignment scoring inputs"
    assert marker in body, "the scaffold no longer has a scoring-inputs block"
    block = body[body.index(marker):]
    return re.findall(r"^\s*#?\s*([a-z][a-z0-9_]*)\s*:", block, re.M)


# ---------------------------------------------------------------------------
# One copy
# ---------------------------------------------------------------------------

def test_the_registry_is_exactly_what_the_model_reads():
    registry = set(cde_inputs.ALL_CDE_INPUT_KEYS)
    model = _model_attr_reads()

    assert not (model - registry), (
        f"win_probability reads {sorted(model - registry)} from CDEProfile.extra "
        "and cde_inputs does not list them. An input the registry cannot see is "
        "an input the scaffold will not offer and the disclosure will not name."
    )
    assert not (registry - model), (
        f"cde_inputs lists {sorted(registry - model)} and the model never reads "
        "them. A registry that promises a field the model ignores is the same "
        "defect the scaffold had, one layer in."
    )


def test_every_scored_input_names_the_sub_score_it_feeds():
    for item in cde_inputs.CDE_SCORING_INPUTS:
        assert item.subscore in cde_inputs.SUBSCORE_LABELS, (
            f"{item.key} claims to feed {item.subscore!r}, which is not a "
            "sub-score this package renders a label for."
        )


def test_a_phase_two_flag_is_not_listed_as_a_scoring_input():
    scored = {i.key for i in cde_inputs.CDE_SCORING_INPUTS}
    for key in ("has_favorable_fee_structure", "has_prior_reporting_issues",
                "non_metro_commitment_pct"):
        assert key not in scored, (
            f"{key} moves no score — it is a Phase 2 / compliance flag — and "
            "listing it as a scoring input is what let the scaffold offer it "
            "under a 'Win Alignment scoring inputs' heading."
        )


# ---------------------------------------------------------------------------
# The scaffold
# ---------------------------------------------------------------------------

def test_the_scaffold_offers_every_input_the_model_reads():
    offered = set(_scaffold_keys())
    missing = [k for k in cde_inputs.ALL_CDE_INPUT_KEYS if k not in offered]
    assert not missing, (
        f"the scaffold does not offer {missing}. The model reads them, so a "
        "CDE that filled in every field this file offers is still scored on "
        "defaults for those — which is the shape that produced 1.5.4 T2."
    )


def test_the_scaffold_offers_nothing_the_model_does_not_read():
    offered = _scaffold_keys()
    unread = [k for k in offered if k not in cde_inputs.ALL_CDE_INPUT_KEYS]
    assert not unread, (
        f"the scaffold offers {unread} and nothing reads them. A scaffold that "
        "promises a field the model ignores is a field a CDE spends time on "
        "for nothing."
    )


def test_the_scaffold_offers_the_scoring_inputs_uncommented():
    """The advertised path must reach them without a CDE editing comments out."""
    with open(_template_path(), encoding="utf-8") as handle:
        body = handle.read()
    block = body[body.index("OPTIONAL — Win Alignment scoring inputs"):]
    for key in cde_inputs.ALL_CDE_INPUT_KEYS:
        assert re.search(rf"^{key}\s*:", block, re.M), (
            f"{key} is offered only as a COMMENT. `nmtcapp init` -> fill in -> "
            "run then yields CDEProfile.extra == {} for it, which is exactly "
            "the state 1.5.4 T2 exists because of."
        )


# ---------------------------------------------------------------------------
# A blank is not an answer, and uncommenting must not move a score
# ---------------------------------------------------------------------------

def _fill_required(data: dict) -> dict:
    data = dict(data)
    data.update({
        "name": "Scaffold Test CDE, LLC",
        "cde_id": "SCAFFOLD-0001",
        "certification_date": "2020-06-30",
        "mission": "Testbench mission.",
        "target_markets": ["Illinois"],
        "contact": {"name": "A B", "title": "CEO", "email": "a@b.org"},
        "governance": {"board_members": 7, "community_representatives": 3},
    })
    return data


def test_a_scaffold_key_left_blank_does_not_reach_extra(tmp_path):
    """The whole point: an untouched scaffold must score identically to none.

    If a blank ``pipeline_pct_identified:`` reached ``extra`` as ``None`` the
    model would divide by it and raise; if it reached as ``0.0`` the sub-score
    would drop from the 0.65 default's 10/15 to 0/15. Either way uncommenting
    the block would have moved a score, and 1.5.4 is a patch.
    """
    with open(_template_path(), encoding="utf-8") as handle:
        data = yaml.safe_load(handle.read())
    path = tmp_path / "blank.yaml"
    path.write_text(yaml.safe_dump(_fill_required(data)), encoding="utf-8")

    profile = CDEProfile.from_yaml(str(path))
    leaked = [k for k in cde_inputs.ALL_CDE_INPUT_KEYS if k in profile.extra]
    assert not leaked, (
        f"an untouched scaffold put {leaked} into CDEProfile.extra. A key "
        "present but blank is not an answer — the same rule from_yaml already "
        "applies to its required fields and _scoring_attrs_only applies to the "
        "workbook path."
    )


def test_a_scaffold_key_that_is_filled_in_does_reach_extra(tmp_path):
    """The other direction: dropping blanks must not drop answers.

    ``False``, ``0`` and ``0.0`` are real declarations and must survive.
    """
    with open(_template_path(), encoding="utf-8") as handle:
        data = yaml.safe_load(handle.read())
    data = _fill_required(data)
    data["lic_board_representation_pct"] = 0.44
    data["has_own_capital_at_risk"] = False
    data["years_in_operation"] = 0
    path = tmp_path / "filled.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    extra = CDEProfile.from_yaml(str(path)).extra
    assert extra.get("lic_board_representation_pct") == 0.44
    assert extra.get("has_own_capital_at_risk") is False, (
        "an explicit `false` was dropped as though it were blank. A CDE that "
        "answered No has answered."
    )
    assert extra.get("years_in_operation") == 0, (
        "an explicit `0` was dropped as though it were blank."
    )


# ---------------------------------------------------------------------------
# The third copy
# ---------------------------------------------------------------------------

def test_page_one_discloses_defaults_for_every_scored_input():
    """Page 1 tells a CDE which fields it is being defaulted on. All of them.

    THIS GATE WAS DEAD FROM BIRTH TOO (1.5.4 audit close). It asserted
    ``"cde_inputs" in source``, which is a string search over a file including
    its comments -- the same shape as B1 and B3, added by the same commit.
    Measured: ``_CDE_DEFAULTS_DISCLOSURE`` was reverted to a hand-maintained
    TWO-key literal (against seventeen scoring inputs), the import was replaced
    with ``# TODO: derive this from nmtcapp.intelligence.cde_inputs``, and the
    FULL SUITE stayed green -- 1,415 passed. The third copy this module exists
    to remove could be reinstated with the gate against it untouched.

    WHAT IT ASSERTS NOW. Two things the AST can see and a comment cannot:

      1. the page IMPORTS ``CDE_SCORING_INPUTS`` from the registry, as an
         ``ast.ImportFrom`` node;
      2. ``_CDE_DEFAULTS_DISCLOSURE`` is a COMPREHENSION that iterates that
         name -- so the dict is DERIVED from the seventeen inputs rather than
         listing some of them.

    (2) is the load-bearing half. (1) alone would pass a page that imports the
    registry and then hand-types the dict beside it, which is the defect with
    one extra line of camouflage.
    """
    with open(_PAGE1, encoding="utf-8") as handle:
        source = handle.read()
    tree = ast.parse(source, filename="1_Pipeline_Analyzer.py")

    imported = {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and (node.module or "").endswith("cde_inputs")
        for alias in node.names
    }
    assert "CDE_SCORING_INPUTS" in imported, (
        "1_Pipeline_Analyzer.py does not import CDE_SCORING_INPUTS from "
        "nmtcapp.intelligence.cde_inputs. A mention of the module in a comment "
        "is not an import: this gate used to accept one, and a hand-maintained "
        f"third copy passed it.\nimported from cde_inputs: {sorted(imported)}"
    )

    derived = []
    for node in ast.walk(tree):
        # AnnAssign as well as Assign: the page writes
        # ``_CDE_DEFAULTS_DISCLOSURE: dict[str, str] = {...}``, and matching
        # only Assign would make this branch unreachable -- a gate that cannot
        # fail, which is the defect being fixed here.
        if isinstance(node, ast.AnnAssign):
            targets = [node.target]
        elif isinstance(node, ast.Assign):
            targets = node.targets
        else:
            continue
        if not any(isinstance(t, ast.Name) and t.id == "_CDE_DEFAULTS_DISCLOSURE"
                   for t in targets):
            continue
        if node.value is None:
            continue
        iterated = {
            name.id
            for comp in ast.walk(node.value)
            if isinstance(comp, ast.comprehension)
            for name in ast.walk(comp.iter)
            if isinstance(name, ast.Name)
        }
        derived.append(iterated)

    assert derived, (
        "_CDE_DEFAULTS_DISCLOSURE is not assigned anywhere in "
        "1_Pipeline_Analyzer.py; this gate is asserting nothing."
    )
    assert any("CDE_SCORING_INPUTS" in iterated for iterated in derived), (
        "_CDE_DEFAULTS_DISCLOSURE is hand-maintained again. It must be a "
        "comprehension over CDE_SCORING_INPUTS, so that a field added to the "
        "model reaches this disclosure without anybody retyping it. It is the "
        "THIRD copy of the input list, and the three disagreed: the template "
        "offered two Phase-2 flags that score nothing and none of the three "
        "offered pct_persistent_poverty, pct_us_territories or "
        f"non_metro_commitment_pct.\niterated instead: "
        f"{sorted(set().union(*derived)) if derived else []}"
    )


# ---------------------------------------------------------------------------
# B4 (1.5.4 audit close) -- every disclosure basis is reachable
# ---------------------------------------------------------------------------

def _reachable_subscores() -> set:
    """The sub-scores ``unsupplied_inputs`` can actually name.

    Derived from the registry rather than listed: a sub-score is reportable
    only if at least ONE of its inputs has no measured substitute, because
    ``unsupplied_inputs`` skips every input that does.
    """
    return {item.subscore for item in cde_inputs.CDE_SCORING_INPUTS
            if not item.has_measured_substitute}


def test_every_not_supplied_basis_entry_can_actually_be_reached():
    """B4. A disclosure basis for text that can never render is not a basis.

    THE DEFECT. ``_NOT_SUPPLIED_BASIS`` carried entries for
    ``special_targeting`` and ``unrelated_entities``, and
    ``unsupplied_inputs`` can never ask for either: both sub-scores have a
    measured substitute for EVERY input they read, so the registry's own rule
    -- correctly -- never reports them absent. A
    ``fund_attribution_allowlist.txt`` row was written and ruled for one of
    them, which is an allowlist adjudicating a Fund attribution in a sentence
    no CDE can be shown.

    BOTH DIRECTIONS, because the failure that matters is not symmetric. An
    unreachable entry is dead weight that reads as coverage; a MISSING entry is
    a ``KeyError`` in ``_not_supplied_rec`` on a real CDE's run.
    """
    from nmtcapp.intelligence.recommendations import _NOT_SUPPLIED_BASIS

    reachable = _reachable_subscores()
    declared = set(_NOT_SUPPLIED_BASIS)

    assert not (declared - reachable), (
        "_NOT_SUPPLIED_BASIS declares a disclosure basis for "
        f"{sorted(declared - reachable)}, which unsupplied_inputs can never "
        "name: every input those sub-scores read has a measured substitute, "
        "so they are always scored from a measurement of the CDE's own "
        "pipeline. Text that cannot render is not covered by having a basis; "
        "delete the entry, or give the sub-score an input with no substitute "
        "and say why absence there is unknown rather than measured."
    )
    assert not (reachable - declared), (
        f"{sorted(reachable - declared)} can be reported unsupplied and has no "
        "entry in _NOT_SUPPLIED_BASIS. RecommendationEngine._not_supplied_rec "
        "indexes that dict directly, so this is a KeyError on the run of any "
        "CDE that leaves the field blank -- which is what the shipped scaffold "
        "and the Streamlit upload path both produce."
    )


def test_the_reachable_set_is_measured_not_assumed():
    """The derivation above, checked against the function itself.

    ``_reachable_subscores`` reasons from the registry; this drives the real
    ``unsupplied_inputs`` over every one of the 2**17 presence combinations of
    the seventeen scoring inputs and asserts the emitted set is identical. If
    the skip rule ever changes, the two disagree and this fails rather than the
    gate above quietly asserting the wrong set.
    """
    keys = [item.key for item in cde_inputs.CDE_SCORING_INPUTS]
    emitted = set()
    for mask in range(2 ** len(keys)):
        attrs = {key: 0.5 for index, key in enumerate(keys) if mask >> index & 1}
        emitted |= set(cde_inputs.unsupplied_inputs(attrs))

    assert emitted == _reachable_subscores(), (
        f"unsupplied_inputs emits {sorted(emitted)} across all "
        f"{2 ** len(keys):,} presence combinations, but the registry-derived "
        f"reachable set is {sorted(_reachable_subscores())}."
    )

"""Gate: the scaffold `nmtcapp init` writes must load in the tool that wrote it.

1.2.0's second stated goal was making `nmtcapp init` work from a wheel. It did
write the files — and the cde_profile.yaml it wrote could not be loaded by
CDEProfile.from_yaml under any completion, because the two disagreed on
VOCABULARY, not just coverage:

    scaffold offered        loader required
    ----------------        ---------------
    mission_statement       mission
    service_area_states     target_markets
    (absent)                certification_date, contact, governance

Every `nmtcapp analyze --cde <the file init just wrote>` exited 1 with a raw
Python set difference. A CDE could not guess the real names from the error or
from the file.

These tests run the real `nmtcapp init`, fill every field the scaffold offers
with a plausible value, and assert the loader accepts it — so the two can never
drift apart again without a red build.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest
import yaml

from nmtcapp.core.cde import CDEProfile


def _init(tmp_path) -> str:
    """Run `nmtcapp init` into tmp_path and return the scaffold path."""
    target = os.path.join(str(tmp_path), "proj")
    result = subprocess.run(
        [sys.executable, "-m", "nmtcapp.cli", "init", target],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"nmtcapp init exited {result.returncode}\n{result.stdout}\n{result.stderr}"
    )
    path = os.path.join(target, "cde_profile.yaml")
    assert os.path.exists(path), f"init did not write {path}"
    return path


# Plausible values for every REQUIRED key. Keyed by the name the scaffold uses,
# which must also be the name the loader reads — that identity is the point.
_FILLED = {
    "name": "Testville Community Capital CDE, LLC",
    "cde_id": "CDE-2025-001",
    "certification_date": "2025-01-15",
    "mission": "Deploy NMTC capital into distressed communities in Testville.",
    "target_markets": ["Illinois", "Ohio"],
    "prior_awards": [
        {"year": 2021, "amount": 40_000_000, "deployment_status": "fully_deployed",
         "states": ["IL"], "sectors": ["healthcare"]},
    ],
    "contact": {"name": "Pat Doe", "title": "CEO", "email": "pat@testville.org"},
    "governance": {"board_members": 7, "community_representatives": 3},
}


def test_scaffold_is_blank(tmp_path):
    """Nothing in the scaffold may be pre-filled with someone else's data."""
    data = yaml.safe_load(open(_init(tmp_path), encoding="utf-8"))
    filled = {k: v for k, v in (data or {}).items() if v not in ("", [], {}, None)}
    assert not filled, (
        f"the init scaffold ships pre-filled values: {filled}. A CDE that "
        "leaves a field alone must not inherit anyone else's answer."
    )


def test_filled_scaffold_loads(tmp_path):
    """Fill every field the scaffold offers; from_yaml must accept it."""
    path = _init(tmp_path)
    data = yaml.safe_load(open(path, encoding="utf-8")) or {}

    unknown = set(_FILLED) - set(data)
    assert not unknown, (
        f"the scaffold does not offer required key(s) {sorted(unknown)}. A CDE "
        "cannot supply a field the scaffold never mentions — this is the "
        "vocabulary mismatch that made every `nmtcapp analyze` exit 1."
    )

    data.update(_FILLED)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh)

    cde = CDEProfile.from_yaml(path)
    assert cde.name == _FILLED["name"]
    assert cde.target_markets == _FILLED["target_markets"]
    assert cde.governance["board_members"] == 7


def test_unfilled_scaffold_names_what_to_complete(tmp_path):
    """An empty scaffold must fail with guidance, not a set-difference dump."""
    path = _init(tmp_path)
    with pytest.raises(ValueError) as exc:
        CDEProfile.from_yaml(path)
    msg = str(exc.value)

    assert "{" not in msg, (
        f"the error is still a raw Python container dump:\n{msg}"
    )
    for key, hint in (
        ("certification_date", "YYYY-MM-DD"),
        ("contact", "email"),
        ("governance", "board"),
    ):
        assert key in msg, f"the error does not name the missing key {key!r}:\n{msg}"
        assert hint in msg, f"the error names {key!r} but not what to put in it:\n{msg}"


def test_analyze_accepts_the_filled_scaffold(tmp_path):
    """End to end: init -> fill -> analyze must exit 0.

    This is the path the init banner prints as step 4. It exited 1 in 1.2.0.
    """
    path = _init(tmp_path)
    data = yaml.safe_load(open(path, encoding="utf-8")) or {}
    data.update(_FILLED)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh)

    csv_path = os.path.join(os.path.dirname(path), "pipeline.csv")
    with open(csv_path, "a", encoding="utf-8") as fh:
        fh.write(
            "P1,Elm Clinic,Elm LLC,3400 S Michigan Ave,Chicago,IL,healthcare,"
            "real_estate,12500000,8500000,8500000,52,18,,24000,2026-09-30,"
            "N,N,N,N,Y,Y,N,urban,17031838200,N,N,\n"
        )

    result = subprocess.run(
        [sys.executable, "-m", "nmtcapp.cli", "analyze", csv_path,
         "--cde", path, "--requested-allocation", "8500000"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"analyze on the tool's own scaffold exited {result.returncode}\n"
        f"{result.stdout}\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# FIX-2 G-5: one list of required CDE fields, and every other statement of it
# is derived
# ---------------------------------------------------------------------------

def test_the_required_cde_field_list_is_not_duplicated():
    """Three hand-maintained copies of the same eight names agreed by luck.

    core/cde._FIELD_GUIDANCE, the ``required`` set inside
    CDEProfile.from_yaml, and validation/completeness_check._REQUIRED_CDE_FIELDS
    each stated the list independently. Measured on the branch head: DELETING
    "governance" FROM THE THIRD PASSED ALL 955 TESTS — a required field silently
    stopped being validated, because every gate that could have noticed was
    itself reading one of the three copies.

    Second live instance of M5's class, after the pipeline columns
    consistency_check retyped. There is now one list, in core/cde, and this
    test asserts the other two are the same OBJECT rather than an equal one:
    equality would pass again the moment somebody re-typed a matching copy.
    """
    from nmtcapp.core.cde import REQUIRED_CDE_FIELDS, _FIELD_GUIDANCE
    from nmtcapp.validation import completeness_check

    assert REQUIRED_CDE_FIELDS, "the authoritative list is empty"
    assert tuple(_FIELD_GUIDANCE) == REQUIRED_CDE_FIELDS, (
        "the guidance dict and the required list have diverged; the list is "
        "supposed to be derived from the dict"
    )
    assert completeness_check._REQUIRED_CDE_FIELDS is REQUIRED_CDE_FIELDS, (
        "completeness_check holds its own copy of the required-field list "
        "again. Import it — an equal copy is what silently dropped "
        "'governance' from validation with the whole suite green."
    )


def test_from_yaml_validates_every_required_field():
    """The derivation has to BITE, not merely exist.

    Asserting that two names point at one object proves the wiring. This
    proves the wiring is load-bearing: drop each field in turn from an
    otherwise complete profile and require from_yaml to refuse it by name.
    """
    import os
    import tempfile

    import pytest
    import yaml

    from nmtcapp.core.cde import REQUIRED_CDE_FIELDS

    complete = {
        "name": "Derivation Check CDE, LLC",
        "cde_id": "CDE-2021-0808",
        "certification_date": "2021-08-08",
        "mission": "Deploy capital in distressed tracts.",
        "target_markets": ["Ohio"],
        "prior_awards": [],
        "contact": {"name": "D", "email": "d@example.org"},
        "governance": {"board_members": 7, "community_representatives": 3},
    }
    assert set(complete) == set(REQUIRED_CDE_FIELDS), (
        "this fixture no longer matches the authoritative list; a field was "
        "added or removed and this test would stop covering it"
    )

    for field in REQUIRED_CDE_FIELDS:
        if field == "prior_awards":
            continue          # [] is a real answer: a first-time applicant
        partial = {k: v for k, v in complete.items() if k != field}
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
            yaml.safe_dump(partial, fh)
            path = fh.name
        try:
            with pytest.raises(ValueError) as exc:
                CDEProfile.from_yaml(path)
            assert field in str(exc.value), (
                f"dropping {field!r} was not reported by name: {exc.value}"
            )
        finally:
            os.unlink(path)


def test_completeness_check_validates_every_required_field(tmp_path):
    """The other consumer, proved the same way.

    A field can be in the list and still not be checked. This drops each one
    from a live CDEProfile and requires check_completeness to name it.
    """
    from nmtcapp.core.application import Application
    from nmtcapp.core.cde import REQUIRED_CDE_FIELDS
    from nmtcapp.core.pipeline import Pipeline
    from nmtcapp.validation.completeness_check import check_completeness

    for field in REQUIRED_CDE_FIELDS:
        cde = CDEProfile(
            name="Completeness Check CDE, LLC", cde_id="CDE-2020-0909",
            certification_date="2020-09-09", mission="Deploy capital.",
            target_markets=["Ohio"], prior_awards=[],
            contact={"name": "C", "email": "c@example.org"},
            governance={"board_members": 5, "community_representatives": 2},
        )
        # prior_awards=[] is already the empty case, and it is a real answer;
        # the check reports it and that is the behaviour under test.
        object.__setattr__(cde, field, "" if isinstance(
            getattr(cde, field), str) else type(getattr(cde, field))())
        app = Application(cde=cde, requested_allocation=30_000_000.0)
        app.add_pipeline(Pipeline.sample(n=3))
        result = check_completeness(app)
        assert any(field in issue for issue in result.issues), (
            f"{field!r} was emptied and check_completeness said nothing. "
            f"Issues: {result.issues}"
        )


def test_the_shipped_scaffold_offers_every_required_field():
    """The fourth statement of the list: the YAML a CDE actually fills in.

    `nmtcapp init` writes this file, and from_yaml refuses a profile missing
    any required key — so a scaffold that omits one hands the CDE a file that
    cannot load, with an error naming a key the scaffold never mentioned.
    Derived from the same list rather than restating it.
    """
    import yaml

    from nmtcapp.core.cde import REQUIRED_CDE_FIELDS
    from tests.conftest import templates_dir

    path = os.path.join(templates_dir(), "cde_profile_template.yaml")
    with open(path, encoding="utf-8") as fh:
        scaffold = yaml.safe_load(fh)

    assert isinstance(scaffold, dict), f"{path} did not parse to a mapping"
    missing = [f for f in REQUIRED_CDE_FIELDS if f not in scaffold]
    assert not missing, (
        f"the shipped scaffold omits required field(s) {missing}. A CDE that "
        "fills in every key this file offers still gets a profile from_yaml "
        "refuses, naming a key the scaffold never showed them."
    )

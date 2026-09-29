"""Contract test: the nmtc-calc API the adapter uses must exist, mean what it
meant, and be USED -- against whichever nmtc-calc is installed (1.7.2).

WHY THIS EXISTS

nmtc-calc 0.3.0 (published 2026-09-28) renamed
``TransactionResult.leverage_ratio`` to ``leverage_loan_to_equity_ratio``.
``integrations/nmtc_calc_adapter`` read the old name inside a blanket
``except Exception``, so on every install that resolved 0.3.0 -- the declared
bound was ``nmtc-calc>=0.1.0``, and 1.7.1 on PyPI resolves 0.3.0 -- the
library path stopped running and a manual fallback ran in its place. The only
signal was a logger warning on stderr; the Streamlit app never shows it.

It shipped no wrong figure only because the fallback models the same
identity. Measured on the published 1.7.1, nmtc-calc 0.2.1 against 0.3.0: the
four generated formats and the CLI's stdout are identical, and the 20-, 5- and
1-project sample economics match key for key. That was luck of construction,
not a property anything checked.

WHAT THIS ASSERTS, AGAINST THE INSTALLED LIBRARY

1. The installed nmtc-calc is inside the bound ``pyproject.toml`` declares.
2. Every ``result.<field>`` the adapter reads, and every keyword it passes to
   ``NMTCDeal``, exists on the installed classes -- DERIVED from the adapter's
   source by AST walk, never hand-copied (the ``test_mapper_contract``
   precedent: a hand list drifts silently).
3. The fields still MEAN what the adapter assumes: 39% of QEI, equity =
   credits x price, leverage = QEI - equity, fee = QEI x rate, and the
   leverage/equity multiple is leverage over equity.
4. The house constants the adapter passes satisfy the installed contract,
   including 0.3.0's negative-tranche bound (``cde_fee_rate`` must not exceed
   39% x ``credit_price``) and its [0, 1) rate bound.
5. The LIBRARY PATH IS TAKEN when nmtc-calc is installed -- with the fallback
   made to raise, so a silent fallback cannot pass.
6. An API mismatch FAILS LOUDLY; only an import failure or nmtc-calc's own
   input refusal (ValueError) falls back.

``ci.yml``'s ``nmtc-calc`` job runs the suite against the floor (0.2.1); the
``test`` matrix resolves the newest version the bound admits (0.3.0 today).
"""
from __future__ import annotations

import ast
import dataclasses
import logging
import re
import sys
from importlib.metadata import version
from pathlib import Path

import pytest

import nmtcapp.integrations.nmtc_calc_adapter as adapter_mod
from nmtcapp.core.pipeline import Pipeline
from nmtcapp.data.schema import NMTC_PROGRAM_CONSTRAINTS

import nmtccalc  # noqa: E402,F401  (a hard dependency; never a skip)
from nmtccalc import NMTCDeal  # noqa: E402
import nmtccalc.models.transaction as nmtc_transaction  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ADAPTER_SOURCE = Path(adapter_mod.__file__)


def _vtuple(text: str) -> tuple:
    return tuple(int(part) for part in re.findall(r"\d+", text)[:3])


def _declared_bound() -> tuple:
    """``(floor, ceiling)`` from pyproject.toml, which the sdist job copies
    out beside tests/ as well."""
    text = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.findall(r'^\s*"nmtc-calc>=([\d.]+),<([\d.]+)",', text, re.M)
    assert len(m) == 1, f"expected one bounded nmtc-calc requirement, found {m}"
    return _vtuple(m[0][0]), _vtuple(m[0][1])


def _adapter_function() -> ast.FunctionDef:
    tree = ast.parse(_ADAPTER_SOURCE.read_text(encoding="utf-8"))
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef)
           and n.name == "_compute_via_library"]
    assert len(fns) == 1, "the adapter has no _compute_via_library to check"
    return fns[0]


def _result_reads() -> set:
    """Attribute names the adapter reads off ``result`` (the structure() return)."""
    reads = {n.attr for n in ast.walk(_adapter_function())
             if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
             and n.value.id == "result"}
    assert reads, "derived no result.<field> reads -- the derivation is broken"
    return reads


def _deal_kwargs() -> set:
    calls = [n for n in ast.walk(_adapter_function())
             if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "NMTCDeal"]
    assert len(calls) == 1, "expected one NMTCDeal(...) construction in the adapter"
    kwargs = {kw.arg for kw in calls[0].keywords}
    assert kwargs and None not in kwargs, "NMTCDeal is built without plain keywords"
    return kwargs


def _one_result():
    p = list(Pipeline.sample(n=1))[0]
    deal = NMTCDeal(
        project_name=p.project_name, total_project_cost=p.total_project_cost,
        nmtc_allocation=p.qei_request,
        credit_price=NMTC_PROGRAM_CONSTRAINTS["standard_credit_price"],
        leverage_loan_rate=0.055, qlici_a_loan_rate=0.01, qlici_b_loan_rate=0.055,
        cde_fee_rate=NMTC_PROGRAM_CONSTRAINTS["cde_fee_rate_typical"],
    )
    return deal, nmtc_transaction.structure(deal)


# ---------------------------------------------------------------------------

def test_the_installed_nmtc_calc_is_inside_the_declared_bound():
    """And, in a checkout, ci.yml's floor leg pins the declared floor.

    The ci.yml half is conditional rather than a skip: .github/ is not in the
    sdist, and a skip there would widen MAX_SDIST_SKIPS for a question the
    tarball cannot ask. In a checkout the file must exist and must agree.
    """
    floor, ceiling = _declared_bound()
    installed = _vtuple(version("nmtc-calc"))
    assert floor <= installed < ceiling, (
        f"nmtc-calc {version('nmtc-calc')} is installed; pyproject.toml admits "
        f">={'.'.join(map(str, floor))},<{'.'.join(map(str, ceiling))}")
    if (_REPO_ROOT / ".git").exists():
        ci = (_REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        pinned = re.findall(r'NMTC_CALC_FLOOR:\s*"([\d.]+)"', ci)
        assert pinned and all(_vtuple(v) == floor for v in pinned), (
            f"ci.yml's nmtc-calc-floor leg pins {pinned}; pyproject.toml's floor is "
            f"{'.'.join(map(str, floor))}. The floor must be the version CI runs.")


def test_every_field_and_keyword_the_adapter_uses_exists_on_the_installed_api():
    result_fields = {f.name for f in dataclasses.fields(nmtc_transaction.TransactionResult)}
    deal_fields = {f.name for f in dataclasses.fields(NMTCDeal)}
    missing_reads = _result_reads() - result_fields
    missing_kwargs = _deal_kwargs() - deal_fields
    ratio = [n for n in adapter_mod.LEVERAGE_TO_EQUITY_FIELDS if n in result_fields]
    assert not missing_reads and not missing_kwargs and ratio, (
        f"nmtc-calc {version('nmtc-calc')}: TransactionResult lacks "
        f"{sorted(missing_reads)}; NMTCDeal lacks {sorted(missing_kwargs)}; "
        f"leverage/equity field present: {ratio or 'NONE of ' + str(adapter_mod.LEVERAGE_TO_EQUITY_FIELDS)}")


def test_the_fields_still_mean_what_the_adapter_assumes():
    deal, r = _one_result()
    price = NMTC_PROGRAM_CONSTRAINTS["standard_credit_price"]
    fee = NMTC_PROGRAM_CONSTRAINTS["cde_fee_rate_typical"]
    assert r.qei == deal.nmtc_allocation
    assert r.total_nmtcs == pytest.approx(0.39 * r.qei, rel=1e-12)
    assert r.investor_equity == pytest.approx(r.total_nmtcs * price, rel=1e-12)
    assert r.leverage_loan == pytest.approx(r.qei - r.investor_equity, rel=1e-12)
    assert r.cde_fee == pytest.approx(r.qei * fee, rel=1e-12)
    assert adapter_mod.leverage_to_equity(r) == pytest.approx(
        r.leverage_loan / r.investor_equity, rel=1e-12)


def test_the_house_constants_satisfy_the_installed_input_contract():
    """0.3.0 refuses a negative B tranche when cde_fee_rate > 0.39 x price, and
    bounds every rate to [0, 1). The adapter's constants must clear both --
    checked arithmetically, not only by construction succeeding."""
    price = NMTC_PROGRAM_CONSTRAINTS["standard_credit_price"]
    fee = NMTC_PROGRAM_CONSTRAINTS["cde_fee_rate_typical"]
    assert 0 < fee <= 0.39 * price, (fee, 0.39 * price)
    for rate in (0.055, 0.01, 0.055):
        assert 0 <= rate < 1
    deal, r = _one_result()
    for tranche in ("investor_equity", "leverage_loan", "qlici_total",
                    "qlici_a_loan", "qlici_b_loan"):
        assert getattr(deal, tranche) >= 0, tranche


def test_the_library_path_is_taken_when_nmtc_calc_is_installed(monkeypatch):
    """The silent-fallback class, closed: the fallback is made to raise."""
    real_fallback = adapter_mod._compute_fallback
    projects = list(Pipeline.sample(n=20))

    def _no_fallback(_projects):
        raise AssertionError("the manual fallback ran with nmtc-calc installed")

    monkeypatch.setattr(adapter_mod, "_compute_fallback", _no_fallback)
    result = adapter_mod.compute_pipeline_economics(Pipeline.sample(n=20))
    # And the two paths agree, which is what makes the fallback safe when it
    # legitimately runs.
    assert result == real_fallback(projects)


def test_an_api_mismatch_fails_loudly_instead_of_falling_back(monkeypatch):
    """What 0.3.0 did to 1.7.1, reproduced: a result without the ratio field."""
    real_structure = nmtc_transaction.structure

    class _Renamed:
        def __init__(self, r):
            self._r = r

        def __getattr__(self, name):
            if name in adapter_mod.LEVERAGE_TO_EQUITY_FIELDS:
                raise AttributeError(name)
            return getattr(self._r, name)

    monkeypatch.setattr(nmtc_transaction, "structure",
                        lambda deal: _Renamed(real_structure(deal)))
    with pytest.raises(AttributeError, match="carries none of"):
        adapter_mod.compute_pipeline_economics(Pipeline.sample(n=3))


def test_an_import_failure_still_falls_back_and_says_so(monkeypatch, caplog):
    monkeypatch.setitem(sys.modules, "nmtccalc", None)
    with caplog.at_level(logging.WARNING, logger=adapter_mod.__name__):
        result = adapter_mod.compute_pipeline_economics(Pipeline.sample(n=5))
    assert "not importable" in caplog.text
    assert result == adapter_mod._compute_fallback(list(Pipeline.sample(n=5)))


def test_nmtc_calcs_own_input_refusal_falls_back_and_says_so(caplog):
    """A row with QEI above total project cost: PipelineProject accepts it,
    every nmtc-calc version refuses it with ValueError. A real input path."""
    projects = list(Pipeline.sample(n=3))
    projects[0].total_project_cost = projects[0].qei_request - 1
    pl = Pipeline()
    for p in projects:
        pl.add(p)
    with caplog.at_level(logging.WARNING, logger=adapter_mod.__name__):
        result = adapter_mod.compute_pipeline_economics(pl)
    assert "refused a deal's inputs" in caplog.text
    assert result == adapter_mod._compute_fallback(projects)

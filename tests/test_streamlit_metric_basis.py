"""A percentage on a screen must name its denominator, as it does in the filing.

THE DEFECT THIS GATE EXISTS FOR (1.3.1 F2)
==========================================

Every generated document names each distress share's basis on the figure's own
face — ``QEI in LIC (Standard Eligible) Tracts``, ``QEI in Deep Distress Tracts
(a share of QEI, not of QLICIs — see the basis note below)``. The Streamlit
Distress tab printed the same shares as::

    c2.metric("LIC (standard)", fmt_pct(lic_pct))
    c3.metric("Native area (CDE-declared)", fmt_pct(native_pct))

A CDE reads a figure off a screen and types it into a form exactly the way it
reads one off a workbook. Producing no file is not the same as reaching no
filing, and the Fund's two distress commitments are measured on QLICIs while
every share this package computes is a share of QEI — which is the single
sentence 1.2.1 and 1.3.0 spent three rounds getting onto the four documents.

WHY THIS IS ASSERTED AGAINST THE DOCUMENT'S OWN LABEL
=====================================================

The wording that ships in the documents was hostile-audited across three
rounds. A paraphrase written for a metric label has not been, and a paraphrase
of a denominator disclosure is a new claim about the denominator. So the fix
was to IMPORT the label, and this gate asserts the import rather than the
wording: it reads the constants out of ``nmtcapp.tables.distress_table`` and
checks the page source uses them.

WHAT IS NOT ASSERTED
====================

Score metrics (``Business Strategy 42 / 50``) carry their denominator in the
value. Count metrics (``Projects selected``) have no denominator to name. This
gate is about SHARES — a bare percentage, where the denominator is invisible
unless the label carries it.
"""
from __future__ import annotations

import ast
import os
import re

import pytest

from nmtcapp.renderers._question_25 import Q25_QEI_BASIS_CLAUSE
from nmtcapp.tables.distress_table import (
    HMR_ROW_LABEL, LIC_ROW_LABEL, NATIVE_AREA_ROW_LABEL,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAGES = os.path.join(_ROOT, "streamlit_app", "pages")

#: The Distress tab's three share metrics, and the basis each must carry.
#: Named by the constant, so a reworded document label moves both together.
_SHARE_METRICS = (
    ("deep/severe", "Q25_QEI_BASIS_CLAUSE", Q25_QEI_BASIS_CLAUSE),
    ("LIC", "LIC_ROW_LABEL", LIC_ROW_LABEL),
    ("native area", "NATIVE_AREA_ROW_LABEL", NATIVE_AREA_ROW_LABEL),
)

_ANALYZER = os.path.join(_PAGES, "1_Pipeline_Analyzer.py")

# ---------------------------------------------------------------------------
# TWO SHARES THIS ROUND FOUND AND DID NOT FIX, RECORDED RATHER THAN EXEMPTED
#
# This gate's AST walk was written for the Distress tab and immediately found
# two more bare percentages on the same page. Both ARE the same class — a share
# of QEI whose denominator is invisible in its label:
#
#   "Rural share"            geographic_analysis.rural_pct — "fraction of QEI
#                            in rural markets", per its own docstring. Renders
#                            as a bare percentage on the Geographic tab, and
#                            the `nmtcapp analyze` block prints the same pair
#                            as "Urban/Rural: 93% / 7%" with no basis either.
#   "High-priority sector %" sector_analysis.high_priority_pct, likewise a
#                            share of QEI.
#
# NOT FIXED IN 1.3.1, and the reason is the one F2 itself gives: the fix for
# the distress metrics was to CARRY the document's own label, because that
# wording was hostile-audited across three rounds. NO DOCUMENT RENDERS EITHER
# OF THESE TWO WITH A BASIS, so there is nothing to carry, and writing one
# would be composing a new denominator disclosure on a patch release — which
# is the move F2 exists to refuse. They are ruled here, with the reason, and
# reported for 1.4.0. An exemption is a hole with a reason attached; this is
# the reason, and test_every_ruled_share_metric_still_exists stops it
# outliving the hole.
# ---------------------------------------------------------------------------

_RULED_SHARE_METRICS = {
    "Rural share": (
        "share of QEI in rural markets. No generated document names its "
        "basis, so there is no audited wording to carry. 1.4.0."
    ),
    "High-priority sector %": (
        "share of QEI in high-priority sectors. Same reason. 1.4.0."
    ),
}


def _source() -> str:
    with open(_ANALYZER, encoding="utf-8") as fh:
        return fh.read()


@pytest.mark.parametrize("what,const,value", _SHARE_METRICS,
                         ids=[m[0] for m in _SHARE_METRICS])
def test_each_distress_share_metric_carries_the_documents_own_label(what, const, value):
    """The screen must use the constant, not a paraphrase of it."""
    source = _source()
    assert re.search(rf"\b{re.escape(const)}\b", source), (
        f"the {what} metric on the Pipeline Analyzer page does not use "
        f"{const}. Every generated document names this share's basis on the "
        f"figure's face ({value!r}); a screen that drops it shows a share of "
        "QEI with no denominator, next to a Fund commitment measured on "
        "QLICIs. Import the constant rather than writing a label — the "
        "shipped wording was hostile-audited and a fresh paraphrase has not "
        "been (1.3.1 F2)."
    )
    assert value not in source or const in source, (
        f"the {what} label is present as a literal rather than as {const}. "
        "That is the third copy of one sentence, which is what 1.3.0 B1 "
        "removed from sections/section_b_outcomes."
    )


def test_the_document_and_the_screen_cannot_drift_apart():
    """The constants the screen imports are the ones Section B renders."""
    from nmtcapp.sections import section_b_outcomes as sb

    for name, value in (("LIC_ROW_LABEL", LIC_ROW_LABEL),
                        ("NATIVE_AREA_ROW_LABEL", NATIVE_AREA_ROW_LABEL),
                        ("HMR_ROW_LABEL", HMR_ROW_LABEL)):
        assert getattr(sb, name) is value, (
            f"section_b_outcomes.{name} is not the object "
            "tables/distress_table exports. Two copies of a label agree by "
            "luck until they do not."
        )
    assert LIC_ROW_LABEL.startswith("QEI in"), (
        "the LIC row label stopped naming its denominator. Section B's rows "
        "are the authority for what every surface calls these shares."
    )


def test_every_bare_percentage_metric_on_the_distress_tab_is_ruled():
    """A share metric with no basis in its label must be a deliberate exception.

    SENSITIVITY IS THE POINT HERE. The three pins above pass as long as the
    constants appear somewhere in the file, which a deleted metric would also
    satisfy. This walks the actual ``.metric(...)`` calls in the Distress tab
    and refuses a percentage whose label is a bare noun.
    """
    tree = ast.parse(_source(), filename="1_Pipeline_Analyzer.py")
    ruled = {"Q25_QEI_BASIS_CLAUSE", "LIC_ROW_LABEL", "NATIVE_AREA_ROW_LABEL",
             "HMR_ROW_LABEL"}

    pct_metrics, bare = 0, []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "metric"
                and len(node.args) >= 2):
            continue
        value = node.args[1]
        # Only metrics whose VALUE is a percentage: fmt_pct(...).
        if not (isinstance(value, ast.Call)
                and getattr(value.func, "id", None) == "fmt_pct"):
            continue
        pct_metrics += 1
        label = node.args[0]
        names = {n.id for n in ast.walk(label) if isinstance(n, ast.Name)}
        if names & ruled:
            continue
        if isinstance(label, ast.Constant) and label.value in _RULED_SHARE_METRICS:
            continue
        literal = ast.get_source_segment(_source(), label) or "<label>"
        bare.append(f"line {node.lineno}: metric({literal[:60]})")

    assert pct_metrics >= 3, (
        f"only {pct_metrics} percentage metric(s) found on the page — the "
        "walk is broken and this gate would pass vacuously"
    )
    assert not bare, (
        f"{len(bare)} percentage metric(s) render a share with no basis in "
        "the label. The generated documents name the denominator on every "
        "one of these figures; the screen is where a CDE reads the number "
        "before it ever generates a document (1.3.1 F2).\n  "
        + "\n  ".join(bare)
    )


def test_every_ruled_share_metric_still_exists():
    """A ruling for a metric that is gone is a hole nobody is holding open."""
    source = _source()
    stale = [label for label in _RULED_SHARE_METRICS
             if f'metric("{label}"' not in source]
    assert not stale, (
        "ruled share metric(s) no longer render. Remove the ruling so the "
        "list stays a description of what is actually exempt:\n  "
        + "\n  ".join(stale)
    )

"""Prose that says the package REFUSES something must be true of the code.

THE DEFECT THIS GATE EXISTS FOR (1.3.1 fix round, R1)
=====================================================

``docs/hooks/generate_sample_output.py`` wrote this onto the published Sample
Output page, inside a ``!!! warning`` box:

    The package refuses to score or generate against this identity outside
    demo mode; see `nmtcapp/core/sample_identity.py`.

Thirty lines below the sentence, the same hook did this::

    app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
    app.add_pipeline(Pipeline.sample(n=20))
    paths = app.generate(out_dir, formats=list(_FORMATS))

No refusal. Four filing-shaped documents for Riverbend, Readiness Grade A,
$65,000,000 — published under a box saying the package would not do that. The
page's own build was the counterexample to the page's own claim, and it had
been so since the hook was written.

THE MECHANISM, WHICH IS THE PART WORTH PINNING
==============================================

``assert_not_sample_identity`` is called from exactly two places in shipped
code: ``cde.py`` inside ``from_yaml`` (gated on ``allow_sample``), and
``streamlit_app/utils.py`` on the CDE Profile upload. ``CDEProfile.sample()``
is a classmethod calling ``cls(...)`` directly, ``__post_init__`` does not
check, and ``generate()`` does not check. The sample path is UNGUARDED, not
misdirected — and since there is no CLI ``generate`` subcommand and no
Streamlit generate path, ``Application.generate()`` is the only way to produce
a document at all, on a path with no guard on it.

WHAT THIS GATE ASSERTS, AND WHAT IT CANNOT SEE
==============================================

It asserts three things:

1. THE BOUNDARY IS WHERE THE DOCS SAY IT IS. The set of shipped modules calling
   ``assert_not_sample_identity`` is exactly ``{nmtcapp/core/cde.py,
   streamlit_app/utils.py}``. Adding or removing a guard makes this red, which
   is the event that should force somebody to re-read the published box.
2. THE UNGUARDED PATH IS REALLY UNGUARDED — by executing it. ``sample()`` then
   ``generate()`` must succeed. If 1.4.0 adds the guard, this goes red and the
   docs must stop saying the package does not refuse it.
3. THE GUARDED PATH REALLY REFUSES — by executing it. ``from_yaml`` on the
   shipped sample must raise ``SampleDataError`` and name the field.

WHAT IT CANNOT SEE, stated plainly rather than implied:

- It does not parse English. It cannot read an arbitrary new sentence and
  decide whether it is true. The broad version of this gate — "any prose
  claiming the package refuses something is true of the code" — is not
  buildable, so what is built instead is a REGISTRY: every sentence in the
  docs matching the refusal vocabulary must be listed in ``_RULED_CLAIMS``
  below with the basis on which it was checked. A new unlisted claim fails.
  That converts an unfalsifiable prose problem into a review event.
- The registry is keyed on a regex over a fixed file list. Prose that says the
  same thing in different words ("blocks", "will not let you") is not matched,
  and a claim added to a file not in ``_DOC_SURFACES`` is not seen.
- It says nothing about whether the refusal is CORRECT policy — only whether
  the prose about it matches the code.
"""
from __future__ import annotations

import ast
import os
import re
import tempfile

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Shipped (non-test) modules that call the refusal. This IS the boundary.
_EXPECTED_GUARD_CALL_SITES = {
    "nmtcapp/core/cde.py",
    "streamlit_app/utils.py",
}

#: Trees searched for calls. Tests are excluded: a test calling the guard is
#: exercising it, not imposing it.
_SCANNED_CODE = ("nmtcapp", "streamlit_app", "docs")

#: Prose surfaces swept for refusal claims.
_DOC_SURFACES = (
    "README.md",
    "CONTRIBUTING.md",
    "docs/index.md",
    "docs/quickstart.md",
    "docs/installation.md",
    "docs/about/limitations.md",
    "docs/about/why.md",
    "docs/about/contributing.md",
    "docs/reference/api.md",
    "docs/reference/methodology.md",
    "docs/reference/data-sources.md",
    "docs/workflow/optimization.md",
    "docs/workflow/output-formats.md",
    "docs/workflow/pipeline-analysis.md",
    "docs/workflow/recommendations.md",
    "docs/workflow/visualizations.md",
    "docs/workflow/win-alignment.md",
    "docs/hooks/generate_sample_output.py",
)

#: The vocabulary that makes a sentence a claim about refusal behaviour.
_REFUSAL_VOCAB = re.compile(
    r"\b(refuses?|refusing|refusal|hard-blocks?|will not (?:let|allow)|"
    r"declines? to)\b", re.I)

#: Every refusal sentence in _DOC_SURFACES, and the basis it was checked on.
#: A sentence not listed here fails this gate. Adding one is a review event,
#: and the review is: run it.
_RULED_CLAIMS = {
    "it never hard-blocks": (
        "README.md, degraded mode. TRUE FOR THE DOCUMENTED FAILURE, FALSE FOR "
        "THE REST, and the docs do not draw that line. Executed both ways "
        "against an unenriched pipeline with nmtcmapper.NMTCMapper patched to "
        "raise: on NMTCMapperError -- the failure the surrounding paragraph "
        "describes -- analyze(), score_win_probability(), recommendations(), "
        "benchmark(), optimize_pipeline() and generate() all succeed, "
        "eligibility_data_status becomes 'unavailable' and the summary carries "
        "the banner. On ANY OTHER exception from the data layer, "
        "application.py:250-254 wraps it and analyze() raises RuntimeError. "
        "nmtc_mapper_adapter's own docstring says 'Unexpected exceptions "
        "propagate', so this is intended behaviour that the README sentence "
        "does not scope. Reported in 1.3.1's fix round; rewording the README "
        "is 1.3.2."
    ),
    "The package does not refuse that path": (
        "docs/hooks/generate_sample_output.py, the Sample Output warning box. "
        "Executed: CDEProfile.sample() -> Application.generate() returns four "
        "formats with no exception "
        "(test_the_sample_to_generate_path_is_unguarded_as_the_docs_now_say)."
    ),
    "Nothing in the package refuses this path": (
        "docs/index.md, the 60-second quickstart caveat. Same claim as the box "
        "above and proven by the same executed test."
    ),
}


def _iter_py(*trees):
    for tree in trees:
        base = os.path.join(_ROOT, tree)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames
                           if d not in {"__pycache__", ".git"}]
            for name in filenames:
                if name.endswith(".py"):
                    yield os.path.join(dirpath, name)


def test_the_refusal_guard_is_called_from_exactly_the_documented_places():
    """The published boundary and the code's boundary are the same set.

    The Sample Output page names ``from_yaml`` and the Streamlit upload. If a
    third call site appears, or one of these two goes away, the page is stale
    the moment it happens — and this is the only thing that would say so.
    """
    if not os.path.isdir(os.path.join(_ROOT, "nmtcapp")):
        pytest.skip("no source tree beside tests/ (unpacked sdist or installed "
                    "tree, not a checkout); this gate reads package source")

    found = set()
    for path in _iter_py(*_SCANNED_CODE):
        rel = os.path.relpath(path, _ROOT).replace(os.sep, "/")
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        if "assert_not_sample_identity" not in source:
            continue
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "assert_not_sample_identity"):
                found.add(rel)

    assert found == _EXPECTED_GUARD_CALL_SITES, (
        "the refusal guard is no longer called from exactly the places the "
        "published Sample Output page says it is.\n"
        f"  expected: {sorted(_EXPECTED_GUARD_CALL_SITES)}\n"
        f"  found:    {sorted(found)}\n\n"
        "The box on that page states the boundary in prose. Move the boundary "
        "and the prose is false until somebody edits it — which is exactly how "
        "'the package refuses to score or generate against this identity "
        "outside demo mode' came to be published over a page whose own build "
        "generated four documents against that identity. Update "
        "docs/hooks/generate_sample_output.py and this set together."
    )


def test_the_sample_to_generate_path_is_unguarded_as_the_docs_now_say():
    """EXECUTES the claim. sample() -> generate() must succeed.

    The page says the package does not refuse this path. That is a statement
    about behaviour, so it is checked by running it rather than by reading it.
    When 1.4.0 puts a guard on ``generate()``, this test is what fails, and the
    sentence has to change in the same commit.
    """
    pytest.importorskip("reportlab", reason="reportlab not installed")
    pytest.importorskip("docx", reason="python-docx not installed")
    pytest.importorskip("openpyxl", reason="openpyxl not installed")

    from nmtcapp.core.application import Application
    from nmtcapp.core.cde import CDEProfile
    from nmtcapp.core.pipeline import Pipeline

    cde = CDEProfile.sample()          # no refusal here: cls(...) directly
    app = Application(cde=cde, requested_allocation=65_000_000)
    app.add_pipeline(Pipeline.sample(n=20))
    paths = app.generate(tempfile.mkdtemp(prefix="unguarded-"),
                         formats=["markdown", "word", "excel", "pdf"])

    assert set(paths) == {"markdown", "word", "excel", "pdf"}, (
        "the docs hook's own path did not produce four formats; the published "
        f"page is built from this call and got {sorted(paths)}"
    )
    for fmt, path in paths.items():
        assert os.path.getsize(path) > 0, f"{fmt} output is empty"


def test_the_from_yaml_path_refuses_and_names_the_field():
    """EXECUTES the other half. The guarded path must actually refuse."""
    import nmtcapp
    from nmtcapp.core.cde import CDEProfile
    from nmtcapp.core.sample_identity import SampleDataError

    sample_yaml = os.path.join(os.path.dirname(nmtcapp.__file__), "templates",
                               "cde_profile_sample.yaml")
    assert os.path.exists(sample_yaml), "the shipped sample profile is not packaged"

    with pytest.raises(SampleDataError) as excinfo:
        CDEProfile.from_yaml(sample_yaml)
    message = str(excinfo.value)
    assert any(field in message for field in ("CDE name", "CDE ID", "EIN")), (
        "the refusal does not name which identity field matched, so a false "
        f"positive is not diagnosable:\n{message}"
    )

    # And the documented escape hatch must still work, or the sentence naming
    # allow_sample=True is itself false.
    loaded = CDEProfile.from_yaml(sample_yaml, allow_sample=True)
    assert loaded.name, "allow_sample=True did not load the shipped sample"


def test_every_refusal_claim_in_the_docs_is_registered():
    """A new sentence claiming a refusal is a review event, not a silent one.

    This does NOT verify English. It verifies that no refusal claim reaches a
    published surface without somebody having written down what it was checked
    against — which is the step that did not happen for the sentence this
    module exists for.
    """
    unregistered = []
    for rel in _DOC_SURFACES:
        path = os.path.join(_ROOT, *rel.split("/"))
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for raw in re.split(r"(?<=[.!?])\s+|\n\n", text):
            sentence = " ".join(raw.split())
            if not sentence or not _REFUSAL_VOCAB.search(sentence):
                continue
            if any(key in sentence for key in _RULED_CLAIMS):
                continue
            unregistered.append(f"{rel}: {sentence[:160]}")

    assert not unregistered, (
        f"{len(unregistered)} sentence(s) claim the package refuses something "
        "and are not registered in _RULED_CLAIMS. Run the claim, then add it "
        "with the basis you checked it on. An unrun refusal claim is how "
        "'the package refuses to score or generate against this identity "
        "outside demo mode' was published over a page that did exactly "
        "that:\n  " + "\n  ".join(unregistered[:12])
    )

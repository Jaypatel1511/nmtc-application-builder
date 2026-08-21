"""THE EMBED GATE: no generated document may carry a chart, and the docs may not say it does.

WHAT THIS CLOSES (1.4.1 S4)

``docs/workflow/output-formats.md`` claimed, under the heading "How
visualizations are embedded", that ``WordApplicationBuilder`` "automatically
generates all five visualization charts ... and embeds them in the relevant
sections", and it named a target section for each of the five. **Zero were
embedded, on every release in which that text appeared.**

A docs/code mismatch is usually a small thing. This one was not, and the reason
is the point of this module:

    THE FALSE CLAIM WAS THE ONLY THING KEEPING THREE UNSOURCED COMPARISONS
    OUT OF A FILED FEDERAL APPLICATION.

``plot_winner_alignment`` draws a pipeline against winner p25/p50/p75 bands for
three metrics. All nine of those values are ``HOUSE`` rows in
``tests/scoring_attribution.txt`` -- no retrievable document supports any of
them, and ``nmtcapp/data/historical_awards.py``'s own header says the
"Source: CDFI Fund Annual Reports" comments above them cite a publication that
does not exist.

So the obvious repair -- make the code match the documentation -- would have
taken nine unsourced numbers and drawn them into a document a CDE files with
the CDFI Fund, where a chart reads as the APPLICANT's assertion rather than the
tool's. The documentation was corrected to match the code instead, and this
gate is what stops the correction from being quietly reversed by someone who
finds a one-line mismatch and helpfully fixes the wrong side of it.

TWO HALVES, BECAUSE THE CLAIM AND THE BEHAVIOUR CAN DRIFT APART SEPARATELY

  1. THE BEHAVIOUR. Generate all four formats and assert the .docx carries no
     chart image. Executed, not reasoned -- with ``matplotlib`` importable, so
     "the optional dependency was missing" can never be the reason it passes.

  2. THE CLAIM. Assert docs/ does not tell a reader that charts are embedded.
     A gate on behaviour alone would stay green while the page went back to
     promising something the code does not do, which is exactly the state
     1.4.0 shipped in.

WHEN THIS SHOULD BE DELETED. When the constants a chart draws are sourced or
gone. Deleting it before that re-opens the path this exists to close; see the
ruling in ``nmtcapp/visualization/maps.plot_winner_alignment``.
"""
from __future__ import annotations

import os
import zipfile

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(_REPO_ROOT, "docs")

#: python-docx writes this into every document it creates. It is a template
#: artifact, not a chart, and naming it here is the difference between "zero
#: images" (false) and "zero CHART images" (true and checkable).
_TEMPLATE_ARTIFACTS = {"docProps/thumbnail.jpeg"}

_IMAGE_SUFFIXES = (".png", ".jpeg", ".jpg", ".gif", ".bmp", ".emf", ".wmf")


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    """All four formats, generated once, with matplotlib PRESENT.

    The optional-dependency path is the obvious false negative here: charts are
    skipped without matplotlib, so a run in an environment lacking it would
    pass this gate while proving nothing. Importing it first turns that into a
    skip with a stated reason rather than a silent pass.
    """
    pytest.importorskip(
        "matplotlib",
        reason="matplotlib absent: charts would be skipped for that reason "
               "alone, so this gate could not distinguish 'not embedded' from "
               "'could not be drawn'.",
    )
    app = Application(cde=CDEProfile.sample(), requested_allocation=50_000_000)
    app.add_pipeline(Pipeline.sample(n=20))
    out = tmp_path_factory.mktemp("embed_gate")
    paths = app.generate(str(out), formats=["markdown", "word", "excel", "pdf"])
    assert set(paths) >= {"markdown", "word", "excel", "pdf"}, (
        f"generate() produced only {sorted(paths)}; this gate cannot answer "
        "its question about a format that was not written."
    )
    return paths


def test_the_word_document_carries_no_chart_image(generated):
    """The behaviour half, executed rather than reasoned."""
    with zipfile.ZipFile(generated["word"]) as archive:
        names = archive.namelist()

    charts = sorted(
        name for name in names
        if name not in _TEMPLATE_ARTIFACTS
        and (name.startswith("word/media/") or name.lower().endswith(_IMAGE_SUFFIXES))
    )
    assert not charts, (
        f"the generated .docx contains {len(charts)} embedded image(s): "
        f"{charts}.\n\n"
        "If this is plot_winner_alignment, STOP: it draws nine unsourced "
        "winner-band constants (all HOUSE rows in "
        "tests/scoring_attribution.txt), and embedding it puts them into a "
        "document a CDE files with the CDFI Fund. See the ruling in "
        "nmtcapp/visualization/maps.plot_winner_alignment.\n\n"
        "If the constants have since been sourced or deleted, this gate is "
        "the thing to remove -- deliberately, in the commit that sources "
        "them, and say so in CHANGELOG.md."
    )


def test_the_docs_do_not_claim_charts_are_embedded():
    """The claim half. Behaviour alone would stay green over a false page."""
    if not os.path.isdir(DOCS_DIR):
        pytest.skip(
            "docs/ is absent (unpacked sdist). MANIFEST.in prunes it, so this "
            "half asks a question about the repository."
        )

    #: Phrases that assert the capability. Each is a real fragment of the
    #: sentence 1.4.0 shipped, so this is keyed on the text that was actually
    #: wrong rather than on a guess at how it might be reworded.
    claims = (
        "and embeds them in the relevant sections",
        "automatically generates all five visualization charts",
        "charts are omitted from the word document",
        "how visualizations are embedded",
    )

    offenders = []
    scanned = 0
    for dirpath, _dirs, names in os.walk(DOCS_DIR):
        for name in sorted(names):
            if not name.endswith(".md"):
                continue
            scanned += 1
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as handle:
                lowered = handle.read().lower()
            for claim in claims:
                if claim in lowered:
                    offenders.append(
                        f"  {os.path.relpath(path, _REPO_ROOT)}: {claim!r}"
                    )

    assert scanned >= 8, (
        f"scanned only {scanned} markdown files under docs/; the walk is "
        "broken and this assertion would pass over nothing."
    )
    assert not offenders, (
        "docs/ claims charts are embedded into a generated document. They are "
        "not, and the claim is not harmless -- it is what would license "
        "someone to 'fix' the code by embedding nine unsourced constants into "
        "a federal filing.\n\n" + "\n".join(offenders)
    )

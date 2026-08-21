"""THE EMBED GATE: no generated document may carry a chart, and the docs may not say it does.

WHAT THIS CLOSES (1.5.0 S4)

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
import re
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


# ---------------------------------------------------------------------------
# THE CLAIM DETECTOR: SEMANTIC, NOT FOUR LITERALS (1.5.0 F2)
#
# WHAT WAS HERE. Four exact lowercase fragments of the sentence 1.4.0 shipped:
#
#     "and embeds them in the relevant sections"
#     "automatically generates all five visualization charts"
#     "charts are omitted from the word document"
#     "how visualizations are embedded"
#
# with a comment defending the choice -- "keyed on the text that was actually
# wrong rather than on a guess at how it might be reworded."
#
# TWENTY LINES AWAY, IN A FILE THIS SUITE ALSO SHIPS,
# ``_fstring_expressions_with_backslashes`` records the opposite conclusion as
# a MEASUREMENT: its first draft was a pattern keyed on the text that was
# actually wrong, and it went green over the exact defect it was written for.
# One gate learned that lesson and its neighbour wrote the inverse down as a
# principle.
#
# AND THE WEAK VERSION WAS ALREADY FAILING, WHICH IS NOT A HYPOTHETICAL. With
# the four literals in place and the suite green,
# ``docs/workflow/visualizations.md`` carried a section headed "Embedding in
# Word output" saying "all five charts are automatically generated and embedded
# in the appropriate document sections", plus "deleted after embedding" and "To
# ensure charts are included in Word output". A live restatement of the exact
# claim, in the tree, under a passing gate -- contradicting output-formats.md
# in the same docs set, and contradicted by this module's own behavioural half.
#
# SO THE RULE IS SEMANTIC. A sentence offends when it puts a CHART word, an
# EMBEDDING word and a GENERATED-DOCUMENT word together without negating them.
# That catches rewordings, because a reworded version of this claim still has
# to name all three things -- there is no way to assert the capability while
# omitting the chart, the document, or the act of putting one in the other.
# ---------------------------------------------------------------------------

#: The thing being embedded.
_CHART_WORDS = (
    "chart", "charts", "visualization", "visualizations", "visualisation",
    "visualisations", "figure", "figures", "png", "pngs", "graphic", "graphics",
)

#: The act of putting it into a document.
_EMBED_WORDS = (
    "embed", "embeds", "embedded", "embedding", "insert", "inserts",
    "inserted", "inserting", "included in", "includes them", "included into",
    "added to", "appear in", "appears in", "placed in", "placed into",
    "attached to", "rendered into", "written into", "baked into",
    # "omitted from the Word document" asserts the capability by describing
    # its absence as the exception. If nothing is ever embedded, nothing can
    # be omitted.
    "omitted from", "left out of", "dropped from",
)

#: Phrases naming the one entry point that would have to do the embedding.
#: ``app.generate()`` writes text and tables and never touches a chart, so a
#: sentence putting a chart word next to it asserts the capability even when it
#: never uses an embedding verb -- "app.generate() automatically generates all
#: five visualization charts" was one of the four sentences that actually
#: shipped.
_GENERATE_WORDS = (
    "app.generate", "generate()", "word output enabled", "with word output",
)

#: The document it would be put into. Kept for the message, not as a
#: REQUIREMENT: "See below for how visualizations are embedded" names no
#: document and is still the claim. Requiring all three ingredients was how the
#: first draft of this detector let four paraphrases through.
_DOC_WORDS = (
    "word", "docx", ".doc", "pdf", "document", "documents", "workbook",
    "excel", "xlsx", "report", "reports", "application", "output", "filing",
)

#: Words that flip the sentence into a true statement. The docs MUST be able to
#: say "no chart is embedded in any output format" -- that sentence contains
#: all three ingredients and is the correction, not the defect.
_NEGATORS = (
    " not ", "n't", " no ", " never ", " none ", " nothing ", "cannot",
    " neither ", " nor ", "must not", "does not", "do not",
    "did not", "is not", "are not", "was not", "were not", "will not",
    "would have", " would ", "used to", "previously", "no longer", "false",
    "untrue", " once ", "becomes a", "hypothetical", "if this", "if that",
    "yours to call",
    # "suitable for embedding in presentations" describes what a READER may do
    # with a PNG this package hands them. It is true, it is the whole point of
    # returning a path, and it is not a claim that the tool does it.
    "suitable for", "you can embed", "if you want", "place it yourself",
    # a heading slug or anchor fragment, where words are joined by hyphens
    "http", ".md#",
)


def _sentences(text: str):
    """Yield (lineno, sentence), joining hard-wrapped lines first.

    SPLITTING ON NEWLINES WAS A BUG, and it was this module's own bug one level
    down. Markdown prose here is hard-wrapped at about 78 columns, so a
    sentence-per-line split cuts sentences in half -- and the half carrying the
    negation goes one way while the half carrying the claim goes the other.
    "This section previously said the opposite: it claimed app.generate() ...
    put them into the document sections automatically" reads as a clean
    assertion of the capability the moment "previously" lands on one line and
    "put them into the document" on the next.

    So paragraphs are joined before sentences are cut. The line reported is the
    first line of the paragraph the sentence came from, which is close enough
    to navigate by and cannot be wrong in a way that hides a claim.
    """
    line = 1
    for block in re.split(r"(\n\s*\n)", text):
        if not block.strip():
            line += block.count("\n")
            continue
        joined = " ".join(block.split())
        # Split only where punctuation is followed by WHITESPACE. A bare "."
        # inside `app.generate()` is not a sentence boundary, and treating it
        # as one severed the negation from the claim in this very file's
        # correction paragraph.
        for sentence in re.split(r"(?<=[.!?])\s+", joined):
            sentence = sentence.strip()
            if sentence:
                yield line, sentence
        line += block.count("\n")


def claims_charts_are_embedded(text: str) -> list:
    """[(lineno, sentence)] for sentences asserting charts go into a document.

    Exported (no leading underscore) because
    ``test_the_claim_detector_catches_rewordings`` drives it directly with
    synthetic sentences. A detector whose robustness is asserted only by the
    corpus it happens to run over is the weak version again.
    """
    hits = []
    for lineno, sentence in _sentences(text):
        low = sentence.lower().replace("*", "").replace("`", "")
        # Hyphens join words in heading slugs and anchor fragments, where
        # "are-not-embedded" must still read as a negation.
        low = " " + low.replace("-", " ").replace("_", " ") + " "
        if any(neg in low for neg in _NEGATORS):
            continue
        if not any(re.search(rf"\b{w}\b", low) for w in _CHART_WORDS):
            continue
        asserts_embedding = any(w in low for w in _EMBED_WORDS)
        asserts_generate = any(w in low for w in _GENERATE_WORDS)
        if not (asserts_embedding or asserts_generate):
            continue
        hits.append((lineno, sentence))
    return hits


def test_the_claim_detector_catches_rewordings():
    """The detector must survive paraphrase, and this proves it does.

    Every POSITIVE below is a different way of saying the same false thing --
    the four literals the old gate matched, the live sentence it MISSED in
    docs/workflow/visualizations.md, and four natural restatements. Every
    NEGATIVE is a sentence the docs must remain free to write, including the
    correction itself, which necessarily contains all three ingredients.
    """
    positives = (
        # the four the old gate keyed on
        "The builder generates the charts and embeds them in the relevant sections.",
        "app.generate() automatically generates all five visualization charts.",
        "If matplotlib is missing the charts are omitted from the Word document.",
        "See below for how visualizations are embedded.",
        # the one that was LIVE in the tree while the old gate was green
        "When you call app.generate() with Word output enabled, all five charts "
        "are automatically generated and embedded in the appropriate document "
        "sections.",
        # natural restatements
        "Each figure is inserted into the corresponding section of the report.",
        "The five PNGs are added to the Word application automatically.",
        "Visualizations appear in the generated PDF without further work.",
        "Charts are placed into the workbook during document construction.",
    )
    negatives = (
        "No chart is embedded in any output format.",
        "Visualizations are NOT embedded in any generated document.",
        "Charts are not inserted into the Word document, and that is deliberate.",
        "This section previously said all five charts were embedded in the document.",
        "All five visualization functions produce 300 DPI PNG files suitable for "
        "embedding in presentations.",
        "The readiness score appears in the Word document.",
    )

    missed = [s for s in positives if not claims_charts_are_embedded(s)]
    assert not missed, (
        f"{len(missed)} phrasing(s) of the false claim are NOT detected:\n\n"
        + "\n".join(f"  {s}" for s in missed)
        + "\n\nThe detector has to survive paraphrase. Keying it on the exact "
        "sentence that happened to ship is how the previous version stayed "
        "green while docs/workflow/visualizations.md carried the claim in "
        "different words."
    )

    wrong = [s for s in negatives if claims_charts_are_embedded(s)]
    assert not wrong, (
        f"{len(wrong)} legitimate sentence(s) are flagged as the false claim:\n\n"
        + "\n".join(f"  {s}" for s in wrong)
        + "\n\nThe docs must stay free to state the correction, which names "
        "all three ingredients by necessity. A detector that forbids the fix "
        "is worse than the bug."
    )


def test_the_docs_do_not_claim_charts_are_embedded():
    """The claim half. Behaviour alone would stay green over a false page."""
    if not os.path.isdir(DOCS_DIR):
        pytest.skip(
            "docs/ is absent (unpacked sdist). MANIFEST.in prunes it, so this "
            "half asks a question about the repository."
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
                text = handle.read()
            for lineno, sentence in claims_charts_are_embedded(text):
                offenders.append(
                    f"  {os.path.relpath(path, _REPO_ROOT)}:{lineno}\n"
                    f"      {sentence[:160]}"
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

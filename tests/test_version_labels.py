"""A version coordinate in a source comment must name a release that exists.

THE DEFECT (1.5.0 F4)

The round now published as **1.5.0** was planned and written as **1.4.1**, and
the version was re-ruled late: S3 deletes public API, so the release is MINOR,
not a patch. The CHANGELOG entry was renamed. FIFTEEN hand-typed ``1.4.1``
labels inside the code and docs were not::

    nmtcapp/renderers/_round_provenance.py:3      THE DEFECT (1.4.1 S1)
    nmtcapp/integrations/_mapper_capabilities.py:3  WHAT THIS CLOSES (1.4.1 S2)
    nmtcapp/data/benchmark_thresholds.py:407      REMOVED (1.4.1 S3)
    nmtcapp/visualization/maps.py:628,638,649,797
    nmtcapp/core/application.py:180
    docs/workflow/output-formats.md:179,218
    ... and five more

Each is a pointer into the release notes, and a reader who follows any of them
finds **no 1.4.1 entry**: there is no such heading in CHANGELOG.md and no
``v1.4.1`` tag. The labels are load-bearing -- they are how a maintainer finds
the reasoning behind a comment that says "do not undo this" -- and every one of
them pointed at nothing.

WHY THIS NEEDED A GATE RATHER THAN A FIX

``test_pinned_constants`` already polices hand-typed coordinates: it re-derives
sweep counts, mention counts and diff stats from the tree and fails when the
prose drifts. NOTHING COVERED SOURCE COMMENTS. So a release could be renumbered
in the one file the gates read and stay stale in fifteen they did not, which is
this project's most-repeated shape: the site was fixed, the class was not.

WHAT THIS DOES NOT DO. It does not check that a label is the RIGHT release --
only that it is a real one. A comment attributing 1.3.0's work to 1.2.1 passes
here, because deciding which round did what is a reading of the history and not
a property of the tree. Pointing at a release that was never published is.
"""
from __future__ import annotations

import os
import re

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Trees whose comments and prose carry these pointers.
_SCANNED = ("nmtcapp", "streamlit_app", "docs", "scripts", "tests")

#: A semantic version mentioned in prose. Anchored so it does not match inside
#: a longer dotted string (an IP, a 4-part version, a file name like
#: ``NMTC_2016_2020``).
#: Restricted to the 1.x series ON PURPOSE. Every release of this package is
#: 1.x, so a 0.x or 3.x string is a dependency or an interpreter and belongs to
#: somebody else's numbering. Scanning all of them produced more exemptions
#: than findings, and an exemption list longer than the thing it guards is
#: where a stale label goes to hide.
_VERSION_RE = re.compile(r"(?<![\w.])(1\.\d+\.\d+)(?![\w.])")

#: Versions that appear in this repository's prose but are NOT releases of this
#: package, so the CHANGELOG is the wrong place to look for them. Each is a
#: dependency floor or an external document's version, and each is listed with
#: what it actually names -- an unexplained entry here would let a stale label
#: hide behind the exemption list, which is the failure mode this file exists
#: to stop.
_NOT_OUR_RELEASES = {
    "1.6.1":  "mkdocs, whose METADATA declares markdown>=3.3.6",
    "1.36.0": "streamlit floor",
    "1.61.1": (
        "the INSTALLED Streamlit whose st.metric delta behaviour was executed "
        "for 1.5.1 T4 — _determine_delta_color_and_direction returns GREEN/UP "
        "for any delta that is neither '-'-prefixed nor exactly '0', which is "
        "why every readiness grade rendered as good news. The version is named "
        "because the finding is a claim about that library at that version"
    ),
}


#: Versions named ONLY to record that they do not exist. A comment that says
#: "this said 1.2.3 until 1.5.0 F4; no 1.2.3 was ever published" has to be able
#: to write the number down, and forbidding that would force the correction to
#: be vaguer than the defect it documents.
#:
#: 1.2.3 was a planned release that never shipped -- the series went
#: 1.2.1 -> 1.3.0. Three deferrals in benchmark_thresholds.py and three lines
#: of docs/reference/methodology.md pointed work at it, so that work had been
#: scheduled against a date that could not arrive for three releases. They now
#: say "a later release" and name no version.
_NAMED_ONLY_AS_HISTORY = {
    "1.2.3": "planned, never published; the series went 1.2.1 -> 1.3.0",
}


def _changelog_versions() -> set:
    """Every version with a real ``## [x.y.z]`` heading in CHANGELOG.md.

    CHANGELOG.md is shipped in the sdist but is NOT copied into the directory
    the release job runs the suite from, so this must skip there rather than
    error. A gate that raises FileNotFoundError in one environment is a gate
    that environment does not have.
    """
    changelog = os.path.join(_REPO_ROOT, "CHANGELOG.md")
    if not os.path.isfile(changelog):
        pytest.skip(
            "CHANGELOG.md does not sit beside tests/ (unpacked sdist). This "
            "gate compares source labels against the release history."
        )
    with open(changelog, encoding="utf-8") as fh:
        text = fh.read()
    found = set(re.findall(r"(?m)^##\s*\[(\d+\.\d+\.\d+)\]", text))
    assert len(found) > 5, (
        f"only {len(found)} release headings parsed from CHANGELOG.md — the "
        "heading regex is broken and this gate would fail everything or "
        "nothing for the wrong reason"
    )
    return found


def _scanned_files() -> list:
    out = []
    self_path = os.path.abspath(__file__)
    for tree in _SCANNED:
        root_dir = os.path.join(_REPO_ROOT, tree)
        if not os.path.isdir(root_dir):
            continue
        for dirpath, _dirs, files in os.walk(root_dir):
            for name in sorted(files):
                if not name.endswith((".py", ".md")):
                    continue
                full = os.path.join(dirpath, name)
                # This module quotes the stale labels it exists to forbid.
                if os.path.abspath(full) == self_path:
                    continue
                out.append(full)
    return sorted(out)


def test_the_scan_reaches_the_tree():
    """Fail closed: no files or no versions means the walk broke."""
    _changelog_versions()   # skips here in an unpacked sdist
    files = _scanned_files()
    assert len(files) > 50, f"only {len(files)} files walked"
    hits = sum(len(_VERSION_RE.findall(open(f, encoding="utf-8").read())) for f in files)
    assert hits > 20, f"only {hits} version-shaped strings found — the regex is broken"


def test_every_version_label_names_a_published_release():
    """No source comment may point at a release that was never published."""
    released = _changelog_versions()
    bad = []
    for path in _scanned_files():
        rel = os.path.relpath(path, _REPO_ROOT)
        with open(path, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                for version in _VERSION_RE.findall(line):
                    if (version in released or version in _NOT_OUR_RELEASES
                            or version in _NAMED_ONLY_AS_HISTORY):
                        continue
                    bad.append(f"  {rel}:{lineno}  names {version}  |  {line.strip()[:96]}")

    assert not bad, (
        f"{len(bad)} version label(s) name a release with no CHANGELOG entry:\n\n"
        + "\n".join(bad)
        + "\n\nEvery one of these is a pointer a reader follows to find why a "
        "comment says what it says. Either the label is stale — the round was "
        "renumbered and this copy was missed, which is exactly what happened "
        "to fifteen `1.4.1` labels when 1.4.1 became 1.5.0 — or it names a "
        "dependency rather than a release of this package, in which case add "
        "it to _NOT_OUR_RELEASES WITH what it names."
    )

"""Gate: the repository must distribute no committed generated artifact.

WHY

Twice now this package has shipped a generated artifact that went stale and
kept distributing a claim the generator no longer produced:

  1. examples/sample_output/*.{md,docx,pdf,xlsx} — four rendered applications
     carrying nine of the eighteen denylisted 1.1.5 fabrications, inside a
     1.2.0 branch, linked from README.md as the model for a CDE to copy.
     Deleted; generated at docs-build time instead.

  2. examples/*.ipynb — 41 cells with stored output across three notebooks.
     examples/02_full_application_walkthrough.ipynb carried "ranking in the
     top quartile tier of historical NMTC applications" verbatim, the exact
     percentile claim deleted from the generator in this same release.
     Stripped.

Both were invisible to every other gate by construction. The denylist test and
the invariance gate read artifacts they render themselves into a temp
directory; a file committed to the repo is outside their world.

The answer is not to scan committed artifacts for known-bad strings — that is
a denylist again, and it would have to be extended for every future claim.
The answer is to commit none, and to check that mechanically.

RE-EXECUTION IS NOT AN ALTERNATIVE. Refreshing a notebook's outputs produces a
new committed generated artifact with a new expiry date. Hand-editing one
produces a fabricated number, which is the thing this release is about.
examples/02 and examples/03 happen to run offline (they use the pre-enriched
Pipeline.sample fixture and never touch the geocoder), so they COULD be
re-executed honestly — and this test still forbids storing the result.
"""
from __future__ import annotations

import json
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# This gate is about what the REPOSITORY distributes, so it needs a git
# checkout. Inside an unpacked sdist there is no repository and no examples/
# (MANIFEST.in prunes it), so the question is not merely unanswerable there —
# it is not the sdist's question. Skip explicitly rather than fail.
#
# The skip is safe to trust because its condition is unambiguous and cannot
# occur in the repo, and because release.yml's FLOOR counts executed tests with
# skips subtracted: four tests silently skipping in CI shows up as a lower
# number, not as green.
_IN_GIT_CHECKOUT = (REPO_ROOT / ".git").exists()

pytestmark = pytest.mark.skipif(
    not _IN_GIT_CHECKOUT,
    reason=(
        "not a git checkout (this is an unpacked sdist or an installed tree). "
        "This gate asks what the repository has committed; there is no "
        "repository here, and MANIFEST.in prunes examples/ from the tarball."
    ),
)

# Extensions a rendered application is produced in. A file with one of these
# under version control is, by definition, output somebody committed.
RENDERED_SUFFIXES = {".docx", ".pdf"}

# Directories that legitimately hold binary inputs the CDE fills in, not
# outputs the tool produced. nmtcapp/templates/*.xlsx is a blank form and a
# labelled fictional sample; both are inputs.
INPUT_DIRS = {"nmtcapp/templates"}


def _tracked_files():
    """Every file git tracks, as repo-relative POSIX paths."""
    import subprocess
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout
    paths = [p for p in out.split("\0") if p]
    assert paths, (
        "git ls-files returned nothing — this gate would pass vacuously. "
        "Is this a git checkout?"
    )
    return paths


def test_git_ls_files_is_not_empty():
    """Fail closed: an empty file list makes every assertion below vacuous."""
    assert len(_tracked_files()) > 50, (
        "fewer than 50 tracked files; the enumeration is broken, not the repo"
    )


def test_no_notebook_carries_stored_output():
    """No committed .ipynb may carry a non-empty outputs array.

    Stored output is a snapshot of what the code produced on somebody's laptop
    on some past date, distributed as if it were current.
    """
    offenders = []
    notebooks = [p for p in _tracked_files() if p.endswith(".ipynb")]
    assert notebooks, (
        "no notebooks found — if examples/ was removed, delete this test "
        "rather than leaving it passing on an empty set"
    )
    for rel in notebooks:
        nb = json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))
        for i, cell in enumerate(nb.get("cells", [])):
            if cell.get("outputs"):
                offenders.append(f"{rel} cell {i}: {len(cell['outputs'])} output(s)")
            if cell.get("execution_count") is not None:
                offenders.append(f"{rel} cell {i}: execution_count is set")
    assert not offenders, (
        f"{len(offenders)} committed notebook cell(s) carry stored output or an "
        "execution count.\n\n"
        "A notebook's stored output is a committed generated artifact. "
        "examples/02_full_application_walkthrough.ipynb carried 'ranking in the "
        "top quartile tier of historical NMTC applications' this way — a claim "
        "deleted from the generator in the same release that still shipped it.\n\n"
        "Clear outputs before committing (Kernel > Restart & Clear Output, or "
        "nbstripout). Do NOT re-execute to refresh them: that just resets the "
        "clock on the same defect.\n\n"
        + "\n".join(f"  {o}" for o in offenders)
    )


def test_no_rendered_application_is_committed():
    """No .docx / .pdf under version control outside the template inputs."""
    offenders = [
        p for p in _tracked_files()
        if pathlib.PurePosixPath(p).suffix.lower() in RENDERED_SUFFIXES
        and not any(p.startswith(d) for d in INPUT_DIRS)
    ]
    assert not offenders, (
        f"{len(offenders)} rendered document(s) are committed:\n"
        + "\n".join(f"  {p}" for p in offenders)
        + "\n\nexamples/sample_output/ shipped four of these carrying the "
        "complete 1.1.5 fabrication set inside a 1.2.0 branch. Sample output "
        "is generated at docs-build time — see docs/hooks/generate_sample_output.py."
    )


@pytest.mark.parametrize("path", ["examples/sample_output"])
def test_deleted_output_directory_stays_deleted(path):
    """The directory is gitignored; assert it is also untracked."""
    tracked = [p for p in _tracked_files() if p.startswith(path)]
    assert not tracked, (
        f"{path} is tracked again ({len(tracked)} files). It is in .gitignore; "
        "something added it with `git add -f`."
    )

"""THE EXAMPLE NOTEBOOKS MUST RUN. Three were shipping broken (1.5.5 audit B1+).

WHY THIS MODULE EXISTS, AND WHY NO STATIC GATE WAS GOING TO DO IT

The 1.5.5 audit-close brief asked for one thing here: remove the ``CY2025``
round literal from ``examples/01_quickstart.ipynb`` and
``examples/02_full_application_walkthrough.ipynb``, and then EXECUTE BOTH
NOTEBOOKS and report what the generated document says. Executing them is what
found the rest of it. Three defects, in all three notebooks, none related to
the round and none visible to any gate in this suite:

  1. ``02`` cell 14  ``df_pipeline[["...", "Sector (NAICS)", ...]]`` ->
     ``KeyError: "['Sector (NAICS)'] not in index"``. The column was renamed to
     "Sector (as supplied)" by ad2c7ba on 2026-08-14 -- because the tool was
     inventing the NAICS code it filed -- and the notebook was not part of the
     rename. Broken for four releases.

  2. ``03`` cell 1   ``from nmtcapp.data.benchmark_thresholds import
     TOP_TIER_AGGREGATE_MIN, TOP_TIER_SECTION_MIN`` -> ``ImportError``. 1.2.2
     renamed both to ``HOUSE_*`` so the name would carry the provenance (the
     CDFI Fund publishes no tier above Highly Qualified). That rename's own
     note says "A rename breaks every consumer at import time, which is the
     only way to guarantee no interpolated surface kept the old wording" --
     and it was right, and nothing was watching this consumer.

  3. ``03`` cells 5 and 12 -> ``TypeError`` on ``None``. When the eligibility
     dataset does not load, the distress sub-scores are WITHDRAWN rather than
     defaulted, and the section's ``max_available`` shrinks from 50 to 25. The
     notebook formatted them with ``f"{value:5.1f}"`` and subtracted them.
     THIS IS THIS RELEASE'S OWN DISCLOSURE MECHANISM CRASHING THE DOCUMENTED
     EXAMPLE -- the same shape as the round defect B1 names, one surface over:
     the tool correctly declines to assert what it cannot verify, and the
     front door falls over instead of showing the reader the disclosure.
     Cell 5 also printed "/ 50" for a section whose maximum was 25.

WHY NOT MORE STATIC GATES. Two of the three have a static shape and one does
not. ``test_documented_keys`` was widened this round to catch (1) by binding
each subscript to the ``build_*`` call that produced the frame, and an import
resolver would catch (2). Nothing static catches (3): the keys all exist, the
types are right in every environment where the dataset loads, and the defect
is a VALUE that is None on one code path. The only mechanism that sees it is
running the cell, which is also the only mechanism that matches what the
reader does.

THE COST, MEASURED RATHER THAN FEARED. 8.5 seconds for all three notebooks on
3.12.13 -- 2.1 + 5.1 + 1.3 -- against a suite that takes about 100. That is
cheap enough that the argument for a static proxy disappears.

WHY ``allow_errors=False``. The client raises on the first failing cell, so
the failure names the cell and carries its traceback. Collecting every error
and asserting on the list reads better and is worse: cell N+1 usually fails
because cell N did, and a list of five downstream NameErrors buries the one
that matters.

SCOPE, STATED. This asserts the notebooks RUN. It does not assert what they
print -- the round disclosure's rendered text is held by
``tests/test_application_round.py::TestRenderedSurfaces`` against the library
directly, which is where a claim about rendered wording belongs. A notebook
gate that pinned output would go red on every unrelated fixture change and be
deleted within two releases.
"""
from __future__ import annotations

import os

import pytest

EXAMPLES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples"
)


#: The example notebooks, NAMED rather than walked.
#:
#: WHY NOT A DIRECTORY WALK, which is what the first draft did. Parametrising
#: over ``os.listdir`` makes the COLLECTED TEST COUNT depend on the
#: environment: ``examples/`` is pruned from the sdist, so the walk returned
#: three names in a checkout and none in the tarball, and the module collected
#: a different number of tests in each. That breaks a property this suite
#: relies on -- ``tests/test_test_count_claims.py`` asserts that ONE published
#: number is what the tree collects, and a number that differs between the
#: checkout and the sdist cannot be published at all. Caught by building the
#: sdist, which is the only place it is visible.
#:
#: Named, the parametrisation is identical everywhere and each case skips in
#: the tarball instead of vanishing from it.
NOTEBOOKS = (
    "01_quickstart.ipynb",
    "02_full_application_walkthrough.ipynb",
    "03_intelligence_and_optimization.ipynb",
)


def _notebooks_on_disk() -> list:
    if not os.path.isdir(EXAMPLES_DIR):
        return []
    return sorted(
        name for name in os.listdir(EXAMPLES_DIR) if name.endswith(".ipynb")
    )


#: MANIFEST.in prunes ``examples/`` from the sdist, so its absence there is
#: correct and this module has nothing to run. Guarded the way every other
#: tree-reading gate in this suite is guarded -- and NOT with a bare
#: ``importorskip`` on nbclient: ``jupyter>=1.0`` is a declared ``[dev]``
#: dependency, so a missing kernel is a broken environment and must be loud.
examples_present = pytest.mark.skipif(
    not os.path.isdir(EXAMPLES_DIR),
    reason="examples/ is pruned from the sdist by MANIFEST.in; nothing to run",
)


@examples_present
def test_the_named_notebooks_are_the_ones_on_disk():
    """Fails closed, in both directions.

    A notebook added to ``examples/`` and not to ``NOTEBOOKS`` would ship
    untested; a name in ``NOTEBOOKS`` that no longer exists would make its
    parametrised case pass over nothing.
    """
    assert _notebooks_on_disk() == sorted(NOTEBOOKS), (
        f"examples/ holds {_notebooks_on_disk()}, this module names "
        f"{sorted(NOTEBOOKS)}. Every example notebook must be executed by this "
        "gate -- README.md links 01 and 02 as the documented front door."
    )


@examples_present
@pytest.mark.parametrize("notebook", NOTEBOOKS)
def test_the_example_notebook_runs_start_to_finish(notebook, tmp_path):
    """Every cell of every example notebook executes without raising.

    A reader who runs the documented walkthrough gets what this test gets.
    """
    import nbformat
    from nbclient import NotebookClient

    path = os.path.join(EXAMPLES_DIR, notebook)
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(
        nb,
        timeout=600,
        kernel_name="python3",
        allow_errors=False,
        # Run in a temp directory: the walkthrough WRITES generated documents,
        # and tests/test_no_committed_generated_artifacts.py exists because
        # they once landed in the repository.
        resources={"metadata": {"path": str(tmp_path)}},
    )
    client.execute()

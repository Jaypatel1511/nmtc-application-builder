"""release.yml deploys the docs after publish, through one job a human can run first.

THE DEFECT (1.7.1 R1). Two consecutive releases shipped federal-fact
corrections to PyPI that never reached the website, because gh-pages was a
manual ``mkdocs gh-deploy`` nobody ran: 1.6.5's stale sample carried dead
deadlines; 1.7.0's carried a live false negative about a federal question,
downloadable as Word and PDF, 52 days before the filing deadline. 1.6.5's own
cycle wrote "a deploy that is manual is a surface that is stale" and left
the remedy as a runbook suggestion.

WHAT THIS ASSERTS, against the workflow TEXT (as tests/test_release_floor
does; PyYAML is not a dev dependency):

  release.yml   has a ``docs`` job; it ``needs: publish`` and nothing runs
                it beside publish; it calls docs-deploy.yml with
                ``deploy: true``; ``contents: write`` is on that job and the
                workflow-level permission is still ``contents: read``.
  docs-deploy   is callable AND dispatchable; the dispatch default is a dry
                run; its toolchain is ci.yml's docs job exactly (Python
                3.12, ``pip install ".[docs]"``, ``--strict``); it fetches
                gh-pages before deploying so the push is a fast-forward; it
                pins the same action SHAs ci.yml pins; the real deploy is
                gated on the input and the dry run pushes with --dry-run.

WHY A TEXT GATE FOR A WORKFLOW. release.yml is edited by a session that
cannot run it. What CAN be checked here is that the shape a reviewer read
is the shape that ships — a job renamed, a ``needs`` dropped, a
``contents: write`` hoisted to the workflow, or a toolchain line "tidied"
into something ci.yml does not run, each go red before a tag depends on
them. The runbook for proving the job itself is in the module docstring of
docs-deploy.yml and in CONTRIBUTING.md.

MUTATION RECORD (2026-09-19): ``needs: publish`` removed -> red;
``contents: write`` moved to the workflow level -> red (two tests);
``.[docs]`` retyped as ``.[dev]`` -> red; ``--strict`` dropped from the
deploy line -> red; ``--dry-run`` dropped -> red.

THE REF GUARD (post-1.7.1). ``workflow_dispatch`` with ``deploy: true`` from
any branch published that branch's docs to gh-pages. The real push is now
gated on the input AND the ref: main for a hand-run, a ``v*`` tag for
release.yml's call (a called workflow sees the CALLER's context, so that run
has ``github.ref == refs/tags/vX.Y.Z`` and ``event_name == push``). A naive
``refs/heads/main`` guard would have skipped every release-time deploy, so
this module EVALUATES both ``if:`` expressions over the full truth table
rather than matching their text. Folded into the existing gated-push test on
purpose: a new test here is a new sdist skip, and MAX_SDIST_SKIPS in
tests/test_release_floor.py sits on its bound. MUTATION RECORD
(2026-09-24): ref guard removed from the deploy step -> red; the tag arm
removed -> red; the refusal step removed -> red.
"""
from __future__ import annotations

import os
import re

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WORKFLOWS = os.path.join(_REPO, ".github", "workflows")


def _read(name: str) -> str:
    path = os.path.join(_WORKFLOWS, name)
    if not os.path.exists(path):
        pytest.skip(f".github/workflows/{name} is absent — an unpacked sdist "
                    "does not ship the workflows; this gate is about the repository.")
    return open(path, encoding="utf-8").read()


def _job_block(text: str, job: str) -> str:
    """The lines of one top-level job, from its key to the next job key."""
    m = re.search(rf"^  {re.escape(job)}:\n(.*?)(?=^  \S|\Z)", text, re.M | re.S)
    assert m, f"no job named {job!r}"
    return m.group(1)


@pytest.fixture(scope="module")
def release() -> str:
    return _read("release.yml")


@pytest.fixture(scope="module")
def deploy() -> str:
    return _read("docs-deploy.yml")


@pytest.fixture(scope="module")
def ci() -> str:
    return _read("ci.yml")


# --- release.yml ------------------------------------------------------------

def test_release_has_a_docs_job_that_runs_after_publish(release):
    block = _job_block(release, "docs")
    needs = re.search(r"^    needs:\s*(.+)$", block, re.M)
    assert needs, "the docs job has no `needs:` — it would run beside publish"
    assert re.fullmatch(r"publish|\[\s*publish\s*\]", needs.group(1).strip()), (
        f"the docs job needs {needs.group(1)!r}; it must wait for publish and "
        "nothing else, so the site never advertises a version PyPI does not serve"
    )
    assert re.search(r"^    uses:\s*\./\.github/workflows/docs-deploy\.yml\s*$", block, re.M), (
        "the docs job does not call docs-deploy.yml — a second definition of "
        "the deploy is the drift this module exists to prevent"
    )
    assert re.search(r"^      deploy:\s*true\s*$", block, re.M), (
        "release.yml must call the deploy with deploy: true; the dispatch "
        "default is a dry run"
    )


def test_release_scopes_contents_write_to_the_docs_job(release):
    block = _job_block(release, "docs")
    assert re.search(r"^    permissions:\n      contents:\s*write\s*$", block, re.M), (
        "the docs job does not carry `permissions: contents: write`; a push "
        "to gh-pages needs it and nothing else in release.yml should have it"
    )
    top = release.split("\njobs:", 1)[0]
    assert re.search(r"^permissions:\n  contents:\s*read\s*$", top, re.M), (
        "release.yml's workflow-level permission is no longer `contents: read`"
    )
    for job in ("verify-version", "build", "test-wheel", "test-sdist"):
        assert "contents: write" not in _job_block(release, job), (
            f"{job} carries contents: write; only the docs job may"
        )


def test_no_other_release_job_deploys_docs(release):
    for job in ("verify-version", "build", "test-wheel", "test-sdist", "publish"):
        block = _job_block(release, job)
        assert "gh-deploy" not in block and "ghp_import" not in block, (
            f"{job} deploys docs; the deploy lives in docs-deploy.yml only"
        )


# --- docs-deploy.yml --------------------------------------------------------

def test_deploy_is_callable_and_dispatchable_and_dispatch_is_a_dry_run(deploy):
    on = deploy.split("\njobs:", 1)[0]
    assert re.search(r"^  workflow_call:", on, re.M), "not callable from release.yml"
    assert re.search(r"^  workflow_dispatch:", on, re.M), "not runnable by hand"
    dispatch = on.split("workflow_dispatch:", 1)[1]
    assert re.search(r"deploy:.*?default:\s*false", dispatch, re.S), (
        "a hand-run must default to the dry run; a maintainer proving the job "
        "must not deploy a branch's docs by accident"
    )
    call = on.split("workflow_call:", 1)[1].split("workflow_dispatch:", 1)[0]
    assert re.search(r"deploy:.*?default:\s*true", call, re.S)


def test_deploy_toolchain_matches_ci_docs_job_exactly(deploy, ci):
    ci_docs = _job_block(ci, "docs")
    for needle in ('python-version: "3.12"', 'pip install ".[docs]"', "mkdocs build --strict"):
        assert needle in ci_docs, f"ci.yml's docs job no longer carries {needle!r}; re-derive this gate"
    assert re.search(r"python-version:\s*['\"]3\.12['\"]", deploy), "deploy does not use Python 3.12"
    assert 'pip install ".[docs]"' in deploy, "deploy does not install the [docs] extra"
    assert "python -m mkdocs build --strict" in deploy, "deploy does not run the strict build first"
    assert re.search(r"python -m mkdocs gh-deploy\b[^\n]*--strict", deploy), (
        "the real deploy line does not pass --strict; the sample-output hook's "
        "RuntimeError is what makes this job mean something"
    )


def test_deploy_pins_the_same_action_shas_as_ci(deploy, ci):
    def pins(text):
        return set(re.findall(r"uses:\s*(actions/(?:checkout|setup-python)@[0-9a-f]{40})", text))
    assert pins(deploy), "no pinned actions in docs-deploy.yml"
    assert pins(deploy) <= pins(ci), (
        f"docs-deploy.yml pins {sorted(pins(deploy) - pins(ci))}, which ci.yml "
        "does not; one pin per action across the repository"
    )


def test_deploy_fetches_gh_pages_before_pushing(deploy):
    steps = deploy.split("\n    steps:", 1)[1]
    fetch = steps.find("refs/heads/gh-pages:refs/remotes/origin/gh-pages")
    real = steps.find("mkdocs gh-deploy")
    dry = steps.find("ghp_import")
    assert fetch != -1, "gh-pages is never fetched; ghp-import would start a fresh root and the push would need --force"
    assert fetch < real and fetch < dry, "the fetch must precede both deploy paths"
    assert "--force" not in steps and "--no-history" not in steps, (
        "a forced deploy rewrites gh-pages history; the branch is fetched so the push fast-forwards"
    )


def _step_if(steps: str, name_prefix: str) -> str:
    """The ``${{ ... }}`` body of the ``if:`` on the step whose name starts so."""
    m = re.search(
        rf"^      - name: {re.escape(name_prefix)}[^\n]*\n"
        r"        if:\s*\$\{\{\s*(.*?)\s*\}\}\s*$",
        steps, re.M,
    )
    assert m, f"no step named {name_prefix!r} with an `if:` on its next line"
    return m.group(1)


def _evaluate(expr: str, *, deploy: bool, event: str, ref: str) -> bool:
    """A GitHub Actions ``if:`` over the four terms this workflow uses.

    Deliberately narrow: any token outside the whitelist fails the test, so a
    condition this translator does not understand cannot evaluate "true" by
    accident. Actions compares strings case-insensitively; every literal here
    is already lower-case, and so is every ref this is fed.
    """
    py = expr
    for a, b in (("&&", " and "), ("||", " or "), ("!", " not "),
                 ("inputs.deploy", "DEPLOY"), ("github.event_name", "EVENT"),
                 ("github.ref", "REF"), ("startsWith", "STARTS")):
        py = py.replace(a, b)
    leftover = re.sub(r"'[^']*'|\b(?:and|or|not|DEPLOY|EVENT|REF|STARTS)\b|==|[(),\s]", "", py)
    assert not leftover, f"unrecognised tokens in the `if:` expression: {leftover!r}"
    return bool(eval(py, {"__builtins__": {}}, {  # noqa: S307 - whitelisted above
        "DEPLOY": deploy, "EVENT": event, "REF": ref,
        "STARTS": lambda s, p: s.startswith(p)}))


#: (event, ref, deploy input) -> may the real push run. The release row is the
#: one a naive `refs/heads/main` guard gets wrong.
_REF_TRUTH_TABLE = (
    ("push", "refs/tags/v1.7.2", True, True),               # release.yml -> workflow_call
    ("workflow_dispatch", "refs/heads/main", True, True),   # manual redeploy from main
    ("workflow_dispatch", "refs/heads/main", False, False),  # dry run on main
    ("workflow_dispatch", "refs/heads/feature/x", True, False),  # THE FINDING
    ("workflow_dispatch", "refs/heads/feature/x", False, False),
    ("workflow_dispatch", "refs/tags/v1.6.5", True, False),  # an old tag's docs over the site
    ("workflow_dispatch", "refs/heads/mainline", True, False),
    ("push", "refs/heads/main", False, False),
)


def test_the_real_push_is_gated_and_the_dry_run_never_writes(deploy):
    steps = deploy.split("\n    steps:", 1)[1]
    real = re.search(r"if:\s*\$\{\{\s*inputs\.deploy\b[^\n]*\}\}.*?gh-deploy", steps, re.S)
    assert real, "the real deploy is not gated on inputs.deploy"

    # THE REF GUARD: evaluated, not pattern-matched.
    push_if = _step_if(steps, "Deploy to gh-pages")
    refuse_if = _step_if(steps, "Refuse a real deploy")
    refuse_step = steps.split("- name: Refuse a real deploy", 1)[1].split("\n      - ", 1)[0]
    assert re.search(r"^\s*exit 1\s*$", refuse_step, re.M), "the refusal step does not fail the run"
    assert steps.find("- name: Refuse a real deploy") < steps.find("uses: actions/checkout"), (
        "the refusal must be the first step, so a refused run fails before building"
    )
    for event, ref, want_deploy, may_push in _REF_TRUTH_TABLE:
        got_push = _evaluate(push_if, deploy=want_deploy, event=event, ref=ref)
        got_refuse = _evaluate(refuse_if, deploy=want_deploy, event=event, ref=ref)
        assert got_push == may_push, (
            f"({event}, {ref}, deploy={want_deploy}): the gh-deploy step would "
            f"{'run' if got_push else 'skip'}; it must {'run' if may_push else 'skip'}"
        )
        assert got_refuse == (want_deploy and not may_push), (
            f"({event}, {ref}, deploy={want_deploy}): the refusal step would "
            f"{'fail' if got_refuse else 'pass'} the run -- a requested deploy "
            "that is not honoured must go red, and an honoured one must not"
        )

    dry = re.search(r"if:\s*\$\{\{\s*!inputs\.deploy\s*\}\}.*?(?=\n      - name:|\Z)", steps, re.S)
    assert dry, "no dry-run step gated on !inputs.deploy"
    assert "git push --dry-run origin gh-pages" in dry.group(0), (
        "the dry run does not exercise the push; a 403 would surface only on release day"
    )
    assert re.search(r"ghp_import\s+-n\b", dry.group(0)), "the dry run must commit without pushing (-n)"
    assert not re.search(r"git push (?!--dry-run)", dry.group(0)), "the dry run pushes for real"

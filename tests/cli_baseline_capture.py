"""Capture `nmtcapp analyze`'s full output in every analyzer state.

WHY THIS EXISTS (1.4.0 proof 2)

`nmtcapp analyze` is a rendered surface — it is where a CDE first reads its own
distress shares, its geographic split and its readiness score back — and it had
no baseline of any kind. The four generated documents have one; the workbook has
a cell-level one; the screen has an AST gate. The CLI summary had nothing, so
any change to it was invisible to review unless someone ran it by eye.

DETERMINISM IS THE WHOLE PROBLEM, and it is solved by REPLAY rather than by
stubbing. `analyze` geocodes every project against the live Census geocoder and
stamps a wall-clock timestamp. A hand-written stub would make the capture
deterministic and would also make it a test of the stub — the exact failure
tests/mapper_doubles.py exists to name. So the mapper's real answers are
recorded once into a JSON fixture and replayed on both sides of a diff: the
diff is then about this package's code and nothing else.

THE FIVE STATES. `enrich_pipeline_eligibility` has four terminal statuses and
one branch inside the fourth that changes what renders, and all five are
captured because the summary text differs in each:

    ok             every project geocoded and its tract was found
    partial        some projects unverified — banner + inline qualifiers
    unavailable    the eligibility dataset would not load; no tier assigned
    pre_enriched   values supplied by the caller, no lookup this run
    empty          a pipeline whose QEI is zero

WHAT IS NORMALISED, AND WHY EACH ONE IS SAFE: the analysis timestamp (wall
clock), absolute paths (machine), and the nmtc-mapper loader's progress lines
(cache state). Nothing else. In particular NO NUMBER is masked — masking digits
is what tests/pinned_constants.txt exists to compensate for elsewhere in this
package, and a CLI baseline that masked them could not see a moved percentage,
which is the thing this capture was built to see.
"""
from __future__ import annotations

import contextlib
import io
import json
import logging
import os
import re
import sys
from contextlib import redirect_stdout, redirect_stderr

import nmtcapp
from unittest.mock import MagicMock, patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPLAY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "cli_baseline_replay.json")

#: The pipeline every state is captured against. The shipped strong sample:
#: 20 projects, 19 states, and the only fixture in the tree wide enough for the
#: geographic split to be interesting.
#:
#: RESOLVED THROUGH THE INSTALLED PACKAGE, not through the repo root. The sdist
#: test job copies ONLY tests/, streamlit_app/, README.md and pyproject.toml
#: out of the tarball into a directory with no nmtcapp/ in it, and imports the
#: package from site-packages — so a path built from
#: ``dirname(dirname(__file__))`` points at a template that is not there.
#: Measured: `analyze` printed "ERROR: Pipeline CSV not found" and all three
#: gates in tests/test_cli_baseline.py went red inside the tarball while the
#: same suite was green in the repo. That is the same shape as the
#: invariant_allowlist.txt packaging defect this repo's MANIFEST.in records.
_PACKAGE_DIR = os.path.dirname(os.path.abspath(nmtcapp.__file__))
SAMPLE_CSV = os.path.join(_PACKAGE_DIR, "templates", "pipeline_sample_strong.csv")

_REPLAY_FIELDS = (
    "address", "tract_id", "nmtc_eligible", "distress_level", "poverty_rate",
    "ami_ratio", "unemployment_rate", "is_non_metro", "is_high_migration_rural",
    "severe_distress", "deep_distress", "geocode_success",
    "is_opportunity_zone", "tract_found",
)


def _normalise(text: str) -> str:
    """Strip the three machine/clock-dependent things, and only those."""
    text = re.sub(r"Analyzed: \d{4}-\d{2}-\d{2}T[\d:.]+", "Analyzed: <TIMESTAMP>", text)
    # Both roots: the repo when run from a checkout, and site-packages when
    # run from the sdist. Longest first, so a nested match is not half-replaced.
    for root, token in sorted(
            ((_PACKAGE_DIR, "<PACKAGE>"), (_ROOT, "<REPO>")),
            key=lambda pair: -len(pair[0])):
        text = text.replace(root, token)
    text = re.sub(r"^.*\.nmtcmapper/cache.*$", "<MAPPER CACHE LINE>", text, flags=re.M)
    text = re.sub(r"^(Loading|Ready\.|Eligibility table loaded|Loaded [\d,]+ Opportunity|"
                  r"Opportunity Zones loaded|Using cached).*$", "<MAPPER LOADER LINE>",
                  text, flags=re.M)
    text = re.sub(r"(?:<MAPPER LOADER LINE>\n|<MAPPER CACHE LINE>\n)+",
                  "<MAPPER LOADER LINES>\n", text)
    return text


def record_replay() -> dict:
    """Run the REAL mapper once over the sample and store every answer.

    Network + the CDFI Fund workbook are needed for this, and only for this.
    Run it deliberately; the JSON it writes is what every later capture uses.
    """
    from nmtcmapper import NMTCMapper
    from nmtcapp.core.pipeline import Pipeline

    mapper = NMTCMapper()
    out = {}
    for project in Pipeline.from_csv(SAMPLE_CSV):
        result = mapper.check_address(project.full_address)
        out[project.full_address] = {
            f: getattr(result, f, None) for f in _REPLAY_FIELDS
        }
    with open(REPLAY_PATH, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    return out


def _replay_mapper(overrides=None):
    """A mapper whose check_address replays the recorded answers.

    Returns real ``EligibilityResult`` objects built from the installed
    dataclass — see tests/mapper_doubles for why a SimpleNamespace here would
    re-arm the defect this round found.
    """
    from tests.mapper_doubles import eligibility_result

    with open(REPLAY_PATH, encoding="utf-8") as fh:
        recorded = json.load(fh)
    overrides = overrides or {}

    def check_address(address):
        fields = dict(recorded[address])
        fields.update(overrides.get(address, {}))
        return eligibility_result(**fields)

    mapper = MagicMock()
    mapper.data_source = "cdfi_fund"
    mapper.check_address.side_effect = check_address
    return mapper


def _run_cli(argv) -> str:
    """Run cmd_analyze in-process and return stdout+stderr, normalised."""
    from nmtcapp import cli

    buf_out, buf_err = io.StringIO(), io.StringIO()
    old = sys.argv
    sys.argv = ["nmtcapp"] + argv
    try:
        with _captured_logging(buf_err), redirect_stdout(buf_out), \
                redirect_stderr(buf_err):
            try:
                cli.main()
            except SystemExit as exc:
                print(f"[exit {exc.code}]", file=buf_out)
    finally:
        sys.argv = old
    return _normalise(buf_out.getvalue() + buf_err.getvalue())


_ADAPTER = "nmtcapp.integrations.nmtc_mapper_adapter"


@contextlib.contextmanager
def _captured_logging(buf):
    """Route this package's log records into ``buf``, and nowhere else.

    WHY THIS IS NOT LEFT TO THE AMBIENT CONFIG. The adapter's warnings —
    "Location could not be verified for project PRJ-S004", "eligibility data
    unavailable" — are part of what a CDE sees, so they belong in the capture.
    Where they GO, though, depends on who is running: under ``python -m`` the
    root logger's last-resort handler writes them to stderr and the redirect
    catches them; under pytest, caplog has already attached a handler and set
    propagation, and they never reach the redirected stream. Same code, two
    different baselines, and the file would flip depending on how it was
    produced.

    So the handler is explicit for the duration of a capture: this package's
    logger gets one handler writing into the buffer, propagation off, level
    pinned. Restored afterwards.
    """
    logger_ = logging.getLogger("nmtcapp")
    handler = logging.StreamHandler(buf)
    handler.setFormatter(logging.Formatter("%(message)s"))
    saved = (logger_.handlers[:], logger_.propagate, logger_.level)
    logger_.handlers = [handler]
    logger_.propagate = False
    # WARNING, not INFO — this captures what a CDE actually sees. Python's
    # last-resort handler is WARNING-level, and `nmtcapp analyze` configures no
    # logging of its own, so WARNING is the real default for someone running
    # the command. INFO would also capture records nobody sees.
    #
    # AND INFO WOULD CRASH THE CAPTURE, which is a finding rather than a
    # reason: nmtcapp/core/application.py:181 logs "allocation $%,.0f", which
    # is not a valid printf conversion in Python, so every Application()
    # construction raises inside logging.Formatter under any INFO-level
    # configuration. logging swallows it to stderr via handleError, so the
    # program keeps running and a "Logging error" traceback prints instead of
    # the record. Out of scope for 1.4.0 by the round's own brief and recorded
    # here so the next person to raise this level knows what they will hit.
    logger_.setLevel(logging.WARNING)
    try:
        yield
    finally:
        logger_.handlers, logger_.propagate, logger_.level = saved


def capture_state(state: str) -> str:
    """Capture the analyze summary in one named analyzer state."""
    argv = ["analyze", SAMPLE_CSV, "--demo"]

    if state == "ok":
        with patch("nmtcmapper.NMTCMapper", return_value=_replay_mapper()):
            return _run_cli(argv)

    if state == "partial":
        # Two projects unverified: one geocode miss, one tract-not-found.
        with open(REPLAY_PATH, encoding="utf-8") as fh:
            addresses = sorted(json.load(fh))
        overrides = {
            addresses[-1]: {"geocode_success": False},
            addresses[-2]: {"tract_found": False},
        }
        with patch("nmtcmapper.NMTCMapper",
                   return_value=_replay_mapper(overrides)):
            return _run_cli(argv)

    if state == "unavailable":
        from nmtcmapper import NMTCMapperError
        with patch("nmtcmapper.NMTCMapper",
                   side_effect=NMTCMapperError(
                       "eligibility dataset could not be loaded (captured)")):
            return _run_cli(argv)

    if state == "pre_enriched":
        # Pipeline.sample() arrives fully enriched, so no lookup happens.
        # Written to a CSV would lose the enrichment, so it is driven through
        # the library rather than through the CLI's from_csv path.
        return _capture_pre_enriched()

    if state == "empty":
        return _capture_empty()

    raise ValueError(f"unknown state {state!r}")


def _capture_pre_enriched() -> str:
    from nmtcapp.core.application import Application
    from nmtcapp.core.cde import CDEProfile
    from nmtcapp.core.pipeline import Pipeline

    buf = io.StringIO()
    app = Application(cde=CDEProfile.sample(), requested_allocation=55_000_000)
    app.add_pipeline(Pipeline.sample())
    with _captured_logging(buf), redirect_stdout(buf), redirect_stderr(buf):
        app.analyze().summary()
    return _normalise(buf.getvalue())


def _capture_empty() -> str:
    """A pipeline whose geographic split has no dollars to divide.

    The three shares are 0.0 here and do NOT sum to 1.0, which is the one case
    the R2 invariant deliberately does not hold; capturing it pins how that
    renders rather than leaving it to be discovered.
    """
    from nmtcapp.intelligence.geographic_analysis import analyze_geographic_diversity
    from nmtcapp.core.pipeline import Pipeline

    result = analyze_geographic_diversity(Pipeline([]))
    return json.dumps(result, indent=2, sort_keys=True, default=str) + "\n"


STATES = ("ok", "partial", "unavailable", "pre_enriched", "empty")


def capture_all() -> str:
    parts = []
    for state in STATES:
        parts.append(f"{'=' * 70}\n@@ STATE: {state}\n{'=' * 70}\n")
        parts.append(capture_state(state))
    return "".join(parts)


if __name__ == "__main__":
    if "--record-replay" in sys.argv:
        record_replay()
        print(f"recorded -> {REPLAY_PATH}")
    else:
        sys.stdout.write(capture_all())

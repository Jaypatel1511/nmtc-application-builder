"""Regenerate tests/rendered_baseline/ — a DELIBERATE act, never automatic.

    python -m tests.regen_rendered_baseline

The baseline is the review artifact. If the gate could write it on failure it
could never fail, which is the shape this package keeps producing; so writing
it is a separate command a human runs, and the result belongs in the same
commit as the change that moved it, where a reviewer reads the rendered diff
alongside the code diff.

Nothing here is imported by the test module at runtime — it reads the same
fixture from tests/test_rendered_output_baseline.py, so the two cannot drift.
"""
from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import tempfile

from nmtcapp.core.application import Application
from tests.test_rendered_output_baseline import (
    APPLICATION_ROUND, BASELINE_DIR, FORMATS, REQUESTED_ALLOCATION,
    _cde, _extract, _normalise, _pipeline,
)


def main() -> int:
    os.makedirs(BASELINE_DIR, exist_ok=True)
    app = Application(
        cde=_cde(),
        requested_allocation=REQUESTED_ALLOCATION,
        application_round=APPLICATION_ROUND,
    )
    app.add_pipeline(_pipeline())

    with tempfile.TemporaryDirectory() as out:
        paths = app.generate(out, formats=list(FORMATS))
        missing = set(FORMATS) - set(paths)
        if missing:
            print(f"REFUSING to write a partial baseline: {sorted(missing)} "
                  "did not render. Install the [dev] extra.", file=sys.stderr)
            return 1
        for fmt in FORMATS:
            text = _normalise(_extract(fmt, paths[fmt]), out).rstrip("\n") + "\n"
            target = os.path.join(BASELINE_DIR, f"{fmt}.txt")
            with open(target, "w", encoding="utf-8") as fh:
                fh.write(text)
            print(f"  wrote {os.path.relpath(target, _REPO_ROOT)} "
                  f"({len(text.splitlines())} lines)")

    print("\nRead the git diff of tests/rendered_baseline/ before committing. "
          "Every changed line is either an intended fix or a regression "
          "nobody chose.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

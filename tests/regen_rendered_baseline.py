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

# THE SAME RENDER THE GATE PERFORMS, through the same function (1.6.4). This
# used to build the Application and normalise here, in parallel with
# _render_projections; the two agreed by inspection. _render_projections now
# also freezes the round-provenance note's Eastern date to LAST_VERIFIED, and
# a regen that did not would write a baseline the gate could never match.
from tests.test_rendered_output_baseline import (
    BASELINE_DIR, FORMATS, _render_projections,
)


def main() -> int:
    os.makedirs(BASELINE_DIR, exist_ok=True)

    with tempfile.TemporaryDirectory() as out:
        try:
            projected = _render_projections(out)
        except AssertionError as exc:
            print(f"REFUSING to write a partial baseline: {exc}",
                  file=sys.stderr)
            return 1
        for fmt in FORMATS:
            text = projected[fmt]
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

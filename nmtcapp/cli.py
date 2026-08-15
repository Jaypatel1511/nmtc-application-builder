"""
Command-line interface for nmtc-application-builder.

Usage::

    nmtcapp init <directory>   — creates a starter project in <directory>
    nmtcapp analyze <csv>      — runs analyze() on a pipeline CSV and prints summary
    nmtcapp version            — prints version
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def _get_templates_dir() -> Path:
    """Locate the packaged templates directory.

    Templates live INSIDE the package (``nmtcapp/templates/``) and are
    declared as package data, so one lookup answers for every install kind:
    wheel, sdist, editable and source tree alike.

    They used to sit at the repo root, which no wheel ever carried —
    ``pyproject.toml`` declared no ``package-data``, and ``MANIFEST.in``
    only governs the sdist. All three of the old strategies resolved to
    ``site-packages/templates``, so ``nmtcapp init`` failed for every user
    who installed from PyPI. Keeping them in the package also avoids
    installing a generic top-level ``templates/`` into site-packages, where
    it would collide with any other distribution doing the same.
    """
    import importlib.resources as pkg_resources

    if hasattr(pkg_resources, "files"):  # Python 3.9+
        candidate = Path(str(pkg_resources.files("nmtcapp") / "templates"))
        if candidate.is_dir():
            return candidate

    # Fallback for exotic loaders: templates sit beside this module.
    candidate = Path(__file__).parent / "templates"
    if candidate.is_dir():
        return candidate

    raise FileNotFoundError(
        "Cannot locate the packaged templates directory (nmtcapp/templates). "
        "This indicates a broken installation — please reinstall "
        "nmtc-application-builder, or report this with your install method."
    )


def _make_starter_notebook() -> str:
    """Return a minimal Jupyter notebook JSON string."""
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.9.0",
            },
        },
        "cells": [
            {
                "cell_type": "code",
                "id": "cell-imports",
                "metadata": {},
                "source": (
                    "# Cell 1: Imports\n"
                    "from nmtcapp.core.application import Application\n"
                    "from nmtcapp.core.cde import CDEProfile\n"
                    "from nmtcapp.core.pipeline import Pipeline\n"
                    "\n"
                    "print('nmtc-application-builder ready.')"
                ),
                "outputs": [],
                "execution_count": None,
            },
            {
                "cell_type": "code",
                "id": "cell-load",
                "metadata": {},
                "source": (
                    "# Cell 2: Load Data\n"
                    "# Edit cde_profile.yaml and pipeline.csv first, then run:\n"
                    "cde = CDEProfile.sample()  # replace with CDEProfile.from_yaml('cde_profile.yaml')\n"
                    "pipeline = Pipeline.from_csv('pipeline.csv')\n"
                    "\n"
                    "app = Application(cde=cde, requested_allocation=55_000_000)\n"
                    "app.add_pipeline(pipeline)\n"
                    "print(f'Pipeline loaded: {len(pipeline)} projects')"
                ),
                "outputs": [],
                "execution_count": None,
            },
            {
                "cell_type": "code",
                "id": "cell-analyze",
                "metadata": {},
                "source": (
                    "# Cell 3: Analyze\n"
                    "analysis = app.analyze()\n"
                    "analysis.summary()\n"
                    "\n"
                    "# Uncomment to score win alignment:\n"
                    "# score = app.score_win_probability()\n"
                    "# print(score.summary())\n"
                    "\n"
                    "# Uncomment to generate documents:\n"
                    "# paths = app.generate('./drafts/')\n"
                    "# print(paths)"
                ),
                "outputs": [],
                "execution_count": None,
            },
        ],
    }
    return json.dumps(notebook, indent=2)


def cmd_init(args: argparse.Namespace) -> int:
    """Create a starter project directory with templates and a notebook."""
    directory = Path(args.directory)
    directory.mkdir(parents=True, exist_ok=True)

    try:
        templates_dir = _get_templates_dir()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Copy pipeline_template.csv → pipeline.csv
    src_pipeline = templates_dir / "pipeline_template.csv"
    dst_pipeline = directory / "pipeline.csv"
    if src_pipeline.exists():
        shutil.copy2(src_pipeline, dst_pipeline)
    else:
        # Write a minimal header if template not found
        dst_pipeline.write_text(
            "project_id,project_name,qalicb_name,address,city,state,"
            "sector,project_type,total_project_cost,qei_request,qlici_amount,"
            "expected_jobs_created,expected_jobs_retained,expected_units_built,"
            "expected_sq_ft,closing_target_date\n"
        )

    # Copy cde_profile_template.yaml → cde_profile.yaml
    src_cde = templates_dir / "cde_profile_template.yaml"
    dst_cde = directory / "cde_profile.yaml"
    if src_cde.exists():
        shutil.copy2(src_cde, dst_cde)
    else:
        dst_cde.write_text(
            "# CDE Profile — complete all fields before running analysis.\n"
            "cde_id: \"\"\nname: \"\"\nmission: \"\"\ntarget_markets: []\n"
            "prior_awards: []\ncontact: {}\ngovernance: {}\n"
            "certification_date: \"\"\n"
        )

    # Write starter notebook
    dst_notebook = directory / "analysis.ipynb"
    dst_notebook.write_text(_make_starter_notebook())

    print(f"Created {directory}/ with:")
    print(f"  pipeline.csv")
    print(f"  cde_profile.yaml")
    print(f"  analysis.ipynb")
    print()
    print("Next steps:")
    print(f"  1. Edit {directory}/cde_profile.yaml with your CDE details")
    print(f"  2. Fill in {directory}/pipeline.csv with your project pipeline")
    print(f"     (a filled-in example ships at {templates_dir}/pipeline_sample_strong.csv)")
    print(f"  3. Open {directory}/analysis.ipynb in Jupyter to run your analysis")
    print(f"  4. Or run: nmtcapp analyze {directory}/pipeline.csv \\")
    print(f"               --cde {directory}/cde_profile.yaml \\")
    print(f"               --requested-allocation <dollars>")
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Load a pipeline CSV and print the analysis summary.

    Refuses to run without a CDE profile and a requested allocation. Scoring
    a real pipeline against a fictional CDE and an invented $55MM request —
    which is what this command used to do silently — produces advice about a
    CDE that does not exist and ratios against a number nobody entered.
    """
    csv_path = args.csv

    if not os.path.exists(csv_path):
        print(f"ERROR: Pipeline CSV not found: {csv_path}", file=sys.stderr)
        return 1

    if not args.demo and (args.cde is None or args.requested_allocation is None):
        print(
            "ERROR: analyze requires your own CDE profile and requested allocation.\n"
            "\n"
            "  nmtcapp analyze <csv> --cde cde_profile.yaml "
            "--requested-allocation 55000000\n"
            "\n"
            "`nmtcapp init <dir>` scaffolds a cde_profile.yaml to fill in.\n"
            "\n"
            "To see the tool run end to end on fictional data instead, pass "
            "--demo. Demo output is labelled as such on every screen and must "
            "not be used for a real application.",
            file=sys.stderr,
        )
        return 2

    try:
        from nmtcapp.core.pipeline import Pipeline
        from nmtcapp.core.sample_identity import SampleDataError
        from nmtcapp.core.cde import CDEProfile
        from nmtcapp.core.application import Application

        pipeline = Pipeline.from_csv(csv_path)

        if args.demo:
            cde = CDEProfile.sample()
            requested = (
                args.requested_allocation
                if args.requested_allocation is not None
                else 55_000_000
            )
            _print_demo_banner(cde, requested)
        else:
            # Not allow_sample: `analyze` is the real-application path.
            # Someone running the shipped sample wants --demo, which
            # labels every screen.
            cde = CDEProfile.from_yaml(args.cde)
            requested = args.requested_allocation

        app = Application(cde=cde, requested_allocation=requested)
        app.add_pipeline(pipeline)
        analysis = app.analyze()
        analysis.summary()

        if args.demo:
            _print_demo_banner(cde, requested)

        failed = [v.check_name for v in analysis.validation_results if not v.passed]
        if failed:
            print(
                "\n"
                + ("=" * 72) + "\n"
                f"  {len(failed)} VALIDATION CHECK(S) FAILED: {', '.join(failed)}\n"
                + (
                    "  --strict was passed, so this run exits non-zero.\n"
                    if args.strict else
                    "  This command exits 0 anyway: the exit code reports whether\n"
                    "  the ANALYSIS RAN, not what it found. Re-run with --strict to\n"
                    "  exit non-zero on a failed check, which is what a CI job or a\n"
                    "  wrapper script should use.\n"
                )
                + ("=" * 72),
                file=sys.stderr,
            )
            if args.strict:
                return 1
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except SampleDataError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: Unexpected error during analysis: {exc}", file=sys.stderr)
        return 1

    return 0


def _print_demo_banner(cde, requested: float) -> None:
    """Label demo output on every screen, above and below the summary."""
    print("=" * 72)
    print("  DEMO MODE — FICTIONAL CDE. NOT YOUR DATA.")
    print(f"  CDE:       {cde.name} (sample profile shipped with this package)")
    print(f"  Requested: ${requested:,.0f} (illustrative figure, not your request)")
    print("  Every CDE-level score, ratio and recommendation below refers to")
    print("  this fictional CDE. Re-run with --cde and --requested-allocation")
    print("  for results about your own application.")
    print("=" * 72)


def cmd_version(args: argparse.Namespace) -> int:
    """Print the package version."""
    try:
        from nmtcapp import __version__
        print(f"nmtc-application-builder {__version__}")
    except ImportError:
        print("nmtc-application-builder (version unknown)")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="nmtcapp",
        description=(
            "nmtc-application-builder — NMTC application intelligence platform\n\n"
            "Commands:\n"
            "  init <directory>   Create a starter project in <directory>\n"
            "  analyze <csv>      Analyze a pipeline CSV and print summary\n"
            "  version            Print the package version\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Print version and exit",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    # init subcommand
    init_parser = subparsers.add_parser(
        "init",
        help="Create a starter project directory with templates and a notebook",
        description=(
            "Creates a starter project in <directory> containing:\n"
            "  pipeline.csv        — pipeline template to fill in\n"
            "  cde_profile.yaml    — CDE profile template to fill in\n"
            "  analysis.ipynb      — starter Jupyter notebook\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    init_parser.add_argument(
        "directory",
        help="Directory to create (will be created if it does not exist)",
    )

    # analyze subcommand
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Run pipeline analysis on a CSV file and print a summary",
        description=(
            "Loads the pipeline from <csv> together with YOUR CDE profile and "
            "requested allocation, runs analyze(), and prints the full analysis "
            "summary to stdout.\n\n"
            "--cde and --requested-allocation are both required: CDE-level "
            "scores, peer ratios and recommendations are meaningless against "
            "someone else's CDE. Use --demo to run on the shipped fictional "
            "profile instead; that output is labelled as a demo throughout.\n\n"
            "EXIT CODE. `analyze` is a report, not a gate, and its exit code "
            "reports whether the analysis RAN — not what it found. A pipeline "
            "whose projects are affirmatively not NMTC-eligible prints [FAIL] "
            "and still exits 0, because refusing to print a report about a "
            "pipeline with problems is the opposite of useful. Pass --strict "
            "to exit non-zero on a failed check; a CI job or a wrapper script "
            "that reads exit 0 as approval wants --strict. Either way the "
            "failure is named on stderr, so it is never silent.\n\n"
            "The library and notebook paths behave the same way and do not "
            "raise: Application.analyze() returns ValidationResult objects "
            "with a `.passed` flag for the caller to act on."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    analyze_parser.add_argument(
        "csv",
        help="Path to a pipeline CSV file (must have required columns)",
    )
    analyze_parser.add_argument(
        "--cde",
        metavar="PATH",
        default=None,
        help="Path to your CDE profile YAML (as scaffolded by `nmtcapp init`)",
    )
    analyze_parser.add_argument(
        "--requested-allocation",
        metavar="DOLLARS",
        type=float,
        default=None,
        help="Allocation amount you are requesting, in dollars (e.g. 55000000)",
    )
    analyze_parser.add_argument(
        "--demo",
        action="store_true",
        help=(
            "Run on the shipped fictional CDE profile. Output is labelled "
            "DEMO MODE and must not be used for a real application."
        ),
    )
    analyze_parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Exit non-zero when any validation check FAILS. Without it the "
            "exit code reports whether the analysis ran, not what it found — "
            "so a pipeline containing projects that are affirmatively NOT "
            "NMTC-eligible still exits 0. Use --strict in CI or any script "
            "that treats exit 0 as approval."
        ),
    )

    # version subcommand
    subparsers.add_parser(
        "version",
        help="Print the package version",
    )

    return parser


def main() -> None:
    """Entry point for the nmtcapp command-line interface."""
    parser = _build_parser()
    args = parser.parse_args()

    # Handle --version flag
    if getattr(args, "version", False):
        sys.exit(cmd_version(args))

    # Route subcommands
    if args.command == "init":
        sys.exit(cmd_init(args))
    elif args.command == "analyze":
        sys.exit(cmd_analyze(args))
    elif args.command == "version":
        sys.exit(cmd_version(args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()

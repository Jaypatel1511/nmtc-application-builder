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
    """Locate the templates directory relative to the installed package or source tree."""
    # 1. Try relative to this file (works in editable installs and source trees)
    here = Path(__file__).parent
    candidate = here.parent / "templates"
    if candidate.is_dir():
        return candidate

    # 2. Try importlib.resources (works for installed packages with package_data)
    try:
        import importlib.resources as pkg_resources
        # Python 3.9+ path
        if hasattr(pkg_resources, "files"):
            ref = pkg_resources.files("nmtcapp") / ".." / "templates"
            resolved = Path(str(ref)).resolve()
            if resolved.is_dir():
                return resolved
    except Exception:
        pass

    # 3. Fallback: templates alongside the package root
    root = Path(__file__).parent.parent
    candidate2 = root / "templates"
    if candidate2.is_dir():
        return candidate2

    raise FileNotFoundError(
        "Cannot locate the templates directory. "
        "If you installed from source, ensure you are running from the repo root."
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
    print(f"     (see templates/pipeline_sample_strong.csv for examples)")
    print(f"  3. Open {directory}/analysis.ipynb in Jupyter to run your analysis")
    print(f"  4. Or run: nmtcapp analyze {directory}/pipeline.csv")
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Load a pipeline CSV and print the analysis summary."""
    csv_path = args.csv

    if not os.path.exists(csv_path):
        print(f"ERROR: Pipeline CSV not found: {csv_path}", file=sys.stderr)
        return 1

    try:
        from nmtcapp.core.pipeline import Pipeline
        from nmtcapp.core.cde import CDEProfile
        from nmtcapp.core.application import Application

        pipeline = Pipeline.from_csv(csv_path)
        cde = CDEProfile.sample()
        app = Application(cde=cde, requested_allocation=55_000_000)
        app.add_pipeline(pipeline)
        analysis = app.analyze()
        analysis.summary()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: Unexpected error during analysis: {exc}", file=sys.stderr)
        return 1

    return 0


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
            "Loads the pipeline from <csv>, creates an Application with a sample "
            "CDE profile and $55M requested allocation, runs analyze(), and prints "
            "the full analysis summary to stdout."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    analyze_parser.add_argument(
        "csv",
        help="Path to a pipeline CSV file (must have required columns)",
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

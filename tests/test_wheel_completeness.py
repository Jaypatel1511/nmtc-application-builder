"""
Wheel completeness test — builds the wheel from source, installs it in a
temporary venv, and verifies every public nmtcapp submodule is importable.

Run with:  pytest tests/test_wheel_completeness.py -v
Skipped in regular test runs unless -m wheel is passed.
"""
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

# Derived from `find nmtcapp -name "*.py"` — every public module in the source tree.
# Update this list whenever a new module is added.
PUBLIC_MODULES = [
    "nmtcapp",
    "nmtcapp.cli",
    "nmtcapp.core",
    "nmtcapp.core.application",
    "nmtcapp.core.cde",
    "nmtcapp.core.pipeline",
    "nmtcapp.data",
    "nmtcapp.data.benchmark_thresholds",
    "nmtcapp.data.historical_awards",
    "nmtcapp.data.schema",
    "nmtcapp.integrations",
    "nmtcapp.integrations.cdfidata_adapter",
    "nmtcapp.integrations.impact_adapter",
    "nmtcapp.integrations.nmtc_calc_adapter",
    "nmtcapp.integrations.nmtc_mapper_adapter",
    "nmtcapp.intelligence",
    "nmtcapp.intelligence.benchmarks",
    "nmtcapp.intelligence.distress_analysis",
    "nmtcapp.intelligence.geographic_analysis",
    "nmtcapp.intelligence.impact_aggregator",
    "nmtcapp.intelligence.pattern_analysis",
    "nmtcapp.intelligence.pipeline_analyzer",
    "nmtcapp.intelligence.recommendations",
    "nmtcapp.intelligence.sector_analysis",
    "nmtcapp.intelligence.win_probability",
    "nmtcapp.optimizer",
    "nmtcapp.optimizer.candidate_pool",
    "nmtcapp.optimizer.constraints",
    "nmtcapp.optimizer.objectives",
    "nmtcapp.optimizer.pipeline_optimizer",
    "nmtcapp.renderers",
    "nmtcapp.renderers.excel_builder",
    "nmtcapp.renderers.markdown_builder",
    "nmtcapp.renderers.pdf_builder",
    "nmtcapp.renderers.styles",
    "nmtcapp.renderers.word_builder",
    "nmtcapp.sections",
    "nmtcapp.sections.base",
    "nmtcapp.sections.section_a_business",
    "nmtcapp.sections.section_b_outcomes",
    "nmtcapp.sections.section_c_management",
    "nmtcapp.sections.section_d_capitalization",
    "nmtcapp.sections.section_e_prior_awards",
    "nmtcapp.tables",
    "nmtcapp.tables.distress_table",
    "nmtcapp.tables.geographic_table",
    "nmtcapp.tables.impact_table",
    "nmtcapp.tables.investor_table",
    "nmtcapp.tables.pipeline_table",
    "nmtcapp.tables.track_record_table",
    "nmtcapp.validation",
    "nmtcapp.validation.completeness_check",
    "nmtcapp.validation.consistency_check",
    "nmtcapp.validation.eligibility_check",
    "nmtcapp.validation.readiness_score",
    "nmtcapp.visualization",
    "nmtcapp.visualization.maps",
]


@pytest.mark.wheel
def test_wheel_completeness(tmp_path):
    """Build wheel from source, install in isolated venv, import every public submodule."""
    # 1. Build wheel into tmp_path
    subprocess.check_call(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(tmp_path)],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    wheels = list(tmp_path.glob("*.whl"))
    assert len(wheels) == 1, f"Expected 1 wheel, found: {wheels}"
    wheel = wheels[0]

    # 2. Create fresh venv and install wheel only (no extras)
    venv_dir = tmp_path / "venv"
    subprocess.check_call(
        [sys.executable, "-m", "venv", str(venv_dir)],
        stdout=subprocess.DEVNULL,
    )
    pip = venv_dir / "bin" / "pip"
    # Install with all extras so optional-dep modules (word, excel, pdf, viz) are importable
    subprocess.check_call(
        [str(pip), "install", f"{wheel}[output,viz]", "--quiet"],
        stdout=subprocess.DEVNULL,
    )

    # 3. Attempt to import each module — collect all failures before asserting
    python = venv_dir / "bin" / "python"
    failures = []
    for module in PUBLIC_MODULES:
        result = subprocess.run(
            [str(python), "-c", f"import {module}"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failures.append(f"{module}:\n  {result.stderr.strip()}")

    assert not failures, (
        f"{len(failures)} module(s) failed to import from the built wheel:\n\n"
        + "\n".join(failures)
    )

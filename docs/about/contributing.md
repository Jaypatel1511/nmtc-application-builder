# Contributing

Contributions are welcome — bug fixes, data updates, new features, and documentation improvements. This page covers the development workflow.

---

## Set up the development environment

```bash
# Clone the repository
git clone https://github.com/Jaypatel1511/nmtc-application-builder.git
cd nmtc-application-builder

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

# Install in editable mode with all dev dependencies
pip install -e ".[dev]"
```

The `[dev]` extra installs `pytest`, `pytest-cov`, `jupyter`, and all output/viz libraries (`python-docx`, `openpyxl`, `reportlab`, `matplotlib`).

## Building the documentation

```bash
pip install -e ".[docs]"
python -m mkdocs build --strict     # or: python -m mkdocs serve
```

The `[docs]` extra installs `mkdocs`, `mkdocs-material` and the output libraries
the docs build itself needs. **It is not optional for a docs build.** The build
runs `docs/hooks/generate_sample_output.py`, which renders the complete sample
application in all four formats; without `python-docx` and `reportlab` that hook
now raises rather than publishing a page claiming four formats over two files.

`[docs]` did not exist before 1.2.1 — `pip install -e ".[docs]"` printed
`WARNING: ... does not provide the extra 'docs'` and installed only the core.
CI builds the docs on every pull request, so an unbuildable docs tree fails
before it is merged.

**Publishing is still manual.** CI builds; it does not deploy. A correction to a
page under `docs/` is not live on the published site until somebody runs
`python -m mkdocs gh-deploy`.

---

## Running tests

```bash
# Run the full test suite
PYTHONPATH=. pytest tests/ -v

# Run a specific test file
PYTHONPATH=. pytest tests/intelligence/test_win_probability.py -v

# Run with coverage
PYTHONPATH=. pytest tests/ -v --cov=nmtcapp --cov-report=term-missing
```

Tests are organized to mirror the source tree:

```
tests/
  core/             # Application, CDEProfile, Pipeline, PipelineProject
  data/             # Historical awards, schema constants
  intelligence/     # Distress, geographic, sector, impact, win probability, recommendations
  optimizer/        # PipelineOptimizer, OptimizationConstraints
  renderers/        # Word, Excel, PDF, Markdown builders
  sections/         # Section A–E generators
  tables/           # Table builders (distress, geographic, impact, etc.)
  validation/       # Completeness, consistency, eligibility, readiness score
  visualization/    # Plot functions
  integrations/     # Adapter stubs
```

All tests should pass before submitting a pull request.

---

## Code style

- **Formatting:** The codebase follows standard Python formatting conventions. Functions have type annotations for parameters and return types where practical.
- **Docstrings:** Public classes and methods have docstrings following the existing style — one-line summary, extended description if needed, and an `Example::` block showing runnable code.
- **Module headers:** Each module has a top-level docstring explaining its purpose, the data sources it draws from (if applicable), and any important methodology notes.
- **Methodology disclosures:** Modules that produce alignment scores or optimization results carry a `_METHODOLOGY` string constant that is always exposed on result objects. Never remove or weaken these disclosures — they are a core design requirement.
- **No implicit imports:** All public-facing imports go through `__init__.py`. Internal cross-module imports use full absolute paths.

---

## Submitting a pull request

1. **Fork** the repository and create a feature branch from `main`.

2. **Write tests** for any new functionality. The existing test suite uses `pytest` fixtures defined in `tests/conftest.py`. Use `CDEProfile.sample()` and `Pipeline.sample()` in tests to avoid external API calls.

3. **Verify all tests pass:**
   ```bash
   PYTHONPATH=. pytest tests/ -v
   ```

4. **Update the relevant documentation page** in `docs/` if your change affects user-facing behavior, API signatures, or methodology.

5. **Open a pull request** against the `main` branch with a clear description of:
   - What the change does
   - Why it is needed
   - Any methodology changes (if applicable)

---

## Reporting issues

Use the [GitHub issue tracker](https://github.com/Jaypatel1511/nmtc-application-builder/issues) to report bugs, request features, or ask questions.

When reporting a bug, please include:
- Python version and OS
- Installed library version (`import nmtcapp; print(nmtcapp.__version__)`)
- Minimal reproducible example
- Full traceback if applicable

---

## Contributing data updates

When the CDFI Fund publishes new award announcement data or annual reports, the `historical_awards.py` constants should be updated. If you have access to new data:

1. Update the relevant constants in `nmtcapp/data/historical_awards.py`
2. Add the new round entry to `NMTC_AWARD_ROUNDS` with a source comment
3. Update `APPLICATION_VOLUME_TRENDS` lists
4. Update `WINNER_DISTRESS_PATTERNS`, `WINNER_GEOGRAPHIC_PATTERNS`, `WINNER_IMPACT_BENCHMARKS`, or `WINNER_SECTOR_PATTERNS` if new annual report data changes the aggregate statistics
5. Update the module docstring to reflect the new data coverage period
6. Run the full test suite — some tests assert on specific constant values and may need updating
7. Submit a pull request with the data source URL in the commit message

Data contributions are particularly valuable as they directly improve the accuracy of alignment scoring for all users.

---

## Running the example notebooks

The `examples/` directory contains three Jupyter notebooks that demonstrate the full platform workflow:

```bash
cd examples
jupyter notebook
```

- `01_quickstart.ipynb` — 5-minute end-to-end workflow
- `02_full_application_walkthrough.ipynb` — Complete application preparation with all output formats
- `03_intelligence_and_optimization.ipynb` — Deep dive into scoring, recommendations, and optimizer

To re-execute all notebooks from scratch (useful before a release):

```bash
PYTHONPATH=. jupyter nbconvert --to notebook --execute examples/01_quickstart.ipynb
PYTHONPATH=. jupyter nbconvert --to notebook --execute examples/02_full_application_walkthrough.ipynb
PYTHONPATH=. jupyter nbconvert --to notebook --execute examples/03_intelligence_and_optimization.ipynb
```

# Contributing to NMTC Application Builder

Thank you for your interest in contributing. Contributions of all kinds are welcome:
bug reports, documentation improvements, new features, and data source integrations.

## Development Setup

```bash
git clone https://github.com/Jaypatel1511/nmtc-application-builder.git
cd nmtc-application-builder
pip install -e ".[dev]"

# To build the documentation as well:
pip install -e ".[docs]"
python -m mkdocs build --strict
```

The `[docs]` extra covers `mkdocs`, `mkdocs-material` and the output libraries
the docs build needs — the build renders the full sample application in all four
formats, and the hook that does so fails the build if any format is missing.
CI builds the docs on every pull request, but does **not** deploy them:
publishing to `gh-pages` is still a manual `python -m mkdocs gh-deploy`.

## Running Tests

```bash
PYTHONPATH=. pytest tests/ -v          # all 1,151 tests
PYTHONPATH=. pytest tests/core/ -v    # specific module
PYTHONPATH=. pytest tests/ -q --tb=short  # quick summary
```

All tests must pass before a PR is accepted. If you add a feature, add tests for it.
Target: keep test count growing, never shrinking.

## Code Style

- **No docstring required** for internal helpers; public API methods need a one-line docstring and an `Example::` block.
- **No comments on obvious code.** Comment only when the *why* is non-obvious.
- **No features beyond the task.** If a bug fix doesn't need refactoring, don't refactor.
- Type hints on all new public functions. Use `from __future__ import annotations`.
- Use the existing logger pattern: `logger = logging.getLogger(__name__)`.

## Adding a Visualization

Add new functions to `nmtcapp/visualization/maps.py`. Follow the existing pattern:
- Accept `(application, output_path)` as arguments
- Call `application.analyze()` for data
- Return `output_path`
- Use brand colors from `nmtcapp.renderers.styles.COLORS`
- Save at 300 DPI with `plt.savefig(output_path, dpi=300, bbox_inches="tight")`
- Add tests in `tests/visualization/test_maps.py`

## Adding a Data Source Integration

Add a new adapter in `nmtcapp/integrations/`. Follow the pattern in `cdfidata_adapter.py`:
- Wrap the external library in a `try/except`
- Provide a fallback that uses only data already in the `Application`
- Log failures at `WARNING` level, never `print()`
- Document the external library in `docs/reference/data-sources.md`

## Pull Request Process

1. Fork the repo and create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes with tests
3. Run `PYTHONPATH=. pytest tests/ -q` — all tests must pass
4. Update `CHANGELOG.md` under `[Unreleased]`
5. Open a PR with a clear description of what changed and why

## Reporting Issues

Use the GitHub issue tracker. Include:
- Python version and OS
- Library version (`python -c "import nmtcapp; print(nmtcapp.__version__)"`)
- Minimal reproducible example
- Full traceback

## Questions

Open a GitHub Discussion — not an Issue — for questions about usage or design.

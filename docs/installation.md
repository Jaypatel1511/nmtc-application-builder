# Installation

## Requirements

- Python 3.9 or later (tested on 3.9, 3.10, 3.11, 3.12)
- pip 21+ recommended

---

## Core install

The core package installs the intelligence engine, pipeline analysis, validation, and Markdown output. No optional output libraries are required to run analysis.

```bash
pip install nmtc-application-builder
```

The core install includes: `pandas`, `numpy`, `pyyaml`, and the five integration libraries (`nmtc-mapper`, `nmtc-calc`, `hmda-analyzer`, `cdfidata`, `impact-ledger`).

---

## Optional extras

Most output formats and visualization require additional libraries. Install only what you need.

| Extra | What it enables | Install command |
|-------|-----------------|-----------------|
| `[word]` | Word (.docx) document output | `pip install "nmtc-application-builder[word]"` |
| `[excel]` | Excel (.xlsx) workbook output | `pip install "nmtc-application-builder[excel]"` |
| `[pdf]` | PDF output | `pip install "nmtc-application-builder[pdf]"` |
| `[viz]` | Matplotlib visualizations (all 5 chart types) | `pip install "nmtc-application-builder[viz]"` |
| `[output]` | Word + Excel + PDF (no viz) | `pip install "nmtc-application-builder[output]"` |

### Install everything

```bash
pip install "nmtc-application-builder[output,viz]"
```

This installs `python-docx`, `openpyxl`, `reportlab`, and `matplotlib` in addition to the core dependencies.

---

## Development install

To contribute or run the test suite, install in editable mode with all dev dependencies:

```bash
git clone https://github.com/Jaypatel1511/nmtc-application-builder.git
cd nmtc-application-builder
pip install -e ".[dev]"
```

The `[dev]` extra includes `pytest`, `pytest-cov`, `jupyter`, and all output/viz libraries.

---

## Verify the install

```python
import nmtcapp
print(nmtcapp.__version__)        # prints the installed version

from nmtcapp.core.pipeline import Pipeline
print(Pipeline.sample(n=5))       # Pipeline(projects=5, total_qei=$...)
```

If both lines execute without error, the install is complete.

---

## Troubleshooting

### NumPy compatibility

If you see `AttributeError: module 'numpy' has no attribute 'bool'` or similar NumPy 1.x / 2.x incompatibilities, pin NumPy explicitly:

```bash
pip install "numpy>=1.21,<2.0" nmtc-application-builder
```

The library is tested against NumPy 1.21–1.26. NumPy 2.x support is tracked in [GitHub issues](https://github.com/Jaypatel1511/nmtc-application-builder/issues).

### Missing `python-docx` when generating Word documents

`app.generate()` will skip Word output and log a warning if `python-docx` is not installed. Install it explicitly:

```bash
pip install "nmtc-application-builder[word]"
```

### Missing `reportlab` when generating PDFs

Same pattern — install the `[pdf]` extra:

```bash
pip install "nmtc-application-builder[pdf]"
```

### `ImportError: matplotlib is required for visualization`

All five visualization functions raise a clear `ImportError` with install instructions if `matplotlib` is absent. Install the `[viz]` extra:

```bash
pip install "nmtc-application-builder[viz]"
```

### Virtual environment recommended

Always install in a virtual environment to avoid dependency conflicts with other projects:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install "nmtc-application-builder[output,viz]"
```

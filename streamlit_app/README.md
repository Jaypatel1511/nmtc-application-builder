# NMTC Application Builder — Streamlit Demo

Interactive demo for the `nmtc-application-builder` library. Includes pipeline
analysis, win alignment scoring, pipeline optimization, and methodology documentation.

## Running locally

### 1. Clone and install

```bash
git clone https://github.com/Jaypatel1511/nmtc-application-builder.git
cd nmtc-application-builder
pip install -e ".[dev]"          # install library in editable mode
pip install streamlit plotly     # install Streamlit and Plotly
```

### 2. Launch the app

```bash
streamlit run streamlit_app/app.py
```

The app opens at `http://localhost:8501`.

## Pages

| Page | Description |
|---|---|
| **Home** | Landing page with feature overview |
| **1 Pipeline Analyzer** | Upload CSV or use sample data; full analysis report |
| **2 Win Alignment Scorer** | Score vs. historical NMTC winner patterns |
| **3 Pipeline Optimizer** | Optimise project subset under budget/diversity constraints |
| **4 About & Methodology** | Data sources, limitations, historical round statistics |

## Deploying to Streamlit Cloud

1. Push the repo to GitHub (public or private with Streamlit Cloud access).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Set:
   - **Repository:** `Jaypatel1511/nmtc-application-builder`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app/app.py`
4. Streamlit Cloud reads `streamlit_app/requirements.txt` automatically.
5. Click **Deploy**.

> **Note:** The `nmtc-application-builder` package must be published to PyPI
> (or the repo root must be pip-installable) for Streamlit Cloud to install it.
> If deploying from the repo directly, add a `packages.txt` if system dependencies
> are needed (none required for the base demo).

## Sample data

No external API calls are needed. `Pipeline.sample(n=20)` returns a pre-enriched
set of 20 realistic projects across 19 states. All distress levels and eligibility
flags are hard-coded in the library.

## License

MIT

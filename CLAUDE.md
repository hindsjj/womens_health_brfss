# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Python data-analysis project that summarizes Idaho BRFSS preconception-health data for women ages 18–49 into a maternal-health poster. Final deliverable format (printable poster vs. interactive web poster vs. both) is not yet decided — treat format as an open design question when suggesting approaches.

At the time of writing the project contains only the source dataset; no analysis code, notebooks, environment files, or tests exist yet.

## Data source

Single workbook: [WomenPrecon_Full_AGG_Final4.3.26.xlsx](WomenPrecon_Full_AGG_Final4.3.26.xlsx)

- Source: Idaho Behavioral Risk Factor Surveillance System (BRFSS), 2020–2024
- Publisher: Idaho Department of Health and Welfare, Performance, Policy & Strategy (April 2026)
- Population: women ages 18–49

Sheets:
- `Notes` — metadata, data-quality caveats, and column definitions. Read this before doing analysis.
- `Precon Health, Aggr 2020-2024` — main long-format table, ~16,400 rows × 11 columns.

Main-table columns: `Years`, `Status`, `Category`, `Group`, `Region`, `Percent`, `Lower_95CI`, `Upper_95CI`, `Sample_Size`, `Estimated_Adults`. `Region` is either `Statewide` or an Idaho public health district.

### Data-quality rules (from the Notes sheet — these affect every analysis)

- Rows with sample size < 50 are already suppressed upstream.
- Unanimous responses (0.0% / 100.0%) have no confidence interval, Estimated_Adults, or RSE.
- Relative Standard Error (RSE) thresholds: RSE > 30 is CDC-unreliable; RSE > 50 is Idaho-BRFSS-very-unreliable. Filter or annotate accordingly when presenting results.
- Variables measured for only a single year or with inconsistent definitions across years were excluded upstream — do not try to back-fill them.

## Workflow contract

- Always read `PLAN.md` at the start of a session. It does not exist yet; create it the first time you do substantive work, and update it after major steps (exploration, schema decisions, figure drafts, deliverable choice).
- Preferred tools for this project: Python, `pandas`, `openpyxl` (for the .xlsx), Plotly (Python) for charts. Use Jupyter notebooks for exploration and plain `.py` modules for anything reused across notebooks.
- If the deliverable becomes a web poster: Flask or FastAPI backend, Bootstrap or Tailwind for layout, PlotlyJS for charts, LeafletJS for any Idaho public-health-district map. Front-end must meet WCAG 2.1 Level AA.

## Layout

- `analysis.ipynb` — **generated, not hand-edited.** Contains the summary + four comparative chart sections.
- `scripts/build_notebook.py` — source of truth for the notebook. Edit this file, then regenerate.
- `requirements.txt` — pinned deps.
- `venv/` — local virtualenv (not tracked once a repo is initialized).

Editing charts: change `scripts/build_notebook.py`, run `./venv/bin/python scripts/build_notebook.py`, then re-execute the notebook. Do not edit `analysis.ipynb` cells by hand — the next regeneration will overwrite them.

## Build / test / run

First-time setup:

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

Regenerate and execute the notebook in one shot:

```bash
./venv/bin/python scripts/build_notebook.py
./venv/bin/jupyter nbconvert --to notebook --execute --inplace analysis.ipynb --ExecutePreprocessor.timeout=120
```

Open interactively:

```bash
./venv/bin/jupyter notebook analysis.ipynb
```

No test suite yet; the execute-in-place command above is the closest thing to a smoke test — it fails loudly if any cell raises.

# PLAN.md — maternal_health_poster

Live status log for the project. Update after major steps.

## Goal

Produce summary and comparative charts of Idaho BRFSS 2020–2024 women-18–49 aggregate data across four thematic groups, each broken out by six stratifiers. Delivered as a Jupyter notebook with interactive Plotly charts plus a static HTML export.

## Scope (confirmed with user 2026-04-20, extended 2026-04-21)

Four thematic groups share the same 6 stratifiers and RSE/CI conventions.

### Part A — Physical health (6 metrics)

1. `14 or more Days of Poor Physical Health`
2. `Fair or Poor Health`
3. `Current Asthma`
4. `Diagnosed with Diabetes`
5. `Obese (BMI >= 30)` — BMI treated as obesity-only; pre-diabetes dropped (not in dataset)
6. `High Blood Pressure` (hypertension)

### Part B — Mental health (7 metrics)

1. `14 or more Days of Poor Mental Health`
2. `Diagnosed with Depressive Disorder`
3. `Always/Usually Feel Stressed`
4. `Always/Usually Feel Socially Isolated`
5. `Seriously Considered Attempting Suicide`
6. `Social/Emotional Support Needs Met Rarely/Never`
7. `Dissatisfied/Very Dissatisfied with Life`

### Part C — Health behaviors (6 metrics, added 2026-04-21)

1. `Did not have a Routine Checkup in the Last Year`
2. `Did not have Dental Visit in Past 12 months`
3. `No Leisure Time Physical Activity`
4. `Current Cigarette Smoker`
5. `High Alcohol Consumption`
6. `Marijuana Use in Past 30 Days`

### Part D — Social drivers of health (5 metrics, added 2026-04-21)

1. `Did Not Seek Medical Care Due to Cost`
2. `Bought Food that Did Not Last (Always/Usually/Sometimes)`
3. `Lost Employment/Hours Reduced`
4. `No Primary Source of Insurance`
5. `Insufficient Access to Transportation`

### Six stratifiers (shared)

1. Health district — `Region` column, 7 districts + Statewide reference
2. Income — `Category = Income`, 6 groups from `<$15k` to `$75k+`
3. Education — `Category = Education`, 4 groups from `K-11th Grade` to `College Graduate+`
4. Race classification — `Category = Race Classification`, 3 groups (White Non-Hispanic / Hispanic / Other Non-Hispanic)
5. Binary residence — `Category = Binary Residence Population Category`, 2 groups (Urban / Rural/Frontier) (added 2026-04-21)
6. BMI status — `Category = BMI Status`, 3 groups (Underweight or Normal / Overweight / Obese) (added 2026-04-21). Note: Part A's *Obese (BMI≥30)* metric stratified by the Obese group is mechanically 100% — consistency check, not new signal.

### Decisions

- RSE > 30 estimates are kept but flagged visually (hatched/marker + figure note), not suppressed.
- Unanimous (0/100%) rows appear without CIs — plot without error bars.
- Output: one Jupyter notebook with interactive Plotly charts; a static HTML export is generated alongside via `nbconvert --to html` (Plotly renderer set to `notebook_connected+plotly_mimetype` so figures render from the CDN).
- Small-multiples grid is 2 columns; number of rows is computed from the metric count. Odd counts (e.g., 7 mental metrics) leave the bottom-right slot blank.

## Deliverables

- `analysis.ipynb` — load data, flag RSE>30, build charts (28 figures)
- `analysis.html` — static HTML export, regenerated from the notebook
- `scripts/build_notebook.py` — single source of truth for notebook contents
- `requirements.txt` — pinned deps
- `WomenPrecon_Full_AGG_Final4.3.26.xlsx` — source data, tracked in git
- `venv/` — local virtualenv (git-ignored)
- GitHub repo: <https://github.com/hindsjj/womens_health_brfss> (private)

## Chart structure

Each of Part A (physical), Part B (mental), Part C (health behaviors), and Part D (social drivers) produces the same 7 figures:

- **Statewide summary** — horizontal bar chart of all metrics in the group, sorted by prevalence, 95% CI error bars, numeric labels placed past the upper whisker.
- **By health district** — small-multiples (one panel per metric), 8 regions per panel; Statewide rendered in darker navy as the reference bar.
- **By income** — 6 bands per panel, shortened labels (`<$15k`, `$15-24k`, …, `$75k+`) to fit the narrow subplot axes.
- **By education** — 4 levels per panel.
- **By race** — 3 groups per panel.
- **By binary residence** — 2 groups per panel (Urban vs Rural/Frontier).
- **By BMI status** — 3 groups per panel (Underweight or Normal / Overweight / Obese).

Every panel: horizontal bars, 95% CI error bars when present, RSE>30 bars rendered with a lighter grey fill + diagonal hatch pattern + `*UNRELIABLE*` in the hover label, figure-level note explaining the flag.

## Status

- [x] Scope confirmed with user (physical + mental)
- [x] CLAUDE.md scaffolded with venv/run commands
- [x] PLAN.md created and updated
- [x] venv + requirements.txt
- [x] `scripts/build_notebook.py` — single source of truth, parameterized by metric group
- [x] Reusable helpers: `_hover`, `_error_x`, `_marker`, `_footer`, `statewide_summary`, `small_multiples`
- [x] Part A — Physical health: summary + 4 stratifier figures
- [x] Part B — Mental health: summary + 4 stratifier figures
- [x] Part C — Health behaviors: summary + 4 stratifier figures
- [x] Part D — Social drivers of health: summary + 4 stratifier figures
- [x] Binary residence and BMI status added as 5th and 6th stratifiers (each Part now has 7 figures, 28 total)
- [x] Full notebook executes end-to-end without error (`nbconvert --execute`)
- [x] Income labels shortened to fit the 7-metric 4×2 layout
- [x] Static HTML export wired up (`nbconvert --to html` produces `analysis.html`)
- [x] Initialized git, pushed to private GitHub repo `hindsjj/womens_health_brfss` (initial commit + data file + HTML export)

## Current state (2026-04-21)

Tracked in the GitHub repo `hindsjj/womens_health_brfss` (private): `analysis.ipynb` (generated, 28 figures), `analysis.html` (static export), `scripts/build_notebook.py`, `requirements.txt`, `WomenPrecon_Full_AGG_Final4.3.26.xlsx`, `CLAUDE.md`, `PLAN.md`, `.gitignore`. Notebook produces 28 interactive Plotly figures:

- **Part A:** 1 statewide summary + 6 comparative (district / income / education / race / residence / BMI) small-multiples for 6 physical-health metrics
- **Part B:** 1 statewide summary + 6 comparative small-multiples for 7 mental-health metrics
- **Part C:** 1 statewide summary + 6 comparative small-multiples for 6 health-behavior metrics
- **Part D:** 1 statewide summary + 6 comparative small-multiples for 5 social-driver metrics

All figures include 95% CI error bars and RSE>30 visual flagging (light-grey hatched bars + `*UNRELIABLE*` in hover).

## Open questions / follow-ups

- Final poster format (print vs. web) still TBD — revisit once charts are reviewed.
- Whether to add an ethnicity breakdown (Hispanic/Non-Hispanic) in addition to Race Classification — not requested, easy to add later.
- Pre-diabetes: confirm with data owner whether it exists in an un-aggregated BRFSS file.

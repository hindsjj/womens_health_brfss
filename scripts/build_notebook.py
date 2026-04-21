"""Generate analysis.ipynb from a single source-of-truth list of cells.

Run with: ./venv/bin/python scripts/build_notebook.py
Edit the CELLS list below to change the notebook; regenerate to sync analysis.ipynb.
"""
from pathlib import Path
import nbformat as nbf

CELLS = []


def md(text):
    CELLS.append(("markdown", text))


def code(text):
    CELLS.append(("code", text))


md("""# Maternal Health — Idaho BRFSS 2020–2024 (women 18–49)

Summary and comparative charts for four thematic groups:

- **Part A — Physical health:** 14+ days poor physical health, fair/poor health, current asthma, diabetes, obesity (BMI ≥ 30), hypertension
- **Part B — Mental health:** 14+ days poor mental health, depressive disorder, dissatisfaction with life, serious suicide ideation, unmet social/emotional support, social isolation, chronic stress
- **Part C — Health behaviors:** no routine checkup, no dental visit, no leisure-time physical activity, cigarette smoking, high alcohol consumption, past-30-day marijuana use
- **Part D — Social drivers of health:** forgone medical care due to cost, food insecurity, lost employment/hours, no primary insurance, insufficient transportation

Stratifiers for each group: health district, household income, education, race classification, binary residence (urban vs rural/frontier), BMI status.

**Data-quality conventions** (from the workbook's Notes sheet):

- Estimates with RSE > 30 are flagged as *CDC-unreliable* (light-grey hatched bars, `*` in hover).
- Rows with sample size < 50 are suppressed upstream.
- Error bars are 95% CIs.
""")

code("""import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

pio.renderers.default = 'notebook_connected+plotly_mimetype'

DATA_PATH = 'WomenPrecon_Full_AGG_Final4.3.26.xlsx'
SHEET = 'Precon Health, Aggr 2020-2024'
RSE_UNRELIABLE = 30

PHYS_METRICS = [
    ('14 or more Days of Poor Physical Health', '14+ Days Poor Physical Health'),
    ('Fair or Poor Health',                     'Fair or Poor Health'),
    ('Current Asthma',                          'Current Asthma'),
    ('Diagnosed with Diabetes',                 'Diabetes'),
    ('Obese (BMI >= 30)',                       'Obesity (BMI \\u2265 30)'),
    ('High Blood Pressure',                     'Hypertension'),
]

MENTAL_METRICS = [
    ('14 or more Days of Poor Mental Health',             '14+ Days Poor Mental Health'),
    ('Diagnosed with Depressive Disorder',                'Depressive Disorder'),
    ('Always/Usually Feel Stressed',                      'Always/Usually Stressed'),
    ('Always/Usually Feel Socially Isolated',             'Always/Usually Isolated'),
    ('Seriously Considered Attempting Suicide',           'Serious Suicide Ideation'),
    ('Social/Emotional Support Needs Met Rarely/Never',   'Unmet Social/Emotional Support'),
    ('Dissatisfied/Very Dissatisfied with Life',          'Dissatisfied With Life'),
]

BEHAV_METRICS = [
    ('Did not have a Routine Checkup in the Last Year', 'No Routine Checkup (past year)'),
    ('Did not have Dental Visit in Past 12 months',     'No Dental Visit (past 12 mo)'),
    ('No Leisure Time Physical Activity',               'No Leisure-Time Physical Activity'),
    ('Current Cigarette Smoker',                        'Current Cigarette Smoker'),
    ('High Alcohol Consumption',                        'High Alcohol Consumption'),
    ('Marijuana Use in Past 30 Days',                   'Marijuana Use (past 30 days)'),
]

SDOH_METRICS = [
    ('Did Not Seek Medical Care Due to Cost',                  'Forgone Care (cost)'),
    ('Bought Food that Did Not Last (Always/Usually/Sometimes)', 'Food Insecurity'),
    ('Lost Employment/Hours Reduced',                          'Lost Employment / Hours'),
    ('No Primary Source of Insurance',                         'No Primary Insurance'),
    ('Insufficient Access to Transportation',                  'Insufficient Transportation'),
]

ALL_STATUSES = [s for s, _ in PHYS_METRICS + MENTAL_METRICS + BEHAV_METRICS + SDOH_METRICS]

DISTRICT_ORDER = [
    'Statewide',
    'Panhandle Public Health District',
    'North Central Public Health District',
    'Southwest Public Health District',
    'Central Public Health District',
    'South Central Public Health District',
    'Southeastern Idaho Public Health District',
    'Eastern Idaho Public Health District',
]
INCOME_ORDER = [
    'Less than $15k',
    '$15,000 - $24,999',
    '$25,000 - $34,999',
    '$35,000 - $49,999',
    '$50,000 - $74,999',
    '$75,000+',
]
INCOME_DISPLAY = {
    'Less than $15k':     '<$15k',
    '$15,000 - $24,999':  '$15-24k',
    '$25,000 - $34,999':  '$25-34k',
    '$35,000 - $49,999':  '$35-49k',
    '$50,000 - $74,999':  '$50-74k',
    '$75,000+':           '$75k+',
}
EDU_ORDER = [
    'K-11th Grade',
    '12th Grade or GED',
    'Some College',
    'College Graduate+',
]
RACE_ORDER = [
    'White, Non-Hispanic',
    'Hispanic',
    'Other, Non-Hispanic',
]
RESIDENCE_ORDER = [
    'Urban',
    'Rural/Frontier',
]
BMI_ORDER = [
    'Underweight or Normal Weight',
    'Overweight',
    'Obese',
]

BAR_COLOR = '#2e6fa7'
STATEWIDE_COLOR = '#08306b'
UNRELIABLE_COLOR = '#bfbfbf'
ERROR_COLOR = '#444'
""")

md("## Load and prepare data")

code("""raw = pd.read_excel(DATA_PATH, sheet_name=SHEET)
for c in ['Percent', 'Lower_95CI', 'Upper_95CI', 'Sample_Size', 'Estimated_Adults', 'RSE']:
    raw[c] = pd.to_numeric(raw[c], errors='coerce')

df = raw[raw['Status'].isin(ALL_STATUSES)].copy()
df['Unreliable'] = df['RSE'].fillna(0) > RSE_UNRELIABLE

print(f'Rows after metric filter: {len(df):,}')
print(f'Rows flagged RSE>{RSE_UNRELIABLE}: {df[\"Unreliable\"].sum()}')
df.head()
""")

md("## Chart helpers")

code("""def _hover(sub):
    out = []
    for _, r in sub.iterrows():
        if pd.notna(r['Lower_95CI']) and pd.notna(r['Upper_95CI']):
            ci = f\"{r['Lower_95CI']:.1f}\\u2013{r['Upper_95CI']:.1f}\"
        else:
            ci = 'n/a'
        unrel = ' <b>*UNRELIABLE (RSE>30)*</b>' if r['Unreliable'] else ''
        n = int(r['Sample_Size']) if pd.notna(r['Sample_Size']) else 'n/a'
        rse = int(r['RSE']) if pd.notna(r['RSE']) else 'n/a'
        out.append(
            f\"<b>{r['Group']}</b><br>\"
            f\"{r['Percent']:.1f}% (95% CI {ci})<br>\"
            f\"n = {n}, RSE = {rse}{unrel}\"
        )
    return out


def _error_x(sub):
    return dict(
        type='data', symmetric=False,
        array=(sub['Upper_95CI'] - sub['Percent']).fillna(0).tolist(),
        arrayminus=(sub['Percent'] - sub['Lower_95CI']).fillna(0).tolist(),
        color=ERROR_COLOR, thickness=1.2, width=4,
    )


def _marker(sub, highlight_col=None, highlight_val=None):
    def pick(row):
        if row['Unreliable']:
            return UNRELIABLE_COLOR
        if highlight_col and row.get(highlight_col) == highlight_val:
            return STATEWIDE_COLOR
        return BAR_COLOR
    colors = [pick(r) for _, r in sub.iterrows()]
    patterns = ['/' if u else '' for u in sub['Unreliable']]
    return dict(
        color=colors,
        pattern=dict(shape=patterns, size=6, solidity=0.3),
        line=dict(color='#333', width=0.5),
    )


def _footer(fig, extra_notes='', y=-0.12):
    notes = (
        'Source: Idaho BRFSS 2020\\u20132024, women ages 18\\u201349. '
        'Error bars: 95% CI. '
        'Grey hatched bars: RSE > 30 (CDC-unreliable).'
    )
    if extra_notes:
        notes = f'{notes} {extra_notes}'
    fig.add_annotation(
        text=notes, xref='paper', yref='paper',
        x=0, y=y, xanchor='left', showarrow=False,
        font=dict(size=10, color='#555'),
    )


def statewide_summary(df, metrics, title):
    rows = []
    for status, label in metrics:
        sub = df[
            (df['Status'] == status)
            & (df['Category'] == 'Total')
            & (df['Region'] == 'Statewide')
        ]
        r = sub.iloc[0]
        rows.append({
            'Metric': label, 'Percent': r['Percent'],
            'Lower_95CI': r['Lower_95CI'], 'Upper_95CI': r['Upper_95CI'],
            'Sample_Size': r['Sample_Size'], 'RSE': r['RSE'],
            'Unreliable': bool(r['Unreliable']), 'Group': label,
        })
    summary = pd.DataFrame(rows).sort_values('Percent', ascending=True).reset_index(drop=True)
    fig = go.Figure(
        go.Bar(
            x=summary['Percent'], y=summary['Metric'], orientation='h',
            marker=_marker(summary), error_x=_error_x(summary),
            customdata=_hover(summary), hovertemplate='%{customdata}<extra></extra>',
        )
    )
    upper = summary['Upper_95CI'].max()
    x_max = max(upper if pd.notna(upper) else 0, summary['Percent'].max()) * 1.25
    for _, r in summary.iterrows():
        fig.add_annotation(
            x=r['Upper_95CI'] if pd.notna(r['Upper_95CI']) else r['Percent'],
            y=r['Metric'],
            text=f\"  {r['Percent']:.1f}%\",
            xanchor='left', yanchor='middle', showarrow=False,
            font=dict(size=12, color='#222'),
        )
    fig.update_layout(
        title=dict(text=title, x=0, xanchor='left'),
        template='plotly_white', height=90 + 55 * len(summary),
        margin=dict(l=280, r=100, t=70, b=110),
        xaxis=dict(title='% of women 18\\u201349', ticksuffix='%', range=[0, x_max]),
        font=dict(family='Helvetica, Arial, sans-serif', size=12),
    )
    _footer(fig, y=-0.28)
    return fig, summary


def small_multiples(df, *, metrics, group_col, group_order, filters, title,
                    display_map=None, highlight_val=None, height=None,
                    footer_y=-0.12):
    n = len(metrics)
    rows = (n + 1) // 2
    cols = 2 if n > 1 else 1
    subtitles = [label for _, label in metrics]
    if n % 2 and cols == 2:
        subtitles = subtitles + ['']
    display_map = display_map or {}
    display_order = [display_map.get(g, g) for g in group_order]
    fig = make_subplots(
        rows=rows, cols=cols, subplot_titles=subtitles,
        horizontal_spacing=0.28, vertical_spacing=0.08,
    )
    for i, (status, _) in enumerate(metrics):
        row, col = i // cols + 1, i % cols + 1
        sub = df[df['Status'] == status].copy()
        for k, v in filters.items():
            sub = sub[sub[k] == v]
        sub = (
            sub.drop_duplicates(subset=[group_col])
               .set_index(group_col)
               .reindex(group_order)
               .reset_index()
        )
        sub['Unreliable'] = sub['Unreliable'].fillna(False)
        sub['_display'] = sub[group_col].map(lambda g: display_map.get(g, g))
        fig.add_trace(
            go.Bar(
                x=sub['Percent'], y=sub['_display'], orientation='h',
                marker=_marker(sub, group_col, highlight_val),
                error_x=_error_x(sub),
                customdata=_hover(sub), hovertemplate='%{customdata}<extra></extra>',
                showlegend=False,
            ),
            row=row, col=col,
        )
        upper = sub['Upper_95CI'].max()
        x_max = max(20, (upper if pd.notna(upper) else sub['Percent'].max()) * 1.2)
        fig.update_xaxes(
            ticksuffix='%', range=[0, x_max], gridcolor='#eee',
            row=row, col=col,
        )
        fig.update_yaxes(
            categoryorder='array', categoryarray=display_order,
            autorange='reversed', row=row, col=col,
        )
    if height is None:
        height = 200 + rows * 260
    highlight_note = ''
    if highlight_val:
        highlight_note = f'Dark-navy bar = {highlight_val} reference.'
    fig.update_layout(
        title=dict(text=title, x=0, xanchor='left'),
        height=height, template='plotly_white', bargap=0.25,
        margin=dict(l=220, r=40, t=90, b=140),
        font=dict(family='Helvetica, Arial, sans-serif', size=12),
    )
    _footer(fig, extra_notes=highlight_note, y=footer_y)
    return fig
""")

# ----- Part A: Physical health -------------------------------------------

md("""---

# Part A — Physical health

Six metrics: poor physical health (≥14 days), fair/poor self-rated health, current asthma, diabetes, obesity (BMI ≥ 30), hypertension.""")

md("## A1. Statewide summary")

code("""phys_summary_fig, phys_summary = statewide_summary(
    df, PHYS_METRICS,
    'Statewide physical-health prevalence \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
)
phys_summary_fig.show()
phys_summary
""")

md("""## A2. By health district

Each panel = one metric across 7 districts, with Statewide as a darker reference bar.""")

code("""small_multiples(
    df, metrics=PHYS_METRICS,
    group_col='Region', group_order=DISTRICT_ORDER,
    filters={'Category': 'Total'},
    highlight_val='Statewide',
    title='Physical health by health district \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## A3. By income")

code("""small_multiples(
    df, metrics=PHYS_METRICS,
    group_col='Group', group_order=INCOME_ORDER,
    filters={'Category': 'Income', 'Region': 'Statewide'},
    display_map=INCOME_DISPLAY,
    title='Physical health by household income \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## A4. By education")

code("""small_multiples(
    df, metrics=PHYS_METRICS,
    group_col='Group', group_order=EDU_ORDER,
    filters={'Category': 'Education', 'Region': 'Statewide'},
    title='Physical health by education \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## A5. By race classification")

code("""small_multiples(
    df, metrics=PHYS_METRICS,
    group_col='Group', group_order=RACE_ORDER,
    filters={'Category': 'Race Classification', 'Region': 'Statewide'},
    title='Physical health by race classification \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## A6. By binary residence (urban vs rural/frontier)")

code("""small_multiples(
    df, metrics=PHYS_METRICS,
    group_col='Group', group_order=RESIDENCE_ORDER,
    filters={'Category': 'Binary Residence Population Category', 'Region': 'Statewide'},
    title='Physical health by urban/rural residence \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("""## A7. By BMI status

Note: the *Obese (BMI ≥ 30)* metric stratified by the *Obese* BMI group is mechanically 100% (and 0% for the other groups) — read that panel as a consistency check, not as new signal.""")

code("""small_multiples(
    df, metrics=PHYS_METRICS,
    group_col='Group', group_order=BMI_ORDER,
    filters={'Category': 'BMI Status', 'Region': 'Statewide'},
    title='Physical health by BMI status \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

# ----- Part B: Mental health ---------------------------------------------

md("""---

# Part B — Mental health

Seven metrics: 14+ days poor mental health, diagnosed depressive disorder, chronic stress, social isolation, serious suicide ideation, unmet social/emotional support needs, dissatisfaction with life.

The lower-prevalence metrics (dissatisfaction with life, suicide ideation, unmet support) have higher sampling variability — expect more RSE>30 flags in the income and race breakdowns.""")

md("## B1. Statewide summary")

code("""mental_summary_fig, mental_summary = statewide_summary(
    df, MENTAL_METRICS,
    'Statewide mental-health prevalence \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
)
mental_summary_fig.show()
mental_summary
""")

md("""## B2. By health district

Each panel = one mental-health metric across 7 districts, with Statewide as a darker reference bar.""")

code("""small_multiples(
    df, metrics=MENTAL_METRICS,
    group_col='Region', group_order=DISTRICT_ORDER,
    filters={'Category': 'Total'},
    highlight_val='Statewide',
    title='Mental health by health district \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## B3. By income")

code("""small_multiples(
    df, metrics=MENTAL_METRICS,
    group_col='Group', group_order=INCOME_ORDER,
    filters={'Category': 'Income', 'Region': 'Statewide'},
    display_map=INCOME_DISPLAY,
    title='Mental health by household income \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## B4. By education")

code("""small_multiples(
    df, metrics=MENTAL_METRICS,
    group_col='Group', group_order=EDU_ORDER,
    filters={'Category': 'Education', 'Region': 'Statewide'},
    title='Mental health by education \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## B5. By race classification")

code("""small_multiples(
    df, metrics=MENTAL_METRICS,
    group_col='Group', group_order=RACE_ORDER,
    filters={'Category': 'Race Classification', 'Region': 'Statewide'},
    title='Mental health by race classification \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## B6. By binary residence (urban vs rural/frontier)")

code("""small_multiples(
    df, metrics=MENTAL_METRICS,
    group_col='Group', group_order=RESIDENCE_ORDER,
    filters={'Category': 'Binary Residence Population Category', 'Region': 'Statewide'},
    title='Mental health by urban/rural residence \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## B7. By BMI status")

code("""small_multiples(
    df, metrics=MENTAL_METRICS,
    group_col='Group', group_order=BMI_ORDER,
    filters={'Category': 'BMI Status', 'Region': 'Statewide'},
    title='Mental health by BMI status \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")


# ----- Part C: Health behaviors ------------------------------------------

md("""---

# Part C — Health behaviors

Six metrics: no routine checkup in the last year, no dental visit in the past 12 months, no leisure-time physical activity, current cigarette smoking, high alcohol consumption, marijuana use in the past 30 days.""")

md("## C1. Statewide summary")

code("""behav_summary_fig, behav_summary = statewide_summary(
    df, BEHAV_METRICS,
    'Statewide health-behavior prevalence \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
)
behav_summary_fig.show()
behav_summary
""")

md("""## C2. By health district

Each panel = one behavior across 7 districts, with Statewide as a darker reference bar.""")

code("""small_multiples(
    df, metrics=BEHAV_METRICS,
    group_col='Region', group_order=DISTRICT_ORDER,
    filters={'Category': 'Total'},
    highlight_val='Statewide',
    title='Health behaviors by health district \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## C3. By income")

code("""small_multiples(
    df, metrics=BEHAV_METRICS,
    group_col='Group', group_order=INCOME_ORDER,
    filters={'Category': 'Income', 'Region': 'Statewide'},
    display_map=INCOME_DISPLAY,
    title='Health behaviors by household income \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## C4. By education")

code("""small_multiples(
    df, metrics=BEHAV_METRICS,
    group_col='Group', group_order=EDU_ORDER,
    filters={'Category': 'Education', 'Region': 'Statewide'},
    title='Health behaviors by education \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## C5. By race classification")

code("""small_multiples(
    df, metrics=BEHAV_METRICS,
    group_col='Group', group_order=RACE_ORDER,
    filters={'Category': 'Race Classification', 'Region': 'Statewide'},
    title='Health behaviors by race classification \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## C6. By binary residence (urban vs rural/frontier)")

code("""small_multiples(
    df, metrics=BEHAV_METRICS,
    group_col='Group', group_order=RESIDENCE_ORDER,
    filters={'Category': 'Binary Residence Population Category', 'Region': 'Statewide'},
    title='Health behaviors by urban/rural residence \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## C7. By BMI status")

code("""small_multiples(
    df, metrics=BEHAV_METRICS,
    group_col='Group', group_order=BMI_ORDER,
    filters={'Category': 'BMI Status', 'Region': 'Statewide'},
    title='Health behaviors by BMI status \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")


# ----- Part D: Social drivers of health ----------------------------------

md("""---

# Part D — Social drivers of health

Five metrics: forgone medical care due to cost, food insecurity (household bought food that did not last always/usually/sometimes), lost employment or reduced hours, no primary source of insurance, insufficient access to transportation.""")

md("## D1. Statewide summary")

code("""sdoh_summary_fig, sdoh_summary = statewide_summary(
    df, SDOH_METRICS,
    'Statewide social-drivers-of-health prevalence \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
)
sdoh_summary_fig.show()
sdoh_summary
""")

md("""## D2. By health district

Each panel = one driver across 7 districts, with Statewide as a darker reference bar.""")

code("""small_multiples(
    df, metrics=SDOH_METRICS,
    group_col='Region', group_order=DISTRICT_ORDER,
    filters={'Category': 'Total'},
    highlight_val='Statewide',
    title='Social drivers of health by health district \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## D3. By income")

code("""small_multiples(
    df, metrics=SDOH_METRICS,
    group_col='Group', group_order=INCOME_ORDER,
    filters={'Category': 'Income', 'Region': 'Statewide'},
    display_map=INCOME_DISPLAY,
    title='Social drivers of health by household income \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## D4. By education")

code("""small_multiples(
    df, metrics=SDOH_METRICS,
    group_col='Group', group_order=EDU_ORDER,
    filters={'Category': 'Education', 'Region': 'Statewide'},
    title='Social drivers of health by education \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## D5. By race classification")

code("""small_multiples(
    df, metrics=SDOH_METRICS,
    group_col='Group', group_order=RACE_ORDER,
    filters={'Category': 'Race Classification', 'Region': 'Statewide'},
    title='Social drivers of health by race classification \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## D6. By binary residence (urban vs rural/frontier)")

code("""small_multiples(
    df, metrics=SDOH_METRICS,
    group_col='Group', group_order=RESIDENCE_ORDER,
    filters={'Category': 'Binary Residence Population Category', 'Region': 'Statewide'},
    title='Social drivers of health by urban/rural residence \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")

md("## D7. By BMI status")

code("""small_multiples(
    df, metrics=SDOH_METRICS,
    group_col='Group', group_order=BMI_ORDER,
    filters={'Category': 'BMI Status', 'Region': 'Statewide'},
    title='Social drivers of health by BMI status \\u2014 women 18\\u201349, Idaho 2020\\u20132024',
).show()
""")


def build():
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
    }
    nb.cells = [
        nbf.v4.new_markdown_cell(src) if kind == "markdown" else nbf.v4.new_code_cell(src)
        for kind, src in CELLS
    ]
    out = Path(__file__).resolve().parent.parent / "analysis.ipynb"
    nbf.write(nb, out)
    print(f"wrote {out}")


if __name__ == "__main__":
    build()

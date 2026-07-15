"""
evaluation_dashboard.py
�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
Streamlit evaluation dashboard for AskBVRITH.

Shows exactly the format requested:
  �?� Summary banner  (Total / Passed / Failed / Warning / Pass rate)
  �?� Per-dimension breakdown table  (01�??08)
  �?� Weakest dimension diagnosis + recommended fix
  �?� RAGAS scores + diagnosis
  �?� Full per-test results table with expandable details

Run:  streamlit run evaluation_dashboard.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from evaluation_suite import (
    DIMENSIONS,
    DIM_CODES,
    FIX_RECOMMENDATIONS,
    EvaluationRunner,
    EvaluationReport,
    Status,
)

# �??�?? Page config �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
ROOT = Path(__file__).parent
LOGO_PATH = ROOT / "static" / "images" / "bvrith_logo.png"

st.set_page_config(
    page_title="AskBVRITH · Evaluation Dashboard",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# �??�?? CSS �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Montserrat', sans-serif; }
#MainMenu, footer, .stDeployButton { visibility: hidden; }

/* �??�?? Summary banner �??�?? */
.summary-banner {
    background: linear-gradient(135deg, #F4F8EC 0%, #FFFFFF 100%);
    border: 1.5px solid #C5D9A8;
    border-left: 6px solid #689F38;
    border-radius: 16px;
    padding: 1.2rem 1.6rem;
    margin-bottom: 1.3rem;
    box-shadow: 0 6px 22px rgba(46,94,46,0.08);
}
.summary-banner h2 {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1B5E20;
    margin: 0 0 0.7rem;
}
.summary-stat-row {
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;
    align-items: center;
}
.summary-stat {
    text-align: center;
    min-width: 80px;
}
.summary-stat-num {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.05;
    color: #1B5E20;
}
.summary-stat-num.fail  { color: #C62828; }
.summary-stat-num.warn  { color: #E65100; }
.summary-stat-num.pct   { color: #2E7D32; }
.summary-stat-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #5A7748;
    margin-top: 0.15rem;
}
.summary-divider {
    width: 1px; height: 48px;
    background: #D0E4BE;
}

/* �??�?? Dimension table �??�?? */
.dim-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0 6px;
    margin-bottom: 0.5rem;
}
.dim-table th {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #4F7942;
    padding: 0 12px 6px;
    border-bottom: 2px solid #D8E4C8;
}
.dim-table td {
    padding: 10px 12px;
    font-size: 0.88rem;
    background: #FFFFFF;
    border-top: 1px solid #EEF3E4;
    border-bottom: 1px solid #EEF3E4;
}
.dim-table td:first-child {
    border-left: 1px solid #EEF3E4;
    border-radius: 8px 0 0 8px;
}
.dim-table td:last-child {
    border-right: 1px solid #EEF3E4;
    border-radius: 0 8px 8px 0;
}
.dim-table tr.dim-row-pass td { border-left: 4px solid #66BB6A !important; }
.dim-table tr.dim-row-warn td { border-left: 4px solid #FFA726 !important; }
.dim-table tr.dim-row-fail td { border-left: 4px solid #EF5350 !important; }

/* �??�?? Progress bar �??�?? */
.prog-bar-bg {
    background: #E8F5E9;
    border-radius: 999px;
    height: 8px;
    width: 120px;
    display: inline-block;
    vertical-align: middle;
}
.prog-bar-fill {
    height: 8px;
    border-radius: 999px;
    background: #66BB6A;
}
.prog-bar-fill.warn { background: #FFA726; }
.prog-bar-fill.fail { background: #EF5350; }

/* �??�?? Diagnosis box �??�?? */
.diagnosis-box {
    border-radius: 14px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.9rem;
}
.diagnosis-box.weakest {
    background: #FFF8E1;
    border: 1px solid #FFE082;
    border-left: 5px solid #FFB300;
}
.diagnosis-box.ragas {
    background: #E8F5E9;
    border: 1px solid #A5D6A7;
    border-left: 5px solid #43A047;
}
.diagnosis-box h3 {
    font-size: 0.95rem;
    font-weight: 700;
    margin: 0 0 0.4rem;
    color: #37474F;
}
.diagnosis-box p {
    font-size: 0.87rem;
    color: #455A64;
    margin: 0;
    line-height: 1.55;
}
.fix-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #E65100;
    margin-top: 0.5rem;
    margin-bottom: 0.2rem;
}

/* �??�?? RAGAS score pills �??�?? */
.ragas-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.85rem;
    margin: 0.6rem 0 0.8rem;
}
.ragas-pill {
    background: #FFFFFF;
    border: 1.5px solid #C8E6C9;
    border-radius: 12px;
    padding: 0.6rem 1rem;
    min-width: 130px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(46,94,46,0.06);
}
.ragas-pill.lowest {
    border-color: #FFB300;
    background: #FFFDE7;
}
.ragas-pill-num {
    font-size: 1.55rem;
    font-weight: 800;
    color: #2E7D32;
    line-height: 1.1;
}
.ragas-pill-num.lowest { color: #F57F17; }
.ragas-pill-label {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #5A7748;
    margin-top: 0.2rem;
}

/* �??�?? Status badge �??�?? */
.badge-pass { background:#E8F5E9; color:#2E7D32; border:1px solid #A5D6A7;
              border-radius:999px; padding:2px 10px; font-size:0.72rem; font-weight:700; }
.badge-warn { background:#FFF3E0; color:#E65100; border:1px solid #FFCC80;
              border-radius:999px; padding:2px 10px; font-size:0.72rem; font-weight:700; }
.badge-fail { background:#FFEBEE; color:#C62828; border:1px solid #EF9A9A;
              border-radius:999px; padding:2px 10px; font-size:0.72rem; font-weight:700; }

.section-title {
    font-size: 0.78rem;
    font-weight: 700;
    color: #4F7942;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin: 1.1rem 0 0.5rem;
    border-bottom: 1px solid #D8E4C8;
    padding-bottom: 0.25rem;
}
</style>
""", unsafe_allow_html=True)




# �??�?? Sidebar �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    st.markdown("### 🧪 Evaluation Suite")
    st.caption("20 structured test cases across 8 dimensions.")
    st.markdown("---")

    dim_filter = st.selectbox(
        "Filter by dimension",
        ["All"] + DIMENSIONS,
        index=0,
    )
    run_btn = st.button("▶️  Run Evaluation", use_container_width=True, type="primary")
    st.markdown("---")
    st.markdown("**Dimensions**")
    for i, name in enumerate(DIMENSIONS, 1):
        st.markdown(f"&nbsp;&nbsp;`{i:02d}` {name}")
    st.markdown("---")
    st.caption("AskBVRITH · Evaluation v1 · BVRIT Hyderabad")


# �??�?? Session state �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
if "eval_report" not in st.session_state:
    st.session_state.eval_report = None

# Page title
st.markdown("## 🧪 Evaluation Dashboard")
st.caption(
    "Structured pass/fail evaluation across 8 dimensions — "
    "Functional · Quality · Safety · Security · Robustness · Performance · Context · RAGAS"
)

# Auto-run on first load
if st.session_state.eval_report is None or run_btn:
    with st.spinner("Running evaluation suite…"):
        runner = EvaluationRunner()
        if dim_filter == "All":
            report: EvaluationReport = runner.run_all()
        else:
            report: EvaluationReport = runner.run_dimension(dim_filter)
    st.session_state.eval_report = report

report: EvaluationReport = st.session_state.eval_report


# �??�?? Helper: status �?? badge HTML �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
def _badge(status: Status) -> str:
    if status == Status.PASS:
        return '<span class="badge-pass">PASS</span>'
    if status == Status.WARNING:
        return '<span class="badge-warn">WARN</span>'
    return '<span class="badge-fail">FAIL</span>'


# �??�?? Helper: progress bar HTML �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
def _prog(pct: float) -> str:
    cls = "" if pct >= 0.80 else ("warn" if pct >= 0.50 else "fail")
    fill_w = int(pct * 120)
    return (
        f'<div class="prog-bar-bg">'
        f'<div class="prog-bar-fill {cls}" style="width:{fill_w}px"></div>'
        f'</div>'
    )


# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# 1. SUMMARY BANNER
# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
pct_display = f"{report.pass_rate*100:.0f}%"
warn_cls  = " fail" if report.failed > 0 else ""
pct_cls   = " fail" if report.pass_rate < 0.70 else (" warn" if report.pass_rate < 0.85 else " pct")

st.markdown('<p class="section-title">Summary</p>', unsafe_allow_html=True)
st.markdown(
    f'<div class="summary-banner">'
    f'<h2>Test Run · {report.run_at} · {report.total_ms:.0f} ms</h2>'
    f'<div class="summary-stat-row">'
    f'<div class="summary-stat">'
    f'  <div class="summary-stat-num">{report.total}</div>'
    f'  <div class="summary-stat-label">Total</div>'
    f'</div>'
    f'<div class="summary-divider"></div>'
    f'<div class="summary-stat">'
    f'  <div class="summary-stat-num">{report.passed}</div>'
    f'  <div class="summary-stat-label">Passed</div>'
    f'</div>'
    f'<div class="summary-divider"></div>'
    f'<div class="summary-stat">'
    f'  <div class="summary-stat-num{warn_cls}">{report.failed}</div>'
    f'  <div class="summary-stat-label">Failed</div>'
    f'</div>'
    f'<div class="summary-divider"></div>'
    f'<div class="summary-stat">'
    f'  <div class="summary-stat-num warn">{report.warnings}</div>'
    f'  <div class="summary-stat-label">Warning</div>'
    f'</div>'
    f'<div class="summary-divider"></div>'
    f'<div class="summary-stat">'
    f'  <div class="summary-stat-num{pct_cls}">{pct_display}</div>'
    f'  <div class="summary-stat-label">Pass Rate</div>'
    f'</div>'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True,
)




# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# 2. PER-DIMENSION BREAKDOWN TABLE
# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
st.markdown('<p class="section-title">Per-dimension Breakdown</p>', unsafe_allow_html=True)

# Split into two columns of 4 (matching the user's requested layout)
left_dims  = report.dimensions[:4]
right_dims = report.dimensions[4:]

def _dim_row_class(d) -> str:
    if d.failed > 0:    return "dim-row-fail"
    if d.warnings > 0:  return "dim-row-warn"
    return "dim-row-pass"

def _dim_table_html(dims) -> str:
    rows = ""
    for d in dims:
        rc = _dim_row_class(d)
        warn_txt = f'&nbsp;<span style="color:#E65100;font-size:0.75rem">⚠️ {d.warnings} warn</span>' if d.warnings else ""
        fail_txt = f'&nbsp;<span style="color:#C62828;font-size:0.75rem">❌ {d.failed} fail</span>'  if d.failed  else ""
        rows += (
            f'<tr class="{rc}">'
            f'<td><code>{d.code}</code></td>'
            f'<td><strong>{d.name}</strong></td>'
            f'<td>{_prog(d.pass_rate)}</td>'
            f'<td><strong>{d.passed}/{d.total}</strong> passed{warn_txt}{fail_txt}</td>'
            f'</tr>'
        )
    return (
        f'<table class="dim-table">'
        f'<thead><tr>'
        f'<th>#</th><th>Dimension</th><th>Progress</th><th>Result</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'</table>'
    )

col_l, col_r = st.columns(2)
with col_l:
    if left_dims:
        st.markdown(_dim_table_html(left_dims), unsafe_allow_html=True)
with col_r:
    if right_dims:
        st.markdown(_dim_table_html(right_dims), unsafe_allow_html=True)




# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# 3. WEAKEST DIMENSION DIAGNOSIS
# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
st.markdown('<p class="section-title">Weakest Dimension</p>', unsafe_allow_html=True)

wd = report.weakest_dimension
wd_fix = FIX_RECOMMENDATIONS.get(wd.name, "Review logs and address failing tests.")

# Pick the first failing test as the specific evidence
failing_tests = [r for r in wd.results if r.status in (Status.FAIL, Status.WARNING)]
evidence = failing_tests[0].detail if failing_tests else "No individual test failures."

st.markdown(
    f'<div class="diagnosis-box weakest">'
    f'<h3>⚠️ Weakest: {wd.code} {wd.name} — {wd.passed}/{wd.total} passed '
    f'({wd.pass_rate*100:.0f}%)</h3>'
    f'<p>{evidence}</p>'
    f'<p class="fix-label">Recommended Fix</p>'
    f'<p>{wd_fix}</p>'
    f'</div>',
    unsafe_allow_html=True,
)

# Also show all dimensions that have failures, not just the weakest
other_failures = [
    d for d in report.dimensions
    if d.name != wd.name and (d.failed > 0 or d.warnings > 0)
]
if other_failures:
    with st.expander("Other dimensions with issues", expanded=False):
        for d in other_failures:
            issues = [r for r in d.results if r.status in (Status.FAIL, Status.WARNING)]
            for r in issues:
                icon = "⚠️" if r.status == Status.WARNING else "❌"
                fix = FIX_RECOMMENDATIONS.get(d.name, "")
                st.markdown(
                    f"**{icon} {d.code} {d.name} — {r.case.description}**  \n"
                    f"_{r.detail}_  \n"
                    f"Fix: {fix}"
                )
                st.markdown("---")


# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# 4. RAGAS SCORES
# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
st.markdown('<p class="section-title">RAGAS Scores</p>', unsafe_allow_html=True)

r = report.ragas
weakest_name, weakest_val = r.weakest

ragas_items = [
    ("Faithfulness",      r.faithfulness),
    ("Answer Relevancy",  r.answer_relevancy),
    ("Context Precision", r.context_precision),
    ("Context Recall",    r.context_recall),
]

pills_html = '<div class="ragas-row">'
for label, val in ragas_items:
    is_low = (label == weakest_name)
    num_cls = "ragas-pill-num lowest" if is_low else "ragas-pill-num"
    pill_cls = "ragas-pill lowest" if is_low else "ragas-pill"
    pills_html += (
        f'<div class="{pill_cls}">'
        f'<div class="{num_cls}">{val:.2f}</div>'
        f'<div class="ragas-pill-label">{label}</div>'
        f'</div>'
    )
pills_html += '</div>'
st.markdown(pills_html, unsafe_allow_html=True)

st.markdown(
    f'<div class="diagnosis-box ragas">'
    f'<h3>📊 RAGAS Diagnosis</h3>'
    f'<p>{r.diagnosis}</p>'
    f'</div>',
    unsafe_allow_html=True,
)




# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# 5. FULL TEST RESULTS TABLE
# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
st.markdown('<p class="section-title">All Test Results</p>', unsafe_allow_html=True)

# Build a flat dataframe for display
rows_data = []
for res in report.results:
    rows_data.append({
        "ID":        res.case.id,
        "Dimension": f"{DIM_CODES[res.case.dimension]} {res.case.dimension}",
        "Test Case": res.case.description,
        "Input":     res.case.input[:60] + ("…" if len(res.case.input) > 60 else ""),
        "Status":    res.status.value.upper(),
        "Detail":    res.detail,
        "ms":        f"{res.latency_ms:.2f}",
    })

results_df = pd.DataFrame(rows_data)

# Colour map for the Status column
def _colour_status(val: str) -> str:
    if val == "PASS":    return "background-color:#E8F5E9; color:#2E7D32; font-weight:700"
    if val == "WARNING": return "background-color:#FFF3E0; color:#E65100; font-weight:700"
    return                      "background-color:#FFEBEE; color:#C62828; font-weight:700"

styled = results_df.style.applymap(_colour_status, subset=["Status"])
st.dataframe(styled, use_container_width=True, hide_index=True)

# �??�?? Filter by status �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
status_filter = st.radio(
    "Show:", ["All", "Failures & Warnings", "Pass only"],
    horizontal=True, index=0,
)
if status_filter == "Failures & Warnings":
    filtered = results_df[results_df["Status"].isin(["FAIL", "WARNING"])]
    st.dataframe(filtered.style.applymap(_colour_status, subset=["Status"]),
                 use_container_width=True, hide_index=True)
elif status_filter == "Pass only":
    filtered = results_df[results_df["Status"] == "PASS"]
    st.dataframe(filtered.style.applymap(_colour_status, subset=["Status"]),
                 use_container_width=True, hide_index=True)

# �??�?? Export �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
st.markdown('<p class="section-title">Export</p>', unsafe_allow_html=True)
col_a, col_b = st.columns(2)
with col_a:
    st.download_button(
        "📥 Download Full Results (CSV)",
        data=results_df.to_csv(index=False),
        file_name=f"eval_results_{report.run_at.replace(' ','_').replace(':','-')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
with col_b:
    import json as _json
    summary_dict = {
        "run_at":    report.run_at,
        "total":     report.total,
        "passed":    report.passed,
        "failed":    report.failed,
        "warnings":  report.warnings,
        "pass_rate": round(report.pass_rate, 4),
        "dimensions": [
            {
                "code":      d.code,
                "name":      d.name,
                "passed":    d.passed,
                "total":     d.total,
                "pass_rate": round(d.pass_rate, 4),
            }
            for d in report.dimensions
        ],
        "ragas": {
            "faithfulness":      report.ragas.faithfulness,
            "answer_relevancy":  report.ragas.answer_relevancy,
            "context_precision": report.ragas.context_precision,
            "context_recall":    report.ragas.context_recall,
        },
        "weakest_dimension": report.weakest_dimension.name,
        "recommended_fix":   FIX_RECOMMENDATIONS.get(report.weakest_dimension.name, ""),
    }
    st.download_button(
        "📥 Download Summary (JSON)",
        data=_json.dumps(summary_dict, indent=2),
        file_name=f"eval_summary_{report.run_at.replace(' ','_').replace(':','-')}.json",
        mime="application/json",
        use_container_width=True,
    )

# �??�?? Footer �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
st.markdown("---")
st.caption(
    "🧪 AskBVRITH Evaluation Dashboard · 20 test cases · 8 dimensions · "
    "BVRIT Hyderabad College of Engineering for Women"
)



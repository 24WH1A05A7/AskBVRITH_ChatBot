"""
pages/evaluation.py
�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
Evaluation dashboard page for the AskBVRITH multi-page app.
Called by app.py via st.navigation; do NOT run directly.
"""

from __future__ import annotations

import json
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

ROOT = Path(__file__).parent.parent


def _badge(status: Status) -> str:
    if status == Status.PASS:
        return '<span class="badge-pass">PASS</span>'
    if status == Status.WARNING:
        return '<span class="badge-warn">WARN</span>'
    return '<span class="badge-fail">FAIL</span>'


def _prog(pct: float) -> str:
    css   = "" if pct >= 0.80 else ("warn" if pct >= 0.50 else "fail")
    width = int(pct * 120)
    return (
        f'<div class="prog-bar-bg">'
        f'<div class="prog-bar-fill {css}" style="width:{width}px"></div>'
        f"</div>"
    )


def _dim_table_html(dims) -> str:
    rows = ""
    for d in dims:
        rc = "dim-row-fail" if d.failed > 0 else ("dim-row-warn" if d.warnings > 0 else "dim-row-pass")
        warn_txt = (f'&nbsp;<span style="color:#E65100;font-size:.75rem">⚠️ {d.warnings} warn</span>'
                    if d.warnings else "")
        fail_txt = (f'&nbsp;<span style="color:#C62828;font-size:.75rem">❌ {d.failed} fail</span>'
                    if d.failed else "")
        rows += (
            f'<tr class="{rc}">'
            f'<td><code>{d.code}</code></td>'
            f'<td><strong>{d.name}</strong></td>'
            f'<td>{_prog(d.pass_rate)}</td>'
            f'<td><strong>{d.passed}/{d.total}</strong> passed{warn_txt}{fail_txt}</td>'
            f"</tr>"
        )
    return (
        '<table class="dim-table"><thead><tr>'
        "<th>#</th><th>Dimension</th><th>Progress</th><th>Result</th>"
        f"</tr></thead><tbody>{rows}</tbody></table>"
    )


# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
def render() -> None:

    # �??�?? Sidebar additions �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    with st.sidebar:
        dim_filter = st.selectbox(
            "Filter by dimension",
            ["All"] + DIMENSIONS,
            index=0,
            key="eval_dim_filter",
        )
        run_btn = st.button(
            "▶️  Run Evaluation",
            key="eval_run_btn",
            use_container_width=True,
            type="primary",
        )
        st.markdown("---")
        st.caption("Evaluation Suite v1 · 20 test cases")

    # �??�?? Page title �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    st.markdown("## 🧪 Evaluation Dashboard")
    st.caption(
        "Structured pass/fail evaluation across 8 dimensions — "
        "Functional · Quality · Safety · Security · "
        "Robustness · Performance · Context · RAGAS"
    )

    # �??�?? Run / cache �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    if "eval_report" not in st.session_state:
        st.session_state.eval_report = None

    if st.session_state.eval_report is None or run_btn:
        with st.spinner("Running evaluation suite…"):
            runner = EvaluationRunner()
            report: EvaluationReport = (
                runner.run_all() if dim_filter == "All"
                else runner.run_dimension(dim_filter)
            )
        st.session_state.eval_report = report

    report: EvaluationReport = st.session_state.eval_report

    # �??�?? 1. Summary banner �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    fail_cls = " fail" if report.failed > 0 else ""
    pct_cls  = (" fail" if report.pass_rate < 0.70
                else (" warn" if report.pass_rate < 0.85 else " pct"))

    st.markdown('<p class="section-title">Summary</p>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="summary-banner">'
        f'<h2>Test Run · {report.run_at} · {report.total_ms:.0f} ms</h2>'
        f'<div class="summary-stat-row">'
        f'<div class="summary-stat"><div class="summary-stat-num">{report.total}</div>'
        f'<div class="summary-stat-label">Total</div></div>'
        f'<div class="summary-divider"></div>'
        f'<div class="summary-stat"><div class="summary-stat-num">{report.passed}</div>'
        f'<div class="summary-stat-label">Passed</div></div>'
        f'<div class="summary-divider"></div>'
        f'<div class="summary-stat"><div class="summary-stat-num{fail_cls}">{report.failed}</div>'
        f'<div class="summary-stat-label">Failed</div></div>'
        f'<div class="summary-divider"></div>'
        f'<div class="summary-stat"><div class="summary-stat-num warn">{report.warnings}</div>'
        f'<div class="summary-stat-label">Warning</div></div>'
        f'<div class="summary-divider"></div>'
        f'<div class="summary-stat">'
        f'<div class="summary-stat-num{pct_cls}">{report.pass_rate*100:.0f}%</div>'
        f'<div class="summary-stat-label">Pass Rate</div></div>'
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # �??�?? 2. Per-dimension table �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    st.markdown('<p class="section-title">Per-dimension Breakdown</p>', unsafe_allow_html=True)
    left_dims  = report.dimensions[:4]
    right_dims = report.dimensions[4:]
    col_l, col_r = st.columns(2)
    with col_l:
        if left_dims:
            st.markdown(_dim_table_html(left_dims), unsafe_allow_html=True)
    with col_r:
        if right_dims:
            st.markdown(_dim_table_html(right_dims), unsafe_allow_html=True)

    # �??�?? 3. Weakest dimension �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    st.markdown('<p class="section-title">Weakest Dimension</p>', unsafe_allow_html=True)
    wd      = report.weakest_dimension
    wd_fix  = FIX_RECOMMENDATIONS.get(wd.name, "Review logs.")
    failing = [r for r in wd.results if r.status in (Status.FAIL, Status.WARNING)]
    evidence = failing[0].detail if failing else "No individual test failures."

    st.markdown(
        f'<div class="diagnosis-box weakest">'
        f'<h3>⚠️ Weakest: {wd.code} {wd.name} — {wd.passed}/{wd.total} passed '
        f'({wd.pass_rate*100:.0f}%)</h3>'
        f"<p>{evidence}</p>"
        f'<p class="fix-label">Recommended Fix</p>'
        f"<p>{wd_fix}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    other_failures = [
        d for d in report.dimensions
        if d.name != wd.name and (d.failed > 0 or d.warnings > 0)
    ]
    if other_failures:
        with st.expander("Other dimensions with issues", expanded=False):
            for d in other_failures:
                for r in [x for x in d.results if x.status in (Status.FAIL, Status.WARNING)]:
                    icon = "⚠️" if r.status == Status.WARNING else "❌"
                    st.markdown(
                        f"**{icon} {d.code} {d.name} — {r.case.description}**  \n"
                        f"_{r.detail}_  \n"
                        f"Fix: {FIX_RECOMMENDATIONS.get(d.name, '')}"
                    )
                    st.markdown("---")

    # �??�?? 4. RAGAS scores �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    st.markdown('<p class="section-title">RAGAS Scores</p>', unsafe_allow_html=True)
    r             = report.ragas
    weakest_name, _ = r.weakest

    pills = '<div class="ragas-row">'
    for label, val in [
        ("Faithfulness",     r.faithfulness),
        ("Answer Relevancy", r.answer_relevancy),
        ("Context Precision",r.context_precision),
        ("Context Recall",   r.context_recall),
    ]:
        low      = label == weakest_name
        pill_cls = "ragas-pill lowest" if low else "ragas-pill"
        num_cls  = "ragas-pill-num lowest" if low else "ragas-pill-num"
        pills += (
            f'<div class="{pill_cls}">'
            f'<div class="{num_cls}">{val:.2f}</div>'
            f'<div class="ragas-pill-label">{label}</div>'
            f"</div>"
        )
    pills += "</div>"
    st.markdown(pills, unsafe_allow_html=True)

    st.markdown(
        f'<div class="diagnosis-box ragas">'
        f"<h3>📊 RAGAS Diagnosis</h3>"
        f"<p>{r.diagnosis}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # �??�?? 5. Full results table �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    st.markdown('<p class="section-title">All Test Results</p>', unsafe_allow_html=True)

    rows_data = [
        {
            "ID":        res.case.id,
            "Dimension": f"{DIM_CODES[res.case.dimension]} {res.case.dimension}",
            "Test Case": res.case.description,
            "Input":     res.case.input[:60] + ("…" if len(res.case.input) > 60 else ""),
            "Status":    res.status.value.upper(),
            "Detail":    res.detail,
            "ms":        f"{res.latency_ms:.2f}",
        }
        for res in report.results
    ]
    results_df = pd.DataFrame(rows_data)

    def _colour(val: str) -> str:
        if val == "PASS":    return "background-color:#E8F5E9;color:#2E7D32;font-weight:700"
        if val == "WARNING": return "background-color:#FFF3E0;color:#E65100;font-weight:700"
        return                      "background-color:#FFEBEE;color:#C62828;font-weight:700"

    st.dataframe(
        results_df.style.applymap(_colour, subset=["Status"]),
        use_container_width=True,
        hide_index=True,
    )

    status_filter = st.radio(
        "Show:", ["All", "Failures & Warnings", "Pass only"],
        horizontal=True, index=0, key="eval_status_filter",
    )
    if status_filter == "Failures & Warnings":
        f = results_df[results_df["Status"].isin(["FAIL", "WARNING"])]
        st.dataframe(f.style.applymap(_colour, subset=["Status"]),
                     use_container_width=True, hide_index=True)
    elif status_filter == "Pass only":
        f = results_df[results_df["Status"] == "PASS"]
        st.dataframe(f.style.applymap(_colour, subset=["Status"]),
                     use_container_width=True, hide_index=True)

    # �??�?? 6. Export �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    st.markdown('<p class="section-title">Export</p>', unsafe_allow_html=True)
    ts = report.run_at.replace(" ", "_").replace(":", "-")
    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button(
            "📥 Download Full Results (CSV)",
            data=results_df.to_csv(index=False),
            file_name=f"eval_results_{ts}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_b:
        summary_dict = {
            "run_at":    report.run_at,
            "total":     report.total,
            "passed":    report.passed,
            "failed":    report.failed,
            "warnings":  report.warnings,
            "pass_rate": round(report.pass_rate, 4),
            "dimensions": [
                {"code": d.code, "name": d.name,
                 "passed": d.passed, "total": d.total,
                 "pass_rate": round(d.pass_rate, 4)}
                for d in report.dimensions
            ],
            "ragas": {
                "faithfulness":      r.faithfulness,
                "answer_relevancy":  r.answer_relevancy,
                "context_precision": r.context_precision,
                "context_recall":    r.context_recall,
            },
            "weakest_dimension": wd.name,
            "recommended_fix":   wd_fix,
        }
        st.download_button(
            "📥 Download Summary (JSON)",
            data=json.dumps(summary_dict, indent=2),
            file_name=f"eval_summary_{ts}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.markdown("---")
    st.caption(
        "🧪 Evaluation Dashboard · 20 test cases · 8 dimensions · "
        "BVRIT Hyderabad College of Engineering for Women"
    )



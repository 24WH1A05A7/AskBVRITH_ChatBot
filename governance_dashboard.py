"""
governance_dashboard.py
�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
Governance & Evaluation Dashboard for AskBVRITH.

8 evaluation categories:
  01 Functional   02 Quality    03 Safety    04 Security
  05 Robustness   06 Performance  07 Context   08 RAGAS

Run:  streamlit run governance_dashboard.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from observability import ObservabilityService

# �??�?? Page config �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
ROOT = Path(__file__).parent
LOGO_PATH = ROOT / "static" / "images" / "bvrith_logo.png"

st.set_page_config(
    page_title="AskBVRITH · Governance & Evaluation",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# �??�?? CSS �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Montserrat', sans-serif; }
#MainMenu, footer, .stDeployButton { visibility: hidden; }

/* Scorecard grid */
.score-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.85rem;
    margin-bottom: 1.4rem;
}
.score-card {
    background: #ffffff;
    border: 1px solid #dde6d5;
    border-top: 4px solid #689F38;
    border-radius: 14px;
    padding: 1rem 1.1rem 0.9rem;
    box-shadow: 0 6px 18px rgba(46,94,46,0.07);
    text-align: center;
}
.score-card.warn  { border-top-color: #E68A2E; }
.score-card.fail  { border-top-color: #C62828; }
.score-card.na    { border-top-color: #90A4AE; }
.score-num {
    font-size: 2rem;
    font-weight: 800;
    color: #1B5E20;
    line-height: 1.1;
}
.score-num.warn  { color: #E65100; }
.score-num.fail  { color: #C62828; }
.score-num.na    { color: #607D8B; }
.score-label {
    font-size: 0.72rem;
    font-weight: 700;
    color: #4F7942;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-top: 0.3rem;
}
.score-sub {
    font-size: 0.78rem;
    color: #6B7F61;
    margin-top: 0.2rem;
    line-height: 1.4;
}

/* Category header pill */
.cat-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    background: #EEF7E7;
    border: 1px solid #C5D9A8;
    border-radius: 999px;
    padding: 0.3rem 0.9rem;
    font-size: 0.8rem;
    font-weight: 700;
    color: #2F6236;
    margin-bottom: 0.7rem;
}

/* Section divider */
.gov-section {
    font-size: 0.78rem;
    font-weight: 700;
    color: #4F7942;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin: 1.1rem 0 0.4rem;
    border-bottom: 1px solid #D8E4C8;
    padding-bottom: 0.25rem;
}

/* Status badge */
.badge-pass { background:#E8F5E9; color:#2E7D32; border:1px solid #A5D6A7;
              border-radius:999px; padding:2px 10px; font-size:0.73rem; font-weight:700; }
.badge-warn { background:#FFF3E0; color:#E65100; border:1px solid #FFCC80;
              border-radius:999px; padding:2px 10px; font-size:0.73rem; font-weight:700; }
.badge-fail { background:#FFEBEE; color:#C62828; border:1px solid #EF9A9A;
              border-radius:999px; padding:2px 10px; font-size:0.73rem; font-weight:700; }
.badge-na   { background:#ECEFF1; color:#546E7A; border:1px solid #B0BEC5;
              border-radius:999px; padding:2px 10px; font-size:0.73rem; font-weight:700; }

/* Hero */
.gov-hero {
    background: linear-gradient(135deg,#FFFFFF 0%,#F4F8EC 100%);
    border: 1px solid #D8E4C8;
    border-left: 5px solid #689F38;
    border-radius: 16px;
    padding: 1.1rem 1.5rem;
    margin-bottom: 1.3rem;
    box-shadow: 0 4px 18px rgba(46,94,46,0.07);
}
.gov-hero h1 { font-size:1.55rem; font-weight:800; color:#1B5E20; margin:0 0 0.3rem; }
.gov-hero p  { color:#4A5D45; font-size:0.9rem; margin:0; line-height:1.55; }
</style>
""", unsafe_allow_html=True)



# �??�?? Service �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
@st.cache_resource
def _get_service() -> ObservabilityService:
    return ObservabilityService()

service = _get_service()


# �??�?? Helper: rows �?? DataFrame �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
def _to_df(rows) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


# �??�?? Helper: score colour class �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
def _cls(val: float | None, good_above: float = 0.75, warn_above: float = 0.50) -> str:
    """Return CSS class string based on threshold."""
    if val is None:
        return "na"
    if val >= good_above:
        return ""       # green (default)
    if val >= warn_above:
        return "warn"
    return "fail"


def _badge(label: str, kind: str = "") -> str:
    cls = {"pass": "badge-pass", "warn": "badge-warn", "fail": "badge-fail"}.get(kind, "badge-na")
    return f'<span class="{cls}">{label}</span>'


def _pct(val: float | None) -> str:
    return f"{val * 100:.0f}%" if val is not None else "N/A"


def _score_card(num: str, label: str, value: str, subtitle: str, cls: str = "") -> str:
    num_cls = f'score-num {cls}'.strip()
    return (
        f'<div class="score-card {cls}">'
        f'<div class="{num_cls}">{value}</div>'
        f'<div class="score-label">{num} · {label}</div>'
        f'<div class="score-sub">{subtitle}</div>'
        f'</div>'
    )


# �??�?? Data pull �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
def _load_data():
    logs_rows  = service.db.get_llm_logs(limit=500)
    alert_rows = service.db.get_alerts(limit=200)
    eval_rows  = service.db.fetch_all(
        "SELECT * FROM evaluation_reports ORDER BY created_at DESC"
    )
    feed_rows  = service.db.fetch_all(
        "SELECT * FROM feedback ORDER BY created_at DESC"
    )
    logs_df    = _to_df(logs_rows)
    alert_df   = _to_df(alert_rows)
    eval_df    = _to_df(eval_rows)
    feed_df    = _to_df(feed_rows)

    # datetime coercion
    for df, col in [(logs_df, "created_at"), (alert_df, "created_at"),
                    (eval_df, "created_at"), (feed_df, "created_at")]:
        if not df.empty and col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return logs_df, alert_df, eval_df, feed_df



# �??�?? Sidebar �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    st.markdown("### 🏛️ Governance Dashboard")
    st.caption("8-category evaluation framework for AskBVRITH.")
    st.markdown("---")
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
    st.markdown("**Categories**")
    for idx, name in enumerate(
        ["Functional", "Quality", "Safety", "Security",
         "Robustness", "Performance", "Context", "RAGAS"], start=1
    ):
        st.markdown(f"&nbsp;&nbsp;`{idx:02d}` {name}")
    st.markdown("---")
    st.caption("AskBVRITH · BVRIT Hyderabad · Governance v1")


# �??�?? Page header �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
st.markdown(
    '<div class="gov-hero">'
    '<h1>�?�?️ Governance &amp; Evaluation Dashboard</h1>'
    '<p>8-category evaluation framework covering Functional correctness, Response quality, '
    'Safety guardrails, Security posture, Robustness, Performance, Contextual grounding, '
    'and RAGAS-style metrics — all derived from live observability data.</p>'
    '</div>',
    unsafe_allow_html=True,
)

# �??�?? Load data �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
logs_df, alert_df, eval_df, feed_df = _load_data()

total_queries    = len(logs_df)
error_queries    = len(logs_df[logs_df["status"] == "failure"]) if not logs_df.empty else 0
success_queries  = total_queries - error_queries
error_rate       = error_queries / total_queries if total_queries else 0.0
avg_latency_ms   = logs_df["latency_ms"].mean() if not logs_df.empty else 0.0
p95_latency_ms   = logs_df["latency_ms"].quantile(0.95) if not logs_df.empty else 0.0
avg_chunks       = logs_df["retrieved_chunk_count"].mean() if not logs_df.empty and "retrieved_chunk_count" in logs_df.columns else 0.0
total_alerts     = len(alert_df)
unacked_alerts   = len(alert_df[alert_df["acknowledged"] == 0]) if not alert_df.empty else 0

# Aggregate evaluation scores
def _avg_col(df: pd.DataFrame, col: str) -> float | None:
    if df.empty or col not in df.columns:
        return None
    vals = df[col].dropna()
    return float(vals.mean()) if len(vals) else None

# Pull from both eval_df and llm_logs inline scores
faith_eval  = _avg_col(eval_df, "faithfulness")
faith_logs  = _avg_col(logs_df, "faithfulness_score")
faithfulness = faith_eval if faith_eval is not None else faith_logs

halluc_eval = _avg_col(eval_df, "hallucination")
halluc_logs = _avg_col(logs_df, "hallucination_score")
hallucination = halluc_eval if halluc_eval is not None else halluc_logs

tox_eval    = _avg_col(eval_df, "toxicity")
tox_logs    = _avg_col(logs_df, "toxicity_score")
toxicity    = tox_eval if tox_eval is not None else tox_logs

bias_eval   = _avg_col(eval_df, "bias")
bias_logs   = _avg_col(logs_df, "bias_score")
bias        = bias_eval if bias_eval is not None else bias_logs

relevancy_eval = _avg_col(eval_df, "relevancy")
relevancy_logs = _avg_col(logs_df, "relevancy_score")
relevancy   = relevancy_eval if relevancy_eval is not None else relevancy_logs

# Feedback stats
avg_rating    = _avg_col(feed_df, "rating")
helpful_pct   = None
if not feed_df.empty and "helpful" in feed_df.columns:
    h = feed_df["helpful"].dropna()
    helpful_pct = float(h.mean()) if len(h) else None

# �??�?? Summary scorecard row �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
st.markdown('<p class="gov-section">Overall Health Scores</p>', unsafe_allow_html=True)

functional_score  = (1.0 - error_rate) if total_queries else None
quality_score     = (avg_rating / 5.0) if avg_rating is not None else None
safety_score      = (1.0 - (toxicity or 0)) if toxicity is not None else None
security_score    = None  # derived below from alert analysis
robustness_score  = (1.0 - error_rate) if total_queries > 5 else None
perf_score        = max(0.0, 1.0 - (avg_latency_ms / 5000.0)) if avg_latency_ms else None
context_score     = relevancy
ragas_score       = faithfulness

cards_html = '<div class="score-grid">'
for num, label, val, subtitle in [
    ("01", "Functional",   functional_score,  f"{success_queries}/{total_queries} queries succeeded"),
    ("02", "Quality",      quality_score,     f"Avg rating {avg_rating:.1f}/5" if avg_rating else "No feedback yet"),
    ("03", "Safety",       safety_score,      f"Toxicity {_pct(toxicity)}" if toxicity is not None else "No eval data"),
    ("04", "Security",     None,              f"{unacked_alerts} unacknowledged alert(s)"),
    ("05", "Robustness",   robustness_score,  f"Error rate {error_rate*100:.1f}%"),
    ("06", "Performance",  perf_score,        f"Avg {avg_latency_ms:.0f} ms · P95 {p95_latency_ms:.0f} ms"),
    ("07", "Context",      context_score,     f"Relevancy {_pct(relevancy)}" if relevancy is not None else "No eval data"),
    ("08", "RAGAS",        ragas_score,       f"Faithfulness {_pct(faithfulness)}" if faithfulness is not None else "No eval data"),
]:
    cls = _cls(val)
    display = f"{val*100:.0f}%" if val is not None else "N/A"
    cards_html += _score_card(num, label, display, subtitle, cls)

cards_html += "</div>"
st.markdown(cards_html, unsafe_allow_html=True)



st.markdown("---")

# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# 01  FUNCTIONAL
# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
with st.expander("01 · Functional — Correctness & Tool Execution", expanded=True):
    st.markdown('<span class="cat-pill">✅ 01 Functional</span>', unsafe_allow_html=True)
    st.caption(
        "Measures whether the chatbot answers questions correctly, invokes tools when needed, "
        "and returns valid results."
    )

    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Total Queries",    total_queries)
    f2.metric("Successful",       success_queries,
              delta=f"-{error_queries} errors" if error_queries else None,
              delta_color="inverse")
    f3.metric("Error Rate",       f"{error_rate*100:.1f}%")

    tool_queries = 0
    if not logs_df.empty and "tool_used" in logs_df.columns:
        tool_queries = int(logs_df["tool_used"].notna().sum())
    f4.metric("Tool Invocations", tool_queries)

    # Routing breakdown
    if not logs_df.empty and "tool_used" in logs_df.columns:
        st.markdown('<p class="gov-section">Tool Usage Breakdown</p>', unsafe_allow_html=True)
        routing_counts = logs_df["tool_used"].fillna("rag_only").value_counts()
        st.bar_chart(routing_counts, height=200)

    # Recent failures
    if not logs_df.empty and error_queries > 0:
        st.markdown('<p class="gov-section">Recent Errors</p>', unsafe_allow_html=True)
        fail_df = logs_df[logs_df["status"] == "failure"][
            ["created_at", "model_name", "error_message"]
        ].head(10)
        st.dataframe(fail_df, use_container_width=True)
    else:
        st.success("✅ No errors recorded in recent logs.")


# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# 02  QUALITY
# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
with st.expander("02 · Quality — Response Quality & User Satisfaction", expanded=True):
    st.markdown('<span class="cat-pill">⭐ 02 Quality</span>', unsafe_allow_html=True)
    st.caption(
        "Aggregated user feedback ratings, helpfulness scores, and response quality indicators."
    )

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Feedback Submissions", len(feed_df) if not feed_df.empty else 0)
    q2.metric("Avg Rating",
              f"{avg_rating:.2f} / 5" if avg_rating is not None else "N/A")
    q3.metric("Helpful %",
              f"{helpful_pct*100:.0f}%" if helpful_pct is not None else "N/A")
    avg_chunks_display = f"{avg_chunks:.1f}" if avg_chunks else "N/A"
    q4.metric("Avg Retrieved Chunks", avg_chunks_display)

    if not feed_df.empty and "rating" in feed_df.columns:
        st.markdown('<p class="gov-section">Rating Distribution</p>', unsafe_allow_html=True)
        rating_counts = feed_df["rating"].value_counts().sort_index()
        rating_counts.index = [f"⭐ {i}" for i in rating_counts.index]
        st.bar_chart(rating_counts, height=180)

    if not feed_df.empty and "feedback_text" in feed_df.columns:
        texts = feed_df["feedback_text"].dropna()
        if len(texts):
            st.markdown('<p class="gov-section">Recent User Comments</p>', unsafe_allow_html=True)
            for t in texts.head(5):
                st.markdown(f"> _{t}_")




# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# 03  SAFETY
# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
with st.expander("03 · Safety — Content Safety & Guardrail Effectiveness", expanded=True):
    st.markdown('<span class="cat-pill">�??�️ 03 Safety</span>', unsafe_allow_html=True)
    st.caption(
        "Toxicity, bias, and hallucination scores from evaluation reports. "
        "Lower toxicity/bias = safer. Higher faithfulness = less hallucination."
    )

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Toxicity Score",     _pct(toxicity) if toxicity is not None else "No data",
              help="Lower is better. Target < 5%.")
    s2.metric("Bias Score",         _pct(bias) if bias is not None else "No data",
              help="Lower is better. Target < 10%.")
    s3.metric("Hallucination Rate", _pct(hallucination) if hallucination is not None else "No data",
              help="Lower is better. Target < 10%.")
    s4.metric("Eval Reports",       len(eval_df) if not eval_df.empty else 0)

    # Guardrail check count from routing labels
    guardrail_hits = 0
    if not logs_df.empty and "tool_used" in logs_df.columns:
        guardrail_hits = int(
            logs_df["tool_used"].fillna("").str.contains("guardrail", case=False).sum()
        )

    st.markdown('<p class="gov-section">Guardrail Summary</p>', unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    g1.metric("Guardrail Blocks", guardrail_hits,
              help="Queries blocked by pre-flight validation (OOS, invalid input, contradictions).")

    # Toxicity / bias trend if eval data exists
    if not eval_df.empty and "toxicity" in eval_df.columns:
        st.markdown('<p class="gov-section">Safety Scores Over Time</p>', unsafe_allow_html=True)
        safety_trend = eval_df[["created_at", "toxicity", "bias", "hallucination"]].dropna(
            subset=["toxicity"]
        ).set_index("created_at").sort_index()
        if not safety_trend.empty:
            st.line_chart(safety_trend, height=200)
    else:
        st.info(
            "No evaluation reports available. Run external evaluations and store them via "
            "`ObservabilityService.evaluation.store_report()` to populate safety metrics."
        )


# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# 04  SECURITY
# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
with st.expander("04 · Security — Prompt Injection & Alert Posture", expanded=True):
    st.markdown('<span class="cat-pill">🔒 04 Security</span>', unsafe_allow_html=True)
    st.caption(
        "Alert history, unacknowledged alerts, and prompt-injection detection indicators."
    )

    sec1, sec2, sec3, sec4 = st.columns(4)
    sec1.metric("Total Alerts",         total_alerts)
    sec2.metric("Unacknowledged",       unacked_alerts,
                delta=f"�?�️ {unacked_alerts} open" if unacked_alerts else None,
                delta_color="inverse")

    injection_alerts = 0
    if not alert_df.empty and "alert_type" in alert_df.columns:
        injection_alerts = int(
            alert_df["alert_type"].str.lower().str.contains("inject|security|prompt").sum()
        )
    sec3.metric("Injection-related Alerts", injection_alerts)

    latency_alerts = 0
    if not alert_df.empty and "alert_type" in alert_df.columns:
        latency_alerts = int(
            alert_df["alert_type"].str.lower().str.contains("latency|slow").sum()
        )
    sec4.metric("Latency Alerts", latency_alerts)

    if not alert_df.empty:
        st.markdown('<p class="gov-section">Alert Log</p>', unsafe_allow_html=True)
        cols = [c for c in ["created_at", "alert_type", "severity", "message",
                             "actual_value", "threshold_value", "acknowledged"]
                if c in alert_df.columns]
        st.dataframe(
            alert_df[cols].sort_values("created_at", ascending=False).head(20),
            use_container_width=True,
        )

        if "severity" in alert_df.columns:
            st.markdown('<p class="gov-section">Alert Severity Breakdown</p>', unsafe_allow_html=True)
            sev_counts = alert_df["severity"].value_counts()
            st.bar_chart(sev_counts, height=160)
    else:
        st.success("✅ No alerts recorded.")




# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# 05  ROBUSTNESS
# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
with st.expander("05 · Robustness — Edge-case & Validation Handling", expanded=True):
    st.markdown('<span class="cat-pill">🛠️ 05 Robustness</span>', unsafe_allow_html=True)
    st.caption(
        "How well the system handles invalid inputs, edge-cases, model fallbacks, "
        "and validation guardrails."
    )

    # Fallback model usage (robustness indicator)
    fallback_count = 0
    primary_model  = ""
    if not logs_df.empty and "model_name" in logs_df.columns:
        model_counts  = logs_df["model_name"].value_counts()
        primary_model = model_counts.index[0] if len(model_counts) else "unknown"
        fallback_count = int((logs_df["model_name"] != primary_model).sum())

    rb1, rb2, rb3, rb4 = st.columns(4)
    rb1.metric("Primary Model",    primary_model or "N/A")
    rb2.metric("Fallback Hits",    fallback_count,
               help="Queries served by a non-primary model due to rate-limits or errors.")
    rb3.metric("Validation Blocks", guardrail_hits,
               help="Requests rejected by pre-flight guardrails before reaching the LLM.")
    rb4.metric("Error Rate",       f"{error_rate*100:.1f}%")

    if not logs_df.empty and "model_name" in logs_df.columns:
        st.markdown('<p class="gov-section">Model Distribution (Fallback View)</p>',
                    unsafe_allow_html=True)
        st.bar_chart(logs_df["model_name"].value_counts(), height=180)

    # Status distribution
    if not logs_df.empty and "status" in logs_df.columns:
        st.markdown('<p class="gov-section">Query Status Distribution</p>', unsafe_allow_html=True)
        st.bar_chart(logs_df["status"].value_counts(), height=150)


# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# 06  PERFORMANCE
# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
with st.expander("06 · Performance — Latency & Throughput", expanded=True):
    st.markdown('<span class="cat-pill">⚡ 06 Performance</span>', unsafe_allow_html=True)
    st.caption("Response time distribution, percentile latencies, and throughput trends.")

    p50 = logs_df["latency_ms"].quantile(0.50) if not logs_df.empty else 0.0
    p99 = logs_df["latency_ms"].quantile(0.99) if not logs_df.empty else 0.0
    max_lat = logs_df["latency_ms"].max() if not logs_df.empty else 0.0

    pf1, pf2, pf3, pf4, pf5 = st.columns(5)
    pf1.metric("Avg Latency",  f"{avg_latency_ms:.0f} ms")
    pf2.metric("P50",          f"{p50:.0f} ms")
    pf3.metric("P95",          f"{p95_latency_ms:.0f} ms")
    pf4.metric("P99",          f"{p99:.0f} ms")
    pf5.metric("Max",          f"{max_lat:.0f} ms")

    if not logs_df.empty and "latency_ms" in logs_df.columns:
        st.markdown('<p class="gov-section">Latency Over Time</p>', unsafe_allow_html=True)
        lat_ts = (
            logs_df[["created_at", "latency_ms"]]
            .dropna()
            .set_index("created_at")
            .sort_index()
        )
        if not lat_ts.empty:
            st.line_chart(lat_ts, height=210)

        st.markdown('<p class="gov-section">Latency Distribution (histogram)</p>',
                    unsafe_allow_html=True)
        bins_df = (
            logs_df["latency_ms"]
            .dropna()
            .pipe(lambda s: pd.cut(s, bins=10))
            .value_counts()
            .sort_index()
            .rename_axis("bucket")
            .reset_index(name="count")
        )
        bins_df["bucket"] = bins_df["bucket"].astype(str)
        st.bar_chart(bins_df.set_index("bucket")["count"], height=180)




# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# 07  CONTEXT
# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
with st.expander("07 · Context — Retrieval Quality & Knowledge Grounding", expanded=True):
    st.markdown('<span class="cat-pill">🔍 07 Context</span>', unsafe_allow_html=True)
    st.caption(
        "How well the retrieval pipeline finds relevant knowledge-base chunks, "
        "and how effectively the LLM uses that context."
    )

    zero_chunk = 0
    if not logs_df.empty and "retrieved_chunk_count" in logs_df.columns:
        zero_chunk = int((logs_df["retrieved_chunk_count"] == 0).sum())

    cx1, cx2, cx3, cx4 = st.columns(4)
    cx1.metric("Avg Chunks Retrieved", f"{avg_chunks:.1f}")
    cx2.metric("Zero-chunk Queries",   zero_chunk,
               help="Queries where no relevant context was found.")
    cx3.metric("Avg Relevancy Score",
               _pct(relevancy) if relevancy is not None else "N/A")
    cx4.metric("Faithfulness Score",
               _pct(faithfulness) if faithfulness is not None else "N/A")

    if not logs_df.empty and "retrieved_chunk_count" in logs_df.columns:
        st.markdown('<p class="gov-section">Retrieved Chunks Distribution</p>',
                    unsafe_allow_html=True)
        chunk_dist = (
            logs_df["retrieved_chunk_count"]
            .dropna()
            .value_counts()
            .sort_index()
            .rename_axis("chunks")
            .reset_index(name="count")
        )
        st.bar_chart(chunk_dist.set_index("chunks")["count"], height=180)

    # Embedding / prompt version breakdown
    if not logs_df.empty and "prompt_version" in logs_df.columns:
        st.markdown('<p class="gov-section">Prompt Version Usage</p>', unsafe_allow_html=True)
        pv = logs_df["prompt_version"].fillna("default").value_counts()
        st.bar_chart(pv, height=150)

    if not logs_df.empty and "embedding_model" in logs_df.columns:
        st.markdown('<p class="gov-section">Embedding Model</p>', unsafe_allow_html=True)
        em = logs_df["embedding_model"].fillna("unknown").value_counts()
        st.bar_chart(em, height=130)

    if zero_chunk > 0:
        st.warning(
            f"�?�️ {zero_chunk} queries returned no context. "
            "Consider expanding the knowledge base or lowering the similarity threshold."
        )
    else:
        st.success("✅ All queries retrieved at least one context chunk.")


# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# 08  RAGAS
# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
with st.expander("08 · RAGAS — RAG Evaluation Metrics", expanded=True):
    st.markdown('<span class="cat-pill">📊 08 RAGAS</span>', unsafe_allow_html=True)
    st.caption(
        "RAGAS-style evaluation: Faithfulness, Answer Relevancy, Context Recall, "
        "and Hallucination Rate. Populated from stored evaluation reports."
    )

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Faithfulness",
              _pct(faithfulness) if faithfulness is not None else "N/A",
              help="Fraction of answer claims supported by retrieved context.")
    r2.metric("Answer Relevancy",
              _pct(relevancy) if relevancy is not None else "N/A",
              help="How relevant the answer is to the user's question.")
    r3.metric("Hallucination Rate",
              _pct(hallucination) if hallucination is not None else "N/A",
              help="Fraction of answers containing unsupported claims. Lower is better.")
    r4.metric("Eval Reports",  len(eval_df) if not eval_df.empty else 0)

    if not eval_df.empty:
        st.markdown('<p class="gov-section">RAGAS Scores Over Time</p>', unsafe_allow_html=True)
        ragas_cols = [c for c in ["faithfulness", "relevancy", "hallucination", "bias", "toxicity"]
                      if c in eval_df.columns]
        if ragas_cols:
            ragas_ts = (
                eval_df[["created_at"] + ragas_cols]
                .dropna(subset=ragas_cols, how="all")
                .set_index("created_at")
                .sort_index()
            )
            if not ragas_ts.empty:
                st.line_chart(ragas_ts, height=220)

        st.markdown('<p class="gov-section">Evaluation Reports Log</p>', unsafe_allow_html=True)
        report_cols = [c for c in
                       ["created_at", "framework", "faithfulness", "relevancy",
                        "hallucination", "bias", "toxicity", "llm_log_id"]
                       if c in eval_df.columns]
        st.dataframe(
            eval_df[report_cols].sort_values("created_at", ascending=False).head(50),
            use_container_width=True,
        )

        # Export
        st.download_button(
            "📥 Download RAGAS Reports (CSV)",
            data=eval_df.to_csv(index=False),
            file_name="ragas_evaluation_reports.csv",
            mime="text/csv",
        )
    else:
        st.info(
            "No RAGAS evaluation data yet.\n\n"
            "To populate this section, run evaluations and store them:\n"
            "```python\n"
            "service.evaluation.store_report(\n"
            "    llm_log_id=log_id,\n"
            "    framework='ragas',\n"
            "    faithfulness=0.91,\n"
            "    relevancy=0.88,\n"
            "    hallucination=0.04,\n"
            "    bias=0.02,\n"
            "    toxicity=0.00,\n"
            ")\n"
            "```"
        )

# �??�?? Footer �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
st.markdown("---")
st.caption(
    "🏛️ AskBVRITH Governance Dashboard · BVRIT Hyderabad College of Engineering for Women · "
    "Evaluation framework: Functional · Quality · Safety · Security · "
    "Robustness · Performance · Context · RAGAS"
)



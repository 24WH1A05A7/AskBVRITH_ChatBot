"""
pages/governance.py
�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
Governance dashboard page for the AskBVRITH multi-page app.
Called by app.py via st.navigation; do NOT run directly.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from observability import ObservabilityService

ROOT      = Path(__file__).parent.parent
LOGO_PATH = ROOT / "static" / "images" / "bvrith_logo.png"

_GOV_CATEGORIES = [
    "Functional", "Quality", "Safety", "Security",
    "Robustness", "Performance", "Context", "RAGAS",
]


@st.cache_resource
def _get_service() -> ObservabilityService:
    return ObservabilityService()


def _to_df(rows) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


def _cls(val: float | None, good: float = 0.75, warn: float = 0.50) -> str:
    if val is None:       return "na"
    if val >= good:       return ""
    if val >= warn:       return "warn"
    return "fail"


def _pct(val: float | None) -> str:
    return f"{val * 100:.0f}%" if val is not None else "N/A"


def _score_card(num: str, label: str, value: str, subtitle: str, css: str = "") -> str:
    nc = f"score-num {css}".strip()
    return (
        f'<div class="score-card {css}">'
        f'<div class="{nc}">{value}</div>'
        f'<div class="score-label">{num} · {label}</div>'
        f'<div class="score-sub">{subtitle}</div>'
        f"</div>"
    )


def _avg_col(df: pd.DataFrame, col: str) -> float | None:
    if df.empty or col not in df.columns:
        return None
    vals = df[col].dropna()
    return float(vals.mean()) if len(vals) else None


def _load_data(service: ObservabilityService):
    logs_df  = _to_df(service.db.get_llm_logs(limit=500))
    alert_df = _to_df(service.db.get_alerts(limit=200))
    eval_df  = _to_df(service.db.fetch_all("SELECT * FROM evaluation_reports ORDER BY created_at DESC"))
    feed_df  = _to_df(service.db.fetch_all("SELECT * FROM feedback ORDER BY created_at DESC"))
    for df, col in [(logs_df, "created_at"), (alert_df, "created_at"),
                    (eval_df, "created_at"), (feed_df, "created_at")]:
        if not df.empty and col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return logs_df, alert_df, eval_df, feed_df


# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
def render() -> None:
    service = _get_service()

    # �??�?? Sidebar additions (app.py sidebar is already rendered) �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    with st.sidebar:
        if st.button("🔄 Refresh", key="gov_refresh", use_container_width=True):
            st.rerun()
        st.markdown("**Categories**")
        for i, name in enumerate(_GOV_CATEGORIES, 1):
            st.markdown(f"&nbsp;&nbsp;`{i:02d}` {name}")
        st.markdown("---")
        st.caption("Governance v1")

    # �??�?? Hero �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    st.markdown(
        '<div class="gov-hero">'
        "<h1>🏛️ Governance &amp; Evaluation Dashboard</h1>"
        "<p>8-category framework: Functional · Quality · Safety · Security · "
        "Robustness · Performance · Context · RAGAS — derived from live observability data.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    logs_df, alert_df, eval_df, feed_df = _load_data(service)

    total_queries   = len(logs_df)
    error_queries   = len(logs_df[logs_df["status"] == "failure"]) if not logs_df.empty else 0
    success_queries = total_queries - error_queries
    error_rate      = error_queries / total_queries if total_queries else 0.0
    avg_latency_ms  = logs_df["latency_ms"].mean()      if not logs_df.empty else 0.0
    p95_latency_ms  = logs_df["latency_ms"].quantile(0.95) if not logs_df.empty else 0.0
    avg_chunks      = (logs_df["retrieved_chunk_count"].mean()
                       if not logs_df.empty and "retrieved_chunk_count" in logs_df.columns else 0.0)
    total_alerts    = len(alert_df)
    unacked_alerts  = len(alert_df[alert_df["acknowledged"] == 0]) if not alert_df.empty else 0

    faithfulness  = (_avg_col(eval_df, "faithfulness")  or _avg_col(logs_df, "faithfulness_score"))
    hallucination = (_avg_col(eval_df, "hallucination") or _avg_col(logs_df, "hallucination_score"))
    toxicity      = (_avg_col(eval_df, "toxicity")      or _avg_col(logs_df, "toxicity_score"))
    bias          = (_avg_col(eval_df, "bias")          or _avg_col(logs_df, "bias_score"))
    relevancy     = (_avg_col(eval_df, "relevancy")     or _avg_col(logs_df, "relevancy_score"))

    avg_rating = _avg_col(feed_df, "rating")
    helpful_pct: float | None = None
    if not feed_df.empty and "helpful" in feed_df.columns:
        h = feed_df["helpful"].dropna()
        helpful_pct = float(h.mean()) if len(h) else None

    # �??�?? Scorecards �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    st.markdown('<p class="gov-section">Overall Health Scores</p>', unsafe_allow_html=True)

    perf_score = max(0.0, 1.0 - (avg_latency_ms / 5000.0)) if avg_latency_ms else None

    cards_html = '<div class="score-grid">'
    for num, label, val, subtitle in [
        ("01", "Functional",  (1.0 - error_rate) if total_queries else None,
         f"{success_queries}/{total_queries} queries succeeded"),
        ("02", "Quality",     (avg_rating / 5.0) if avg_rating else None,
         f"Avg rating {avg_rating:.1f}/5" if avg_rating else "No feedback yet"),
        ("03", "Safety",      (1.0 - (toxicity or 0)) if toxicity is not None else None,
         f"Toxicity {_pct(toxicity)}" if toxicity is not None else "No eval data"),
        ("04", "Security",    None,
         f"{unacked_alerts} unacknowledged alert(s)"),
        ("05", "Robustness",  (1.0 - error_rate) if total_queries > 5 else None,
         f"Error rate {error_rate*100:.1f}%"),
        ("06", "Performance", perf_score,
         f"Avg {avg_latency_ms:.0f} ms · P95 {p95_latency_ms:.0f} ms"),
        ("07", "Context",     relevancy,
         f"Relevancy {_pct(relevancy)}" if relevancy is not None else "No eval data"),
        ("08", "RAGAS",       faithfulness,
         f"Faithfulness {_pct(faithfulness)}" if faithfulness is not None else "No eval data"),
    ]:
        css     = _cls(val)
        display = f"{val*100:.0f}%" if val is not None else "N/A"
        cards_html += _score_card(num, label, display, subtitle, css)
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    st.markdown("---")

    guardrail_hits = 0
    if not logs_df.empty and "tool_used" in logs_df.columns:
        guardrail_hits = int(
            logs_df["tool_used"].fillna("").str.contains("guardrail", case=False).sum()
        )

    # �??�?? 01 Functional �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    with st.expander("01 · Functional — Correctness & Tool Execution", expanded=True):
        st.markdown('<span class="cat-pill">✅ 01 Functional</span>', unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns(4)
        tool_q = int(logs_df["tool_used"].notna().sum()) if not logs_df.empty and "tool_used" in logs_df.columns else 0
        f1.metric("Total Queries",    total_queries)
        f2.metric("Successful",       success_queries,
                  delta=f"-{error_queries} errors" if error_queries else None,
                  delta_color="inverse")
        f3.metric("Error Rate",       f"{error_rate*100:.1f}%")
        f4.metric("Tool Invocations", tool_q)
        if not logs_df.empty and "tool_used" in logs_df.columns:
            st.markdown('<p class="gov-section">Tool Usage Breakdown</p>', unsafe_allow_html=True)
            st.bar_chart(logs_df["tool_used"].fillna("rag_only").value_counts(), height=200)
        if not logs_df.empty and error_queries > 0:
            st.markdown('<p class="gov-section">Recent Errors</p>', unsafe_allow_html=True)
            st.dataframe(
                logs_df[logs_df["status"] == "failure"][
                    ["created_at", "model_name", "error_message"]
                ].head(10),
                use_container_width=True,
            )
        else:
            st.success("✅ No errors recorded in recent logs.")

    # �??�?? 02 Quality �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    with st.expander("02 · Quality — Response Quality & User Satisfaction", expanded=True):
        st.markdown('<span class="cat-pill">⭐ 02 Quality</span>', unsafe_allow_html=True)
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Feedback Submissions", len(feed_df) if not feed_df.empty else 0)
        q2.metric("Avg Rating",   f"{avg_rating:.2f} / 5" if avg_rating else "N/A")
        q3.metric("Helpful %",    f"{helpful_pct*100:.0f}%" if helpful_pct else "N/A")
        q4.metric("Avg Chunks",   f"{avg_chunks:.1f}" if avg_chunks else "N/A")
        if not feed_df.empty and "rating" in feed_df.columns:
            st.markdown('<p class="gov-section">Rating Distribution</p>', unsafe_allow_html=True)
            rc = feed_df["rating"].value_counts().sort_index()
            rc.index = [f"⭐ {i}" for i in rc.index]
            st.bar_chart(rc, height=180)
        if not feed_df.empty and "feedback_text" in feed_df.columns:
            texts = feed_df["feedback_text"].dropna()
            if len(texts):
                st.markdown('<p class="gov-section">Recent User Comments</p>', unsafe_allow_html=True)
                for t in texts.head(5):
                    st.markdown(f"> _{t}_")

    # �??�?? 03 Safety �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    with st.expander("03 · Safety — Content Safety & Guardrail Effectiveness", expanded=True):
        st.markdown('<span class="cat-pill">�??�️ 03 Safety</span>', unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Toxicity",      _pct(toxicity)     if toxicity     else "No data")
        s2.metric("Bias",          _pct(bias)          if bias         else "No data")
        s3.metric("Hallucination", _pct(hallucination) if hallucination else "No data")
        s4.metric("Eval Reports",  len(eval_df) if not eval_df.empty else 0)
        st.markdown('<p class="gov-section">Guardrail Summary</p>', unsafe_allow_html=True)
        g1, _, _ = st.columns(3)
        g1.metric("Guardrail Blocks", guardrail_hits)
        if not eval_df.empty and "toxicity" in eval_df.columns:
            trend = eval_df[["created_at", "toxicity", "bias", "hallucination"]].dropna(
                subset=["toxicity"]).set_index("created_at").sort_index()
            if not trend.empty:
                st.markdown('<p class="gov-section">Safety Scores Over Time</p>', unsafe_allow_html=True)
                st.line_chart(trend, height=200)
        else:
            st.info("No evaluation reports — use `service.evaluation.store_report()` to populate.")

    # �??�?? 04 Security �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    with st.expander("04 · Security — Prompt Injection & Alert Posture", expanded=True):
        st.markdown('<span class="cat-pill">🔒 04 Security</span>', unsafe_allow_html=True)
        sec1, sec2, sec3, sec4 = st.columns(4)
        sec1.metric("Total Alerts",   total_alerts)
        sec2.metric("Unacknowledged", unacked_alerts,
                    delta=f"�?�️ {unacked_alerts} open" if unacked_alerts else None,
                    delta_color="inverse")
        inj = int(alert_df["alert_type"].str.lower().str.contains("inject|security|prompt").sum()) if not alert_df.empty and "alert_type" in alert_df.columns else 0
        lat_a = int(alert_df["alert_type"].str.lower().str.contains("latency|slow").sum()) if not alert_df.empty and "alert_type" in alert_df.columns else 0
        sec3.metric("Injection Alerts", inj)
        sec4.metric("Latency Alerts",   lat_a)
        if not alert_df.empty:
            cols = [c for c in ["created_at", "alert_type", "severity", "message",
                                 "actual_value", "threshold_value", "acknowledged"]
                    if c in alert_df.columns]
            st.dataframe(alert_df[cols].sort_values("created_at", ascending=False).head(20),
                         use_container_width=True)
            if "severity" in alert_df.columns:
                st.bar_chart(alert_df["severity"].value_counts(), height=160)
        else:
            st.success("✅ No alerts recorded.")

    # �??�?? 05 Robustness �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    with st.expander("05 · Robustness — Edge-case & Validation Handling", expanded=True):
        st.markdown('<span class="cat-pill">🛠️ 05 Robustness</span>', unsafe_allow_html=True)
        primary_model  = ""
        fallback_count = 0
        if not logs_df.empty and "model_name" in logs_df.columns:
            mc = logs_df["model_name"].value_counts()
            primary_model  = mc.index[0] if len(mc) else "unknown"
            fallback_count = int((logs_df["model_name"] != primary_model).sum())
        rb1, rb2, rb3, rb4 = st.columns(4)
        rb1.metric("Primary Model",     primary_model or "N/A")
        rb2.metric("Fallback Hits",     fallback_count)
        rb3.metric("Validation Blocks", guardrail_hits)
        rb4.metric("Error Rate",        f"{error_rate*100:.1f}%")
        if not logs_df.empty and "model_name" in logs_df.columns:
            st.markdown('<p class="gov-section">Model Distribution</p>', unsafe_allow_html=True)
            st.bar_chart(logs_df["model_name"].value_counts(), height=180)
        if not logs_df.empty and "status" in logs_df.columns:
            st.markdown('<p class="gov-section">Query Status Distribution</p>', unsafe_allow_html=True)
            st.bar_chart(logs_df["status"].value_counts(), height=150)

    # �??�?? 06 Performance �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    with st.expander("06 · Performance — Latency & Throughput", expanded=True):
        st.markdown('<span class="cat-pill">⚡ 06 Performance</span>', unsafe_allow_html=True)
        p50     = logs_df["latency_ms"].quantile(0.50) if not logs_df.empty else 0.0
        p99     = logs_df["latency_ms"].quantile(0.99) if not logs_df.empty else 0.0
        max_lat = logs_df["latency_ms"].max()          if not logs_df.empty else 0.0
        pf1, pf2, pf3, pf4, pf5 = st.columns(5)
        pf1.metric("Avg",  f"{avg_latency_ms:.0f} ms")
        pf2.metric("P50",  f"{p50:.0f} ms")
        pf3.metric("P95",  f"{p95_latency_ms:.0f} ms")
        pf4.metric("P99",  f"{p99:.0f} ms")
        pf5.metric("Max",  f"{max_lat:.0f} ms")
        if not logs_df.empty:
            lat_ts = logs_df[["created_at", "latency_ms"]].dropna().set_index("created_at").sort_index()
            if not lat_ts.empty:
                st.markdown('<p class="gov-section">Latency Over Time</p>', unsafe_allow_html=True)
                st.line_chart(lat_ts, height=210)
            bins_df = (
                logs_df["latency_ms"].dropna()
                .pipe(lambda s: pd.cut(s, bins=10))
                .value_counts().sort_index()
                .rename_axis("bucket").reset_index(name="count")
            )
            bins_df["bucket"] = bins_df["bucket"].astype(str)
            st.markdown('<p class="gov-section">Latency Distribution</p>', unsafe_allow_html=True)
            st.bar_chart(bins_df.set_index("bucket")["count"], height=180)

    # �??�?? 07 Context �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    with st.expander("07 · Context — Retrieval Quality & Knowledge Grounding", expanded=True):
        st.markdown('<span class="cat-pill">🔍 07 Context</span>', unsafe_allow_html=True)
        zero_chunk = int((logs_df["retrieved_chunk_count"] == 0).sum()) if not logs_df.empty and "retrieved_chunk_count" in logs_df.columns else 0
        cx1, cx2, cx3, cx4 = st.columns(4)
        cx1.metric("Avg Chunks",    f"{avg_chunks:.1f}")
        cx2.metric("Zero-chunk",    zero_chunk)
        cx3.metric("Relevancy",     _pct(relevancy)    if relevancy    else "N/A")
        cx4.metric("Faithfulness",  _pct(faithfulness) if faithfulness else "N/A")
        if not logs_df.empty and "retrieved_chunk_count" in logs_df.columns:
            cd = (logs_df["retrieved_chunk_count"].dropna().value_counts().sort_index()
                  .rename_axis("chunks").reset_index(name="count"))
            st.markdown('<p class="gov-section">Chunk Distribution</p>', unsafe_allow_html=True)
            st.bar_chart(cd.set_index("chunks")["count"], height=180)
        if not logs_df.empty and "prompt_version" in logs_df.columns:
            st.markdown('<p class="gov-section">Prompt Version Usage</p>', unsafe_allow_html=True)
            st.bar_chart(logs_df["prompt_version"].fillna("default").value_counts(), height=150)
        (st.warning if zero_chunk > 0 else st.success)(
            f"�?�️ {zero_chunk} queries returned no context." if zero_chunk > 0
            else "✅ All queries retrieved at least one context chunk."
        )

    # �??�?? 08 RAGAS �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    with st.expander("08 · RAGAS — RAG Evaluation Metrics", expanded=True):
        st.markdown('<span class="cat-pill">📊 08 RAGAS</span>', unsafe_allow_html=True)
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Faithfulness",   _pct(faithfulness)  if faithfulness  else "N/A")
        r2.metric("Relevancy",      _pct(relevancy)      if relevancy      else "N/A")
        r3.metric("Hallucination",  _pct(hallucination)  if hallucination  else "N/A")
        r4.metric("Eval Reports",   len(eval_df) if not eval_df.empty else 0)
        if not eval_df.empty:
            rcols = [c for c in ["faithfulness", "relevancy", "hallucination", "bias", "toxicity"]
                     if c in eval_df.columns]
            if rcols:
                ts = (eval_df[["created_at"] + rcols]
                      .dropna(subset=rcols, how="all")
                      .set_index("created_at").sort_index())
                if not ts.empty:
                    st.markdown('<p class="gov-section">RAGAS Over Time</p>', unsafe_allow_html=True)
                    st.line_chart(ts, height=220)
            report_cols = [c for c in ["created_at", "framework", "faithfulness", "relevancy",
                                        "hallucination", "bias", "toxicity"] if c in eval_df.columns]
            st.dataframe(eval_df[report_cols].sort_values("created_at", ascending=False).head(50),
                         use_container_width=True)
            st.download_button("📥 Download RAGAS Reports (CSV)", eval_df.to_csv(index=False),
                               "ragas_reports.csv", "text/csv")
        else:
            st.info("No RAGAS data yet. Use `service.evaluation.store_report()` to populate.")

    st.markdown("---")
    st.caption(
        "🏛️ Governance Dashboard · BVRIT Hyderabad · "
        "Functional · Quality · Safety · Security · Robustness · Performance · Context · RAGAS"
    )



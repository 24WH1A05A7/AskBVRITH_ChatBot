"""

observability_dashboard.py

�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??

Live administration dashboard for the BVRIT AI observability layer.

Run: streamlit run observability_dashboard.py

"""



from pathlib import Path



import pandas as pd

import streamlit as st



from observability import ObservabilityService





def _rows_to_frame(rows):

    if not rows:

        return pd.DataFrame()

    return pd.DataFrame([dict(row) for row in rows])





def _style_kpi(value: str) -> str:

    return f"<div style='font-size:2.4rem;font-weight:800;margin-bottom:0.15rem;'>{value}</div>"





st.set_page_config(

    page_title="AskBVRITH · Observability",

    page_icon="📊",

    layout="wide",

    initial_sidebar_state="expanded",

)



service = ObservabilityService()



st.markdown(

    """

    <style>

    body { font-family: 'Montserrat', sans-serif; }

    .kpi-card { background: #fff; border: 1px solid rgba(58,87,107,.12); border-radius: 16px; padding: 18px; box-shadow: 0 18px 30px rgba(0,0,0,.04); }

    .kpi-label { color: #556c7c; font-size: 0.9rem; margin-bottom: 6px; }

    .alert-row { padding: 12px 10px; border-bottom: 1px solid rgba(0,0,0,.06); }

    .alert-type { font-weight: 700; }

    </style>

    """,

    unsafe_allow_html=True,

)



st.title("📊 BVRIT AI Observability Dashboard")

st.caption("Live performance, cost, alerting, and prompt experiment monitoring.")



refresh = st.sidebar.button("Refresh metrics")



if refresh:

    st.rerun()



metrics = service.metrics.get_live_metrics()

alert_metrics = service.metrics.get_alert_metrics()

prompt_usage = service.metrics.get_prompt_version_usage()

model_usage = service.metrics.get_model_usage()

cost_trends = service.metrics.get_cost_trends()

active_experiment = service.db.get_active_experiment()

active_prompt = service.db.get_active_prompt_version()



log_rows = service.db.get_llm_logs(limit=50)

session_rows = service.db.get_sessions()

alert_rows = service.db.get_alerts(limit=100)



if refresh:

    st.experimental_rerun()



# KPI row

k1, k2, k3, k4, k5, k6 = st.columns([1,1,1,1,1,1])

k1.markdown(_style_kpi(str(metrics.get("query_count", 0))), unsafe_allow_html=True)

k1.markdown("<div class='kpi-label'>Queries</div>", unsafe_allow_html=True)

k2.markdown(_style_kpi(f"{metrics.get('total_users', 0)}"), unsafe_allow_html=True)

k2.markdown("<div class='kpi-label'>Users</div>", unsafe_allow_html=True)

k3.markdown(_style_kpi(f"${metrics.get('total_cost', 0.0):.2f}"), unsafe_allow_html=True)

k3.markdown("<div class='kpi-label'>Total Cost</div>", unsafe_allow_html=True)

k4.markdown(_style_kpi(f"{metrics.get('avg_latency_ms', 0.0):.1f} ms"), unsafe_allow_html=True)

k4.markdown("<div class='kpi-label'>Avg Latency</div>", unsafe_allow_html=True)

k5.markdown(_style_kpi(f"{metrics.get('p95_latency_ms', 0.0):.1f} ms"), unsafe_allow_html=True)

k5.markdown("<div class='kpi-label'>P95 Latency</div>", unsafe_allow_html=True)

k6.markdown(_style_kpi(f"{alert_metrics.get('active_alerts', 0)}"), unsafe_allow_html=True)

k6.markdown("<div class='kpi-label'>Active Alerts</div>", unsafe_allow_html=True)



st.markdown("---")



with st.expander("Cost & Model Adoption", expanded=True):

    c1, c2 = st.columns(2)

    with c1:

        st.subheader("Cost trend")

        cost_df = _rows_to_frame(cost_trends)

        if not cost_df.empty:

            cost_df = cost_df.rename(columns={"total_cost": "cost_cents", "date": "date"})

            cost_df["cost"] = cost_df["cost_cents"] / 100.0

            cost_df["date"] = pd.to_datetime(cost_df["date"])

            st.line_chart(cost_df.set_index("date")["cost"])

        else:

            st.info("No cost data available yet.")

    with c2:

        st.subheader("Model usage")

        model_df = _rows_to_frame(model_usage)

        if not model_df.empty:

            st.bar_chart(model_df.set_index("model_name")["usage_count"])

        else:

            st.info("No model usage data yet.")



with st.expander("Prompt Versions & Experiments", expanded=True):

    p1, p2 = st.columns(2)

    with p1:

        st.subheader("Prompt version usage")

        prompt_df = _rows_to_frame(prompt_usage)

        if not prompt_df.empty:

            st.bar_chart(prompt_df.set_index("prompt_version")["usage_count"])

        else:

            st.info("No prompt usage recorded yet.")

    with p2:

        st.subheader("Active experiment")

        if active_experiment:

            st.markdown(f"**{active_experiment['name']}**")

            st.markdown(f"Status: {active_experiment['status']}\n\nTraffic split: {active_experiment['traffic_split_percentage']}%")

            st.markdown(f"Variant A: {active_experiment['variant_a_id']}\n\nVariant B: {active_experiment['variant_b_id']}")

        else:

            st.info("No active prompt experiment.")

        if active_prompt:

            st.markdown("---")

            st.markdown(f"**Active prompt version:** {active_prompt['version_name']}")

            st.markdown(f"Created: {active_prompt['created_at']}")

        else:

            st.info("No active prompt version.")



with st.expander("Alerts & Notification History", expanded=True):

    if alert_rows:

        alert_df = _rows_to_frame(alert_rows)

        alert_df["created_at"] = pd.to_datetime(alert_df.get("created_at"), errors="coerce")

        alert_columns = [

            "created_at",

            "alert_type",

            "severity",

            "message",

            "actual_value",

            "threshold_value",

            "session_id",

            "llm_log_id",

        ]

        visible_columns = [col for col in alert_columns if col in alert_df.columns]

        if visible_columns:

            st.dataframe(alert_df[visible_columns].sort_values(by="created_at", ascending=False, na_position="last"))

        else:

            st.info("Alert data is present but no displayable columns were found.")

    else:

        st.info("No alerts logged yet.")



with st.expander("Recent Logs & Sessions", expanded=True):

    st.subheader("Recent LLM calls")

    logs_df = _rows_to_frame(log_rows)

    if not logs_df.empty:

        logs_df["created_at"] = pd.to_datetime(logs_df["created_at"])

        st.dataframe(logs_df[["created_at", "model_name", "prompt_version", "ab_test_variant", "status", "latency_ms", "total_cost", "retrieved_chunk_count"]].sort_values(by="created_at", ascending=False))

    else:

        st.info("No LLM logs recorded yet.")



    st.subheader("Recent sessions")

    sessions_df = _rows_to_frame(session_rows)

    if not sessions_df.empty:

        sessions_df["started_at"] = pd.to_datetime(sessions_df["started_at"])

        st.dataframe(sessions_df[["id", "user_id_hash", "started_at", "query_count", "session_cost", "primary_model"]].sort_values(by="started_at", ascending=False))

    else:

        st.info("No session activity yet.")



with st.expander("Exports", expanded=True):

    st.markdown("Download observability data for offline analysis.")

    if not logs_df.empty:

        st.download_button(

            "Download LLM logs (CSV)",

            data=logs_df.to_csv(index=False),

            file_name="llm_logs.csv",

            mime="text/csv",

        )

    if not alert_rows:

        st.markdown("No alerts available for export.")

    if not sessions_df.empty:

        st.download_button(

            "Download sessions (CSV)",

            data=sessions_df.to_csv(index=False),

            file_name="sessions.csv",

            mime="text/csv",

        )

    if not cost_trends:

        pass



st.markdown("---")

st.caption("For production-grade observability, use the BVRIT AI dashboard to inspect latency, cost, prompt performance, alerts, and session health.")




import os
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.fraud_detection.config import CONFIG
from src.fraud_detection.analysis.kpi import real_time_fraud_pct

st.set_page_config(
    layout="wide",
    page_title="Bank Fraud Detection · Real-Time Control Center",
    page_icon="🛡️"
)

# Custom header styling
st.markdown("""
    <div style='background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0;'>🛡️ Bank Fraud Detection System</h1>
        <p style='color: #e0e0e0; margin: 5px 0 0 0;'>Real-time AI Streaming Pipeline · Datacycle Grupo 4 · Caso 2</p>
    </div>
""", unsafe_allow_html=True)

alerts_path = "data/alerts.parquet"
if not os.path.exists(alerts_path):
    st.error("⚠️ `data/alerts.parquet` not found. Please run the pipeline first (`python -m src.fraud_detection.streaming.consumer`).")
    st.stop()

df = pd.read_parquet(alerts_path)

# Sidebar interactive controls
st.sidebar.header("⚙️ Pipeline Controls & Thresholds")
n_threshold = st.sidebar.slider(
    "N: Real-time Latency Threshold (seconds)",
    min_value=0.5,
    max_value=10.0,
    value=2.0,
    step=0.5,
    help="Transactions alerted within N seconds count towards the Real-Time Fraud Detection KPI."
)

optimal_th = 0.65
if os.path.exists("models/metrics.json"):
    with open("models/metrics.json", "r") as f:
        m = json.load(f)
        optimal_th = float(m.get("optimal_threshold", 0.65))

ml_threshold = st.sidebar.slider(
    "Decision Threshold (Probability)",
    min_value=0.10,
    max_value=0.95,
    value=optimal_th,
    step=0.05,
    help="Threshold on ML output probability to trigger a fraud alert."
)

# Dynamically apply the selected threshold
df["is_alert_custom"] = (df["fraud_score"] >= ml_threshold).astype(int)

# Top KPI Banner
st.subheader("🎯 Primary KPI & Real-time Linage Metric")
kpi_custom = real_time_fraud_pct(
    pd.DataFrame({
        "is_fraud": df["is_fraud"],
        "is_alert": df["is_alert_custom"],
        "detection_latency_seconds": df["detection_latency_seconds"]
    }),
    n_threshold
)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("⚡ Real-Time Fraud KPI", f"{kpi_custom:.1f}%", help=f"Frauds alerted within {n_threshold}s")
col2.metric("⏱️ Mean Latency", f"{df['detection_latency_seconds'].mean():.2f}s")
col3.metric("📈 95th Percentile Latency", f"{np.percentile(df['detection_latency_seconds'], 95):.2f}s")
col4.metric("🚨 Total Alerts Triggered", f"{df['is_alert_custom'].sum()}")
col5.metric("📦 Scored Transactions", f"{len(df):,}")

st.markdown("---")

# Financial Impact
st.subheader("💰 Financial Impact & Risk Analysis")
frauds = df[df["is_fraud"] == 1]
normals = df[df["is_fraud"] == 0]

tp = df[(df["is_fraud"] == 1) & (df["is_alert_custom"] == 1)]
fp = df[(df["is_fraud"] == 0) & (df["is_alert_custom"] == 1)]
fn = df[(df["is_fraud"] == 1) & (df["is_alert_custom"] == 0)]

money_saved = float(tp["amount"].sum())
money_lost = float(fn["amount"].sum())
money_fp_blocked = float(fp["amount"].sum())

colA, colB, colC = st.columns(3)
colA.metric("🟢 Money Saved (Fraud Prevented)", f"€{money_saved:,.2f}")
colB.metric("🔴 Money Lost to Missed Fraud", f"€{money_lost:,.2f}", delta_color="inverse")
colC.metric("🟠 Money Blocked by False Positives", f"€{money_fp_blocked:,.2f}", delta_color="inverse")

st.markdown("---")

# Scenarios Comparison
st.subheader("🔬 Scenarios Comparison (Caso 2 · Actividad Datacycle)")
col_scen, col_bar = st.columns([1.2, 1])

# Scenario calculations
# Scenario A: Batch rules (latency > 3600s)
kpi_a = 0.0
rec_a = (df[(df['is_fraud']==1) & (df['rule_alert']==1)].shape[0] / len(frauds)) * 100
prec_a = (df[(df['is_fraud']==1) & (df['rule_alert']==1)].shape[0] / max(1, df['rule_alert'].sum())) * 100
fp_a = df[(df['is_fraud']==0) & (df['rule_alert']==1)].shape[0]

# Scenario B: Streaming rules
kpi_b = real_time_fraud_pct(
    pd.DataFrame({
        "is_fraud": df["is_fraud"],
        "is_alert": df["rule_alert"],
        "detection_latency_seconds": df["detection_latency_seconds"]
    }),
    n_threshold
)
rec_b = rec_a
prec_b = prec_a
fp_b = fp_a

# Scenario C: Streaming ML
rec_c = (len(tp) / len(frauds)) * 100.0 if len(frauds) > 0 else 0.0
prec_c = (len(tp) / (len(tp) + len(fp))) * 100.0 if (len(tp) + len(fp)) > 0 else 0.0
fp_c = len(fp)

scenarios_df = pd.DataFrame([
    {
        "Scenario": "A (Batch Rules)",
        "Architecture": "Nightly Batch",
        "Real-Time KPI (%)": f"{kpi_a:.1f}%",
        "Recall (%)": f"{rec_a:.1f}%",
        "Precision (%)": f"{prec_a:.1f}%",
        "False Positives": fp_a,
        "Mean Latency": "4.0 hours"
    },
    {
        "Scenario": "B (Streaming Rules)",
        "Architecture": "Stream Rules Engine",
        "Real-Time KPI (%)": f"{kpi_b:.1f}%",
        "Recall (%)": f"{rec_b:.1f}%",
        "Precision (%)": f"{prec_b:.1f}%",
        "False Positives": fp_b,
        "Mean Latency": f"{df['detection_latency_seconds'].mean():.2f}s"
    },
    {
        "Scenario": "C (Streaming ML)",
        "Architecture": "Stream + LightGBM",
        "Real-Time KPI (%)": f"{kpi_custom:.1f}%",
        "Recall (%)": f"{rec_c:.1f}%",
        "Precision (%)": f"{prec_c:.1f}%",
        "False Positives": fp_c,
        "Mean Latency": f"{df['detection_latency_seconds'].mean():.2f}s"
    }
])

with col_scen:
    st.table(scenarios_df)

with col_bar:
    fig_scen = go.Figure(data=[
        go.Bar(name='Real-Time KPI (%)', x=['Scenario A', 'Scenario B', 'Scenario C'], y=[kpi_a, kpi_b, kpi_custom], marker_color='#2ca02c'),
        go.Bar(name='Recall (%)', x=['Scenario A', 'Scenario B', 'Scenario C'], y=[rec_a, rec_b, rec_c], marker_color='#1f77b4'),
        go.Bar(name='Precision (%)', x=['Scenario A', 'Scenario B', 'Scenario C'], y=[prec_a, prec_b, prec_c], marker_color='#ff7f0e')
    ])
    fig_scen.update_layout(barmode='group', title="Scenario Metrics Comparison", height=320, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_scen, use_container_width=True)

st.markdown("---")

# Per-Pattern Fraud Detection Breakdown
st.subheader("🕵️‍♂️ Multi-Pattern Fraud Detection Across Use Cases")
fraud_groups = frauds.groupby("fraud_type")
pattern_stats = []
for ftype, grp in fraud_groups:
    tot = len(grp)
    det_rules = grp["rule_alert"].sum()
    det_ml = grp["is_alert_custom"].sum()
    pattern_stats.append({
        "Fraud Pattern / Use Case": ftype,
        "Total Incidents": tot,
        "Rules Recall (%)": round((det_rules / tot) * 100.0, 1),
        "ML Recall (%)": round((det_ml / tot) * 100.0, 1)
    })

df_patterns = pd.DataFrame(pattern_stats)
fig_patterns = go.Figure(data=[
    go.Bar(name='Baseline Rules Recall (%)', x=df_patterns["Fraud Pattern / Use Case"], y=df_patterns["Rules Recall (%)"], marker_color='#e74c3c'),
    go.Bar(name='Machine Learning Recall (%)', x=df_patterns["Fraud Pattern / Use Case"], y=df_patterns["ML Recall (%)"], marker_color='#2ecc71')
])
fig_patterns.update_layout(
    barmode='group',
    title="Recall by Fraud Use Case: Expert Rules vs Machine Learning",
    yaxis_title="Detection Recall (%)",
    height=400,
    xaxis_tickangle=-30
)
st.plotly_chart(fig_patterns, use_container_width=True)

# Feature Importance & Latency Distribution
st.markdown("---")
col_fi, col_lat = st.columns(2)

with col_fi:
    st.subheader("🧠 Top Feature Importances")
    fi_path = "models/feature_importance.csv"
    if os.path.exists(fi_path):
        df_fi = pd.read_csv(fi_path).head(10)
        fig_fi = px.bar(
            df_fi,
            x="importance",
            y="feature",
            orientation="h",
            title="Top 10 Influential Features (LightGBM)",
            color="importance",
            color_continuous_scale="Viridis"
        )
        fig_fi.update_layout(yaxis=dict(autorange="reversed"), height=360)
        st.plotly_chart(fig_fi, use_container_width=True)

with col_lat:
    st.subheader("⏱️ Detection Latency Distribution")
    fig_lat = px.histogram(
        df,
        x="detection_latency_seconds",
        nbins=40,
        title="Streaming Processing Latency (Seconds)",
        color_discrete_sequence=['#3498db']
    )
    fig_lat.add_vline(x=n_threshold, line_dash="dash", line_color="red", annotation_text=f"N={n_threshold}s SLA Threshold")
    fig_lat.update_layout(height=360)
    st.plotly_chart(fig_lat, use_container_width=True)

# Alerts Drill-down Explorer
st.markdown("---")
st.subheader("📋 Real-time Alert Explorer")
selected_filter = st.selectbox(
    "Filter transactions:",
    ["All Alerted Transactions", "Confirmed Fraud Only", "False Positives Only", "All Transactions"]
)

if selected_filter == "All Alerted Transactions":
    display_df = df[df["is_alert_custom"] == 1]
elif selected_filter == "Confirmed Fraud Only":
    display_df = df[df["is_fraud"] == 1]
elif selected_filter == "False Positives Only":
    display_df = df[(df["is_fraud"] == 0) & (df["is_alert_custom"] == 1)]
else:
    display_df = df

st.dataframe(
    display_df[["transaction_id", "customer_id", "amount", "channel", "event_timestamp", "detection_latency_seconds", "fraud_score", "is_alert_custom", "is_fraud", "fraud_type"]].sort_values("event_timestamp", ascending=False).head(200),
    use_container_width=True
)

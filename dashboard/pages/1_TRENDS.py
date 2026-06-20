"""TRENDS — Real-time process data visualization"""

from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import config
from engine import SimulationEngine

st.set_page_config(page_title="TRENDS", layout="wide", page_icon="⏣")

# ══════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    .stApp { background: #f5f3ef; }
    header[data-testid="stHeader"] {
        background: linear-gradient(90deg, #1a1f2e 0%, #252b3d 50%, #1a1f2e 100%);
        border-bottom: 2px solid #c49860;
    }
    header[data-testid="stHeader"] * { color: #e8e0d5 !important; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f2e 0%, #141822 100%);
        border-right: 1px solid #2a3040;
    }
    [data-testid="stSidebar"] * { color: #c8c0b4 !important; }
    [data-testid="stSidebar"] .stButton > button {
        background: #c49860 !important; color: #1a1f2e !important;
        border: none !important; border-radius: 4px !important;
        font-weight: 600 !important; letter-spacing: 0.04em !important;
        text-transform: uppercase !important; font-size: 0.78rem !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #d4a870 !important;
    }
    [data-testid="stSidebar"] hr { border-color: #2a3040 !important; }
    .section-label {
        font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.1em; color: #8b7355; margin: 16px 0 4px 0;
        border-bottom: 2px solid #c49860; padding-bottom: 4px;
    }
    .sidebar-section {
        font-size: 0.58rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.12em; color: #c49860; margin-top: 12px; margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# ENGINE
# ══════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_engine() -> SimulationEngine:
    e = SimulationEngine(use_mqtt=os.environ.get("USE_MQTT", "0") == "1")
    e.start()
    return e

engine = get_engine()

if "refresh_s" not in st.session_state:
    st.session_state["refresh_s"] = 3
if "window_s" not in st.session_state:
    st.session_state["window_s"] = config.HISTORY_WINDOW_S

# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:8px 0;">
        <div style="font-size:1.05rem;font-weight:800;color:#e8dcc8;letter-spacing:0.06em;">TRENDS</div>
        <div style="font-size:0.55rem;color:#c49860;letter-spacing:0.1em;">REAL-TIME DATA</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="sidebar-section">Chart Settings</div>', unsafe_allow_html=True)
    st.session_state["window_s"] = st.slider("Time Window (s)", 30, 600, st.session_state["window_s"], 30)
    st.session_state["refresh_s"] = st.slider("Refresh (s)", 1, 10, st.session_state["refresh_s"])
    st.divider()

    if st.button("Export CSV", use_container_width=True):
        path = engine.historian.export_csv()
        st.success(f"Exported to {path}")

    st.divider()
    st.caption("Historian: SQLite")

# ══════════════════════════════════════════════════════════════════════
# MAIN — TRENDS PAGE
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(90deg,#1a1f2e,#252b3d,#1a1f2e);border-radius:8px;
padding:12px 24px;margin-bottom:8px;border-bottom:2px solid #c49860;">
<div style="font-size:1.15rem;font-weight:800;color:#e8dcc8;letter-spacing:0.08em;">TRENDS</div>
<div style="font-size:0.62rem;color:#8b8070;letter-spacing:0.06em;">LIVE SENSOR DATA · HISTORICAL COMPARISON · ANOMALY MARKERS</div>
</div>""", unsafe_allow_html=True)


@st.fragment(run_every=f"{st.session_state['refresh_s']}s")
def trends_view():
    window = st.session_state["window_s"]
    history = engine.historian.recent(window_s=window)

    if not history:
        st.info("No data yet. Press Start on the SCHEMATICS page to begin production.")
        return

    df = pd.DataFrame(history)
    df["time"] = pd.to_datetime(df["ts"], unit="s")

    latest = engine.latest()
    alarm_code = int(latest.get("alarm_code", 0))
    frozen = alarm_code == config.ALARM_DATA_STALE

    if frozen:
        st.warning("Data feed is frozen — displaying last known values.")

    # ── 2x2 Sensor Trends ──
    st.markdown('<div class="section-label">Sensor Trends</div>', unsafe_allow_html=True)

    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=("Pasteurization Temperature (°C)", "Tank Level (%)",
                                        "Flow Rate (L/min)", "Bottles Capped"))
    clrs = {"pasteur_temp": "#c0392b", "tank_level": "#3b6f8c",
            "flow_rate": "#2d8a4e", "bottle_count": "#d4a040"}

    for (key, clr), (row, col) in zip(clrs.items(), [(1,1),(1,2),(2,1),(2,2)]):
        if key in df.columns:
            fig.add_trace(go.Scatter(x=df["time"], y=df[key], name=key,
                          line=dict(color=clr, width=2.2), fill="tozeroy",
                          fillcolor=f"rgba({','.join(str(int(clr[i:i+2],16)) for i in (1,3,5))},0.06)"),
                          row=row, col=col)

    # Safe zone bands
    fig.add_hline(y=config.PASTEUR_SAFE_MAX, line_dash="dot", line_color="#c0392b", row=1, col=1)
    fig.add_hline(y=config.PASTEUR_SAFE_MIN, line_dash="dot", line_color="#c0392b", row=1, col=1)

    # Alarm markers
    for ev in engine.historian.recent_alarms(50):
        code = int(ev.get("alarm_code", 0))
        ts_val = ev.get("ts", 0)
        if code and ts_val >= df["ts"].iloc[0]:
            fig.add_vline(x=pd.to_datetime(ts_val, unit="s"), line_color="#c0392b",
                          line_dash="dash", line_width=1.8, row=1, col=1)

    fig.update_layout(height=520, showlegend=False, margin=dict(t=45, b=15, l=40, r=20),
                      plot_bgcolor="#fdfcf9", paper_bgcolor="#fdfcf9",
                      font=dict(color="#3a3a3a", size=11))
    fig.update_xaxes(gridcolor="#e8e0d5"); fig.update_yaxes(gridcolor="#e8e0d5")
    st.plotly_chart(fig, use_container_width=True, key="trend_2x2")

    # ── Actuator Charts ──
    st.markdown('<div class="section-label">Actuator Commands</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        if "heater_power_cmd" in df.columns:
            fig_h = go.Figure()
            fig_h.add_trace(go.Scatter(x=df["time"], y=df["heater_power_cmd"],
                                       name="Heater", line=dict(color="#e8841a", width=2.5),
                                       fill="tozeroy", fillcolor="rgba(232,132,26,0.08)"))
            fig_h.update_layout(height=260, title="Heater Power (%)",
                               plot_bgcolor="#fdfcf9", paper_bgcolor="#fdfcf9",
                               margin=dict(t=35, b=15, l=30, r=10),
                               font=dict(color="#3a3a3a", size=10))
            fig_h.update_xaxes(gridcolor="#e8e0d5"); fig_h.update_yaxes(gridcolor="#e8e0d5")
            st.plotly_chart(fig_h, use_container_width=True)

    with c2:
        fig_c = make_subplots(specs=[[{"secondary_y": True}]])
        if "cooler_temp" in df.columns:
            fig_c.add_trace(go.Scatter(x=df["time"], y=df["cooler_temp"],
                                       name="Cooler °C", line=dict(color="#3b6f8c", width=2.2)))
        if "cooling_valve_cmd" in df.columns:
            fig_c.add_trace(go.Scatter(x=df["time"], y=df["cooling_valve_cmd"],
                                       name="Cooling %", line=dict(color="#2d8a4e", width=1.8, dash="dot")),
                            secondary_y=True)
        fig_c.update_layout(height=260, title="Cooler Temperature & Valve",
                           plot_bgcolor="#fdfcf9", paper_bgcolor="#fdfcf9",
                           margin=dict(t=35, b=15, l=30, r=10),
                           font=dict(color="#3a3a3a", size=10), showlegend=True,
                           legend=dict(orientation="h", yanchor="bottom", y=1.02))
        fig_c.update_xaxes(gridcolor="#e8e0d5"); fig_c.update_yaxes(gridcolor="#e8e0d5")
        st.plotly_chart(fig_c, use_container_width=True)

    # ── Raw Data ──
    with st.expander("Raw Data (last 20 records)"):
        st.dataframe(df.tail(20).sort_values("time", ascending=False),
                     use_container_width=True, hide_index=True)


trends_view()

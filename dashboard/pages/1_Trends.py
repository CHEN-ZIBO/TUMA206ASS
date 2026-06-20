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

BG = "#0d1117"
CARD_BG = "#161b22"
BORDER = "#30363d"
TEXT = "#c9d1d9"
TEXT_DIM = "#8b949e"
ACCENT = "#58a6ff"

st.markdown(f"""
<style>
    .stApp {{ background: {BG}; }}
    header[data-testid="stHeader"] {{
        background: linear-gradient(90deg, {BG}, {CARD_BG}, {BG});
        border-bottom: 1px solid {BORDER};
    }}
    header[data-testid="stHeader"] * {{ color: {TEXT} !important; }}
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {BG}, #010409);
        border-right: 1px solid {BORDER};
    }}
    [data-testid="stSidebar"] * {{ color: {TEXT_DIM} !important; }}
    [data-testid="stSidebar"] .stButton > button {{
        background: #21262d !important; color: {TEXT} !important;
        border: 1px solid {BORDER} !important; border-radius: 6px !important;
        font-weight: 600 !important; letter-spacing: 0.03em !important;
        text-transform: uppercase !important; font-size: 0.75rem !important;
        transition: all 0.15s !important;
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        background: #30363d !important; border-color: {ACCENT} !important;
    }}
    [data-testid="stSidebar"] hr {{ border-color: {BORDER} !important; }}
    .sidebar-section {{
        font-size: 0.55rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.1em; color: {ACCENT}; margin-top: 10px; margin-bottom: 4px;
    }}
    .section-label {{
        font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.1em; color: {TEXT_DIM};
        margin: 14px 0 8px 0; padding-bottom: 6px;
        border-bottom: 1px solid {BORDER};
    }}
    .freeze-btn {{
        display: inline-block; padding: 2px 12px; border-radius: 4px;
        font-size: 0.62rem; font-weight: 600; cursor: pointer; border: 1px solid {BORDER};
        background: #21262d; color: {TEXT_DIM}; margin-left: 8px;
        transition: all 0.2s;
    }}
    .freeze-btn.active {{
        background: {ACCENT}22; color: {ACCENT}; border-color: {ACCENT};
    }}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_engine() -> SimulationEngine:
    e = SimulationEngine(use_mqtt=os.environ.get("USE_MQTT", "0") == "1")
    e.start()
    return e

engine = get_engine()

if "refresh_s" not in st.session_state: st.session_state["refresh_s"] = 3
if "window_s" not in st.session_state: st.session_state["window_s"] = config.HISTORY_WINDOW_S
for k in ("freeze_sensors", "freeze_actuators"):
    if k not in st.session_state: st.session_state[k] = False

with st.sidebar:
    st.markdown(f"""<div style="text-align:center;padding:8px 0;">
        <div style="font-size:1rem;font-weight:700;color:{TEXT};letter-spacing:0.06em;">TRENDS</div>
        <div style="font-size:0.52rem;color:{ACCENT};letter-spacing:0.1em;">REAL-TIME DATA</div></div>""", unsafe_allow_html=True)
    st.divider()
    st.markdown('<div class="sidebar-section">Settings</div>', unsafe_allow_html=True)
    st.session_state["window_s"] = st.slider("Window (s)", 30, 600, st.session_state["window_s"], 30)
    st.session_state["refresh_s"] = st.slider("Refresh (s)", 1, 10, st.session_state["refresh_s"])
    st.divider()
    if st.button("Export CSV", use_container_width=True):
        path = engine.historian.export_csv()
        st.toast("Exported", icon=":material/download:")
    st.divider()
    st.caption("Historian: SQLite")

st.markdown(f"""<div style="background:linear-gradient(90deg,{BG},{CARD_BG},{BG});border-radius:8px;
padding:10px 22px;margin-bottom:6px;border-bottom:1px solid {BORDER};">
<div style="font-size:1.1rem;font-weight:700;color:{TEXT};letter-spacing:0.06em;">TRENDS</div>
<div style="font-size:0.58rem;color:{TEXT_DIM};">LIVE SENSOR DATA &bull; ACTUATOR COMMANDS &bull; ANOMALY MARKERS</div></div>""", unsafe_allow_html=True)

_LAYOUT = dict(plot_bgcolor=CARD_BG, paper_bgcolor=BG, font=dict(color=TEXT, size=10),
               uirevision="constant", margin=dict(t=40, b=15, l=45, r=15))
_AXIS = dict(gridcolor=BORDER, zeroline=False)


def _clean_data(history):
    """Filter out IDLE/STOP states so trends only show meaningful production data."""
    df = pd.DataFrame(history)
    if df.empty: return df
    df["time"] = pd.to_datetime(df["ts"], unit="s")
    # Exclude IDLE rows where all actuators are 0 (not meaningful for trends)
    if "plc_state" in df.columns:
        df = df[df["plc_state"] != "IDLE"]
    # Round for display precision
    for c in ["pasteur_temp", "cooler_temp", "tank_level", "flow_rate",
              "heater_power_cmd", "cooling_valve_cmd", "bottle_count"]:
        if c in df.columns: df[c] = df[c].round(1)
    return df


@st.fragment(run_every=f"{st.session_state['refresh_s']}s")
def trends_view():
    window = st.session_state["window_s"]
    history = engine.historian.recent(window_s=window)
    if not history:
        st.info("No data yet. Press START on the SCHEMATIC page.")
        return

    df = _clean_data(history)
    if df.empty:
        st.info("Waiting for production data...")
        return

    latest = engine.latest()
    alarm_code = int(latest.get("alarm_code", 0))
    frozen = alarm_code == config.ALARM_DATA_STALE
    if frozen: st.warning("Data frozen.")

    # ── Sensor Trends with Freeze toggle ──
    c_title, c_btn = st.columns([6, 1])
    with c_title:
        st.markdown('<div class="section-label" style="margin-bottom:0;">Sensor Trends</div>', unsafe_allow_html=True)
    with c_btn:
        frozen_label = "UNFREEZE" if st.session_state["freeze_sensors"] else "FREEZE"
        if st.button(frozen_label, key="btn_freeze_sensors", use_container_width=True):
            st.session_state["freeze_sensors"] = not st.session_state["freeze_sensors"]

    if not st.session_state["freeze_sensors"]:
        fig = make_subplots(rows=2, cols=2, subplot_titles=("Pasteurization Temp", "Tank Level", "Flow Rate", "Bottles Capped"))
        traces = [
            ("pasteur_temp", "#f85149", 1, 1, "°C"), ("tank_level", "#58a6ff", 1, 2, "%"),
            ("flow_rate", "#3fb950", 2, 1, "L/min"), ("bottle_count", "#d2991d", 2, 2, ""),
        ]
        yranges = {"pasteur_temp": [60, 82], "tank_level": [20, 90], "flow_rate": [0, 50], "bottle_count": None}
        for key, clr, row, col, unit in traces:
            if key not in df.columns: continue
            fig.add_trace(go.Scatter(x=df["time"], y=df[key], name=key,
                          line=dict(color=clr, width=1.8, shape="spline"),
                          mode="lines", hovertemplate=f"%{{y:.1f}} {unit}<extra></extra>"), row=row, col=col)
            yr = yranges.get(key)
            if yr: fig.update_yaxes(range=yr, row=row, col=col, **_AXIS)
        fig.add_hline(y=config.PASTEUR_SAFE_MAX, line_dash="dot", line_color="rgba(248,81,73,0.4)", row=1, col=1)
        fig.add_hline(y=config.PASTEUR_SAFE_MIN, line_dash="dot", line_color="rgba(248,81,73,0.4)", row=1, col=1)
        for ev in engine.historian.recent_alarms(50):
            code = int(ev.get("alarm_code", 0)); ts_val = ev.get("ts", 0)
            if code and ts_val >= df["ts"].iloc[0]:
                fig.add_vline(x=pd.to_datetime(ts_val, unit="s"), line_color="#f85149", line_dash="dash", line_width=1.5, row=1, col=1)
        fig.update_layout(height=500, showlegend=False, **_LAYOUT)
        fig.update_xaxes(**_AXIS); fig.update_yaxes(**_AXIS)
        st.plotly_chart(fig, use_container_width=True, key="sensor_2x2")
    else:
        st.caption("Sensors chart frozen — unfreeze to update.")

    # ── Actuator Charts with Freeze toggle ──
    c_title2, c_btn2 = st.columns([6, 1])
    with c_title2:
        st.markdown('<div class="section-label" style="margin-bottom:0;">Actuator Commands</div>', unsafe_allow_html=True)
    with c_btn2:
        frozen_label2 = "UNFREEZE" if st.session_state["freeze_actuators"] else "FREEZE"
        if st.button(frozen_label2, key="btn_freeze_actuators", use_container_width=True):
            st.session_state["freeze_actuators"] = not st.session_state["freeze_actuators"]

    if not st.session_state["freeze_actuators"]:
        c1, c2 = st.columns(2)
        with c1:
            if "heater_power_cmd" in df.columns:
                fh = go.Figure()
                fh.add_trace(go.Scatter(x=df["time"], y=df["heater_power_cmd"], name="Heater",
                              line=dict(color="#d2991d", width=2, shape="spline"),
                              mode="lines", hovertemplate="%{y:.0f} %<extra></extra>"))
                fh.update_layout(title="Heater Power (%)", height=260, **_LAYOUT)
                fh.update_yaxes(range=[0, 105], **_AXIS); fh.update_xaxes(**_AXIS)
                st.plotly_chart(fh, use_container_width=True, key="heater_chart")
        with c2:
            fc = make_subplots(specs=[[{"secondary_y": True}]])
            if "cooler_temp" in df.columns:
                fc.add_trace(go.Scatter(x=df["time"], y=df["cooler_temp"], name="Cooler °C",
                              line=dict(color="#58a6ff", width=2, shape="spline"),
                              mode="lines", hovertemplate="%{y:.1f} °C<extra></extra>"))
            if "cooling_valve_cmd" in df.columns:
                fc.add_trace(go.Scatter(x=df["time"], y=df["cooling_valve_cmd"], name="Cooling %",
                              line=dict(color="#3fb950", width=1.5, dash="dot"),
                              mode="lines", hovertemplate="%{y:.0f} %<extra></extra>"), secondary_y=True)
            fc.update_layout(title="Cooler Temperature & Valve", height=260, **_LAYOUT,
                             showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02))
            fc.update_yaxes(range=[0, 35], **_AXIS)
            fc.update_yaxes(range=[0, 105], secondary_y=True, **_AXIS)
            fc.update_xaxes(**_AXIS)
            st.plotly_chart(fc, use_container_width=True, key="cooler_chart")
    else:
        st.caption("Actuator charts frozen — unfreeze to update.")

    with st.expander("Raw Data (last 20 active records)"):
        st.dataframe(df.tail(20).sort_values("time", ascending=False), use_container_width=True, hide_index=True)


trends_view()

"""ALARMS — AI operator assistant + alarm event log"""

from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

import config
from ai_assistant import AIAssistant
from engine import SimulationEngine

st.set_page_config(page_title="ALARMS", layout="wide", page_icon="⏣")

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
    .diagnosis-panel {
        background: #fdfcf9; border-radius: 10px; border: 1px solid #d8d0c4;
        border-left: 5px solid #c49860; padding: 16px 20px; margin: 8px 0;
    }
    .confidence-high {
        background: #2d8a4e; color: #fff; padding: 2px 10px;
        border-radius: 10px; font-size: 0.7rem; font-weight: 700;
    }
    .confidence-medium {
        background: #d4a040; color: #1a1f2e; padding: 2px 10px;
        border-radius: 10px; font-size: 0.7rem; font-weight: 700;
    }
    .confidence-model {
        background: #3b6f8c; color: #fff; padding: 2px 10px;
        border-radius: 10px; font-size: 0.7rem; font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# ENGINE + AI
# ══════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_engine() -> SimulationEngine:
    e = SimulationEngine(use_mqtt=os.environ.get("USE_MQTT", "0") == "1")
    e.start()
    return e

@st.cache_resource
def get_assistant() -> AIAssistant:
    return AIAssistant()

engine = get_engine()
assistant = get_assistant()

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
        <div style="font-size:1.05rem;font-weight:800;color:#e8dcc8;letter-spacing:0.06em;">ALARMS</div>
        <div style="font-size:0.55rem;color:#c49860;letter-spacing:0.1em;">AI DIAGNOSTICS</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="sidebar-section">Actions</div>', unsafe_allow_html=True)
    if st.button("Force Analysis", use_container_width=True):
        st.session_state.pop("ai_cache", None)
        st.rerun()

    if st.button("Clear Cache", use_container_width=True):
        st.session_state.pop("ai_cache", None)
        st.success("Cache cleared.")

    st.divider()
    st.caption(f"Engine: {'Claude API' if assistant.using_claude else 'Rule-based (offline)'}")

# ══════════════════════════════════════════════════════════════════════
# MAIN — ALARMS PAGE
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(90deg,#1a1f2e,#252b3d,#1a1f2e);border-radius:8px;
padding:12px 24px;margin-bottom:8px;border-bottom:2px solid #c49860;">
<div style="font-size:1.15rem;font-weight:800;color:#e8dcc8;letter-spacing:0.08em;">ALARMS</div>
<div style="font-size:0.62rem;color:#8b8070;letter-spacing:0.06em;">AUTOMATIC FAULT DIAGNOSIS · OPERATOR RECOMMENDATIONS · EVENT HISTORY</div>
</div>""", unsafe_allow_html=True)


@st.fragment(run_every=f"{st.session_state['refresh_s']}s")
def alarms_view():
    latest = engine.latest()
    alarm_code = int(latest.get("alarm_code", config.ALARM_NONE))
    history = engine.historian.recent(window_s=st.session_state["window_s"])

    # ── Current Status ──
    col1, col2, col3 = st.columns(3)
    plc_state = latest.get("plc_state", "IDLE")
    plc_color = "#2d8a4e" if plc_state == "RUNNING" else ("#c0392b" if plc_state == "FAULT" else "#d4a040")
    alarm_label = config.ALARM_LABELS.get(alarm_code, "None")
    alarm_color = "#c0392b" if alarm_code else "#2d8a4e"
    fault_label = config.FAULT_LABELS.get(int(latest.get("fault_status", 0)), "Normal")

    col1.metric("PLC State", plc_state)
    col2.metric("Active Alarm", alarm_label, delta="ACTIVE" if alarm_code else "CLEAR")
    col3.metric("Fault Status", fault_label)

    st.divider()

    # ── AI Diagnosis Panel ──
    st.markdown('<div class="section-label">Diagnosis & Recommendation</div>', unsafe_allow_html=True)

    cache = st.session_state.setdefault("ai_cache", {})

    if alarm_code:
        if alarm_code not in cache:
            with st.spinner("Analyzing system state..."):
                cache[alarm_code] = assistant.diagnose(latest, alarm_code, history)
        result = cache.get(alarm_code)

        if result:
            conf = result.get("confidence_level", "unknown")
            if conf == "high":
                conf_class = "confidence-high"
            elif conf == "medium":
                conf_class = "confidence-medium"
            else:
                conf_class = "confidence-model"

            st.markdown(f"""
            <div class="diagnosis-panel">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                    <span style="font-size:1.1rem;font-weight:700;color:#3a2f1f;">{result['diagnosis_label']}</span>
                    <span class="{conf_class}">{conf.upper()}</span>
                    <span style="font-size:0.7rem;color:#8b7355;">via {result.get('engine', 'unknown')}</span>
                </div>
                <div style="color:#3a2f1f;line-height:1.6;font-size:0.92rem;padding:8px 0;">
                    {result['recommendation_text']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No active alarms — system operating normally. The AI assistant activates automatically when an alarm is detected.")

    st.divider()

    # ── Alarm Event Log ──
    st.markdown('<div class="section-label">Alarm Event Log</div>', unsafe_allow_html=True)

    alarms = engine.historian.recent_alarms(100)
    if alarms:
        adf = pd.DataFrame(alarms)
        adf["time"] = pd.to_datetime(adf["ts"], unit="s")
        adf = adf.sort_values("time", ascending=False)

        total_alarms = len(adf)
        unique_types = adf["label"].nunique() if "label" in adf.columns else 0
        st.caption(f"{total_alarms} events recorded · {unique_types} alarm types")

        def highlight_row(row):
            code = row.get("alarm_code", 0)
            if code == 0:
                return [''] * len(row)
            return ['background-color: #fce8e6'] * len(row)

        display_cols = [c for c in ["time", "label", "description"] if c in adf.columns]
        if display_cols:
            styled = adf[display_cols].style.apply(highlight_row, axis=1)
            st.dataframe(styled, use_container_width=True, hide_index=True, height=300)

        if "label" in adf.columns and total_alarms > 1:
            st.markdown('<div class="section-label" style="margin-top:12px;">Alarm Type Distribution</div>', unsafe_allow_html=True)
            dist = adf["label"].value_counts()
            cols = st.columns(len(dist))
            for i, (label, count) in enumerate(dist.items()):
                cols[i].metric(label, count)
    else:
        st.info("No alarm events recorded yet. Start the line and inject faults to see alarms here.")


alarms_view()

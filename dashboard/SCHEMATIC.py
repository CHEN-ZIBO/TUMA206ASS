"""SCHEMATIC — Process Flow Diagram + Stage Details + KPIs"""

from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotly.graph_objects as go
import streamlit as st

import config
from engine import SimulationEngine

# ══════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    .stApp { background: #f5f3ef; }
    .main .block-container { padding-top: 0.8rem; }
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
        transition: all 0.12s ease !important; cursor: pointer !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #d4a870 !important; transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(196,152,96,0.4) !important;
    }
    [data-testid="stSidebar"] .stButton > button:active {
        background: #8b5e30 !important; color: #fff !important;
        transform: scale(0.96) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3) inset !important;
    }
    [data-testid="stSidebar"] .stButton > button:focus {
        animation: btn-flash 0.6s ease-out;
    }
    @keyframes btn-flash {
        0% { box-shadow: 0 0 0 0 rgba(196,152,96,0.7); }
        70% { box-shadow: 0 0 0 12px rgba(196,152,96,0); }
        100% { box-shadow: 0 0 0 0 rgba(196,152,96,0); }
    }
    [data-testid="stSidebar"] hr { border-color: #2a3040 !important; }
    .banner-ok {
        background: linear-gradient(90deg, #2d5a27, #3d7a33); color: #fff;
        border-radius: 6px; padding: 10px 20px; font-weight: 700;
        font-size: 0.88rem; margin: 6px 0; border-left: 4px solid #5cb85c;
        letter-spacing: 0.02em;
    }
    .banner-alarm {
        background: linear-gradient(90deg, #7b1a10, #a82020); color: #fff;
        border-radius: 6px; padding: 10px 20px; font-weight: 700;
        font-size: 0.88rem; margin: 6px 0; border-left: 4px solid #ff4444;
        animation: alarm-pulse 2s infinite; letter-spacing: 0.02em;
    }
    .banner-frozen {
        background: linear-gradient(90deg, #3a3a3a, #4a4a4a); color: #bbb;
        border-radius: 6px; padding: 10px 20px; font-weight: 700;
        font-size: 0.88rem; margin: 6px 0; border-left: 4px solid #666;
        letter-spacing: 0.02em;
    }
    @keyframes alarm-pulse { 0%,100% {opacity:1;} 50% {opacity:0.88;} }
    .section-label {
        font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.1em; color: #8b7355; margin: 16px 0 6px 0;
        border-bottom: 2px solid #c49860; padding-bottom: 4px;
    }
    .kpi-card {
        background: #fffdf9; border-radius: 6px; padding: 10px 14px;
        margin: 3px 0; min-height: 80px; box-shadow: 0 1px 6px rgba(0,0,0,0.06);
        border: 1px solid #e8e0d5; transition: all 0.2s;
    }
    .kpi-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.10); }
    .kpi-label {
        font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.08em; margin-bottom: 2px;
    }
    .kpi-value {
        font-size: 1.5rem; font-weight: 800; color: #1a1f2e; line-height: 1.15;
    }
    .kpi-unit { font-size: 0.75rem; font-weight: 400; color: #8b7355; }
    .kpi-sub { font-size: 0.6rem; color: #8b7355; margin-top: 2px; }
    .stage-card {
        background: #fffdf9; border-radius: 8px; padding: 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06); border: 1px solid #e8e0d5;
        overflow: hidden; transition: all 0.25s;
    }
    .stage-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10); }
    .stage-card-header {
        padding: 8px 14px; font-weight: 800; font-size: 0.78rem;
        letter-spacing: 0.05em; color: #fff; display: flex;
        justify-content: space-between; align-items: center;
    }
    .stage-card-body { padding: 10px 14px; }
    .stage-data-row {
        display: flex; justify-content: space-between; align-items: baseline;
        padding: 3px 0; border-bottom: 1px solid #f0ebe0; font-size: 0.72rem;
    }
    .stage-data-label { color: #8b7355; font-weight: 500; }
    .stage-data-value { color: #1a1f2e; font-weight: 700; }
    .stage-requirement {
        font-size: 0.62rem; color: #6b5a45; margin-top: 4px; font-style: italic;
    }
    .status-badge {
        display: inline-block; padding: 2px 10px; border-radius: 3px;
        font-size: 0.62rem; font-weight: 700; letter-spacing: 0.06em;
        text-transform: uppercase;
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

# ══════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════
ACTUATORS = ["pump_cmd", "inlet_valve_cmd", "heater_power_cmd", "cooling_valve_cmd", "conveyor_cmd"]
for a in ACTUATORS:
    if f"man_{a}" not in st.session_state:
        st.session_state[f"man_{a}"] = False
    if f"val_{a}" not in st.session_state:
        st.session_state[f"val_{a}"] = 0 if a == "heater_power_cmd" else 0
if "refresh_s" not in st.session_state:
    st.session_state["refresh_s"] = 3

def apply_manual(act_name, is_manual, value):
    st.session_state[f"man_{act_name}"] = is_manual
    st.session_state[f"val_{act_name}"] = value
    if is_manual:
        engine.set_manual_actuator(act_name, value)
    else:
        engine.clear_manual_actuator(act_name)

# ══════════════════════════════════════════════════════════════════════
# COLORS
# ══════════════════════════════════════════════════════════════════════
C_RUN   = "#2d8a4e"
C_WARN  = "#d4a040"
C_FLT   = "#c0392b"
C_OFF   = "#9ca3af"
C_FLOW  = "#4a90d9"
C_PIPE  = "#c4bfb8"
C_HEAT  = "#e8841a"
C_COOL  = "#3b8fc4"

# ══════════════════════════════════════════════════════════════════════
# P&ID DIAGRAM — Plotly Shapes (No raw SVG)
# ══════════════════════════════════════════════════════════════════════
def build_pid_figure(latest, plc_state, alarm_code, frozen, manual_overrides):
    tl  = float(latest.get("tank_level", 50))
    pt  = float(latest.get("pasteur_temp", 25))
    ct  = float(latest.get("cooler_temp", 25))
    fr  = float(latest.get("flow_rate", 0))
    bc  = int(latest.get("bottle_count", 0))
    belt_q = int(latest.get("conveyor_queue", 0))
    max_q  = int(latest.get("conveyor_max", 8))
    bp  = int(latest.get("bottle_present", 0))
    pc  = float(latest.get("pump_cmd", 0))
    pf  = int(latest.get("pump_feedback", 0))
    ic  = float(latest.get("inlet_valve_cmd", 0))
    hc  = float(latest.get("heater_power_cmd", 0))
    cc  = float(latest.get("cooling_valve_cmd", 0))
    fc  = int(latest.get("fill_valve_cmd", 0))
    cvc = float(latest.get("conveyor_cmd", 0))
    fcode = int(latest.get("fault_status", 0))
    man = set(manual_overrides or {})

    running = plc_state in ("RUNNING", "STARTING") and not frozen
    flow_on = running and pc > 0 and pf == 1 and not frozen

    pump_clr  = C_FLT if fcode == config.FAULT_PUMP_FAIL else (C_RUN if pc > 0 else C_OFF)
    inl_clr   = C_RUN if ic > 0 else C_OFF
    heat_clr  = C_FLT if fcode == config.FAULT_TEMP_EXCURSION else (C_HEAT if hc > 0 else C_OFF)
    cool_clr  = C_COOL if cc > 0 else C_OFF
    conv_clr  = C_RUN if cvc > 0 else C_OFF
    temp_ok   = config.PASTEUR_SAFE_MIN <= pt <= config.PASTEUR_SAFE_MAX
    temp_clr  = C_RUN if temp_ok else C_FLT
    fill_clr  = C_RUN if (fc and bp) else C_OFF
    pipe_clr  = C_FLOW if flow_on else C_PIPE
    pipe_w    = 3 if flow_on else 1.5

    fig = go.Figure()
    fig.update_layout(
        xaxis=dict(range=[0, 1], visible=False, fixedrange=True),
        yaxis=dict(range=[0, 1], visible=False, fixedrange=True),
        plot_bgcolor="#fdfcfa", paper_bgcolor="#fdfcfa",
        margin=dict(l=8, r=8, t=8, b=8), height=360,
    )

    def r(x0, y0, x1, y1, fill, stroke="#8b8b7a", sw=1.8):
        fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                      fillcolor=fill, line=dict(color=stroke, width=sw))

    def c(cx, cy, rad, fill, stroke, sw=2):
        fig.add_shape(type="circle", x0=cx-rad, y0=cy-rad, x1=cx+rad, y1=cy+rad,
                      fillcolor=fill, line=dict(color=stroke, width=sw))

    def L(x0, y0, x1, y1, color, w=2):
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1,
                      line=dict(color=color, width=w))

    def A(x, y, text, size=10, color="#3a2f1f", bold=False, bg=None):
        a = dict(x=x, y=y, text=text, showarrow=False,
                 font=dict(size=size, color=color, family="Arial"))
        if bold: a["font"]["weight"] = "bold"
        if bg: a["bgcolor"] = bg; a["borderpad"] = 2
        fig.add_annotation(a)

    def M(x, y, act):
        if act in man:
            A(x, y, "M", size=8, color="#1a1f2e", bold=True, bg="#d4a040")

    # ── PIPES ──
    py = 0.42
    L(0.195, py, 0.235, py, pipe_clr, pipe_w)
    L(0.285, py, 0.355, py, pipe_clr, pipe_w)
    L(0.475, py, 0.530, py, pipe_clr, pipe_w)
    L(0.600, py, 0.600, 0.62, pipe_clr, pipe_w)
    L(0.530, 0.62, 0.600, 0.62, pipe_clr, pipe_w)
    L(0.685, 0.62, 0.720, 0.62, pipe_clr, pipe_w)
    if flow_on:
        for ax in [0.215, 0.320, 0.502, 0.565]:
            A(ax, py+0.018, ">", size=14, color=C_FLOW, bold=True)

    # ── INLET PUMP ──
    c(0.065, 0.25, 0.04, "#fafaf7", inl_clr, 2.5)
    A(0.065, 0.25, "INLET", size=7, color="#4a3f35", bold=True)
    A(0.065, 0.20, "PUMP", size=7, color="#4a3f35", bold=True)
    M(0.065, 0.16, 'inlet_valve_cmd')

    # ── RAW TANK ──
    tx, ty, tw, th = 0.10, 0.18, 0.09, 0.36
    r(tx, ty, tx+tw, ty+th, "#fafaf7")
    fh = th * tl / 100
    r(tx+0.003, ty+th-fh, tx+tw-0.003, ty+th, "#5ba0d0", None, 0)
    A(tx+tw/2, ty+th/2+0.01, f"{tl:.0f}%", size=14, color="#1a1f2e", bold=True)
    A(tx+tw/2, ty+th+0.04, "RAW TANK", size=8, color="#4a3f35", bold=True)

    # ── FEED PUMP ──
    c(0.260, 0.42, 0.04, "#fafaf7", pump_clr, 3)
    A(0.260, 0.42, f"{fr:.0f}", size=9, color=pump_clr, bold=True)
    A(0.260, 0.48, "FEED PUMP", size=7, color="#4a3f35", bold=True)
    if fcode == config.FAULT_PUMP_FAIL:
        A(0.260, 0.50, "FAULT", size=7, color=C_FLT, bold=True)
    M(0.260, 0.51, 'pump_cmd')

    # ── PASTEURIZER ──
    px, py2, pw, ph = 0.355, 0.22, 0.12, 0.28
    r(px, py2, px+pw, py2+ph, "#fafaf7")
    r(px+0.015, py2+ph-0.06, px+0.015+(pw-0.03)*hc/100, py2+ph-0.04, heat_clr, None, 0)
    A(px+pw/2, py2+ph/2+0.02, f"{pt:.1f}C", size=14, color=temp_clr, bold=True)
    A(px+pw/2, py2+ph/2-0.05, f"Heater {hc:.0f}%", size=7, color="#6b5a45")
    A(px+pw/2, py2+ph+0.04, "PASTEURIZER", size=8, color="#4a3f35", bold=True)
    M(px, py2+ph+0.055, 'heater_power_cmd')

    # ── COOLER ──
    cx, cy, cw, ch = 0.530, 0.24, 0.10, 0.24
    r(cx, cy, cx+cw, cy+ch, "#fafaf7")
    r(cx+0.015, cy+ch-0.06, cx+0.015+(cw-0.03)*cc/100, cy+ch-0.04, cool_clr, None, 0)
    A(cx+cw/2, cy+ch/2+0.02, f"{ct:.1f}C", size=14, color="#1a1f2e", bold=True)
    A(cx+cw/2, cy+ch/2-0.05, f"Cool {cc:.0f}%", size=7, color="#6b5a45")
    A(cx+cw/2, cy+ch+0.04, "COOLER", size=8, color="#4a3f35", bold=True)
    M(cx, cy+ch+0.055, 'cooling_valve_cmd')

    # ── FILLER ──
    fx, fy, fw, fh = 0.720, 0.48, 0.10, 0.32
    r(fx, fy, fx+fw, fy+fh, "#fafaf7")
    if bp:
        r(fx+0.035, fy+0.08, fx+0.065, fy+0.20, "#5ba0d0", "#3b7fc4", 1.2)
    A(fx+fw/2, fy+fh/2+0.03, "FILLING" if (fc and bp) else "IDLE", size=10, color=fill_clr, bold=True)
    A(fx+fw/2, fy+fh+0.04, "FILLER", size=8, color="#4a3f35", bold=True)

    # ── CONVEYOR & CAPPER ──
    vx, vy, vw, vh = 0.845, 0.48, 0.14, 0.32
    r(vx, vy, vx+vw, vy+vh, "#fafaf7")
    r(vx+0.008, vy+0.12, vx+vw-0.008, vy+0.16, "#e8e0d5", conv_clr, 1.5)
    n = min(belt_q, 6)
    for i in range(n):
        bx = vx + 0.018 + i * 0.02
        r(bx, vy+0.05, bx+0.012, vy+0.095, "#3b7fc4" if cvc > 0 else C_OFF, conv_clr, 0.8)
    A(vx+vw/2, vy+vh/2+0.05, f"{bc} capped", size=14, color="#1a1f2e", bold=True)
    A(vx+vw/2, vy+vh/2-0.05, f"Q: {belt_q}/{max_q}", size=8, color="#6b5a45")
    A(vx+vw/2, vy+vh+0.04, "CONVEYOR & CAP", size=8, color="#4a3f35", bold=True)
    M(vx, vy+vh+0.055, 'conveyor_cmd')

    # ── OUTLET ──
    A(0.995, 0.56, "OUTPUT", size=7, color="#8b7355", bold=True)

    # ── STATUS LINE ──
    if frozen:
        r(0.35, 0.60, 0.65, 0.72, C_FLT, C_FLT, 1)
        A(0.50, 0.66, "DATA FROZEN", size=16, color="#fff", bold=True)
    elif alarm_code:
        A(0.50, 0.66, f"ALARM: {config.ALARM_LABELS.get(alarm_code, '?')}",
          size=10, color=C_FLT, bold=True)
    else:
        A(0.50, 0.66, f"PLC: {plc_state} - NORMAL", size=10, color=C_RUN, bold=True)

    return fig


# ══════════════════════════════════════════════════════════════════════
# STAGE DETAIL CARD
# ══════════════════════════════════════════════════════════════════════
def stage_card(stage_id, name, status, color, rows, requirement=""):
    badge = f'<span class="status-badge" style="background:{color}20;color:{color};">{status}</span>'
    rows_html = "".join(
        f'<div class="stage-data-row"><span class="stage-data-label">{l}</span><span class="stage-data-value">{v}</span></div>'
        for l, v in rows
    )
    req_html = f'<div class="stage-requirement">{requirement}</div>' if requirement else ""
    return (f'<div class="stage-card">'
            f'<div class="stage-card-header" style="background:{color};"><span>{stage_id}: {name}</span>{badge}</div>'
            f'<div class="stage-card-body">{rows_html}{req_html}</div></div>')


def kpi_card(label, value, unit, color, sub=""):
    return (f'<div class="kpi-card">'
            f'<div class="kpi-label" style="color:{color};">{label}</div>'
            f'<div class="kpi-value">{value}<span class="kpi-unit"> {unit}</span></div>'
            f'<div class="kpi-sub">{sub}</div></div>')


# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:8px 0;">
        <div style="font-size:1.05rem;font-weight:800;color:#e8dcc8;letter-spacing:0.06em;">PRODUCTION</div>
        <div style="font-size:1.05rem;font-weight:800;color:#e8dcc8;letter-spacing:0.06em;">CONTROL</div>
        <div style="font-size:0.55rem;color:#c49860;letter-spacing:0.1em;">INTELLIGENT LINE SUPERVISOR</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="sidebar-section">Line Control</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("START", use_container_width=True, type="primary"):
        for a in ACTUATORS:
            st.session_state[f"man_{a}"] = False
            engine.clear_manual_actuator(a)
        engine.start_line()
        st.toast("Line started - all actuators in AUTO", icon=":material/check_circle:")
    if c2.button("STOP", use_container_width=True):
        engine.stop_line()
        for a in ACTUATORS:
            st.session_state[f"man_{a}"] = False
            engine.clear_manual_actuator(a)
        st.toast("Line stopped - all actuators off", icon=":material/stop_circle:")

    st.divider()

    st.markdown('<div class="sidebar-section">Manual Override</div>', unsafe_allow_html=True)
    st.caption("Override individual actuators (in process order).")

    # Inlet Valve (first in process flow)
    man_inlet = st.checkbox("Inlet Valve", key="man_inlet_cb")
    if man_inlet:
        val = st.slider("Open %", 0, 100, int(st.session_state.get("val_inlet_valve_cmd", 0)),
                        key="sli_inlet", label_visibility="collapsed")
        apply_manual("inlet_valve_cmd", True, float(val))
    else:
        apply_manual("inlet_valve_cmd", False, 0.0)

    # Feed Pump (second)
    man_pump = st.checkbox("Feed Pump", key="man_pump_cb")
    if man_pump:
        val = st.slider("Speed %", 0, 100, int(st.session_state.get("val_pump_cmd", 0)),
                        key="sli_pump", label_visibility="collapsed")
        apply_manual("pump_cmd", True, float(val))
    else:
        apply_manual("pump_cmd", False, 0.0)

    # Heater
    man_heater = st.checkbox("Heater", key="man_heater_cb")
    if man_heater:
        val = st.slider("Power %", 0, 100, int(st.session_state.get("val_heater_power_cmd", 0)),
                        5, key="sli_heater", label_visibility="collapsed")
        apply_manual("heater_power_cmd", True, float(val))
    else:
        apply_manual("heater_power_cmd", False, 0.0)

    # Cooling Valve
    man_cool = st.checkbox("Cooling Valve", key="man_cool_cb")
    if man_cool:
        val = st.slider("Open %", 0, 100, int(st.session_state.get("val_cooling_valve_cmd", 0)),
                        key="sli_cool", label_visibility="collapsed")
        apply_manual("cooling_valve_cmd", True, float(val))
    else:
        apply_manual("cooling_valve_cmd", False, 0.0)

    # Conveyor
    man_conv = st.checkbox("Conveyor", key="man_conv_cb")
    if man_conv:
        val = st.slider("Speed %", 0, 100, int(st.session_state.get("val_conveyor_cmd", 0)),
                        key="sli_conv", label_visibility="collapsed")
        apply_manual("conveyor_cmd", True, float(val))
    else:
        apply_manual("conveyor_cmd", False, 0.0)

    st.divider()

    st.markdown('<div class="sidebar-section">Fault Injection</div>', unsafe_allow_html=True)
    fault_choice = st.selectbox("Type", options=list(config.FAULT_LABELS.keys()),
                                format_func=lambda c: f"{c} - {config.FAULT_LABELS[c]}",
                                label_visibility="collapsed")
    c3, c4 = st.columns(2)
    if c3.button("INJECT", use_container_width=True):
        engine.inject_fault(fault_choice)
        st.toast(f"Fault injected: {config.FAULT_LABELS.get(fault_choice)}", icon=":material/warning:")
    if c4.button("RESET", use_container_width=True):
        engine.reset_fault()
        st.toast("Fault cleared - line reset", icon=":material/refresh:")

    st.divider()
    st.markdown('<div class="sidebar-section">Settings</div>', unsafe_allow_html=True)
    st.session_state["refresh_s"] = st.slider("Refresh (s)", 1, 10, st.session_state["refresh_s"])

    st.divider()
    st.caption(f"Manual overrides: {len(engine.manual_overrides)} active")


# ══════════════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(90deg,#1a1f2e,#252b3d,#1a1f2e);border-radius:8px;
padding:12px 24px;margin-bottom:8px;border-bottom:2px solid #c49860;">
<div style="font-size:1.15rem;font-weight:800;color:#e8dcc8;letter-spacing:0.06em;">SCHEMATIC</div>
<div style="font-size:0.62rem;color:#8b8070;letter-spacing:0.06em;">PROCESS FLOW DIAGRAM - STAGE DETAILS - PRODUCTION KPIs</div>
</div>""", unsafe_allow_html=True)


@st.fragment(run_every=f"{st.session_state['refresh_s']}s")
def live_view():
    latest = engine.latest()
    alarm_code = int(latest.get("alarm_code", config.ALARM_NONE))
    plc_state = latest.get("plc_state", config.PLC_IDLE)
    frozen = alarm_code == config.ALARM_DATA_STALE

    if frozen:
        st.markdown(f'<div class="banner-frozen">DATA LINK FROZEN - PLC: {plc_state}</div>', unsafe_allow_html=True)
    elif alarm_code:
        st.markdown(f'<div class="banner-alarm">ALARM [{config.ALARM_LABELS.get(alarm_code)}] - '
                    f'{config.ALARM_DESCRIPTIONS.get(alarm_code)} - PLC: {plc_state}</div>', unsafe_allow_html=True)
    else:
        n_man = len(engine.manual_overrides)
        man_note = f" - {n_man} actuator(s) in MANUAL" if n_man else ""
        st.markdown(f'<div class="banner-ok">NORMAL OPERATION - PLC: {plc_state}{man_note}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Process Flow Diagram</div>', unsafe_allow_html=True)
    fig = build_pid_figure(latest, plc_state, alarm_code, frozen, engine.manual_overrides)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Stage Cards
    st.markdown('<div class="section-label">Stage Details</div>', unsafe_allow_html=True)
    level = float(latest.get("tank_level", 0))
    temp  = float(latest.get("pasteur_temp", 0))
    cool  = float(latest.get("cooler_temp", 0))
    flow  = float(latest.get("flow_rate", 0))
    bp2   = int(latest.get("bottle_present", 0))
    bc2   = int(latest.get("bottle_count", 0))
    hc2   = float(latest.get("heater_power_cmd", 0))
    pc2   = float(latest.get("pump_cmd", 0))
    ic2   = float(latest.get("inlet_valve_cmd", 0))
    cc2   = float(latest.get("cooling_valve_cmd", 0))
    fc2   = int(latest.get("fill_valve_cmd", 0))
    cvc2  = float(latest.get("conveyor_cmd", 0))
    pf2   = int(latest.get("pump_feedback", 0))

    s1_ok = config.TANK_LEVEL_LOW <= level <= config.TANK_LEVEL_HIGH
    s2_ok = config.PASTEUR_SAFE_MIN <= temp <= config.PASTEUR_SAFE_MAX
    s3_ok = cool <= config.COOLER_MAX_BOTTLING
    s4_ok = (fc2 and bp2)
    s5_ok = cvc2 > 0

    cols = st.columns(5)
    cards = [
        ("S1", "RAW TANK", "NORMAL" if s1_ok else ("LOW" if level < config.TANK_LEVEL_LOW else "HIGH"),
         C_RUN if s1_ok else C_WARN,
         [("Tank Level", f"{level:.1f} %"), ("Flow Rate", f"{flow:.1f} L/min"),
          ("Inlet Valve", f"{'OPEN' if ic2 > 0 else 'SHUT'} ({ic2:.0f}%)"),
          ("Feed Pump", f"{'ON' if pc2 > 0 else 'OFF'} - FB: {'OK' if pf2 else '-'}")],
         f"Req: {config.TANK_LEVEL_LOW:.0f}-{config.TANK_LEVEL_HIGH:.0f}%"),

        ("S2", "PASTEURIZER", "NORMAL" if s2_ok else ("LOW" if temp < config.PASTEUR_SAFE_MIN else "HIGH"),
         C_RUN if s2_ok else C_FLT,
         [("Temperature", f"{temp:.1f} C"), ("Heater Power", f"{hc2:.0f} %"),
          ("Safe Range", f"{config.PASTEUR_SAFE_MIN:.0f}-{config.PASTEUR_SAFE_MAX:.0f} C"),
          ("Status", "At Setpoint" if s2_ok else ("Heating" if temp < config.PASTEUR_SETPOINT else "Overheating"))],
         f"Setpoint: {config.PASTEUR_SETPOINT:.0f}C - Proportional gain 4.0"),

        ("S3", "COOLER", "READY" if s3_ok else "COOLING",
         C_RUN if s3_ok else C_COOL,
         [("Temperature", f"{cool:.1f} C"), ("Cooling Valve", f"{cc2:.0f} %"),
          ("Target", f"{config.COOLER_SETPOINT:.0f} C"), ("Bottling Limit", f"{config.COOLER_MAX_BOTTLING:.0f} C")],
         f"Valve opens >{config.COOLER_OPEN_ABOVE:.0f}C"),

        ("S4", "FILLER", "FILLING" if s4_ok else ("READY" if bp2 else "IDLE"),
         C_RUN if s4_ok else (C_WARN if bp2 else C_OFF),
         [("Bottle Present", "Yes" if bp2 else "No"), ("Fill Valve", "OPEN" if fc2 else "CLOSED"),
          ("Fill Timer", f"{config.FILL_DURATION_TICKS} ticks"),
          ("Status", "Filling" if s4_ok else "Waiting")],
         f"Fill: {config.FILL_DURATION_TICKS} ticks"),

        ("S5", "CAPPER", "RUNNING" if s5_ok else "STOPPED",
         C_RUN if s5_ok else C_OFF,
         [("Bottles Capped", str(bc2)), ("Conveyor", f"{cvc2:.0f} %"),
          ("Capper", "ENGAGED" if cvc2 > 0 else "STOPPED"),
          ("Cycle", f"{config.BOTTLE_CYCLE_TICKS} ticks/bottle")],
         f"Conveyor: {config.BOTTLE_CYCLE_TICKS} ticks/bottle"),
    ]
    for col, (sid, name, stat, clr, rows, req) in zip(cols, cards):
        with col:
            st.markdown(stage_card(sid, name, stat, clr, rows, req), unsafe_allow_html=True)

    # KPI Row
    st.markdown('<div class="section-label">Production Summary</div>', unsafe_allow_html=True)
    kc = st.columns(6)
    kc[0].markdown(kpi_card("TANK LEVEL", f"{level:.1f}", "%", C_RUN if s1_ok else C_WARN,
                             f"Target: {config.TANK_LEVEL_LOW:.0f}-{config.TANK_LEVEL_HIGH:.0f}%"), unsafe_allow_html=True)
    kc[1].markdown(kpi_card("PASTEUR TEMP", f"{temp:.1f}", "C", C_RUN if s2_ok else C_FLT,
                             f"SP: {config.PASTEUR_SETPOINT:.0f}C"), unsafe_allow_html=True)
    kc[2].markdown(kpi_card("COOLER TEMP", f"{cool:.1f}", "C", C_RUN if s3_ok else C_COOL,
                             f"Target: {config.COOLER_SETPOINT:.0f}C"), unsafe_allow_html=True)
    kc[3].markdown(kpi_card("FLOW RATE", f"{flow:.1f}", "L/min", C_RUN if flow > 0 else C_OFF,
                             f"Pump: {'ON' if pc2 > 0 else 'OFF'}"), unsafe_allow_html=True)
    kc[4].markdown(kpi_card("BOTTLES", str(bc2), "capped", C_WARN if bc2 > 0 else C_OFF,
                             f"Conveyor: {cvc2:.0f}%"), unsafe_allow_html=True)
    kc[5].markdown(kpi_card("PLC STATE", plc_state, "", C_RUN if plc_state == "RUNNING" else (C_FLT if plc_state == "FAULT" else C_WARN),
                             f"Tick #{latest.get('tick', 0)}"), unsafe_allow_html=True)


live_view()

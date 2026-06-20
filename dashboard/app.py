"""M4 Dashboard · SCHEMATIC — Process Flow Diagram + Stage Details + KPIs"""

from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

import config
from engine import SimulationEngine

st.set_page_config(page_title="SCHEMATIC", layout="wide", page_icon="⏣")

# ══════════════════════════════════════════════════════════════════════
# GLOBAL CSS — Industrial Control Room Theme
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
        transition: all 0.2s !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #d4a870 !important; transform: translateY(-1px);
    }
    [data-testid="stSidebar"] hr { border-color: #2a3040 !important; }

    .banner-ok {
        background: linear-gradient(90deg, #2d5a27, #3d7a33);
        color: #fff; border-radius: 6px; padding: 10px 20px;
        font-weight: 700; font-size: 0.88rem; margin: 6px 0;
        border-left: 4px solid #5cb85c; letter-spacing: 0.02em;
    }
    .banner-alarm {
        background: linear-gradient(90deg, #7b1a10, #a82020);
        color: #fff; border-radius: 6px; padding: 10px 20px;
        font-weight: 700; font-size: 0.88rem; margin: 6px 0;
        border-left: 4px solid #ff4444;
        animation: alarm-pulse 2s infinite; letter-spacing: 0.02em;
    }
    .banner-frozen {
        background: linear-gradient(90deg, #3a3a3a, #4a4a4a);
        color: #bbb; border-radius: 6px; padding: 10px 20px;
        font-weight: 700; font-size: 0.88rem; margin: 6px 0;
        border-left: 4px solid #666; letter-spacing: 0.02em;
    }
    @keyframes alarm-pulse { 0%,100% {opacity:1;} 50% {opacity:0.88;} }

    .section-label {
        font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.1em; color: #8b7355; margin: 16px 0 6px 0;
        border-bottom: 2px solid #c49860; padding-bottom: 4px;
    }

    .kpi-card {
        background: #fffdf9; border-radius: 6px; padding: 10px 14px;
        margin: 3px 0; min-height: 80px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06);
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
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border: 1px solid #e8e0d5; overflow: hidden;
        transition: all 0.25s;
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
        padding: 3px 0; border-bottom: 1px solid #f0ebe0;
        font-size: 0.72rem;
    }
    .stage-data-label { color: #8b7355; font-weight: 500; }
    .stage-data-value { color: #1a1f2e; font-weight: 700; }
    .stage-requirement { font-size: 0.62rem; color: #6b5a45; margin-top: 4px; font-style: italic; }

    .status-badge {
        display: inline-block; padding: 2px 10px; border-radius: 3px;
        font-size: 0.62rem; font-weight: 700; letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .sidebar-section {
        font-size: 0.58rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.12em; color: #c49860; margin-top: 12px; margin-bottom: 4px;
    }

    /* Pump rotation animation */
    @keyframes pump-spin {
        from { transform: rotate(0deg); transform-origin: center; }
        to { transform: rotate(360deg); transform-origin: center; }
    }
    .pump-on { animation: pump-spin 2s linear infinite; }

    /* Flow animation in pipes */
    @keyframes flow-march {
        from { stroke-dashoffset: 20; }
        to { stroke-dashoffset: 0; }
    }
    .pipe-flow { animation: flow-march 0.6s linear infinite; }
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
# COLOR CONSTANTS
# ══════════════════════════════════════════════════════════════════════
C_RUN    = "#2d8a4e"
C_WARN   = "#d4a040"
C_FLT    = "#c0392b"
C_OFF    = "#9ca3af"
C_FLOW   = "#4a90d9"
C_FLOW2  = "#6db3f2"
C_PIPE   = "#c4bfb8"
C_TANK   = "#6b8fa3"
C_HEAT   = "#e8841a"
C_COOL   = "#3b8fc4"
C_BG     = "#fdfcfa"
C_BORDER = "#d8d0c4"

# ══════════════════════════════════════════════════════════════════════
# P&ID SCHEMATIC SVG — Professional Process Flow Diagram
# ══════════════════════════════════════════════════════════════════════
def build_schematic_svg(latest, plc_state, alarm_code, frozen, manual_overrides):
    tl  = float(latest.get("tank_level", 50))
    pt  = float(latest.get("pasteur_temp", 25))
    ct  = float(latest.get("cooler_temp", 25))
    fr  = float(latest.get("flow_rate", 0))
    bc  = int(latest.get("bottle_count", 0))
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

    # State flags
    running = plc_state in ("RUNNING", "STARTING") and not frozen
    flow_on = running and pc > 0 and pf == 1 and not frozen
    has_alarm = alarm_code != config.ALARM_NONE

    # Equipment colors
    pump_clr  = C_FLT if fcode == config.FAULT_PUMP_FAIL else (C_RUN if pc > 0 else C_OFF)
    inl_clr   = C_RUN if ic > 0 else C_OFF
    heat_clr  = C_FLT if fcode == config.FAULT_TEMP_EXCURSION else (C_HEAT if hc > 0 else C_OFF)
    cool_clr  = C_COOL if cc > 0 else C_OFF
    temp_clr  = C_FLT if (running and (pt > config.PASTEUR_SAFE_MAX or pt < config.PASTEUR_SAFE_MIN)) else C_RUN
    conv_clr  = C_RUN if cvc > 0 else C_OFF

    # Pipe color: blue when flow, gray when empty
    pipe_c = C_FLOW if flow_on else C_PIPE
    pipe_w = 3.5 if flow_on else 2.5

    # Flow segments in pipes (small colored bars)
    def pipe_flow_segments(x1, y1, x2, y2, active):
        if not active:
            return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{C_PIPE}" stroke-width="3" stroke-linecap="round"/>'
        # Draw pipe body + animated dash overlay for flow
        dx, dy = x2-x1, y2-y1
        length = (dx*dx + dy*dy)**0.5
        return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{C_PIPE}" stroke-width="6" stroke-linecap="round"/>'
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{C_FLOW}" stroke-width="3.5"'
                f' stroke-dasharray="8,8" class="pipe-flow" stroke-linecap="round"/>')

    def man_tag(x, y, act):
        if act in man:
            return (f'<rect x="{x}" y="{y}" width="32" height="11" rx="5.5" fill="#d4a040" opacity="0.9"/>'
                    f'<text x="{x+16}" y="{y+8.5}" text-anchor="middle" font-size="6.5" font-weight="700" fill="#1a1f2e">MAN</text>')
        return ''

    # Flow arrows at pipe midpoints
    def flow_arrow(mx, my, active):
        if not active: return ''
        return f'<polygon points="{mx-5},{my-4} {mx+5},{my} {mx-5},{my+4}" fill="{C_FLOW}" opacity="0.7"/>'

    svg = f'''<svg width="100%" viewBox="0 0 1200 580" xmlns="http://www.w3.org/2000/svg"
     style="background:{C_BG};border-radius:10px;box-shadow:0 2px 16px rgba(0,0,0,0.06);border:1px solid {C_BORDER};">
    <defs>
        <filter id="shadow"><feDropShadow dx="0" dy="1.5" stdDeviation="2.5" flood-opacity="0.08"/></filter>
        <filter id="glow"><feGaussianBlur stdDeviation="3" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
        <linearGradient id="liquidGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#5ba0d0" stop-opacity="0.7"/>
            <stop offset="100%" stop-color="#3878a8" stop-opacity="0.4"/>
        </linearGradient>
        <linearGradient id="heatGrad" x1="1" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#ff9a3c" stop-opacity="0.3"/>
            <stop offset="100%" stop-color="#e8841a" stop-opacity="0.08"/>
        </linearGradient>
        <linearGradient id="coolGrad" x1="1" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#5bb8e8" stop-opacity="0.3"/>
            <stop offset="100%" stop-color="#3b8fc4" stop-opacity="0.08"/>
        </linearGradient>
    </defs>

    <!-- Background grid -->
    <pattern id="gr" width="30" height="30" patternUnits="userSpaceOnUse">
        <path d="M30 0L0 0 0 30" fill="none" stroke="#e8e0d5" stroke-width="0.3"/>
    </pattern>
    <rect width="1200" height="580" fill="url(#gr)" opacity="0.45"/>

    <!-- ═══════════════════════ RAW SUPPLY INLET (top-left) ═══════════════════════ -->
    <text x="60" y="42" font-size="7.5" fill="#8b7355" font-weight="600">RAW BEVERAGE SUPPLY</text>
    {pipe_flow_segments(60, 52, 60, 82, flow_on)}
    <!-- INLET PUMP (raw supply side) -->
    <g filter="url(#shadow)">
        <circle cx="60" cy="100" r="18" fill="#fafaf7" stroke={inl_clr} stroke-width="2.5"/>
        <polygon points="60,86 75,100 60,114" fill={inl_clr} opacity="0.25" stroke={inl_clr} stroke-width="1"
                 {'class="pump-on"' if ic > 0 else ''}/>
        <circle cx="60" cy="100" r="3.5" fill={inl_clr}/>
        <text x="60" y="130" text-anchor="middle" font-size="7" font-weight="700" fill="#4a3f35">INLET</text>
        <text x="60" y="140" text-anchor="middle" font-size="7" font-weight="700" fill="#4a3f35">PUMP</text>
    </g>
    {man_tag(30, 144, 'inlet_valve_cmd')}
    {pipe_flow_segments(60, 118, 60, 150, flow_on)}
    {flow_arrow(60, 134, flow_on)}

    <!-- ═══════════════════════ S1: RAW TANK (cylinder) ═══════════════════════ -->
    <g filter="url(#shadow)">
        <!-- Cylinder body -->
        <ellipse cx="110" cy="170" rx="42" ry="12" fill="#e8e8e2" stroke="#8b8b7a" stroke-width="1.8"/>
        <path d="M68,170 L68,280 A42,12 0 0,0 152,280 L152,170" fill="#fafaf7" stroke="#8b8b7a" stroke-width="1.8"/>
        <!-- Liquid fill (clipped) -->
        <clipPath id="tankFill"><path d="M70,280 L70,{280 - 110 * tl/100} A40,11 0 0,1 150,{280 - 110 * tl/100} L150,280 Z"/></clipPath>
        <rect x="68" y="170" width="84" height="115" fill="url(#liquidGrad)" clip-path="url(#tankFill)"/>
        <!-- Liquid surface ellipse (animated by clipping change) -->
        <ellipse cx="110" cy="{280 - 110 * tl/100}" rx="40" ry="10" fill="#5ba0d0" opacity="0.35" clip-path="url(#tankFill)"/>
        <!-- Cylinder top ellipse (redraw over fill) -->
        <ellipse cx="110" cy="170" rx="42" ry="12" fill="none" stroke="#8b8b7a" stroke-width="2.2"/>
        <!-- Level text -->
        <text x="110" y="240" text-anchor="middle" font-size="16" font-weight="800" fill="#1a1f2e">{tl:.0f}%</text>
        <!-- Stage label -->
        <text x="110" y="310" text-anchor="middle" font-size="9.5" font-weight="700" fill="#4a3f35">RAW TANK</text>
        <text x="110" y="324" text-anchor="middle" font-size="7" fill="#8b7355">S1 · Balance Tank</text>
    </g>

    <!-- ═══════════════════════ PIPE: Tank → Feed Pump ═══════════════════════ -->
    {pipe_flow_segments(152, 230, 205, 230, flow_on)}
    {flow_arrow(178, 230, flow_on)}

    <!-- ═══════════════════════ FEED PUMP ═══════════════════════ -->
    <g filter="url(#shadow)">
        <circle cx="235" cy="230" r="30" fill="#fafaf7" stroke={pump_clr} stroke-width="3"/>
        <polygon points="235,208 260,245 210,245" fill={pump_clr} opacity="0.2" stroke={pump_clr} stroke-width="1.5"
                 {'class="pump-on"' if flow_on else ''}/>
        <circle cx="235" cy="230" r="5" fill={pump_clr}/>
        <text x="235" y="270" text-anchor="middle" font-size="7.5" font-weight="700" fill="#4a3f35">FEED</text>
        <text x="235" y="282" text-anchor="middle" font-size="7.5" font-weight="700" fill="#4a3f35">PUMP</text>
        <text x="235" y="296" text-anchor="middle" font-size="7" fill={pump_clr} font-weight="600">{fr:.0f} L/min</text>
        {f'<text x="235" y="310" text-anchor="middle" font-size="7" fill="{C_FLT}" font-weight="700">FAULT</text>' if fcode == config.FAULT_PUMP_FAIL else ''}
    </g>
    {man_tag(260, 314, 'pump_cmd')}

    <!-- ═══════════════════════ PIPE: Feed Pump → Pasteurizer ═══════════════════════ -->
    {pipe_flow_segments(265, 230, 350, 230, flow_on)}
    {flow_arrow(307, 230, flow_on)}

    <!-- ═══════════════════════ S2: PASTEURIZER (horizontal thermal vessel) ═══════════════════════ -->
    <g filter="url(#shadow)">
        <!-- Vessel body (horizontal cylinder) -->
        <rect x="350" y="160" width="180" height="140" rx="20" fill="#fafaf7" stroke="#8b8b7a" stroke-width="2"/>
        <!-- Heating jacket glow -->
        <rect x="355" y="160" width="170" height="140" rx="18" fill="url(#heatGrad)" opacity="0.5"/>
        <!-- Internal heating coil -->
        <path d="M370 190Q400 175 430 190Q460 205 490 190" fill="none" stroke={heat_clr} stroke-width="2.8" opacity="0.6"
              {'class="pump-on"' if hc > 10 else ''}/>
        <path d="M370 210Q400 195 430 210Q460 225 490 210" fill="none" stroke={heat_clr} stroke-width="2.2" opacity="0.45"
              {'class="pump-on"' if hc > 10 else ''}/>
        <path d="M370 230Q400 215 430 230Q460 245 490 230" fill="none" stroke={heat_clr} stroke-width="1.6" opacity="0.3"/>
        <!-- Temperature readout -->
        <text x="440" y="248" text-anchor="middle" font-size="22" font-weight="800" fill={temp_clr}>{pt:.1f}°C</text>
        <!-- Heater indicator bar -->
        <rect x="390" y="258" width="100" height="7" rx="3.5" fill="#e8e0d5"/>
        <rect x="390" y="258" width="{100*hc/100}" height="7" rx="3.5" fill={heat_clr}/>
        <!-- Labels -->
        <text x="440" y="280" text-anchor="middle" font-size="8" fill="#6b5a45">Heater {hc:.0f}%</text>
        <text x="440" y="320" text-anchor="middle" font-size="9.5" font-weight="700" fill="#4a3f35">PASTEURIZER</text>
        <text x="440" y="334" text-anchor="middle" font-size="7" fill="#8b7355">S2 · 72°C Thermal Treatment</text>
    </g>
    {man_tag(370, 340, 'heater_power_cmd')}

    <!-- ═══════════════════════ PIPE: Pasteurizer → Cooler ═══════════════════════ -->
    {pipe_flow_segments(530, 230, 590, 230, flow_on)}
    {flow_arrow(560, 230, flow_on)}

    <!-- ═══════════════════════ S3: COOLER (vertical shell-and-tube exchanger) ═══════════════════════ -->
    <g filter="url(#shadow)">
        <!-- Cooler vessel -->
        <rect x="590" y="140" width="140" height="180" rx="10" fill="#fafaf7" stroke="#8b8b7a" stroke-width="2"/>
        <!-- Tube bundle (vertical lines) -->
        <line x1="612" y1="150" x2="612" y2="310" stroke="#a0c8d8" stroke-width="1.2"/>
        <line x1="630" y1="150" x2="630" y2="310" stroke="#a0c8d8" stroke-width="1.2"/>
        <line x1="648" y1="150" x2="648" y2="310" stroke="#a0c8d8" stroke-width="1.2"/>
        <line x1="666" y1="150" x2="666" y2="310" stroke="#a0c8d8" stroke-width="1.2"/>
        <line x1="684" y1="150" x2="684" y2="310" stroke="#a0c8d8" stroke-width="1.2"/>
        <line x1="702" y1="150" x2="702" y2="310" stroke="#a0c8d8" stroke-width="1.2"/>
        <!-- Cooling coil overlay -->
        <ellipse cx="660" cy="190" rx="50" ry="16" fill="none" stroke={cool_clr} stroke-width="2.2" stroke-dasharray="8,4"/>
        <ellipse cx="660" cy="215" rx="38" ry="12" fill="none" stroke={cool_clr} stroke-width="1.8" stroke-dasharray="8,4"/>
        <!-- Temperature -->
        <text x="660" y="250" text-anchor="middle" font-size="22" font-weight="800" fill="#1a1f2e">{ct:.1f}°C</text>
        <!-- Cooling valve indicator -->
        <rect x="635" y="260" width="50" height="12" rx="6" fill={cool_clr} opacity="0.18" stroke={cool_clr} stroke-width="1.3"/>
        <text x="660" y="269" text-anchor="middle" font-size="7" font-weight="700" fill={cool_clr}>COOL {cc:.0f}%</text>
        <!-- Labels -->
        <text x="660" y="310" text-anchor="middle" font-size="9.5" font-weight="700" fill="#4a3f35">COOLER</text>
        <text x="660" y="324" text-anchor="middle" font-size="7" fill="#8b7355">S3 · Heat Exchanger</text>
    </g>
    {man_tag(620, 330, 'cooling_valve_cmd')}

    <!-- ═══════════════════════ PIPE: Cooler down to Filler ═══════════════════════ -->
    {pipe_flow_segments(660, 320, 660, 370, flow_on)}
    {flow_arrow(660, 345, flow_on)}
    {pipe_flow_segments(660, 370, 760, 370, flow_on)}

    <!-- ═══════════════════════ S4: FILLER (filling station) ═══════════════════════ -->
    <g filter="url(#shadow)">
        <rect x="730" y="330" width="140" height="170" rx="10" fill="#fafaf7" stroke="#8b8b7a" stroke-width="2"/>
        <!-- Fill head / nozzle -->
        <line x1="800" y1="370" x2="800" y2="410" stroke="#6b6b5a" stroke-width="3"/>
        <rect x="785" y="360" width="30" height="12" rx="4" fill={C_RUN if fc else C_OFF} opacity="0.3" stroke={C_RUN if fc else C_OFF} stroke-width="1.3"/>
        <text x="800" y="369" text-anchor="middle" font-size="6.5" font-weight="700" fill="#fff">FILL</text>
        <!-- Bottle -->
        {f'<rect x="776" y="415" width="48" height="52" rx="7" fill="#5ba0d0" opacity="0.3" stroke="#3b7fc4" stroke-width="1.5"/>' if bp else f'<rect x="776" y="415" width="48" height="52" rx="7" fill="none" stroke="#b0b8c4" stroke-width="1.2" stroke-dasharray="5,3"/>'}
        <!-- Fill stream -->
        {f'<line x1="800" y1="410" x2="800" y2="435" stroke="#3b7fc4" stroke-width="3.5" opacity="0.5"/>' if fc and bp else ''}
        <!-- Labels -->
        <text x="800" y="488" text-anchor="middle" font-size="8" font-weight="700" fill="#4a3f35">{"FILLING" if (fc and bp) else "IDLE"}</text>
        <text x="800" y="505" text-anchor="middle" font-size="9.5" font-weight="700" fill="#4a3f35">FILLER</text>
        <text x="800" y="518" text-anchor="middle" font-size="7" fill="#8b7355">S4 · Bottle Fill Station</text>
    </g>

    <!-- ═══════════════════════ PIPE: Filler → Conveyor ═══════════════════════ -->
    {pipe_flow_segments(870, 415, 920, 415, False)}  <!-- bottles move by conveyor, not pipe -->

    <!-- ═══════════════════════ S5: CONVEYOR / CAPPER ═══════════════════════ -->
    <g filter="url(#shadow)">
        <rect x="910" y="340" width="230" height="160" rx="10" fill="#fafaf7" stroke="#8b8b7a" stroke-width="2"/>
        <!-- Conveyor belt (special graphic) -->
        <!-- Belt body: two parallel lines + cross ticks -->
        <rect x="925" y="430" width="200" height="14" rx="7" fill="#e8e0d5" stroke={conv_clr} stroke-width="1.5"/>
        <!-- Cross ticks (belt treads) -->
        {''.join(f'<line x1="{x}" y1="430" x2="{x}" y2="444" stroke="{conv_clr}" stroke-width="1.2" opacity="0.5"/>' for x in range(935, 1115, 10))}
        <!-- Rollers -->
        <circle cx="933" cy="437" r="10" fill="#d0d0d0" stroke="#8b8b7a" stroke-width="1.5"
                {'class="pump-on"' if cvc > 0 else ''}/>
        <circle cx="1118" cy="437" r="10" fill="#d0d0d0" stroke="#8b8b7a" stroke-width="1.5"
                {'class="pump-on"' if cvc > 0 else ''}/>
        <!-- Bottles on conveyor -->
        <rect x="960" y="406" width="16" height="24" rx="4" fill="#3b7fc4" opacity="0.55" stroke="#3b7fc4" stroke-width="0.8"/>
        <rect x="957" y="403" width="22" height="5" rx="2.5" fill="#22c55e" opacity="0.8"/>
        <rect x="995" y="408" width="14" height="22" rx="4" fill="#3b7fc4" opacity="0.45" stroke="#3b7fc4" stroke-width="0.8"/>
        <rect x="992" y="405" width="20" height="5" rx="2.5" fill="#22c55e" opacity="0.7"/>
        <rect x="1025" y="406" width="16" height="24" rx="4" fill="#3b7fc4" opacity="0.55" stroke="#3b7fc4" stroke-width="0.8"/>
        <rect x="1022" y="403" width="22" height="5" rx="2.5" fill="#22c55e" opacity="0.8"/>
        <!-- Capper mechanism (above belt) -->
        <rect x="1065" y="385" width="24" height="30" rx="5" fill="#fafaf7" stroke="#8b8b7a" stroke-width="1.5"/>
        <circle cx="1077" cy="400" r="8" fill="none" stroke="#8b8b7a" stroke-width="1.8"
                {'class="pump-on"' if cvc > 0 else ''}/>
        <text x="1077" y="403" text-anchor="middle" font-size="6.5" fill="#6b5a45">C</text>
        <!-- Count -->
        <text x="1025" y="472" text-anchor="middle" font-size="20" font-weight="800" fill="#1a1f2e">{bc}</text>
        <text x="1025" y="486" text-anchor="middle" font-size="7" fill="#8b7355">Bottles Capped</text>
        <text x="1025" y="505" text-anchor="middle" font-size="9.5" font-weight="700" fill="#4a3f35">CAPPER / CONVEYOR</text>
        <text x="1025" y="518" text-anchor="middle" font-size="7" fill="#8b7355">S5 · Bottling Line</text>
    </g>
    {man_tag(940, 522, 'conveyor_cmd')}

    <!-- ═══════════════════════ OUTLET ═══════════════════════ -->
    <line x1="1140" y1="437" x2="1175" y2="437" stroke="#8b8b7a" stroke-width="5" stroke-linecap="round"/>
    <polygon points="1168,432 1178,437 1168,442" fill="#8b7355"/>
    <text x="1185" y="440" font-size="7" fill="#8b7355">OUTPUT</text>

    <!-- ═══════════════════════ LEGEND ═══════════════════════ -->
    <g>
        <rect x="30" y="540" width="1140" height="32" rx="6" fill="#fafaf7" stroke="#e0d8cc" stroke-width="0.8"/>
        <text x="48" y="561" font-size="7" font-weight="700" fill="#6b5a45">LEGEND:</text>
        <circle cx="130" cy="557" r="4" fill={C_FLOW}/><text x="138" y="561" font-size="6.5" fill="#6b5a45">Liquid flow ON</text>
        <line x1="210" y1="557" x2="234" y2="557" stroke={C_PIPE} stroke-width="2.5"/><text x="238" y="561" font-size="6.5" fill="#6b5a45">No flow</text>
        <circle cx="295" cy="557" r="6" fill="none" stroke={C_RUN} stroke-width="2"/><text x="305" y="561" font-size="6.5" fill="#6b5a45">Pump (green=OK)</text>
        <circle cx="400" cy="557" r="6" fill="none" stroke={C_FLT} stroke-width="2"/><text x="410" y="561" font-size="6.5" fill="#6b5a45">Pump fault</text>
        <rect x="478" y="553" width="14" height="8" rx="4" fill={C_HEAT}/><text x="496" y="561" font-size="6.5" fill="#6b5a45">Heater</text>
        <rect x="540" y="553" width="14" height="8" rx="4" fill={C_COOL}/><text x="558" y="561" font-size="6.5" fill="#6b5a45">Cooling</text>
        <rect x="610" y="553" width="14" height="8" rx="4" fill="#8b8b7a"/><text x="628" y="561" font-size="6.5" fill="#6b5a45">Vessel wall</text>
        <rect x="700" y="553" width="14" height="8" rx="4" fill="#d4a040"/><text x="718" y="561" font-size="6.5" fill="#6b5a45">Manual override</text>
        <rect x="810" y="553" width="14" height="8" rx="4" fill="#e8e0d5"/><text x="828" y="561" font-size="6.5" fill="#6b5a45">Conveyor belt</text>
        <line x1="900" y1="557" x2="920" y2="557" stroke={C_FLOW} stroke-width="2" stroke-dasharray="6,4"/><text x="924" y="561" font-size="6.5" fill="#6b5a45">Flow animation</text>
    </g>

    <!-- ═══════════════════════ DATA FROZEN OVERLAY ═══════════════════════ -->
    {f'''
    <rect x="0" y="0" width="1200" height="580" fill="#1a1f2e" opacity="0.55"/>
    <rect x="380" y="220" width="440" height="70" rx="12" fill="#c0392b" opacity="0.9"/>
    <text x="600" y="252" text-anchor="middle" font-size="20" font-weight="800" fill="#fff">DATA LINK FROZEN</text>
    <text x="600" y="274" text-anchor="middle" font-size="10" fill="#fdd">Monitoring link down — displayed values are not updating</text>
    ''' if frozen else ''}
</svg>'''
    return svg


# ══════════════════════════════════════════════════════════════════════
# STAGE DETAIL CARD (unified format)
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
    if c1.button("START", use_container_width=True):
        engine.start_line()
    if c2.button("STOP", use_container_width=True):
        engine.stop_line()
        for a in ACTUATORS:
            st.session_state[f"man_{a}"] = False
            engine.clear_manual_actuator(a)

    st.divider()

    st.markdown('<div class="sidebar-section">Manual Override</div>', unsafe_allow_html=True)
    st.caption("Override individual actuators.")

    man_pump = st.checkbox("Feed Pump", key="man_pump_cb")
    if man_pump:
        val = st.slider("Speed %", 0.0, 100.0, float(st.session_state.get("val_pump_cmd", 0.0)), key="sli_pump", label_visibility="collapsed")
        apply_manual("pump_cmd", True, float(val))
    else:
        apply_manual("pump_cmd", False, 0.0)

    man_inlet = st.checkbox("Inlet Valve", key="man_inlet_cb")
    if man_inlet:
        val = st.slider("Open %", 0.0, 100.0, float(st.session_state.get("val_inlet_valve_cmd", 0.0)), key="sli_inlet", label_visibility="collapsed")
        apply_manual("inlet_valve_cmd", True, float(val))
    else:
        apply_manual("inlet_valve_cmd", False, 0.0)

    man_heater = st.checkbox("Heater", key="man_heater_cb")
    if man_heater:
        val = st.slider("Power %", 0.0, 100.0, float(st.session_state.get("val_heater_power_cmd", 0.0)), 5.0, key="sli_heater", label_visibility="collapsed")
        apply_manual("heater_power_cmd", True, float(val))
    else:
        apply_manual("heater_power_cmd", False, 0.0)

    man_cool = st.checkbox("Cooling Valve", key="man_cool_cb")
    if man_cool:
        val = st.slider("Open %", 0.0, 100.0, float(st.session_state.get("val_cooling_valve_cmd", 0.0)), key="sli_cool", label_visibility="collapsed")
        apply_manual("cooling_valve_cmd", True, float(val))
    else:
        apply_manual("cooling_valve_cmd", False, 0.0)

    man_conv = st.checkbox("Conveyor", key="man_conv_cb")
    if man_conv:
        val = st.slider("Speed %", 0.0, 100.0, float(st.session_state.get("val_conveyor_cmd", 0.0)), key="sli_conv", label_visibility="collapsed")
        apply_manual("conveyor_cmd", True, float(val))
    else:
        apply_manual("conveyor_cmd", False, 0.0)

    st.divider()

    st.markdown('<div class="sidebar-section">Fault Injection</div>', unsafe_allow_html=True)
    fault_choice = st.selectbox("Type", options=list(config.FAULT_LABELS.keys()),
                                format_func=lambda c: f"{c} - {config.FAULT_LABELS[c]}", label_visibility="collapsed")
    c3, c4 = st.columns(2)
    if c3.button("INJECT", use_container_width=True):
        engine.inject_fault(fault_choice)
    if c4.button("RESET", use_container_width=True):
        engine.reset_fault()

    st.divider()
    st.markdown('<div class="sidebar-section">Settings</div>', unsafe_allow_html=True)
    st.session_state["refresh_s"] = st.slider("Refresh (s)", 1, 10, st.session_state["refresh_s"])

    st.divider()
    st.caption(f"Manual overrides: {len(engine.manual_overrides)} active")


# ══════════════════════════════════════════════════════════════════════
# MAIN CONTENT — SCHEMATIC PAGE
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(90deg,#1a1f2e,#252b3d,#1a1f2e);border-radius:8px;
padding:12px 24px;margin-bottom:8px;border-bottom:2px solid #c49860;">
<div style="font-size:1.15rem;font-weight:800;color:#e8dcc8;letter-spacing:0.06em;">SCHEMATIC</div>
<div style="font-size:0.62rem;color:#8b8070;letter-spacing:0.06em;">PROCESS FLOW DIAGRAM — STAGE DETAILS — PRODUCTION KPIs</div>
</div>""", unsafe_allow_html=True)


@st.fragment(run_every=f"{st.session_state['refresh_s']}s")
def live_view():
    latest = engine.latest()
    alarm_code = int(latest.get("alarm_code", config.ALARM_NONE))
    plc_state = latest.get("plc_state", config.PLC_IDLE)
    frozen = alarm_code == config.ALARM_DATA_STALE

    # ── Status Banner ──
    if frozen:
        st.markdown(f'<div class="banner-frozen">DATA LINK FROZEN — Monitoring offline. PLC: {plc_state}</div>', unsafe_allow_html=True)
    elif alarm_code:
        st.markdown(f'<div class="banner-alarm">ALARM [{config.ALARM_LABELS.get(alarm_code)}] — '
                    f'{config.ALARM_DESCRIPTIONS.get(alarm_code)} · PLC: {plc_state}</div>', unsafe_allow_html=True)
    else:
        n_man = len(engine.manual_overrides)
        man_note = f" · {n_man} actuator(s) in MANUAL" if n_man else ""
        st.markdown(f'<div class="banner-ok">NORMAL OPERATION · PLC: {plc_state}{man_note}</div>', unsafe_allow_html=True)

    # ── P&ID Schematic ──
    st.markdown('<div class="section-label">Process Flow Diagram</div>', unsafe_allow_html=True)
    svg = build_schematic_svg(latest, plc_state, alarm_code, frozen, engine.manual_overrides)
    st.components.v1.html(svg, height=595, scrolling=False)

    # ── 5 Stage Detail Cards ──
    st.markdown('<div class="section-label">Stage Details</div>', unsafe_allow_html=True)

    level = float(latest.get("tank_level", 0))
    temp  = float(latest.get("pasteur_temp", 0))
    cool  = float(latest.get("cooler_temp", 0))
    flow  = float(latest.get("flow_rate", 0))
    bp    = int(latest.get("bottle_present", 0))
    bc    = int(latest.get("bottle_count", 0))
    hc    = float(latest.get("heater_power_cmd", 0))
    pc    = float(latest.get("pump_cmd", 0))
    ic    = float(latest.get("inlet_valve_cmd", 0))
    cc    = float(latest.get("cooling_valve_cmd", 0))
    fc    = int(latest.get("fill_valve_cmd", 0))
    cvc   = float(latest.get("conveyor_cmd", 0))
    pf    = int(latest.get("pump_feedback", 0))

    s1_stat = "NORMAL" if config.TANK_LEVEL_LOW <= level <= config.TANK_LEVEL_HIGH else ("LOW" if level < config.TANK_LEVEL_LOW else "HIGH")
    s1_col  = C_RUN if s1_stat == "NORMAL" else C_WARN
    s2_temp_ok = config.PASTEUR_SAFE_MIN <= temp <= config.PASTEUR_SAFE_MAX
    s2_stat = "NORMAL" if s2_temp_ok else ("LOW" if temp < config.PASTEUR_SAFE_MIN else "HIGH")
    s2_col  = C_RUN if s2_stat == "NORMAL" else C_FLT
    s3_stat = "READY" if cool <= config.COOLER_MAX_BOTTLING else "COOLING"
    s3_col  = C_RUN if s3_stat == "READY" else C_COOL
    s4_stat = "FILLING" if (fc and bp) else ("READY" if bp else "IDLE")
    s4_col  = C_RUN if s4_stat == "FILLING" else (C_WARN if s4_stat == "READY" else C_OFF)
    s5_stat = "RUNNING" if cvc > 0 else "STOPPED"
    s5_col  = C_RUN if s5_stat == "RUNNING" else C_OFF

    cols = st.columns(5)
    cards = [
        ("S1", "RAW TANK", s1_stat, s1_col,
         [("Tank Level", f"{level:.1f} %"), ("Flow Rate", f"{flow:.1f} L/min"),
          ("Inlet Valve", f"{'OPEN' if ic > 0 else 'SHUT'} ({ic:.0f}%)"),
          ("Feed Pump", f"{'ON' if pc > 0 else 'OFF'} · FB: {'OK' if pf else '—'}")],
         f"Level: {config.TANK_LEVEL_LOW:.0f}–{config.TANK_LEVEL_HIGH:.0f}% · Pump guard: >{config.TANK_LEVEL_MIN_PUMP:.0f}%"),
        ("S2", "PASTEURIZER", s2_stat, s2_col,
         [("Temperature", f"{temp:.1f} °C"), ("Heater Power", f"{hc:.0f} %"),
          ("Safe Range", f"{config.PASTEUR_SAFE_MIN:.0f}–{config.PASTEUR_SAFE_MAX:.0f} °C"),
          ("Status", "At Setpoint" if s2_temp_ok else ("Heating" if temp < config.PASTEUR_SETPOINT else "Overheating"))],
         f"Setpoint: {config.PASTEUR_SETPOINT:.0f}°C · Proportional gain: 4.0"),
        ("S3", "COOLER", s3_stat, s3_col,
         [("Temperature", f"{cool:.1f} °C"), ("Cooling Valve", f"{cc:.0f} %"),
          ("Target", f"{config.COOLER_SETPOINT:.0f} °C"), ("Bottling Limit", f"{config.COOLER_MAX_BOTTLING:.0f} °C")],
         f"Valve opens >{config.COOLER_OPEN_ABOVE:.0f}°C · PI control"),
        ("S4", "FILLER", s4_stat, s4_col,
         [("Bottle Present", "Yes" if bp else "No"), ("Fill Valve", "OPEN" if fc else "CLOSED"),
          ("Fill Timer", f"{config.FILL_DURATION_TICKS} ticks"),
          ("Status", "Filling" if (fc and bp) else "Waiting")],
         f"Fill duration: {config.FILL_DURATION_TICKS} ticks · Bottle cycle: {config.BOTTLE_CYCLE_TICKS} ticks"),
        ("S5", "CAPPER", s5_stat, s5_col,
         [("Bottles Capped", str(bc)), ("Conveyor", f"{cvc:.0f} %"),
          ("Capper", "ENGAGED" if cvc > 0 else "STOPPED"),
          ("Cycle", f"{config.BOTTLE_CYCLE_TICKS} ticks/bottle")],
         f"Conveyor cycle: {config.BOTTLE_CYCLE_TICKS} ticks · Speed: proportional 0-100%"),
    ]
    for col, (sid, name, stat, clr, rows, req) in zip(cols, cards):
        with col:
            st.markdown(stage_card(sid, name, stat, clr, rows, req), unsafe_allow_html=True)

    # ── KPI Row ──
    st.markdown('<div class="section-label">Production Summary</div>', unsafe_allow_html=True)
    kc1, kc2, kc3, kc4, kc5, kc6 = st.columns(6)
    kc1.markdown(kpi_card("TANK LEVEL", f"{level:.1f}", "%", C_RUN,
                           f"Target: {config.TANK_LEVEL_LOW:.0f}–{config.TANK_LEVEL_HIGH:.0f}%"), unsafe_allow_html=True)
    kc2.markdown(kpi_card("PASTEUR TEMP", f"{temp:.1f}", "°C", C_RUN if s2_temp_ok else C_FLT,
                           f"SP: {config.PASTEUR_SETPOINT:.0f}°C  Safe: {config.PASTEUR_SAFE_MIN:.0f}–{config.PASTEUR_SAFE_MAX:.0f}°C"), unsafe_allow_html=True)
    kc3.markdown(kpi_card("COOLER TEMP", f"{cool:.1f}", "°C", C_COOL if cool > config.COOLER_MAX_BOTTLING else C_RUN,
                           f"Target: {config.COOLER_SETPOINT:.0f}°C  Max bottling: {config.COOLER_MAX_BOTTLING:.0f}°C"), unsafe_allow_html=True)
    kc4.markdown(kpi_card("FLOW RATE", f"{flow:.1f}", "L/min", C_RUN if flow > 0 else C_OFF,
                           f"Feed Pump: {'ON' if pc > 0 else 'OFF'}"), unsafe_allow_html=True)
    kc5.markdown(kpi_card("BOTTLES", str(bc), "capped", C_WARN if bc > 0 else C_OFF,
                           f"Conveyor: {cvc:.0f}%"), unsafe_allow_html=True)
    kc6.markdown(kpi_card("PLC STATE", plc_state, "", C_RUN if plc_state == "RUNNING" else (C_FLT if plc_state == "FAULT" else C_WARN),
                           f"Tick #{latest.get('tick', 0)}"), unsafe_allow_html=True)


live_view()

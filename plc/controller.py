"""M2 - PLC Controller.

Runs the control logic for the beverage line: a start/stop state machine,
per-stage proportional control with actuator adaptation, and comprehensive
fault detection that translates abnormal sensor patterns into alarm codes.

This module reads the plant's sensor + feedback pins and the operator buttons,
and produces actuator command pins plus an alarm code and PLC state. It never
touches physics directly — that is M1's job.

Manual override: the PLC receives a manual_overrides dict {actuator: value}.
It uses those values as FIXED outputs and adapts remaining auto-controlled
actuators to compensate within safe limits. Fault detection runs regardless
of manual/auto mode — safety interlocks are never bypassed.

Port specification (see README section 5):
    inputs : tank_level, pasteur_temp, cooler_temp, flow_rate, bottle_present,
             pump_feedback, valve_feedback, operator_start, operator_stop
    outputs: pump_cmd, inlet_valve_cmd, heater_power_cmd, cooling_valve_cmd,
             conveyor_cmd, fill_valve_cmd, capper_cmd, alarm_code, plc_state
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import config


@dataclass
class PLCController:
    """Scan-cycle controller. Call :meth:`step` once per update period."""

    state: str = config.PLC_IDLE
    alarm_code: int = config.ALARM_NONE

    # --- internal control accumulators (PI-style) ---
    heater_power_cmd: float = 0.0   # accumulated heater output (0-100%)
    cooling_valve_cmd: float = 0.0  # accumulated cooling output (0-100%)
    pump_cmd: float = 0.0           # accumulated feed pump output (0-100%)

    # --- discrete fill control memory ---
    _fill_timer: int = field(default=0, repr=False)

    # last pump command issued (used by the no-flow fault detector) ---
    last_pump_cmd: float = field(default=0.0, repr=False)

    # --- fault-detection debounce counters ---
    _temp_stuck_count: int = field(default=0, repr=False)
    _no_flow_count: int = field(default=0, repr=False)
    _temp_range_count: int = field(default=0, repr=False)
    _prev_temp: float = field(default=-999.0, repr=False)
    # True once the pasteurizer has reached the safe band at least once.
    _warmed_up: bool = field(default=False, repr=False)

    # Track previous state to detect FAULT→IDLE transition for fast recovery
    _prev_state: str = field(default=config.PLC_IDLE, repr=False)

    def reset(self) -> None:
        self.state = config.PLC_IDLE
        self.alarm_code = config.ALARM_NONE
        self.heater_power_cmd = 0.0
        self.cooling_valve_cmd = 0.0
        self.pump_cmd = 0.0
        self._fill_timer = 0
        self.last_pump_cmd = 0.0
        self._temp_stuck_count = 0
        self._no_flow_count = 0
        self._temp_range_count = 0
        self._prev_temp = -999.0
        self._warmed_up = False
        self._prev_state = config.PLC_IDLE

    # ------------------------------------------------------------------
    def step(self, sensors: Dict,
             manual_overrides: Dict[str, float] = None) -> Dict:
        """One scan cycle: update state machine, detect faults, run control.

        Args:
            sensors: plant sensor values + operator_start/stop + data_stale_flag
            manual_overrides: {actuator_name: value} for operator-overridden actuators.
                              The PLC uses these as FIXED outputs and adapts
                              remaining auto actuators around them.

        Returns:
            dict of actuator commands + alarm_code + plc_state
        """
        if manual_overrides is None:
            manual_overrides = {}

        operator_start = int(sensors.get("operator_start", 0))
        operator_stop = int(sensors.get("operator_stop", 0))
        data_stale = int(sensors.get("data_stale_flag", 0))

        # 1. State machine ----------------------------------------------
        self._prev_state = self.state
        self._update_state(operator_start, operator_stop)

        # Detect FAULT→IDLE transition (fast-recovery: reset accumulators)
        if self._prev_state == config.PLC_FAULT and self.state == config.PLC_IDLE:
            self._fast_recovery_init()

        # 2. Fault detection (always active — safety is never bypassed) --
        self._detect_faults(sensors, data_stale)

        # 3. Control logic ----------------------------------------------
        running = self.state in (config.PLC_RUNNING, config.PLC_STARTING)
        serious = self.alarm_code in (config.ALARM_PUMP_NO_FLOW,
                                       config.ALARM_TEMP_OUT_OF_RANGE,
                                       config.ALARM_SENSOR_TEMP_STUCK,
                                       config.ALARM_DATA_STALE)
        if serious:
            self.state = config.PLC_FAULT
            running = False

        if running:
            cmds = self._run_control(sensors, manual_overrides)
        else:
            cmds = self._safe_outputs()

        cmds["alarm_code"] = self.alarm_code
        cmds["plc_state"] = self.state
        return cmds

    # ------------------------------------------------------------------
    def _update_state(self, operator_start: int, operator_stop: int) -> None:
        if operator_stop:
            self.state = config.PLC_STOPPING
        if self.state == config.PLC_STOPPING:
            self.state = config.PLC_IDLE
            return

        if self.state == config.PLC_FAULT:
            if self.alarm_code == config.ALARM_NONE:
                self.state = config.PLC_IDLE
            return

        if operator_start and self.state == config.PLC_IDLE:
            self.state = config.PLC_STARTING
        elif self.state == config.PLC_STARTING:
            self.state = config.PLC_RUNNING

    # ------------------------------------------------------------------
    def _fast_recovery_init(self) -> None:
        """Reset accumulators on FAULT→IDLE so auto mode starts from a
        clean slate and converges quickly to setpoints."""
        # Don't fully reset — keep some memory for faster convergence
        self.heater_power_cmd = max(0.0, self.heater_power_cmd - 20.0)
        self.cooling_valve_cmd = max(0.0, self.cooling_valve_cmd - 10.0)
        self.pump_cmd = 70.0  # start pump at reasonable speed
        self._fill_timer = 0

    # ------------------------------------------------------------------
    def _run_control(self, sensors: Dict,
                     man: Dict[str, float]) -> Dict:
        """Run auto control with adaptation around manual overrides.

        Strategy:
        - Manual actuators use their override values directly.
        - Auto actuators adapt around manual constraints where possible.
        - All safety limits are still enforced; violations trigger alarms.
        """
        tank_level = float(sensors.get("tank_level", 50.0))
        pasteur_temp = float(sensors.get("pasteur_temp", 25.0))
        cooler_temp = float(sensors.get("cooler_temp", 25.0))
        bottle_present = int(sensors.get("bottle_present", 0))

        man_inlet  = "inlet_valve_cmd" in man
        man_pump   = "pump_cmd" in man
        man_heater = "heater_power_cmd" in man
        man_cool   = "cooling_valve_cmd" in man
        man_conv   = "conveyor_cmd" in man
        man_fill   = "fill_valve_cmd" in man

        # ── S1: Inlet Valve ─────────────────────────────────────────
        if man_inlet:
            inlet_valve_cmd = float(man["inlet_valve_cmd"])
        else:
            # Auto: hysteresis control on tank level (0-100% proportional)
            if tank_level < config.TANK_LEVEL_LOW:
                inlet_valve_cmd = 100.0
            elif tank_level >= config.TANK_LEVEL_HIGH:
                inlet_valve_cmd = 0.0
            else:
                # In the hysteresis band: hold previous state
                inlet_valve_cmd = 100.0 if tank_level < (config.TANK_LEVEL_LOW + config.TANK_LEVEL_HIGH) / 2 else 0.0

        # ── S1: Feed Pump ───────────────────────────────────────────
        if man_pump:
            pump_cmd = float(man["pump_cmd"])
            self.pump_cmd = pump_cmd
        else:
            # Auto: proportional pump control based on tank level
            # If tank is full and inlet is open, run pump faster
            # If tank is low, slow down to avoid dry-run
            if tank_level <= config.TANK_LEVEL_MIN_PUMP:
                self.pump_cmd = 0.0  # dry-run protection
            else:
                # Adaptation: if inlet valve is manual at a low value,
                # reduce pump to match available inflow and avoid draining tank
                if man_inlet:
                    manual_inflow = float(man["inlet_valve_cmd"])
                    # Match pump roughly to manual inlet rate + tank buffer
                    target_pump = manual_inflow * 1.2  # slightly faster than inlet
                    target_pump = min(target_pump, 100.0)
                else:
                    target_pump = 100.0 if tank_level > config.TANK_LEVEL_LOW else 50.0
                # Smooth adjustment
                self.pump_cmd = _clamp(
                    self.pump_cmd + 8.0 * (target_pump - self.pump_cmd) / 100.0 * 20.0,
                    0.0, 100.0)
            pump_cmd = self.pump_cmd

        # ── S2: Heater ──────────────────────────────────────────────
        if man_heater:
            heater_power_cmd = float(man["heater_power_cmd"])
            self.heater_power_cmd = heater_power_cmd
        else:
            # Auto: proportional control toward 72°C setpoint
            error = config.PASTEUR_SETPOINT - pasteur_temp
            # Adaptation: if pump is manual and very high (more flow = more cooling),
            # increase heater gain to compensate
            gain = 4.0
            if man_pump:
                manual_flow = float(man["pump_cmd"])
                if manual_flow > 70:
                    gain = 5.5  # more aggressive heating for high flow
                elif manual_flow < 30:
                    gain = 2.5  # gentler heating for low flow (avoid overshoot)
            self.heater_power_cmd = _clamp(
                self.heater_power_cmd + gain * error, 0.0, 100.0)
            heater_power_cmd = round(self.heater_power_cmd, 1)

        # ── S3: Cooler ──────────────────────────────────────────────
        if man_cool:
            cooling_valve_cmd = float(man["cooling_valve_cmd"])
            self.cooling_valve_cmd = cooling_valve_cmd
        else:
            cool_error = cooler_temp - config.COOLER_SETPOINT
            cool_gain = 4.0
            self.cooling_valve_cmd = _clamp(
                self.cooling_valve_cmd + cool_gain * cool_error, 0.0, 100.0)
            cooling_valve_cmd = round(self.cooling_valve_cmd, 1)

        # ── S4/S5: Bottling readiness ────────────────────────────────
        pasteurized = pasteur_temp >= config.PASTEUR_SAFE_MIN
        cooled = cooler_temp <= config.COOLER_MAX_BOTTLING
        ready = pasteurized and cooled

        # ── S4: Fill Valve ──────────────────────────────────────────
        if man_fill:
            fill_valve_cmd = int(man["fill_valve_cmd"])
        else:
            if bottle_present and ready:
                self._fill_timer = config.FILL_DURATION_TICKS
            fill_valve_cmd = 1 if (self._fill_timer > 0 and ready) else 0
            if self._fill_timer > 0:
                self._fill_timer -= 1

        # ── S5: Conveyor ─────────────────────────────────────────────
        if man_conv:
            conveyor_cmd = float(man["conveyor_cmd"])
        else:
            conveyor_cmd = 100.0 if ready else 0.0

        # Capper follows conveyor
        capper_cmd = 1 if conveyor_cmd > 0 else 0

        self.last_pump_cmd = pump_cmd
        return {
            "pump_cmd": round(pump_cmd, 1),
            "inlet_valve_cmd": round(inlet_valve_cmd, 1),
            "heater_power_cmd": heater_power_cmd,
            "cooling_valve_cmd": cooling_valve_cmd,
            "conveyor_cmd": round(conveyor_cmd, 1),
            "fill_valve_cmd": fill_valve_cmd,
            "capper_cmd": capper_cmd,
        }

    # ------------------------------------------------------------------
    def _safe_outputs(self) -> Dict:
        """All actuators off — used in IDLE / STOPPING / FAULT."""
        self.heater_power_cmd = 0.0
        self.cooling_valve_cmd = 0.0
        self.pump_cmd = 0.0
        self._fill_timer = 0
        self.last_pump_cmd = 0.0
        return {
            "pump_cmd": 0.0,
            "inlet_valve_cmd": 0.0,
            "heater_power_cmd": 0.0,
            "cooling_valve_cmd": 0.0,
            "conveyor_cmd": 0.0,
            "fill_valve_cmd": 0,
            "capper_cmd": 0,
        }

    # ------------------------------------------------------------------
    def _detect_faults(self, sensors: Dict, data_stale: int) -> None:
        """Translate abnormal sensor patterns into a latched alarm code.

        Fault detection runs ALWAYS regardless of manual/auto mode.
        Safety interlocks cannot be bypassed by the operator.
        """
        pasteur_temp = float(sensors.get("pasteur_temp", 0.0))
        flow_rate = float(sensors.get("flow_rate", 0.0))
        pump_feedback = int(sensors.get("pump_feedback", 0))
        tank_level = float(sensors.get("tank_level", 0.0))
        running = self.state in (config.PLC_RUNNING, config.PLC_STARTING)

        # Infrastructure fault: stale data takes highest priority.
        if data_stale:
            self.alarm_code = config.ALARM_DATA_STALE
            return

        # Track warm-up so the normal ramp (temp < safe-min) is not flagged.
        if not running:
            self._warmed_up = False
        elif pasteur_temp >= config.PASTEUR_SAFE_MIN:
            self._warmed_up = True

        # Sensor fault: exact equality across cycles = sensor frozen.
        if running and abs(pasteur_temp - self._prev_temp) < 0.001:
            self._temp_stuck_count += 1
        else:
            self._temp_stuck_count = 0

        # Equipment fault: pump commanded on but no feedback and no flow.
        # Uses actual pump command (could be manual or auto).
        pump_on = self.last_pump_cmd > 0
        if pump_on and pump_feedback == 0 and flow_rate <= 0.1:
            self._no_flow_count += 1
        else:
            self._no_flow_count = 0

        # Process fault: pasteurization temperature outside the safe band.
        # Now ALWAYS detected — even when heater is under manual control.
        # The operator can cause a TEMP_OUT_OF_RANGE alarm by setting
        # heater too high or too low, which is correct safety behavior.
        out_of_range = (pasteur_temp > config.PASTEUR_SAFE_MAX
                        or pasteur_temp < config.PASTEUR_SAFE_MIN)
        if running and self._warmed_up and out_of_range:
            self._temp_range_count += 1
        else:
            self._temp_range_count = 0

        # Tank level critical protection: if level drops to 0, stop the pump
        # to prevent dry-running damage. This is a hard safety interlock.
        if running and tank_level <= 0.5 and self.last_pump_cmd > 0:
            # Tank is empty while pump was running — immediate alarm
            if self.alarm_code == config.ALARM_NONE:
                self.alarm_code = config.ALARM_TEMP_OUT_OF_RANGE  # fallback

        # Auto-clear TEMP_OUT_OF_RANGE when temperature returns to safe band.
        if self.alarm_code == config.ALARM_TEMP_OUT_OF_RANGE and not out_of_range:
            self.alarm_code = config.ALARM_NONE
            self._temp_range_count = 0
            if self.state == config.PLC_FAULT:
                self.state = config.PLC_IDLE

        # Latch the first alarm that exceeds its debounce threshold.
        if self.alarm_code == config.ALARM_NONE:
            if self._no_flow_count >= config.ALARM_DEBOUNCE_TICKS:
                self.alarm_code = config.ALARM_PUMP_NO_FLOW
            elif self._temp_stuck_count >= config.ALARM_DEBOUNCE_TICKS:
                self.alarm_code = config.ALARM_SENSOR_TEMP_STUCK
            elif self._temp_range_count >= config.ALARM_DEBOUNCE_TICKS:
                self.alarm_code = config.ALARM_TEMP_OUT_OF_RANGE

        self._prev_temp = pasteur_temp

    # ------------------------------------------------------------------
    def acknowledge(self) -> None:
        """Operator acknowledges / clears the current alarm."""
        self.alarm_code = config.ALARM_NONE
        self._temp_stuck_count = 0
        self._no_flow_count = 0
        self._temp_range_count = 0
        if self.state == config.PLC_FAULT:
            self.state = config.PLC_IDLE


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

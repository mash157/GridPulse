#!/usr/bin/env python
"""
GridPulse Streaming Service
Generates live telemetry events for WebSocket delivery
"""

import uuid
import random
import time
from datetime import datetime
from typing import Dict, Any

import numpy as np


# Grid topology (shared with data generation)
REGIONS = ["North", "South", "East", "West", "Central", "North-East"]

SUBSTATION_COORDS = {
    "SUB-001": {"region": "North", "name": "Delhi"},
    "SUB-002": {"region": "North", "name": "Jaipur"},
    "SUB-003": {"region": "North", "name": "Jammu"},
    "SUB-004": {"region": "North", "name": "Lucknow"},
    "SUB-005": {"region": "West", "name": "Mumbai"},
    "SUB-006": {"region": "West", "name": "Ahmedabad"},
    "SUB-007": {"region": "West", "name": "Pune"},
    "SUB-008": {"region": "South", "name": "Chennai"},
    "SUB-009": {"region": "South", "name": "Hyderabad"},
    "SUB-010": {"region": "South", "name": "Bengaluru"},
    "SUB-011": {"region": "East", "name": "Kolkata"},
    "SUB-012": {"region": "East", "name": "Bhopal"},
    "SUB-013": {"region": "East", "name": "Nagpur"},
    "SUB-014": {"region": "Central", "name": "Varanasi"},
    "SUB-015": {"region": "Central", "name": "Prayagraj"},
    "SUB-016": {"region": "Central", "name": "Jhansi"},
    "SUB-017": {"region": "North-East", "name": "Meerut"},
    "SUB-018": {"region": "North-East", "name": "Panipat"},
    "SUB-019": {"region": "West", "name": "Indore"},
    "SUB-020": {"region": "East", "name": "Varanasi East"},
    "SUB-021": {"region": "West", "name": "Thane"},
    "SUB-022": {"region": "South", "name": "Hubli"},
    "SUB-023": {"region": "East", "name": "Jabalpur"},
    "SUB-024": {"region": "North", "name": "Bareilly"},
    "SUB-025": {"region": "West", "name": "Jaipur West"},
    "SUB-026": {"region": "South", "name": "Warangal"},
    "SUB-027": {"region": "North-East", "name": "Rohtak"},
    "SUB-028": {"region": "Central", "name": "Raipur"},
}

TRANSFORMERS_PER_SUBSTATION = 20

# Build transformer maps
T2S = {}
T2R = {}
TRANSFORMER_IDS = []

for sid, info in SUBSTATION_COORDS.items():
    for i in range(1, TRANSFORMERS_PER_SUBSTATION + 1):
        tid = f"TR-{sid.split('-')[1]}{i:03d}"
        T2S[tid] = sid
        T2R[tid] = info["region"]
        TRANSFORMER_IDS.append(tid)

BASE_VOLTAGE = 40.0
BASE_CURRENT = 50.0
BASE_LOAD = 60.0
BASE_FREQ = 50.0
BASE_PF = 0.95
BASE_TEMP = 45.0
ANOMALY_PROB = 0.15


class StreamingService:
    """Generates live telemetry events."""

    def __init__(self):
        self.rng = np.random.default_rng(seed=int(time.time()))

    def generate_live_event(self) -> Dict[str, Any]:
        """Generate a single live telemetry event."""
        tid = TRANSFORMER_IDS[self.rng.integers(0, len(TRANSFORMER_IDS))]
        sid = T2S[tid]
        region = T2R[tid]
        now = datetime.now()
        hour = now.hour

        # Diurnal pattern
        diurnal = 0.7 + 0.6 * np.sin(np.pi * (hour - 6) / 12) if 6 <= hour <= 18 else 0.5
        xfmr = self.rng.uniform(0.85, 1.15)

        # Generate telemetry
        load = float(np.clip(BASE_LOAD * diurnal * xfmr + self.rng.normal(0, 6), 15, 100))
        force = self.rng.random() < ANOMALY_PROB
        if force:
            load = min(load + self.rng.uniform(10, 25), 100)

        current = BASE_CURRENT * (load / BASE_LOAD) + self.rng.normal(0, 4)
        voltage = float(np.clip(BASE_VOLTAGE + self.rng.normal(0, 2), 35, 45))
        if force:
            voltage = float(np.clip(BASE_VOLTAGE + self.rng.uniform(-4, 4), 35, 45))

        freq = float(np.clip(BASE_FREQ + self.rng.normal(0, 0.1), 49.5, 50.5))
        pf = float(np.clip(BASE_PF - 0.08 * (load / 100) + self.rng.normal(0, 0.03), 0.65, 1.0))
        power = (voltage * max(current, 5) * pf) / 1000
        temp = float(np.clip(BASE_TEMP + (load - BASE_LOAD) * 0.25 + self.rng.normal(0, 2), 38, 85))
        if force:
            temp = min(temp + self.rng.uniform(10, 25), 85)

        fault_prob = 0.005
        if load > 90 or temp > 70 or voltage < 36:
            fault_prob = 0.12
        if force:
            fault_prob = min(fault_prob + 0.2, 0.5)
        fault = 1 if self.rng.random() < fault_prob else 0

        # Anomaly score
        anomaly_score = 0.0
        if fault:
            anomaly_score = self.rng.uniform(0.7, 0.95)
        elif load > 85 or temp > 65:
            anomaly_score = self.rng.uniform(0.3, 0.6)

        # Risk score
        risk_score = 0
        if load > 90: risk_score += 20
        elif load > 80: risk_score += 15
        elif load > 70: risk_score += 10
        if temp > 75: risk_score += 20
        elif temp > 70: risk_score += 15
        elif temp > 65: risk_score += 10
        if abs(voltage - 40) > 4: risk_score += 15
        elif abs(voltage - 40) > 3: risk_score += 12
        if fault: risk_score += 15
        risk_score = min(100, risk_score)

        # Status
        if risk_score >= 70: status = "Critical"
        elif risk_score >= 50: status = "High Risk"
        elif risk_score >= 25: status = "Warning"
        else: status = "Normal"

        # Anomaly type
        anomaly_type = "Normal"
        if status != "Normal":
            if load > 90 and temp > 70: anomaly_type = "Compound Anomaly"
            elif load > 90: anomaly_type = "Overload"
            elif temp > 65: anomaly_type = "Temperature Spike"
            elif abs(voltage - 40) > 4: anomaly_type = "Voltage Fluctuation"
            elif abs(freq - 50) > 0.25: anomaly_type = "Frequency Deviation"
            elif pf < 0.75: anomaly_type = "Power Factor Anomaly"
            else:
                anomaly_type = random.choice([
                    "Voltage Fluctuation", "Overload", "Temperature Spike",
                    "Frequency Deviation", "Power Factor Anomaly",
                ])

        # Message for live feed
        messages = {
            "Normal": f"Normal operation at {SUBSTATION_COORDS[sid]['name']}",
            "Warning": f"Warning: {anomaly_type} at {sid}",
            "High Risk": f"High Risk: {anomaly_type} at {sid}",
            "Critical": f"⚠ Critical: {anomaly_type} at {sid}",
        }

        return {
            "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
            "timestamp": now.isoformat(),
            "region": region,
            "substation_id": sid,
            "transformer_id": tid,
            "voltage_kv": round(voltage, 2),
            "current_amp": round(max(current, 5), 2),
            "power_mw": round(power, 2),
            "frequency_hz": round(freq, 2),
            "load_percent": round(load, 2),
            "power_factor": round(pf, 4),
            "temperature_c": round(temp, 2),
            "fault_indicator": fault,
            "anomaly_score": round(anomaly_score, 4),
            "risk_score": risk_score,
            "status": status,
            "anomaly_type": anomaly_type,
            "message": messages.get(status, ""),
        }

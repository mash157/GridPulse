#!/usr/bin/env python
"""
GridPulse Data Generator (Configurable)

Generates realistic smart-grid telemetry records with configurable
status distributions and anomaly variety.

The status is derived from underlying electrical conditions rather
than randomly assigned. Anomaly types are mapped to realistic
measurement patterns.

Environment-variable / CLI configurable ratios:
  NORMAL_RATIO, WARNING_RATIO, HIGH_RISK_RATIO, CRITICAL_RATIO
  ANOMALY_RATIO — probability that any given record is anomalous
"""

import argparse
import os
import sys
import zlib
from datetime import datetime, timedelta
from typing import List, Dict, Any

import numpy as np
import pandas as pd


# ── Configurable target ratios ────────────────────────────────────────
# 5-band status mapping: 0-29 Normal, 30-49 Low, 50-69 Warning,
# 70-84 High Risk, 85-100 Critical.
# Donut targets (Low folds into Normal): Normal ~55-65%, Warning ~18-22%,
# High Risk ~10-15%, Critical ~5-8%.
DEFAULT_NORMAL_RATIO = 0.57
DEFAULT_LOW_RATIO = 0.07
DEFAULT_WARNING_RATIO = 0.21
DEFAULT_HIGH_RISK_RATIO = 0.10
DEFAULT_CRITICAL_RATIO = 0.05
DEFAULT_ANOMALY_RATIO = 0.30  # fraction of records that carry an anomaly type

# Per-transformer asset condition spread. Each transformer gets a stable
# condition factor drawn from N(1, CONDITION_STD) clipped to a sane range.
# Healthy assets (condition < 1) lean Normal/Low; aging/stressed assets
# (condition > 1) lean Warning/High Risk/Critical — this is what spreads
# the *transformer-level* status distribution across all five bands.
#
# The bucket-selection weights are compensated by the inverse of the
# expected distortion E[exp(k*(level-2)*(condition-1))], so the overall
# RECORD-level distribution still equals DEFAULT_*_RATIO while individual
# transformers' mixes diverge (the transformer-level spread). A small risk
# offset then nudges stressed assets up within their band without pushing
# whole buckets into the adjacent band.
CONDITION_STD = 0.35
CONDITION_MIN = 0.5
CONDITION_MAX = 2.05
CONDITION_RISK_OFFSET = 6.0  # risk-score points added per unit of (condition - 1)
CONDITION_WEIGHT_SENSITIVITY = 1.8  # how strongly condition shifts bucket selection


# ── Grid hierarchy configuration ─────────────────────────────────────
REGIONS = ["North", "South", "East", "West", "Central", "North-East"]

SUBSTATION_COORDS = {
    "SUB-001": {"lat": 28.6139, "lon": 77.2090, "region": "North"},
    "SUB-002": {"lat": 26.9124, "lon": 75.7873, "region": "North"},
    "SUB-003": {"lat": 32.3246, "lon": 74.7901, "region": "North"},
    "SUB-004": {"lat": 25.2048, "lon": 77.3948, "region": "North"},
    "SUB-005": {"lat": 19.0760, "lon": 72.8777, "region": "West"},
    "SUB-006": {"lat": 23.0225, "lon": 72.5799, "region": "West"},
    "SUB-007": {"lat": 18.5204, "lon": 73.8567, "region": "West"},
    "SUB-008": {"lat": 13.0827, "lon": 80.2707, "region": "South"},
    "SUB-009": {"lat": 17.3850, "lon": 78.4867, "region": "South"},
    "SUB-010": {"lat": 12.9716, "lon": 77.5946, "region": "South"},
    "SUB-011": {"lat": 22.5726, "lon": 88.3639, "region": "East"},
    "SUB-012": {"lat": 23.2599, "lon": 77.4126, "region": "East"},
    "SUB-013": {"lat": 21.1466, "lon": 79.0882, "region": "East"},
    "SUB-014": {"lat": 26.8206, "lon": 80.2701, "region": "Central"},
    "SUB-015": {"lat": 25.3948, "lon": 79.4625, "region": "Central"},
    "SUB-016": {"lat": 24.8688, "lon": 76.6562, "region": "Central"},
    "SUB-017": {"lat": 28.2960, "lon": 76.5920, "region": "North-East"},
    "SUB-018": {"lat": 29.0588, "lon": 76.0231, "region": "North-East"},
    "SUB-019": {"lat": 22.3167, "lon": 78.0300, "region": "West"},
    "SUB-020": {"lat": 25.5941, "lon": 82.4720, "region": "East"},
    "SUB-021": {"lat": 19.6776, "lon": 72.7323, "region": "West"},
    "SUB-022": {"lat": 15.2993, "lon": 74.1240, "region": "South"},
    "SUB-023": {"lat": 21.2787, "lon": 82.1406, "region": "East"},
    "SUB-024": {"lat": 26.7461, "lon": 78.9824, "region": "North"},
    "SUB-025": {"lat": 24.4781, "lon": 73.3114, "region": "West"},
    "SUB-026": {"lat": 17.3618, "lon": 78.5310, "region": "South"},
    "SUB-027": {"lat": 28.5355, "lon": 76.2346, "region": "North-East"},
    "SUB-028": {"lat": 20.2884, "lon": 76.2009, "region": "Central"},
    "SUB-029": {"lat": 26.9124, "lon": 75.7873, "region": "North"},
}

TRANSFORMERS_PER_SUBSTATION = 20

# ── Base electrical parameters ────────────────────────────────────────
BASE_VOLTAGE_KV = 40.0
BASE_CURRENT_AMP = 50.0
BASE_LOAD_PERCENT = 55.0
BASE_FREQUENCY_HZ = 50.0
BASE_POWER_FACTOR = 0.95
BASE_TEMPERATURE_C = 43.0
BASE_LATENCY_MS = 5.0


def generate_transformer_ids() -> List[str]:
    """Generate transformer IDs for all substations."""
    transformer_ids = []
    for substation_id in SUBSTATION_COORDS.keys():
        for i in range(1, TRANSFORMERS_PER_SUBSTATION + 1):
            transformer_ids.append(f"TR-{substation_id.split('-')[1]}{i:03d}")
    return transformer_ids


def get_transformer_to_substation_map() -> Dict[str, str]:
    """Create mapping from transformer ID to substation ID."""
    mapping = {}
    for substation_id in SUBSTATION_COORDS.keys():
        for i in range(1, TRANSFORMERS_PER_SUBSTATION + 1):
            transformer_id = f"TR-{substation_id.split('-')[1]}{i:03d}"
            mapping[transformer_id] = substation_id
    return mapping


def get_transformer_to_region_map() -> Dict[str, str]:
    """Create mapping from transformer ID to region."""
    substation_to_region = {
        sid: info["region"] for sid, info in SUBSTATION_COORDS.items()
    }
    transformer_to_substation = get_transformer_to_substation_map()
    return {
        tid: substation_to_region[transformer_to_substation[tid]]
        for tid in transformer_to_substation.keys()
    }


# ── Anomaly-type assignment based on measurement conditions ──────────
# Each anomaly type has a characteristic "signature" that must match
# the underlying measurements in the record.  The generator creates
# the measurements first, then classifies the anomaly type.

ANOMALY_TYPES = [
    "Voltage Fluctuation",
    "Overload",
    "Temperature Spike",
    "Frequency Deviation",
    "Power Factor Anomaly",
    "Transformer Fault",
    "Communication Failure",
    "Unexpected Consumption",
    "Generation Drop",
    "Compound Anomaly",
]


def classify_anomaly_type(
    load: float,
    temp: float,
    voltage: float,
    frequency: float,
    pf: float,
    latency: float,
    energy_gen: float,
    energy_cons: float,
    fault: int,
    rng: np.random.Generator,
) -> str:
    """Classify the anomaly type from the actual measurement values.

    The conditions are hierarchical — the most severe / specific
    conditions are checked first.  This ensures that the anomaly
    label always corresponds to what the numbers actually show.
    """

    # Determine which measurements are abnormal
    abnormal_load = load > 82
    abnormal_temp = temp > 68
    abnormal_voltage = abs(voltage - BASE_VOLTAGE_KV) > 3.5
    abnormal_freq = abs(frequency - BASE_FREQUENCY_HZ) > 0.25
    abnormal_pf = pf < 0.78
    abnormal_latency = latency > 45
    has_fault = fault == 1

    # Count severe abnormalities (for compound detection)
    severe_indicators = sum([
        abnormal_load and load > 90,
        abnormal_temp and temp > 75,
        abnormal_voltage and abs(voltage - BASE_VOLTAGE_KV) > 4,
        abnormal_freq and abs(frequency - BASE_FREQUENCY_HZ) > 0.3,
        has_fault,
    ])

    # Compound: 3+ severe indicators
    if severe_indicators >= 3:
        return "Compound Anomaly"

    # --- Priority-based anomaly type assignment ---
    # Use weighted random selection among matching types
    candidates = []

    if has_fault and (abnormal_load or abnormal_temp):
        candidates.append(("Transformer Fault", 30))
    elif has_fault:
        candidates.append(("Transformer Fault", 10))

    if abnormal_load:
        candidates.append(("Overload", 25))

    if abnormal_temp:
        candidates.append(("Temperature Spike", 20))

    if abnormal_voltage:
        candidates.append(("Voltage Fluctuation", 22))

    if abnormal_freq:
        candidates.append(("Frequency Deviation", 18))

    if abnormal_pf:
        candidates.append(("Power Factor Anomaly", 15))

    if abnormal_latency:
        candidates.append(("Communication Failure", 20))

    # Unexpected consumption
    if energy_cons > 0 and energy_gen > 0:
        ratio = energy_cons / max(energy_gen, 1)
        if ratio > 1.25:
            candidates.append(("Unexpected Consumption", 15))

    # Generation drop
    if energy_gen > 0 and energy_gen < 80:
        candidates.append(("Generation Drop", 12))

    # Compound: 2+ severe indicators (lower threshold)
    if severe_indicators >= 2:
        candidates.append(("Compound Anomaly", 25))

    if not candidates:
        # Fallback: distribute evenly among all types
        weights = [0.12, 0.12, 0.12, 0.10, 0.10, 0.10, 0.10, 0.09, 0.08, 0.07]
        return rng.choice(ANOMALY_TYPES, p=weights)

    # Weighted random selection among candidates
    types, w = zip(*candidates)
    total_w = sum(w)
    probs = [x / total_w for x in w]
    return rng.choice(list(types), p=probs)


def compute_anomaly_score(
    load: float,
    temp: float,
    voltage: float,
    frequency: float,
    pf: float,
    latency: float,
    fault: int,
) -> float:
    """Compute a realistic anomaly score (0.0 - 1.0) from measurements."""
    score = 0.0

    # Load contribution (0-0.25)
    load_dev = max(0, (load - 70) / 30)
    score += load_dev * 0.25

    # Temperature contribution (0-0.25)
    temp_dev = max(0, (temp - 55) / 30)
    score += temp_dev * 0.25

    # Voltage deviation (0-0.20)
    v_dev = abs(voltage - BASE_VOLTAGE_KV) / 5
    score += v_dev * 0.20

    # Frequency deviation (0-0.10)
    f_dev = abs(frequency - BASE_FREQUENCY_HZ) / 0.5
    score += f_dev * 0.10

    # Power factor (0-0.10)
    pf_dev = max(0, (0.9 - pf) / 0.3)
    score += pf_dev * 0.10

    # Fault indicator (0-0.20)
    if fault:
        score += 0.20

    return round(min(score, 1.0), 4)


def compute_risk_score(
    anomaly_score: float,
    load: float,
    temp: float,
    voltage: float,
    frequency: float,
    fault: int,
    rng: np.random.Generator,
) -> int:
    """Compute a composite risk score (0-100) from measurements.

    Weights are calibrated from the actual per-bucket measurement profiles
    so each status bucket's median risk lands in its canonical band:
    Normal 0-29, Low 30-49, Warning 50-69, High Risk 70-84, Critical 85-100.
    """
    risk = 0.0

    # Load risk (starts above 20% load)
    risk += max(0, (load - 20) * 0.75)

    # Temperature risk (starts above 32C)
    risk += max(0, (temp - 32) * 0.35)

    # Voltage deviation risk (0-18)
    v_dev = abs(voltage - BASE_VOLTAGE_KV)
    risk += min(18, v_dev * 5.5)

    # Frequency deviation risk (0-15)
    f_dev = abs(frequency - BASE_FREQUENCY_HZ)
    risk += min(15, f_dev * 25.0)

    # Fault indicator bonus (10-12)
    if fault:
        risk += 10 + rng.uniform(0, 2)

    # Small random jitter
    risk += rng.uniform(-2, 2)

    return int(min(round(max(risk, 0)), 100))


def derive_status(risk_score: int) -> str:
    """Classify status from risk score using the canonical 5-band mapping:

    0-29 Normal, 30-49 Low, 50-69 Warning, 70-84 High Risk, 85-100 Critical.
    """
    if risk_score >= 85:
        return "Critical"
    elif risk_score >= 70:
        return "High Risk"
    elif risk_score >= 50:
        return "Warning"
    elif risk_score >= 30:
        return "Low"
    return "Normal"


STATUS_LEVELS = ["Normal", "Low", "Warning", "High Risk", "Critical"]

BASE_STATUS_WEIGHTS = np.array([
    DEFAULT_NORMAL_RATIO,
    DEFAULT_LOW_RATIO,
    DEFAULT_WARNING_RATIO,
    DEFAULT_HIGH_RISK_RATIO,
    DEFAULT_CRITICAL_RATIO,
])

# Numerical expected distortion of the selection weights caused by the
# spread of `condition` across transformers (convexity of exp() inflates
# the extreme levels). Dividing by this keeps the overall record mix equal
# to BASE_STATUS_WEIGHTS.
def _condition_distortion_factors() -> np.ndarray:
    rng = np.random.default_rng(0)
    cond = np.clip(
        rng.normal(1.0, CONDITION_STD, 200000),
        CONDITION_MIN, CONDITION_MAX,
    )
    levels = np.arange(len(STATUS_LEVELS))
    shift = np.exp(
        CONDITION_WEIGHT_SENSITIVITY * (levels[None, :] - 2) * (cond[:, None] - 1.0)
    )
    return shift.mean(axis=0)

CONDITION_DISTORTION = _condition_distortion_factors()


def transformer_condition(transformer_id: str) -> float:
    """Deterministic per-transformer asset condition factor.

    Drawn from N(1, CONDITION_STD) clipped to [CONDITION_MIN, CONDITION_MAX],
    seeded from crc32 so it is stable across runs (Python's built-in hash is
    salted per-process and cannot be used here).
    """
    seed = zlib.crc32(transformer_id.encode("utf-8"))
    rng = np.random.default_rng(seed)
    return float(np.clip(rng.normal(1.0, CONDITION_STD), CONDITION_MIN, CONDITION_MAX))


def generate_status_bucket(rng: np.random.Generator, condition: float = 1.0) -> str:
    """Pick a target status bucket according to the configured ratios.

    The per-transformer `condition` shifts the distribution: healthy assets
    (condition < 1) lean Normal/Low while aging/stressed assets (condition > 1)
    lean Warning/High Risk/Critical. Averaged over all assets the overall
    record distribution stays close to the configured ratios.
    """
    level_index = np.arange(len(STATUS_LEVELS))
    shift = np.exp(
        CONDITION_WEIGHT_SENSITIVITY * (level_index - 2) * (condition - 1.0)
    )
    # Divide by the average distortion so the overall record mix across all
    # transformers matches the configured ratios regardless of condition spread.
    weights = BASE_STATUS_WEIGHTS * shift / CONDITION_DISTORTION
    weights = weights / weights.sum()
    return str(rng.choice(STATUS_LEVELS, p=weights))


def generate_telemetry_record(
    event_id: int,
    timestamp: datetime,
    transformer_id: str,
    transformer_to_substation: Dict[str, str],
    transformer_to_region: Dict[str, str],
    substation_coords: Dict[str, Dict],
    rng: np.random.Generator,
) -> Dict[str, Any]:
    """Generate a single telemetry record conditioned on a target status bucket.

    The target bucket influences the measurement ranges so that
    the resulting risk_score and status naturally land in the
    desired distribution.
    """

    substation_id = transformer_to_substation[transformer_id]
    region = transformer_to_region[transformer_id]
    coords = substation_coords[substation_id]

    # Stable per-transformer asset condition (spreads the transformer-level
    # status distribution across all five bands).
    condition = transformer_condition(transformer_id)
    target_status = generate_status_bucket(rng, condition)

    # ── Diurnal pattern ──────────────────────────────────────────────
    hour = timestamp.hour
    diurnal_factor = (
        0.7 + 0.6 * np.sin(np.pi * (hour - 6) / 12)
        if 6 <= hour <= 18
        else 0.4
    )
    transformer_factor = rng.uniform(0.85, 1.15)

    # ── Generate measurements conditioned on target status ───────────
    # Each bucket's measurement windows are kept tight around its band so
    # the derived risk_score (and therefore status) stays inside the band.
    if target_status == "Normal":
        # Healthy conditions — everything near nominal
        load = float(np.clip(
            BASE_LOAD_PERCENT * diurnal_factor * transformer_factor + rng.normal(0, 5),
            15, 48
        ))
        voltage = float(np.clip(BASE_VOLTAGE_KV + rng.normal(0, 0.9), 39.0, 41.0))
        frequency = float(np.clip(BASE_FREQUENCY_HZ + rng.normal(0, 0.06), 49.90, 50.10))
        pf = float(np.clip(BASE_POWER_FACTOR - 0.03 * (load / 100) + rng.normal(0, 0.02), 0.90, 1.0))
        temp = float(np.clip(BASE_TEMPERATURE_C + (load - BASE_LOAD_PERCENT) * 0.12 + rng.normal(0, 1.5), 35, 50))
        latency = float(np.clip(rng.exponential(BASE_LATENCY_MS) + 1, 0.5, 12))
        fault = 0

    elif target_status == "Low":
        # Mild deviations — a few readings just outside nominal
        load = float(np.clip(
            BASE_LOAD_PERCENT * diurnal_factor * transformer_factor + rng.uniform(4, 12),
            40, 66
        ))
        voltage = float(np.clip(BASE_VOLTAGE_KV + rng.normal(0, 1.6), 37.5, 42.5))
        frequency = float(np.clip(BASE_FREQUENCY_HZ + rng.normal(0, 0.10), 49.80, 50.20))
        pf = float(np.clip(BASE_POWER_FACTOR - 0.06 * (load / 100) + rng.normal(0, 0.03), 0.85, 0.97))
        temp = float(np.clip(BASE_TEMPERATURE_C + (load - BASE_LOAD_PERCENT) * 0.22 + rng.normal(0, 2), 44, 60))
        latency = float(np.clip(rng.exponential(6) + 2, 0.5, 22))
        fault = 1 if rng.random() < 0.01 else 0

    elif target_status == "Warning":
        # Moderate deviations — some readings clearly outside normal range
        load = float(np.clip(
            BASE_LOAD_PERCENT * diurnal_factor * transformer_factor + rng.uniform(14, 30),
            58, 84
        ))
        voltage = float(np.clip(
            BASE_VOLTAGE_KV + rng.choice([-1, 1]) * rng.uniform(2.2, 3.6),
            35, 45
        ))
        frequency = float(np.clip(
            BASE_FREQUENCY_HZ + rng.choice([-1, 1]) * rng.uniform(0.15, 0.26),
            49.68, 50.32
        ))
        pf = float(np.clip(BASE_POWER_FACTOR - 0.10 * (load / 100) + rng.normal(0, 0.05), 0.74, 0.90))
        temp = float(np.clip(BASE_TEMPERATURE_C + (load - BASE_LOAD_PERCENT) * 0.32 + rng.normal(0, 3), 50, 68))
        latency = float(np.clip(rng.exponential(10) + 3, 0.5, 38))
        fault = 1 if rng.random() < 0.04 else 0

    elif target_status == "High Risk":
        # Multiple concerning readings — clearly above Warning
        load = float(np.clip(
            BASE_LOAD_PERCENT * diurnal_factor * transformer_factor + rng.uniform(16, 30),
            70, 90
        ))
        voltage = float(np.clip(
            BASE_VOLTAGE_KV + rng.choice([-1, 1]) * rng.uniform(2.4, 3.8),
            33, 46
        ))
        frequency = float(np.clip(
            BASE_FREQUENCY_HZ + rng.choice([-1, 1]) * rng.uniform(0.18, 0.30),
            49.60, 50.40
        ))
        pf = float(np.clip(BASE_POWER_FACTOR - 0.16 * (load / 100) + rng.normal(0, 0.07), 0.64, 0.84))
        temp = float(np.clip(BASE_TEMPERATURE_C + (load - BASE_LOAD_PERCENT) * 0.40 + rng.normal(0, 3.5), 56, 72))
        latency = float(np.clip(rng.exponential(15) + 4, 1, 55))
        fault = 1 if rng.random() < 0.15 else 0

    else:  # Critical
        # Severe conditions — multiple readings in danger zones
        load = float(np.clip(
            BASE_LOAD_PERCENT * diurnal_factor * transformer_factor + rng.uniform(28, 46),
            85, 100
        ))
        voltage = float(np.clip(
            BASE_VOLTAGE_KV + rng.choice([-1, 1]) * rng.uniform(3.4, 5.5),
            32, 48
        ))
        frequency = float(np.clip(
            BASE_FREQUENCY_HZ + rng.choice([-1, 1]) * rng.uniform(0.30, 0.45),
            49.48, 50.52
        ))
        pf = float(np.clip(BASE_POWER_FACTOR - 0.22 * (load / 100) + rng.normal(0, 0.09), 0.56, 0.78))
        temp = float(np.clip(BASE_TEMPERATURE_C + (load - BASE_LOAD_PERCENT) * 0.50 + rng.normal(0, 4), 63, 82))
        latency = float(np.clip(rng.exponential(22) + 6, 2, 90))
        fault = 1 if rng.random() < 0.30 else 0

    # ── Derived measurements ─────────────────────────────────────────
    current_amp = BASE_CURRENT_AMP * (load / BASE_LOAD_PERCENT) + rng.normal(0, 5)
    current_amp = max(current_amp, 5)
    power_mw = (voltage * current_amp * pf) / 1000

    # Energy: generated vs consumed (anomaly can create imbalance)
    energy_generated_mwh = power_mw * 0.95 + rng.normal(0, 50)
    energy_consumed_mwh = power_mw + rng.normal(0, 20)

    # For some Warning+ records, introduce consumption/generation imbalance
    if target_status != "Normal" and rng.random() < 0.15:
        imbalance_factor = rng.uniform(1.2, 1.6)
        if rng.random() < 0.5:
            energy_consumed_mwh *= imbalance_factor
        else:
            energy_generated_mwh *= (1.0 / imbalance_factor)

    # Outage duration (rare, more common in Critical)
    outage_prob = 0.005 if target_status == "Normal" else 0.04 if target_status == "Warning" else 0.10 if target_status == "High Risk" else 0.18
    outage_duration_min = float(rng.exponential(30)) if rng.random() < outage_prob else 0.0

    # ── Anomaly score, risk score, status ────────────────────────────
    anomaly_score = compute_anomaly_score(load, temp, voltage, frequency, pf, latency, fault)
    risk_score = compute_risk_score(anomaly_score, load, temp, voltage, frequency, fault, rng)

    # Per-transformer condition bias: an aging/stressed asset (condition > 1)
    # scores higher for the same readings, a healthy asset (condition < 1)
    # scores lower. Status always derives from the (biased) risk score so the
    # two can never disagree.
    risk_score = int(min(100, max(0, round(risk_score + (condition - 1.0) * CONDITION_RISK_OFFSET))))
    status = derive_status(risk_score)

    # ── Anomaly type (only for non-Normal) ───────────────────────────
    anomaly_type = "Normal"
    if status != "Normal":
        anomaly_type = classify_anomaly_type(
            load, temp, voltage, frequency, pf, latency,
            energy_generated_mwh, energy_consumed_mwh, fault, rng,
        )
    elif rng.random() < 0.02:
        # A small fraction of "Normal" records carry a mild anomaly label
        anomaly_type = rng.choice(ANOMALY_TYPES[:6])  # milder types only

    return {
        "event_id": f"EVT-{event_id:07d}",
        "timestamp": timestamp,
        "region": region,
        "substation_id": substation_id,
        "transformer_id": transformer_id,
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "voltage_kv": round(voltage, 2),
        "current_amp": round(current_amp, 2),
        "power_mw": round(power_mw, 2),
        "frequency_hz": round(frequency, 2),
        "load_percent": round(load, 2),
        "power_factor": round(pf, 4),
        "temperature_c": round(temp, 2),
        "energy_generated_mwh": round(energy_generated_mwh, 2),
        "energy_consumed_mwh": round(energy_consumed_mwh, 2),
        "outage_duration_min": round(outage_duration_min, 2),
        "communication_latency_ms": round(latency, 2),
        "fault_indicator": fault,
        "anomaly_score": anomaly_score,
        "risk_score": risk_score,
        "status": status,
        "anomaly_type": anomaly_type,
    }


def generate_dataset(num_records: int = 150000, output_dir: str = None) -> pd.DataFrame:
    """Generate realistic smart-grid telemetry dataset.

    Args:
        num_records: Number of records to generate
        output_dir:  Directory to save the generated CSV

    Returns:
        DataFrame with generated telemetry data
    """
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "raw"
        )

    os.makedirs(output_dir, exist_ok=True)

    print(f"Generating {num_records:,} telemetry records...")
    print(f"  Target ratios: Normal={DEFAULT_NORMAL_RATIO:.0%}, "
          f"Warning={DEFAULT_WARNING_RATIO:.0%}, "
          f"High Risk={DEFAULT_HIGH_RISK_RATIO:.0%}, "
          f"Critical={DEFAULT_CRITICAL_RATIO:.0%}")

    rng = np.random.default_rng(seed=42)

    transformer_to_substation = get_transformer_to_substation_map()
    transformer_to_region = get_transformer_to_region_map()
    transformer_ids = list(transformer_to_substation.keys())

    print(f"  Total transformers: {len(transformer_ids)}")
    print(f"  Total substations:  {len(SUBSTATION_COORDS)}")
    print(f"  Total regions:      {len(REGIONS)}")

    # Generate records over an 89-day window (Apr 1 - Jun 29). The dashboard's
    # default "last 90 days" filter therefore covers the ENTIRE dataset, so the
    # unfiltered Grid Health donut shows all 150,000 records.
    start_date = datetime(2025, 4, 1, 0, 0, 0)
    end_date = datetime(2025, 6, 29, 0, 0, 0)
    total_time = (end_date - start_date).total_seconds()

    records = []
    n_transformers = len(transformer_ids)
    for i in range(num_records):
        random_time = start_date + timedelta(seconds=rng.uniform(0, total_time))

        # Guarantee full coverage: the first pass assigns at least one record
        # to every transformer (and therefore every substation and region).
        # The remainder is filled with random picks as before.
        if i < n_transformers:
            transformer_id = transformer_ids[i]
        else:
            transformer_id = transformer_ids[rng.integers(0, n_transformers)]

        record = generate_telemetry_record(
            event_id=i,
            timestamp=random_time,
            transformer_id=transformer_id,
            transformer_to_substation=transformer_to_substation,
            transformer_to_region=transformer_to_region,
            substation_coords=SUBSTATION_COORDS,
            rng=rng,
        )
        records.append(record)

        if (i + 1) % 25000 == 0:
            print(f"  Generated {i + 1:,} records...")

    df = pd.DataFrame(records)

    # Save to CSV
    output_path = os.path.join(output_dir, "grid_telemetry_raw.csv")
    df.to_csv(output_path, index=False)
    print(f"\nDataset saved to: {output_path}")
    print(f"Total records: {len(df):,}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    # ── Distribution report ───────────────────────────────────────────
    print("\nStatus Distribution:")
    status_counts = df["status"].value_counts()
    for status, count in status_counts.items():
        print(f"  {status}: {count:,} ({count / len(df) * 100:.1f}%)")

    print("\nAnomaly Type Distribution (non-Normal records):")
    anom_df = df[df["status"] != "Normal"]
    if len(anom_df) > 0:
        anomaly_counts = anom_df["anomaly_type"].value_counts()
        for atype, count in anomaly_counts.items():
            print(f"  {atype}: {count:,} ({count / len(anom_df) * 100:.1f}%)")
    else:
        print("  (none)")

    # ── Energy distribution report ───────────────────────────────────────
    print("\nEnergy Distribution by Region (all records):")
    reg_energy = df.groupby("region").agg(
        record_count=("event_id", "count"),
        total_generated_mwh=("energy_generated_mwh", "sum"),
        total_consumed_mwh=("energy_consumed_mwh", "sum"),
    ).reset_index()
    for _, r in reg_energy.iterrows():
        pct = r["record_count"] / len(df) * 100
        print(
            f"  {r['region']:<12} {r['record_count']:>8,} records ({pct:5.1f}%)  "
            f"gen {r['total_generated_mwh']:>13,.1f} MWh  cons {r['total_consumed_mwh']:>13,.1f} MWh"
        )
    print(
        f"  {'TOTAL':<12} {len(df):>8,} records (100.0%)  "
        f"gen {df['energy_generated_mwh'].sum():>13,.1f} MWh  cons {df['energy_consumed_mwh'].sum():>13,.1f} MWh"
    )

    # ── Coverage report ──────────────────────────────────────────────────
    print("\nCoverage (guaranteed full coverage pass):")
    print(f"  Transformers with data: {df['transformer_id'].nunique():,} / {len(transformer_ids):,}")
    print(f"  Substations with data:  {df['substation_id'].nunique():,} / {len(SUBSTATION_COORDS):,}")
    print(f"  Regions with data:      {df['region'].nunique():,} / {len(REGIONS):,}")

    return df


def main():
    parser = argparse.ArgumentParser(description="GridPulse Data Generator")
    parser.add_argument(
        "--records", type=int, default=150000,
        help="Number of records to generate (default: 150000)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output directory for generated data",
    )
    args = parser.parse_args()

    if args.records < 10000:
        print(f"Warning: Generating fewer than 10,000 records (requested: {args.records})")

    generate_dataset(num_records=args.records, output_dir=args.output)
    print("\nGeneration complete!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
GridPulse Streaming Data Generator
Generates continuous telemetry events simulating real-time grid data.
Writes append-style JSONL batch files and a heartbeat for dashboard status detection.
"""

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

import numpy as np


# ---------------------------------------------------------------------------
# Grid topology (shared with generate_dataset.py)
# ---------------------------------------------------------------------------
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
}

TRANSFORMERS_PER_SUBSTATION = 20

BASE_VOLTAGE_KV = 40.0
BASE_CURRENT_AMP = 50.0
BASE_LOAD_PERCENT = 60.0
BASE_FREQUENCY_HZ = 50.0
BASE_POWER_FACTOR = 0.95
BASE_TEMPERATURE_C = 45.0

ANOMALY_PROBABILITY = 0.15  # 15% chance of forced anomaly per event


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------
def _build_transformer_maps():
    """Return (transformer_to_substation, transformer_to_region, transformer_ids)."""
    t2s: Dict[str, str] = {}
    for sid in SUBSTATION_COORDS:
        for i in range(1, TRANSFORMERS_PER_SUBSTATION + 1):
            tid = f"TR-{sid.split('-')[1]}{i:03d}"
            t2s[tid] = sid
    sub2region = {s: info["region"] for s, info in SUBSTATION_COORDS.items()}
    t2r = {tid: sub2region[t2s[tid]] for tid in t2s}
    return t2s, t2r, list(t2s.keys())


T2S, T2R, TRANSFORMER_IDS = _build_transformer_maps()


# ---------------------------------------------------------------------------
# Single-event generation
# ---------------------------------------------------------------------------
def generate_event(
    rng: np.random.Generator,
    current_time: datetime,
    force_anomaly: bool = False,
) -> Dict[str, Any]:
    """Generate a single telemetry event."""

    tid = TRANSFORMER_IDS[rng.integers(0, len(TRANSFORMER_IDS))]
    sid = T2S[tid]
    region = T2R[tid]
    coords = SUBSTATION_COORDS[sid]

    hour = current_time.hour
    diurnal = 0.7 + 0.6 * np.sin(np.pi * (hour - 6) / 12) if 6 <= hour <= 18 else 0.5
    xfmr = rng.uniform(0.85, 1.15)

    load = BASE_LOAD_PERCENT * diurnal * xfmr
    load = float(np.clip(load + rng.normal(0, 6), 15, 100))
    if force_anomaly:
        load = min(load + rng.uniform(10, 25), 100)

    current = BASE_CURRENT_AMP * (load / BASE_LOAD_PERCENT) + rng.normal(0, 4)
    current = max(current, 5)

    voltage = BASE_VOLTAGE_KV + rng.normal(0, 2)
    if force_anomaly:
        voltage = BASE_VOLTAGE_KV + rng.uniform(-4, 4)
    voltage = float(np.clip(voltage, 35, 45))

    freq = BASE_FREQUENCY_HZ + rng.normal(0, 0.1)
    if force_anomaly:
        freq = BASE_FREQUENCY_HZ + rng.uniform(-0.3, 0.3)
    freq = float(np.clip(freq, 49.5, 50.5))

    pf = float(np.clip(
        BASE_POWER_FACTOR - 0.08 * (load / 100) + rng.normal(0, 0.03), 0.65, 1.0
    ))
    power = (voltage * current * pf) / 1000

    temp = BASE_TEMPERATURE_C + (load - BASE_LOAD_PERCENT) * 0.25 + rng.normal(0, 2)
    if force_anomaly:
        temp = min(temp + rng.uniform(10, 25), 85)
    temp = float(np.clip(temp, 38, 85))

    energy_consumed = power + rng.normal(0, 15)

    fault_prob = 0.005
    if load > 90 or temp > 70 or voltage < 36:
        fault_prob = 0.12
    if force_anomaly:
        fault_prob = min(fault_prob + 0.2, 0.5)
    fault = 1 if rng.random() < fault_prob else 0

    # Pre-compute anomaly score (pipeline may refine)
    anomaly_score = 0.0
    if fault:
        anomaly_score = rng.uniform(0.7, 0.95)
    elif load > 85 or temp > 65:
        anomaly_score = rng.uniform(0.3, 0.6)

    # Status
    if anomaly_score > 0.7 or fault:
        if load > 90 or temp > 75:
            status = "Critical"
        elif anomaly_score > 0.5:
            status = "High Risk"
        else:
            status = "Warning"
    elif load > 75 or temp > 55:
        status = "Warning"
    else:
        status = "Normal"

    # Anomaly type
    anomaly_type = "Normal"
    if status != "Normal":
        types = [
            "Overload", "Temperature Spike", "Voltage Fluctuation",
            "Frequency Deviation", "Power Factor Anomaly",
            "Transformer Fault", "Compound Anomaly",
        ]
        if load > 90:
            anomaly_type = "Overload" if temp < 65 else "Compound Anomaly"
        elif temp > 65:
            anomaly_type = "Temperature Spike"
        elif abs(voltage - BASE_VOLTAGE_KV) > 4:
            anomaly_type = "Voltage Fluctuation"
        else:
            anomaly_type = rng.choice(types)

    return {
        "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
        "timestamp": current_time.isoformat(),
        "region": region,
        "substation_id": sid,
        "transformer_id": tid,
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "voltage_kv": round(voltage, 2),
        "current_amp": round(current, 2),
        "power_mw": round(power, 2),
        "frequency_hz": round(freq, 2),
        "load_percent": round(load, 2),
        "power_factor": round(pf, 4),
        "temperature_c": round(temp, 2),
        "energy_consumed_mwh": round(energy_consumed, 2),
        "fault_indicator": fault,
        "anomaly_score": round(anomaly_score, 4),
        "risk_score": 0,
        "status": status,
        "anomaly_type": anomaly_type,
    }


# ---------------------------------------------------------------------------
# Streaming loop
# ---------------------------------------------------------------------------
def run_stream(
    interval: float = 1.0,
    count: int = 500,
    batch_size: int = 1,
    output_dir: str = None,
):
    """
    Generate *count* events, emitting one batch file every *interval* seconds.

    Files are appended (never overwritten).  A heartbeat JSON is kept up to
    date so the dashboard can detect whether the stream is ONLINE.
    """
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "streaming",
        )

    events_dir = os.path.join(output_dir, "events")
    os.makedirs(events_dir, exist_ok=True)

    heartbeat_path = os.path.join(output_dir, "heartbeat.json")

    rng = np.random.default_rng(seed=int(time.time()))
    start_time = datetime.now()

    print(f"GridPulse Stream Generator")
    print(f"  Interval  : {interval}s")
    print(f"  Count     : {count}")
    print(f"  Batch size: {batch_size}")
    print(f"  Output    : {events_dir}")
    print(f"  Heartbeat : {heartbeat_path}")
    print(f"{'='*56}")

    events_generated = 0
    total_anomalies = 0

    try:
        while events_generated < count:
            batch_ts = datetime.now()
            events_in_batch = []

            for _ in range(min(batch_size, count - events_generated)):
                force = rng.random() < ANOMALY_PROBABILITY
                event = generate_event(rng, batch_ts, force_anomaly=force)
                events_in_batch.append(event)
                events_generated += 1

                if event["status"] != "Normal":
                    total_anomalies += 1

            # --- Write batch file (append-style: unique name per batch) ---
            ts_str = batch_ts.strftime("%Y%m%d_%H%M%S_%f")
            batch_file = os.path.join(events_dir, f"stream_batch_{ts_str}.jsonl")
            with open(batch_file, "w") as fh:
                for evt in events_in_batch:
                    fh.write(json.dumps(evt, default=str) + "\n")

            # --- Update heartbeat ---
            heartbeat = {
                "last_update": datetime.now().isoformat(),
                "events_generated": events_generated,
                "anomalies_detected": total_anomalies,
                "stream_start": start_time.isoformat(),
                "status": "running",
            }
            with open(heartbeat_path, "w") as fh:
                json.dump(heartbeat, fh, indent=2)

            status_sym = "!" if events_in_batch[-1]["status"] != "Normal" else "OK"
            print(
                f"  [{events_generated:>{len(str(count))}}/{count}] "
                f"{status_sym} batch -> {os.path.basename(batch_file)}  "
                f"({len(events_in_batch)} events)"
            )

            if events_generated < count:
                time.sleep(interval)

    except KeyboardInterrupt:
        print("\n  Stream interrupted by user.")
    finally:
        # Mark stream as stopped
        heartbeat = {
            "last_update": datetime.now().isoformat(),
            "events_generated": events_generated,
            "anomalies_detected": total_anomalies,
            "stream_start": start_time.isoformat(),
            "status": "stopped",
        }
        with open(heartbeat_path, "w") as fh:
            json.dump(heartbeat, fh, indent=2)

    print(f"{'='*56}")
    print(f"Stream complete.  Events: {events_generated}  Anomalies: {total_anomalies}")
    return events_generated


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="GridPulse Streaming Data Generator"
    )
    parser.add_argument(
        "--interval", type=float, default=1.0,
        help="Seconds between batch writes (default: 1)",
    )
    parser.add_argument(
        "--count", type=int, default=500,
        help="Total events to generate (default: 500)",
    )
    parser.add_argument(
        "--batch-size", type=int, default=1,
        help="Events per batch file (default: 1)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output directory (default: data/streaming)",
    )
    args = parser.parse_args()
    run_stream(
        interval=args.interval,
        count=args.count,
        batch_size=args.batch_size,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()

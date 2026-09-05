#!/usr/bin/env python
"""
GridPulse Streaming Ingestion

Reads new JSONL batch files from data/streaming/events/, processes each
event (refines anomaly_score -> risk_score -> status), and appends the
result to the Bronze layer (data/bronze/streaming/).

Uses PySpark Structured Streaming when Java/Spark are available,
otherwise falls back to a pure-pandas streaming processor.

Usage:
    python pipeline/02_stream_ingest.py [--trigger SEC]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_BASE = Path(__file__).resolve().parent.parent
DEFAULT_EVENTS_DIR = str(_BASE / "data" / "streaming" / "events")
DEFAULT_OUTPUT_DIR = str(_BASE / "data" / "bronze" / "streaming")
DEFAULT_CHECKPOINT = str(_BASE / "data" / "streaming" / "_checkpoint")
DEFAULT_HEARTBEAT = str(_BASE / "data" / "streaming" / "heartbeat.json")

PROCESSED_MARKER = "_processed.json"  # tracks which files have been ingested


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------
def compute_risk_score(row):
    """Derive a composite risk_score (0-100)."""
    anomaly = row.get("anomaly_score", 0.0) or 0.0
    load = row.get("load_percent", 0.0) or 0.0
    temp = row.get("temperature_c", 0.0) or 0.0
    fault = row.get("fault_indicator", 0) or 0

    risk = anomaly * 40
    if load > 70:
        risk += (load - 70) * 0.3
    if temp > 55:
        risk += (temp - 55) * 0.2
    if fault == 1:
        risk += 25
    return round(min(risk, 100.0), 2)


def derive_status(row):
    """Classify overall status."""
    risk = row.get("risk_score", 0.0) or 0.0
    anomaly = row.get("anomaly_score", 0.0) or 0.0
    fault = row.get("fault_indicator", 0) or 0

    if fault == 1 or risk >= 70:
        return "Critical"
    elif risk >= 50 or anomaly >= 0.6:
        return "High Risk"
    elif risk >= 25 or anomaly >= 0.2:
        return "Warning"
    return "Normal"


# ---------------------------------------------------------------------------
# PySpark path
# ---------------------------------------------------------------------------
def _try_pyspark(args):
    """Attempt PySpark Structured Streaming; returns True on success."""
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F
        from pyspark.sql.types import (
            StructType, StructField, StringType, DoubleType, IntegerType,
        )
    except ImportError:
        return False

    # Quick smoke test -- can we actually create a SparkSession?
    try:
        _test = SparkSession.builder.appName("__probe").getOrCreate()
        _test.stop()
    except Exception:
        return False

    EVENT_SCHEMA = StructType([
        StructField("event_id",          StringType(),  True),
        StructField("timestamp",         StringType(),  True),
        StructField("region",            StringType(),  True),
        StructField("substation_id",     StringType(),  True),
        StructField("transformer_id",    StringType(),  True),
        StructField("latitude",          DoubleType(),  True),
        StructField("longitude",         DoubleType(),  True),
        StructField("voltage_kv",        DoubleType(),  True),
        StructField("current_amp",       DoubleType(),  True),
        StructField("power_mw",          DoubleType(),  True),
        StructField("frequency_hz",      DoubleType(),  True),
        StructField("load_percent",      DoubleType(),  True),
        StructField("power_factor",      DoubleType(),  True),
        StructField("temperature_c",     DoubleType(),  True),
        StructField("energy_consumed_mwh", DoubleType(), True),
        StructField("fault_indicator",   IntegerType(), True),
        StructField("anomaly_score",     DoubleType(),  True),
        StructField("risk_score",        DoubleType(),  True),
        StructField("status",            StringType(),  True),
        StructField("anomaly_type",      StringType(),  True),
    ])

    @F.udf(returnType=DoubleType())
    def risk_udf(anomaly_score, load_percent, temperature_c, fault_indicator):
        a = anomaly_score or 0.0
        l = load_percent or 0.0
        t = temperature_c or 0.0
        f = fault_indicator or 0
        risk = a * 40
        if l > 70:  risk += (l - 70) * 0.3
        if t > 55:  risk += (t - 55) * 0.2
        if f == 1:  risk += 25
        return round(min(risk, 100.0), 2)

    @F.udf(returnType=StringType())
    def status_udf(risk_score, anomaly_score, fault_indicator):
        r = risk_score or 0.0
        a = anomaly_score or 0.0
        f = fault_indicator or 0
        if f == 1 or r >= 70: return "Critical"
        if r >= 50 or a >= 0.6: return "High Risk"
        if r >= 25 or a >= 0.2: return "Warning"
        return "Normal"

    print("[pyspark] Starting Structured Streaming ...")
    print(f"  Source     : {args.events_dir}")
    print(f"  Output     : {args.output_dir}")
    print(f"  Checkpoint : {args.checkpoint_dir}")

    spark = (
        SparkSession.builder
        .appName("GridPulse-StreamIngest")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.checkpoint_dir, exist_ok=True)

    raw = (
        spark.readStream
        .schema(EVENT_SCHEMA)
        .option("maxFilesPerTrigger", 10)
        .json(args.events_dir)
    )

    enriched = (
        raw
        .withColumn("ts", F.to_timestamp("timestamp"))
        .withColumn("risk_score", risk_udf(
            F.col("anomaly_score"), F.col("load_percent"),
            F.col("temperature_c"), F.col("fault_indicator"),
        ))
        .withColumn("status", status_udf(
            F.col("risk_score"), F.col("anomaly_score"),
            F.col("fault_indicator"),
        ))
        .withColumn("ingestion_time", F.current_timestamp())
        .withColumn("source", F.lit("stream"))
    )

    cols = [
        "event_id", "ts", "region", "substation_id", "transformer_id",
        "latitude", "longitude", "voltage_kv", "current_amp", "power_mw",
        "frequency_hz", "load_percent", "power_factor", "temperature_c",
        "energy_consumed_mwh", "fault_indicator", "anomaly_score",
        "risk_score", "status", "anomaly_type", "ingestion_time", "source",
    ]

    q = (
        enriched.select(*cols).writeStream
        .format("parquet")
        .option("path", args.output_dir)
        .option("checkpointLocation", args.checkpoint_dir)
        .outputMode("append")
        .trigger(processingTime=args.trigger)
        .start()
    )

    print(f"[pyspark] Query started (id={q.id})")

    try:
        last_hb = None
        while q.isActive:
            time.sleep(5)
            if os.path.exists(DEFAULT_HEARTBEAT):
                with open(DEFAULT_HEARTBEAT) as f:
                    hb = json.load(f)
                if hb.get("status") == "stopped":
                    print("[pyspark] Generator stopped, waiting for drain ...")
                    time.sleep(10)
                    break
                hb_last = hb.get("last_update")
                if hb_last != last_hb:
                    last_hb = hb_last
                    n = sum(1 for _ in Path(args.output_dir).rglob("*.parquet"))
                    print(
                        f"  events={hb.get('events_generated')} "
                        f"anomalies={hb.get('anomalies_detected')} "
                        f"parquet_parts={n}"
                    )
    except KeyboardInterrupt:
        pass

    q.stop()
    q.awaitTermination(timeout=15)

    # Summary
    try:
        df = spark.read.parquet(args.output_dir)
        total = df.count()
        anom = df.filter(F.col("status") != "Normal").count()
        latest = df.agg(F.max("ts")).collect()[0][0]
        print(f"\n  Events processed  : {total:,}")
        print(f"  Anomalies detected: {anom:,}")
        if latest:
            print(f"  Last event ts     : {latest}")
    except Exception:
        pass

    spark.stop()
    return True


# ---------------------------------------------------------------------------
# Pandas-based streaming processor (fallback)
# ---------------------------------------------------------------------------
def _pandas_stream(args):
    """
    Poll data/streaming/events/ for new JSONL files, process them with
    pandas, and append Parquet to data/bronze/streaming/.
    """
    events_dir = Path(args.events_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    processed_marker = output_dir / PROCESSED_MARKER
    processed_files = set()
    if processed_marker.exists():
        with open(processed_marker) as f:
            processed_files = set(json.load(f))

    print("[pandas] Streaming processor started (polling mode)")
    print(f"  Source : {events_dir}")
    print(f"  Output : {output_dir}")
    print(f"  Trigger: every {args.trigger}")

    trigger_sec = _parse_trigger(args.trigger)

    stats = {"received": 0, "processed": 0, "anomalies": 0}
    last_ts = None

    try:
        while True:
            new_files = sorted(
                f for f in events_dir.glob("stream_batch_*.jsonl")
                if f.name not in processed_files
            )

            if new_files:
                frames = []
                for fp in new_files:
                    try:
                        df = pd.read_json(fp, lines=True)
                        if len(df) > 0:
                            frames.append(df)
                        processed_files.add(fp.name)
                    except Exception as e:
                        print(f"  [warn] Skipping {fp.name}: {e}")
                        processed_files.add(fp.name)

                if frames:
                    batch = pd.concat(frames, ignore_index=True)
                    stats["received"] += len(batch)

                    # ── Process ──────────────────────────────────────
                    batch["risk_score"] = batch.apply(compute_risk_score, axis=1)
                    batch["status"] = batch.apply(derive_status, axis=1)
                    batch["ingestion_time"] = datetime.now().isoformat()
                    batch["source"] = "stream"

                    n_anom = int((batch["status"] != "Normal").sum())
                    stats["anomalies"] += n_anom
                    stats["processed"] += len(batch)

                    if "timestamp" in batch.columns:
                        last_ts = batch["timestamp"].max()

                    # Rename ts
                    if "timestamp" in batch.columns:
                        batch = batch.rename(columns={"timestamp": "ts"})

                    # ── Write parquet ────────────────────────────────
                    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    out_path = output_dir / f"processed_{ts_str}.parquet"
                    batch.to_parquet(out_path, index=False)

                    # Save processed-file list
                    with open(processed_marker, "w") as f:
                        json.dump(sorted(processed_files), f)

                    print(
                        f"  [{stats['processed']:>6}] "
                        f"+{len(batch)} events "
                        f"(anomalies={n_anom}) -> {out_path.name}"
                    )

            # Check heartbeat
            hb_status = _check_heartbeat()
            if hb_status == "stopped" and not new_files:
                # No new files and generator stopped -> done
                time.sleep(trigger_sec * 2)
                # One final check for stragglers
                still_new = any(
                    f.name not in processed_files
                    for f in events_dir.glob("stream_batch_*.jsonl")
                )
                if not still_new:
                    break

            time.sleep(trigger_sec)

    except KeyboardInterrupt:
        print("\n  Interrupted.")

    # ── Summary ──────────────────────────────────────────────────────────
    _print_summary(output_dir, stats, last_ts)


def _check_heartbeat():
    if os.path.exists(DEFAULT_HEARTBEAT):
        try:
            with open(DEFAULT_HEARTBEAT) as f:
                return json.load(f).get("status", "unknown")
        except Exception:
            pass
    return "unknown"


def _parse_trigger(trigger_str):
    """Parse '5 seconds' -> 5.0"""
    parts = trigger_str.strip().split()
    try:
        return float(parts[0])
    except (ValueError, IndexError):
        return 5.0


def _print_summary(output_dir, stats, last_ts):
    print()
    print("=" * 60)
    print("STREAMING INGESTION SUMMARY")
    print("=" * 60)

    # Also count existing parquet records
    try:
        existing = pd.read_parquet(output_dir)
        total = len(existing)
        anom = int((existing["status"] != "Normal").sum())
        if "ts" in existing.columns:
            latest = existing["ts"].max()
        elif "timestamp" in existing.columns:
            latest = existing["timestamp"].max()
        else:
            latest = last_ts
    except Exception:
        total = stats["processed"]
        anom = stats["anomalies"]
        latest = last_ts

    print(f"  Events received   : {stats['received']:,}")
    print(f"  Events processed  : {total:,}")
    print(f"  Anomalies detected: {anom:,}")
    if latest:
        print(f"  Last event ts     : {latest}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="GridPulse Streaming Ingestion"
    )
    parser.add_argument("--events-dir", default=DEFAULT_EVENTS_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--checkpoint-dir", default=DEFAULT_CHECKPOINT)
    parser.add_argument("--trigger", default="5 seconds",
                        help="Poll / trigger interval (default: 5 seconds)")
    args = parser.parse_args()

    print("=" * 60)
    print("GRIDPULSE -- STREAMING INGESTION")
    print("=" * 60)
    print(f"  Start time: {datetime.now().isoformat()}")
    print(f"  Heartbeat : {DEFAULT_HEARTBEAT}")
    print("=" * 60)

    # Try PySpark first, fall back to pandas
    pyspark_ok = _try_pyspark(args)
    if not pyspark_ok:
        print("[fallback] PySpark not available, using pandas processor.\n")
        _pandas_stream(args)


if __name__ == "__main__":
    main()

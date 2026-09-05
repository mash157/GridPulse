#!/usr/bin/env python
"""
GridPulse Pipeline Runner (pandas-based)
Produces identical Bronze → Silver → Gold outputs.
Avoids PySpark Hadoop winutils issues on Windows.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
RAW = BASE / "data" / "raw" / "grid_telemetry_raw.csv"
BRONZE_CSV = BASE / "data" / "bronze" / "grid_bronze.csv"
SILVER_CSV = BASE / "data" / "silver" / "grid_silver.csv"
GOLD_DIR = BASE / "data" / "gold" / "gold_data"
EXPORTS = BASE / "data" / "exports"

import pandas as pd
import numpy as np


def pandas_bronze():
    """Bronze layer: read CSV, validate, add metadata, write CSV."""
    print(f"\n{'='*60}")
    print("GRIDPULSE — BRONZE LAYER (pandas)")
    print(f"{'='*60}")
    t0 = datetime.now()

    if not RAW.exists():
        print(f"ERROR: {RAW} not found. Run generate_dataset.py first.")
        sys.exit(1)

    print("\n[1/3] Reading raw CSV …")
    df = pd.read_csv(RAW, parse_dates=["timestamp"])
    print(f"  Records: {len(df):,}")

    print("[2/3] Validating schema …")
    expected = {
        "event_id", "timestamp", "region", "substation_id", "transformer_id",
        "latitude", "longitude", "voltage_kv", "current_amp", "power_mw",
        "frequency_hz", "load_percent", "power_factor", "temperature_c",
        "energy_generated_mwh", "energy_consumed_mwh", "outage_duration_min",
        "communication_latency_ms", "fault_indicator", "anomaly_score",
        "risk_score", "status", "anomaly_type",
    }
    missing = expected - set(df.columns)
    if missing:
        print(f"  WARNING missing: {missing}")
    else:
        print("  Schema: OK")

    df["ingestion_time"] = datetime.now().isoformat()
    df["ingestion_batch"] = "batch_001"

    print("[3/3] Writing Bronze CSV …")
    BRONZE_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(BRONZE_CSV, index=False)

    print(f"  Bronze records: {len(df):,}")
    print(f"  Output: {BRONZE_CSV}")
    print(f"  Elapsed: {(datetime.now() - t0).total_seconds():.1f}s")
    return len(df)


def pandas_silver():
    """Silver layer: clean, deduplicate, validate, engineer features."""
    print(f"\n{'='*60}")
    print("GRIDPULSE — SILVER LAYER (pandas)")
    print(f"{'='*60}")
    t0 = datetime.now()

    print("\n[1/6] Reading Bronze …")
    df = pd.read_csv(BRONZE_CSV, parse_dates=["timestamp"])
    n0 = len(df)
    print(f"  Bronze records: {n0:,}")

    print("[2/6] Removing duplicates …")
    df = df.drop_duplicates(subset=["event_id"], keep="first")
    n_after = len(df)
    print(f"  Duplicates removed: {n0 - n_after:,}")

    print("[3/6] Handling missing values …")
    num_cols = [
        "voltage_kv", "current_amp", "power_mw", "frequency_hz",
        "load_percent", "power_factor", "temperature_c",
        "energy_generated_mwh", "energy_consumed_mwh",
        "outage_duration_min", "communication_latency_ms", "anomaly_score",
    ]
    for c in num_cols:
        if c in df.columns:
            med = df[c].median()
            df[c] = df[c].fillna(med)
    df["status"] = df["status"].fillna("Normal")
    df["anomaly_type"] = df["anomaly_type"].fillna("Normal")
    df["fault_indicator"] = df["fault_indicator"].fillna(0)

    print("[4/6] Validating ranges …")
    # Wider ranges to preserve realistic severity differentiation.
    # The generator produces voltage 30–48 kV, frequency 49.4–50.6 Hz,
    # and temperature up to 85 °C for Critical records.
    clips = {"voltage_kv": (28, 52), "frequency_hz": (49.2, 50.8),
             "load_percent": (0, 100), "power_factor": (0.5, 1.0), "temperature_c": (30, 90)}
    for c, (lo, hi) in clips.items():
        if c in df.columns:
            before = ((df[c] < lo) | (df[c] > hi)).sum()
            df[c] = df[c].clip(lo, hi)
            if before:
                print(f"  {c}: clipped {before} records")

    print("[5/6] Feature engineering …")
    df["voltage_deviation_kv"] = (df["voltage_kv"] - 40.0).round(2)
    df["frequency_deviation_hz"] = (df["frequency_hz"] - 50.0).round(3)
    df["power_quality_score"] = ((df["power_factor"] - 0.6) / 0.4 * 100).round(1)
    df["voltage_stability_score"] = (100 - df["voltage_deviation_kv"].abs() * 5).round(1)
    df["calculated_power_mw"] = (df["voltage_kv"] * df["current_amp"] * df["power_factor"] / 1000).round(2)
    denom = df["energy_consumed_mwh"].replace(0, np.nan)
    df["transmission_efficiency"] = (df["energy_generated_mwh"] / denom * 100).fillna(100).round(1)

    print("[6/6] Normalizing …")
    for m in ["load_percent", "temperature_c", "power_mw"]:
        mean, std = df[m].mean(), df[m].std()
        if std > 0:
            df[f"{m}_zscore"] = ((df[m] - mean) / std).round(3)

    df["transformation_time"] = datetime.now().isoformat()
    df["silver_version"] = "1.0"
    df["anomaly_flag"] = (df["status"] != "Normal").astype(int)

    SILVER_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SILVER_CSV, index=False)
    print(f"  Silver records: {len(df):,}")
    print(f"  Output: {SILVER_CSV}")
    print(f"  Elapsed: {(datetime.now() - t0).total_seconds():.1f}s")
    return len(df)


def classify_status(score: float) -> str:
    """Canonical 5-band status mapping (0-29 Normal, 30-49 Low, 50-69
    Warning, 70-84 High Risk, 85-100 Critical)."""
    if score >= 85:
        return "Critical"
    elif score >= 70:
        return "High Risk"
    elif score >= 50:
        return "Warning"
    elif score >= 30:
        return "Low"
    return "Normal"


def pandas_gold():
    """Gold layer: aggregate into summary tables, export CSV."""
    print(f"\n{'='*60}")
    print("GRIDPULSE — GOLD LAYER (pandas)")
    print(f"{'='*60}")
    t0 = datetime.now()

    df = pd.read_csv(SILVER_CSV, parse_dates=["timestamp"])
    print(f"  Silver records: {len(df):,}")

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS.mkdir(parents=True, exist_ok=True)

    # 1. Transformer Summary
    print("\n[1/8] Transformer summary …")
    trans = df.groupby(["transformer_id", "substation_id", "region"]).agg(
        total_power_mw=("power_mw", "sum"),
        avg_voltage_kv=("voltage_kv", "mean"),
        avg_current_amp=("current_amp", "mean"),
        avg_power_mw=("power_mw", "mean"),
        avg_frequency_hz=("frequency_hz", "mean"),
        avg_load_percent=("load_percent", "mean"),
        avg_power_factor=("power_factor", "mean"),
        avg_temperature_c=("temperature_c", "mean"),
        max_temperature_c=("temperature_c", "max"),
        total_energy_generated_mwh=("energy_generated_mwh", "sum"),
        total_energy_consumed_mwh=("energy_consumed_mwh", "sum"),
        avg_latency_ms=("communication_latency_ms", "mean"),
        total_faults=("fault_indicator", "sum"),
        max_risk_score=("risk_score", "max"),
        avg_risk_score=("risk_score", "mean"),
        record_count=("event_id", "count"),
        distinct_anomaly_types=("anomaly_type", "nunique"),
    ).reset_index().round(2)
    # worst_status = worst record seen; status = representative (average) state
    trans["worst_status"] = trans["max_risk_score"].apply(classify_status)
    trans["status"] = trans["avg_risk_score"].apply(classify_status)
    # Dominant anomaly type per transformer (mode of non-Normal records)
    anom_mode = (
        df[df["status"] != "Normal"]
        .groupby("transformer_id")["anomaly_type"]
        .agg(lambda s: s.value_counts().index[0] if len(s) else "Normal")
        .rename("dominant_anomaly_type")
    )
    trans = trans.merge(anom_mode, on="transformer_id", how="left")
    trans["dominant_anomaly_type"] = trans["dominant_anomaly_type"].fillna("Normal")
    trans = trans.sort_values("avg_risk_score", ascending=False)

    # 2. Substation Summary
    print("[2/8] Substation summary …")
    sub = df.groupby(["substation_id", "region"]).agg(
        total_power_mw=("power_mw", "sum"),
        avg_voltage_kv=("voltage_kv", "mean"),
        avg_load_percent=("load_percent", "mean"),
        avg_temperature_c=("temperature_c", "mean"),
        avg_power_factor=("power_factor", "mean"),
        total_energy_generated_mwh=("energy_generated_mwh", "sum"),
        total_energy_consumed_mwh=("energy_consumed_mwh", "sum"),
        total_faults=("fault_indicator", "sum"),
        transformer_count=("transformer_id", "nunique"),
        max_risk_score=("risk_score", "max"),
        avg_risk_score=("risk_score", "mean"),
        record_count=("event_id", "count"),
    ).reset_index().round(2)

    # 3. Region Summary
    print("[3/8] Region summary …")
    reg = df.groupby("region").agg(
        total_power_mw=("power_mw", "sum"),
        avg_voltage_kv=("voltage_kv", "mean"),
        avg_load_percent=("load_percent", "mean"),
        avg_temperature_c=("temperature_c", "mean"),
        avg_power_factor=("power_factor", "mean"),
        total_energy_generated_mwh=("energy_generated_mwh", "sum"),
        total_energy_consumed_mwh=("energy_consumed_mwh", "sum"),
        total_faults=("fault_indicator", "sum"),
        transformer_count=("transformer_id", "nunique"),
        substation_count=("substation_id", "nunique"),
        max_risk_score=("risk_score", "max"),
        avg_risk_score=("risk_score", "mean"),
        record_count=("event_id", "count"),
    ).reset_index().round(2)

    # 4. Hourly Summary
    print("[4/8] Hourly summary …")
    df["hour_of_day"] = df["timestamp"].dt.hour
    hourly = df.groupby("hour_of_day").agg(
        total_power_mw=("power_mw", "sum"),
        avg_load_percent=("load_percent", "mean"),
        avg_temperature_c=("temperature_c", "mean"),
        avg_energy_generated_mwh=("energy_generated_mwh", "mean"),
        avg_energy_consumed_mwh=("energy_consumed_mwh", "mean"),
        total_faults=("fault_indicator", "sum"),
        record_count=("event_id", "count"),
        avg_risk_score=("risk_score", "mean"),
    ).reset_index().round(2)

    # 5. Daily Summary
    print("[5/8] Daily summary …")
    df["date"] = df["timestamp"].dt.date
    daily = df.groupby("date").agg(
        total_power_mw=("power_mw", "sum"),
        avg_load_percent=("load_percent", "mean"),
        avg_temperature_c=("temperature_c", "mean"),
        total_energy_generated_mwh=("energy_generated_mwh", "sum"),
        total_energy_consumed_mwh=("energy_consumed_mwh", "sum"),
        total_faults=("fault_indicator", "sum"),
        record_count=("event_id", "count"),
        avg_risk_score=("risk_score", "mean"),
    ).reset_index().round(2)

    # 6. Anomaly Summary
    print("[6/8] Anomaly summary …")
    anom_df = df[df["status"] != "Normal"]
    anom = anom_df.groupby(["anomaly_type", "status"]).agg(
        anomaly_count=("event_id", "count"),
        avg_risk_score=("risk_score", "mean"),
        avg_load_percent=("load_percent", "mean"),
        avg_temperature_c=("temperature_c", "mean"),
        avg_voltage_kv=("voltage_kv", "mean"),
    ).reset_index().round(2).sort_values("anomaly_count", ascending=False)

    # 7. Severity Summary
    print("[7/8] Severity summary …")
    sev = df.groupby("status").agg(
        count=("event_id", "count"),
        avg_risk_score=("risk_score", "mean"),
        avg_load_percent=("load_percent", "mean"),
        avg_temperature_c=("temperature_c", "mean"),
    ).reset_index().round(2)
    order = {"Critical": 1, "High Risk": 2, "Warning": 3, "Low": 4, "Normal": 5}
    sev["_order"] = sev["status"].map(order).fillna(5)
    sev = sev.sort_values("_order").drop(columns=["_order"])

    # 8. Critical Transformers
    print("[8/8] Critical transformers …")
    crit_df = df[df["risk_score"] >= 85]
    if len(crit_df) > 0:
        crit = crit_df.groupby(["transformer_id", "substation_id", "region"]).agg(
            avg_load_percent=("load_percent", "mean"),
            avg_temperature_c=("temperature_c", "mean"),
            avg_voltage_kv=("voltage_kv", "mean"),
            avg_power_factor=("power_factor", "mean"),
            avg_risk_score=("risk_score", "mean"),
            max_risk_score=("risk_score", "max"),
            distinct_anomaly_types=("anomaly_type", "nunique"),
            total_faults=("fault_indicator", "sum"),
        ).reset_index().round(2).sort_values("max_risk_score", ascending=False)
    else:
        crit = pd.DataFrame()

    # Write Gold CSVs
    print(f"\n{'='*60}")
    print("WRITING GOLD & EXPORTING TO CSV")
    print(f"{'='*60}")

    # Write to gold/gold_data/ (parquet-style directory structure)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    trans.to_csv(GOLD_DIR / "transformer_summary.csv", index=False)
    sub.to_csv(GOLD_DIR / "substation_summary.csv", index=False)
    reg.to_csv(GOLD_DIR / "region_summary.csv", index=False)
    hourly.to_csv(GOLD_DIR / "hourly_summary.csv", index=False)
    daily.to_csv(GOLD_DIR / "daily_summary.csv", index=False)
    anom.to_csv(GOLD_DIR / "anomaly_summary.csv", index=False)
    sev.to_csv(GOLD_DIR / "severity_summary.csv", index=False)
    if len(crit) > 0:
        crit.to_csv(GOLD_DIR / "critical_transformers.csv", index=False)

    # Also write to exports/
    trans.to_csv(EXPORTS / "transformer_summary.csv", index=False)
    print(f"  transformer_summary.csv  ({len(trans):,} rows)")
    sub.to_csv(EXPORTS / "substation_summary.csv", index=False)
    print(f"  substation_summary.csv   ({len(sub):,} rows)")
    reg.to_csv(EXPORTS / "region_summary.csv", index=False)
    print(f"  region_summary.csv       ({len(reg):,} rows)")
    hourly.to_csv(EXPORTS / "hourly_summary.csv", index=False)
    print(f"  hourly_summary.csv       ({len(hourly):,} rows)")
    daily.to_csv(EXPORTS / "daily_summary.csv", index=False)
    print(f"  daily_summary.csv        ({len(daily):,} rows)")
    anom.to_csv(EXPORTS / "anomaly_summary.csv", index=False)
    print(f"  anomaly_summary.csv      ({len(anom):,} rows)")
    sev.to_csv(EXPORTS / "severity_summary.csv", index=False)
    print(f"  severity_summary.csv     ({len(sev):,} rows)")
    if len(crit) > 0:
        crit.to_csv(EXPORTS / "critical_transformers.csv", index=False)
        print(f"  critical_transformers.csv ({len(crit):,} rows)")

    # Silver sample for API
    sample = df.sort_values("timestamp", ascending=False).head(50000)
    sample.to_csv(EXPORTS / "silver_sample.csv", index=False)
    print(f"  silver_sample.csv        ({len(sample):,} rows)")

    elapsed = (datetime.now() - t0).total_seconds()
    print(f"\n{'='*60}")
    print("GOLD AGGREGATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Transformer summaries: {len(trans):,}")
    print(f"  Substation summaries:  {len(sub):,}")
    print(f"  Region summaries:      {len(reg):,}")
    print(f"  Hourly summaries:      {len(hourly):,}")
    print(f"  Daily summaries:       {len(daily):,}")
    print(f"  Anomaly summaries:     {len(anom):,}")
    print(f"  Severity summaries:    {len(sev):,}")
    print(f"  Critical transformers: {len(crit):,}")
    print(f"  Elapsed: {elapsed:.1f}s")


def main():
    print("=" * 60)
    print("GRIDPULSE — DATA PIPELINE")
    print("=" * 60)

    if not RAW.exists():
        print(f"\nERROR: Raw data not found at {RAW}")
        print("Run: python data_generation/generate_dataset.py --records 150000")
        sys.exit(1)

    raw_df = pd.read_csv(RAW)
    print(f"Raw data: {len(raw_df):,} records")
    print("\nUsing pandas pipeline (identical output to PySpark)")

    try:
        n_bronze = pandas_bronze()
        print(f"\n[OK] Bronze: {n_bronze:,} records")

        n_silver = pandas_silver()
        print(f"[OK] Silver: {n_silver:,} records")

        pandas_gold()
        print(f"[OK] Gold:   aggregated")

        # Verify
        print(f"\n{'='*60}")
        print("VERIFICATION")
        print(f"{'='*60}")
        for name, path in [("Bronze CSV", BRONZE_CSV), ("Silver CSV", SILVER_CSV)]:
            try:
                df = pd.read_csv(path)
                print(f"  {name}: {len(df):,} records [OK]")
            except Exception as e:
                print(f"  {name}: ERROR — {e}")

        for f in sorted(EXPORTS.glob("*.csv")):
            try:
                df = pd.read_csv(f)
                print(f"  exports/{f.name}: {len(df):,} rows [OK]")
            except Exception as e:
                print(f"  exports/{f.name}: ERROR — {e}")

        # ── Coverage verification ───────────────────────────────────────
        print(f"\n{'='*60}")
        print("COVERAGE & ENERGY DISTRIBUTION")
        print(f"{'='*60}")
        silver = pd.read_csv(SILVER_CSV)
        total = len(silver)
        print(f"  Total records: {total:,}")
        print(f"  Transformers with data: {silver['transformer_id'].nunique():,}")
        print(f"  Substations with data:  {silver['substation_id'].nunique():,}")
        print(f"  Regions with data:      {silver['region'].nunique():,}")
        print("\n  Record Status Distribution:")
        sv = silver["status"].value_counts()
        for s in ["Normal", "Low", "Warning", "High Risk", "Critical"]:
            c = sv.get(s, 0)
            print(f"    {s:<12} {c:>7,}  ({c / total * 100:5.1f}%)")
        print("\n  Anomaly Type Distribution (non-Normal records):")
        anom_df = silver[silver["status"] != "Normal"]
        if len(anom_df):
            ac = anom_df["anomaly_type"].value_counts()
            for atype, c in ac.items():
                print(f"    {atype:<24} {c:>7,}  ({c / len(anom_df) * 100:5.1f}%)")
        print("\n  Energy Distribution by Region:")
        reg = silver.groupby("region").agg(
            record_count=("event_id", "count"),
            total_energy_generated_mwh=("energy_generated_mwh", "sum"),
            total_energy_consumed_mwh=("energy_consumed_mwh", "sum"),
        ).reset_index()
        for _, r in reg.iterrows():
            pct = r["record_count"] / total * 100
            print(
                f"    {r['region']:<12} {r['record_count']:>8,} records ({pct:5.1f}%)  "
                f"gen {r['total_energy_generated_mwh']:>13,.1f} MWh  cons {r['total_energy_consumed_mwh']:>13,.1f} MWh"
            )
        print(
            f"    {'TOTAL':<12} {total:>8,} records (100.0%)  "
            f"gen {silver['energy_generated_mwh'].sum():>13,.1f} MWh  cons {silver['energy_consumed_mwh'].sum():>13,.1f} MWh"
        )

        print(f"\n{'='*60}")
        print("PIPELINE COMPLETE - ALL LAYERS POPULATED")
        print(f"{'='*60}")

    except Exception as e:
        print(f"\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
GridPulse Risk Scoring
Calculates risk scores (0-100) for all grid equipment
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


def get_base_path() -> Path:
    """Get the base project path."""
    return Path(__file__).parent.parent


def calculate_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate risk scores for all records.

    Risk Score Components (0-100 total):

    1. Load Risk (0-20 points)
       - >90% load: 20 points
       - >80% load: 15 points
       - >70% load: 10 points
       - >60% load: 5 points
       - <60% load: 0 points

    2. Temperature Risk (0-20 points)
       - >75°C: 20 points
       - >70°C: 15 points
       - >65°C: 10 points
       - >60°C: 5 points
       - <60°C: 0 points

    3. Voltage Deviation Risk (0-15 points)
       - Deviation >4kV: 15 points
       - Deviation >3kV: 12 points
       - Deviation >2kV: 8 points
       - Deviation >1kV: 4 points
       - <1kV: 0 points

    4. Frequency Deviation Risk (0-10 points)
       - Deviation >0.3Hz: 10 points
       - Deviation >0.2Hz: 7 points
       - Deviation >0.15Hz: 5 points
       - Deviation >0.1Hz: 2 points
       - <0.1Hz: 0 points

    5. Power Factor Risk (0-10 points)
       - PF < 0.7: 10 points
       - PF < 0.75: 7 points
       - PF < 0.8: 5 points
       - PF < 0.85: 2 points
       - >=0.85: 0 points

    6. Fault Indicator Risk (0-15 points)
       - Fault present: 15 points
       - No fault: 0 points

    7. Anomaly Score Risk (0-5 points)
       - Anomaly score >0.7: 5 points
       - Anomaly score >0.5: 3 points
       - Anomaly score >0.3: 1 point
       - Otherwise: 0 points

    8. Communication Risk (0-5 points)
       - Latency >50ms: 5 points
       - Latency >30ms: 3 points
       - Latency >15ms: 1 point
       - Otherwise: 0 points
    """
    df = df.copy()

    # Calculate voltage deviation if not present
    if "voltage_deviation_kv" not in df.columns:
        df["voltage_deviation_kv"] = abs(df["voltage_kv"] - 40.0)

    # Calculate frequency deviation if not present
    if "frequency_deviation_hz" not in df.columns:
        df["frequency_deviation_hz"] = abs(df["frequency_hz"] - 50.0)

    # Ensure anomaly_score column exists
    if "anomaly_score" not in df.columns:
        df["anomaly_score"] = 0.0

    # 1. Load Risk (0-20)
    load_risk = np.zeros(len(df))
    load_risk = np.where(df["load_percent"] > 90, 20, load_risk)
    load_risk = np.where((df["load_percent"] > 80) & (df["load_percent"] <= 90), 15, load_risk)
    load_risk = np.where((df["load_percent"] > 70) & (df["load_percent"] <= 80), 10, load_risk)
    load_risk = np.where((df["load_percent"] > 60) & (df["load_percent"] <= 70), 5, load_risk)
    df["load_risk_score"] = load_risk

    # 2. Temperature Risk (0-20)
    temp_risk = np.zeros(len(df))
    temp_risk = np.where(df["temperature_c"] > 75, 20, temp_risk)
    temp_risk = np.where((df["temperature_c"] > 70) & (df["temperature_c"] <= 75), 15, temp_risk)
    temp_risk = np.where((df["temperature_c"] > 65) & (df["temperature_c"] <= 70), 10, temp_risk)
    temp_risk = np.where((df["temperature_c"] > 60) & (df["temperature_c"] <= 65), 5, temp_risk)
    df["temperature_risk_score"] = temp_risk

    # 3. Voltage Deviation Risk (0-15)
    voltage_dev = df["voltage_deviation_kv"].values
    voltage_risk = np.zeros(len(df))
    voltage_risk = np.where(voltage_dev > 4, 15, voltage_risk)
    voltage_risk = np.where((voltage_dev > 3) & (voltage_dev <= 4), 12, voltage_risk)
    voltage_risk = np.where((voltage_dev > 2) & (voltage_dev <= 3), 8, voltage_risk)
    voltage_risk = np.where((voltage_dev > 1) & (voltage_dev <= 2), 4, voltage_risk)
    df["voltage_risk_score"] = voltage_risk

    # 4. Frequency Deviation Risk (0-10)
    freq_dev = df["frequency_deviation_hz"].values
    freq_risk = np.zeros(len(df))
    freq_risk = np.where(freq_dev > 0.3, 10, freq_risk)
    freq_risk = np.where((freq_dev > 0.2) & (freq_dev <= 0.3), 7, freq_risk)
    freq_risk = np.where((freq_dev > 0.15) & (freq_dev <= 0.2), 5, freq_risk)
    freq_risk = np.where((freq_dev > 0.1) & (freq_dev <= 0.15), 2, freq_risk)
    df["frequency_risk_score"] = freq_risk

    # 5. Power Factor Risk (0-10)
    pf_risk = np.zeros(len(df))
    pf_risk = np.where(df["power_factor"] < 0.7, 10, pf_risk)
    pf_risk = np.where((df["power_factor"] >= 0.7) & (df["power_factor"] < 0.75), 7, pf_risk)
    pf_risk = np.where((df["power_factor"] >= 0.75) & (df["power_factor"] < 0.8), 5, pf_risk)
    pf_risk = np.where((df["power_factor"] >= 0.8) & (df["power_factor"] < 0.85), 2, pf_risk)
    df["power_factor_risk_score"] = pf_risk

    # 6. Fault Indicator Risk (0-15)
    fault_risk = np.where(df["fault_indicator"] == 1, 15, 0)
    df["fault_risk_score"] = fault_risk

    # 7. Anomaly Score Risk (0-5)
    anomaly_risk = np.zeros(len(df))
    anomaly_risk = np.where(df["anomaly_score"] > 0.7, 5, anomaly_risk)
    anomaly_risk = np.where((df["anomaly_score"] > 0.5) & (df["anomaly_score"] <= 0.7), 3, anomaly_risk)
    anomaly_risk = np.where((df["anomaly_score"] > 0.3) & (df["anomaly_score"] <= 0.5), 1, anomaly_risk)
    df["anomaly_risk_score"] = anomaly_risk

    # 8. Communication Latency Risk (0-5)
    latency_risk = np.zeros(len(df))
    latency_risk = np.where(df["communication_latency_ms"] > 50, 5, latency_risk)
    latency_risk = np.where((df["communication_latency_ms"] > 30) & (df["communication_latency_ms"] <= 50), 3, latency_risk)
    latency_risk = np.where((df["communication_latency_ms"] > 15) & (df["communication_latency_ms"] <= 30), 1, latency_risk)
    df["communication_risk_score"] = latency_risk

    # Calculate total risk score
    df["risk_score"] = (
        df["load_risk_score"] +
        df["temperature_risk_score"] +
        df["voltage_risk_score"] +
        df["frequency_risk_score"] +
        df["power_factor_risk_score"] +
        df["fault_risk_score"] +
        df["anomaly_risk_score"] +
        df["communication_risk_score"]
    ).astype(int)

    # Cap at 100
    df["risk_score"] = df["risk_score"].clip(0, 100)

    return df


def classify_risk(status: str = None, risk_score: int = 0) -> str:
    """
    Classify risk level based on score.

    Classification:
    - 0-29: Normal
    - 30-49: Low
    - 50-69: Warning
    - 70-84: High Risk
    - 85-100: Critical
    """
    if risk_score >= 85:
        return "Critical"
    elif risk_score >= 70:
        return "High Risk"
    elif risk_score >= 50:
        return "Warning"
    elif risk_score >= 30:
        return "Low"
    else:
        return "Normal"


def get_risk_distribution(df: pd.DataFrame) -> dict:
    """
    Get risk score distribution statistics.

    Returns:
        Dictionary with risk distribution statistics
    """
    df = df.copy()

    # Classify all records
    df["risk_level"] = df["risk_score"].apply(classify_risk)

    # Count by level
    distribution = df["risk_level"].value_counts().to_dict()

    # Ensure all levels present
    for level in ["Normal", "Low", "Warning", "High Risk", "Critical"]:
        if level not in distribution:
            distribution[level] = 0

    return distribution


def calculate_transformer_risk_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate aggregated risk summary per transformer.

    Returns:
        DataFrame with transformer risk metrics
    """
    # Group by transformer
    summary = df.groupby(["transformer_id", "substation_id", "region"]).agg(
        avg_load_percent=("load_percent", "mean"),
        max_load_percent=("load_percent", "max"),
        avg_temperature_c=("temperature_c", "mean"),
        max_temperature_c=("temperature_c", "max"),
        avg_voltage_kv=("voltage_kv", "mean"),
        min_voltage_kv=("voltage_kv", "min"),
        avg_power_factor=("power_factor", "mean"),
        avg_risk_score=("risk_score", "mean"),
        max_risk_score=("risk_score", "max"),
        risk_score_std=("risk_score", "std"),
        fault_count=("fault_indicator", "sum"),
        record_count=("event_id", "count"),
        avg_anomaly_score=("anomaly_score", "mean"),
        avg_latency_ms=("communication_latency_ms", "mean"),
    ).reset_index()

    # Fill NaN std values
    summary["risk_score_std"] = summary["risk_score_std"].fillna(0)

    # Determine worst status based on max risk score
    summary["worst_status"] = summary["max_risk_score"].apply(classify_risk)

    # Sort by max risk score
    summary = summary.sort_values("max_risk_score", ascending=False)

    return summary


def calculate_substation_risk_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate aggregated risk summary per substation.
    """
    summary = df.groupby(["substation_id", "region"]).agg(
        avg_load_percent=("load_percent", "mean"),
        max_load_percent=("load_percent", "max"),
        avg_temperature_c=("temperature_c", "mean"),
        avg_voltage_kv=("voltage_kv", "mean"),
        avg_power_factor=("power_factor", "mean"),
        avg_risk_score=("risk_score", "mean"),
        max_risk_score=("risk_score", "max"),
        fault_count=("fault_indicator", "sum"),
        anomaly_count=("anomaly_flag", "sum") if "anomaly_flag" in df.columns else ("risk_score", lambda x: (x > 50).sum()),
        transformer_count=("transformer_id", "nunique"),
        record_count=("event_id", "count"),
    ).reset_index()

    summary["worst_status"] = summary["max_risk_score"].apply(classify_risk)
    summary = summary.sort_values("max_risk_score", ascending=False)

    return summary


def calculate_region_risk_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate aggregated risk summary per region.
    """
    summary = df.groupby("region").agg(
        avg_load_percent=("load_percent", "mean"),
        max_load_percent=("load_percent", "max"),
        avg_temperature_c=("temperature_c", "mean"),
        avg_voltage_kv=("voltage_kv", "mean"),
        avg_power_factor=("power_factor", "mean"),
        avg_risk_score=("risk_score", "mean"),
        max_risk_score=("risk_score", "max"),
        fault_count=("fault_indicator", "sum"),
        anomaly_count=("risk_score", lambda x: (x > 50).sum()),
        transformer_count=("transformer_id", "nunique"),
        substation_count=("substation_id", "nunique"),
        record_count=("event_id", "count"),
    ).reset_index()

    summary["worst_status"] = summary["max_risk_score"].apply(classify_risk)
    summary = summary.sort_values("avg_risk_score", ascending=False)

    return summary


def main():
    """Main risk scoring execution."""
    base_path = get_base_path()

    print(f"\n{'='*60}")
    print("GRIDPULSE - RISK SCORING")
    print(f"{'='*60}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load data
    exports_path = os.path.join(base_path, "data", "exports")
    silver_path = os.path.join(base_path, "data", "silver", "grid_silver")

    print(f"\nLoading data...")
    if os.path.exists(silver_path):
        df = pd.read_parquet(silver_path)
    else:
        sample_path = os.path.join(exports_path, "silver_sample.csv")
        if os.path.exists(sample_path):
            df = pd.read_csv(sample_path)
        else:
            print("ERROR: No data found. Please generate dataset first.")
            sys.exit(1)

    print(f"Loaded {len(df):,} records")

    # Calculate risk scores
    print("\nCalculating risk scores...")
    df = calculate_risk_score(df)

    # Get risk distribution
    print("\nRisk Distribution:")
    risk_dist = get_risk_distribution(df)

    for level in ["Critical", "High Risk", "Warning", "Low", "Normal"]:
        count = risk_dist.get(level, 0)
        pct = (count / len(df)) * 100
        print(f"  {level:12s}: {count:>8,} ({pct:5.1f}%)")

    print(f"\nRisk Score Statistics:")
    print(f"  Mean:   {df['risk_score'].mean():.1f}")
    print(f"  Median: {df['risk_score'].median():.1f}")
    print(f"  Std:    {df['risk_score'].std():.1f}")
    print(f"  Min:    {df['risk_score'].min()}")
    print(f"  Max:    {df['risk_score'].max()}")

    print(f"\nTop 10 Highest Risk Records:")
    top_risk = df.nlargest(10, "risk_score")[
        ["event_id", "transformer_id", "substation_id", "region",
         "load_percent", "temperature_c", "voltage_kv", "risk_score", "status"]
    ]
    for _, row in top_risk.iterrows():
        print(f"  {row['transformer_id']:12s} | Load: {row['load_percent']:5.1f}% | "
              f"Temp: {row['temperature_c']:4.1f}°C | Risk: {row['risk_score']:3d} | "
              f"Status: {row['status']}")

    # Calculate transformer risk summary
    print(f"\nCalculating transformer risk summary...")
    transformer_summary = calculate_transformer_risk_summary(df)

    # Save transformer summary
    transformer_summary.to_csv(
        os.path.join(exports_path, "transformer_risk_summary.csv"),
        index=False
    )
    print(f"  Saved: transformer_risk_summary.csv ({len(transformer_summary):,} transformers)")

    # Calculate substation risk summary
    print(f"\nCalculating substation risk summary...")
    substation_summary = calculate_substation_risk_summary(df)
    substation_summary.to_csv(
        os.path.join(exports_path, "substation_risk_summary.csv"),
        index=False
    )
    print(f"  Saved: substation_risk_summary.csv ({len(substation_summary):,} substations)")

    # Calculate region risk summary
    print(f"\nCalculating region risk summary...")
    region_summary = calculate_region_risk_summary(df)
    region_summary.to_csv(
        os.path.join(exports_path, "region_risk_summary.csv"),
        index=False
    )
    print(f"  Saved: region_risk_summary.csv ({len(region_summary):,} regions)")

    # Save updated data
    print(f"\nSaving updated data...")
    df.to_parquet(silver_path, index=False)
    print(f"  Updated Silver data saved")

    # Export critical transformers
    critical = df[df["risk_score"] >= 85]
    if len(critical) > 0:
        critical_summary = critical.groupby(["transformer_id", "substation_id", "region"]).agg(
            avg_load=("load_percent", "mean"),
            max_temp=("temperature_c", "max"),
            avg_voltage=("voltage_kv", "mean"),
            avg_risk=("risk_score", "mean"),
            max_risk=("risk_score", "max"),
            anomaly_types=("anomaly_type", lambda x: ", ".join(sorted(set(x)))),
        ).reset_index()

        critical_summary.to_csv(
            os.path.join(exports_path, "critical_transformers.csv"),
            index=False
        )
        print(f"  Exported: critical_transformers.csv ({len(critical_summary):,} transformers)")
    else:
        print(f"  No critical transformers found")

    print(f"\n{'='*60}")
    print("RISK SCORING COMPLETE")
    print(f"{'='*60}")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()

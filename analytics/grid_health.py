#!/usr/bin/env python
"""
GridPulse Grid Health Analytics
Calculates overall grid health metrics and transformer health assessments
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def get_base_path() -> Path:
    """Get the base project path."""
    return Path(__file__).parent.parent


def calculate_grid_health(df: pd.DataFrame) -> dict:
    """
    Calculate overall grid health metrics.

    Returns:
        Dictionary with grid health statistics
    """
    df = df.copy()

    total_records = len(df)
    total_transformers = df["transformer_id"].nunique()
    total_substations = df["substation_id"].nunique()
    total_regions = df["region"].nunique()

    # Status distribution
    status_counts = df["status"].value_counts().to_dict()

    # Calculate health metrics
    normal_count = status_counts.get("Normal", 0)
    warning_count = status_counts.get("Warning", 0)
    high_risk_count = status_counts.get("High Risk", 0)
    critical_count = status_counts.get("Critical", 0)
    low_count = status_counts.get("Low", 0)

    # Health percentage (normal / total)
    health_percentage = (normal_count / total_records) * 100 if total_records > 0 else 0

    # Fault statistics
    total_faults = df["fault_indicator"].sum()
    fault_rate = (total_faults / total_records) * 100 if total_records > 0 else 0

    # Average metrics
    avg_load = df["load_percent"].mean()
    avg_temperature = df["temperature_c"].mean()
    avg_voltage = df["voltage_kv"].mean()
    avg_power_factor = df["power_factor"].mean()
    avg_risk = df["risk_score"].mean()
    avg_anomaly_score = df["anomaly_score"].mean()

    # Peak metrics
    max_load = df["load_percent"].max()
    max_temperature = df["temperature_c"].max()
    max_risk = df["risk_score"].max()

    # Energy metrics
    total_generation = df["energy_generated_mwh"].sum()
    total_consumption = df["energy_consumed_mwh"].sum()
    avg_efficiency = df["transmission_efficiency"].mean() if "transmission_efficiency" in df.columns else 0

    # Anomaly statistics
    anomaly_count = df["anomaly_flag"].sum() if "anomaly_flag" in df.columns else (df["risk_score"] > 50).sum()
    anomaly_rate = (anomaly_count / total_records) * 100 if total_records > 0 else 0

    # Communication latency
    avg_latency = df["communication_latency_ms"].mean()
    max_latency = df["communication_latency_ms"].max()

    # Load distribution
    load_distribution = {
        "low": int((df["load_percent"] < 30).sum()),
        "medium": int(((df["load_percent"] >= 30) & (df["load_percent"] < 60)).sum()),
        "high": int(((df["load_percent"] >= 60) & (df["load_percent"] < 85)).sum()),
        "critical": int((df["load_percent"] >= 85).sum()),
    }

    # Temperature distribution
    temp_distribution = {
        "normal": int((df["temperature_c"] < 50).sum()),
        "elevated": int(((df["temperature_c"] >= 50) & (df["temperature_c"] < 60)).sum()),
        "high": int(((df["temperature_c"] >= 60) & (df["temperature_c"] < 70)).sum()),
        "critical": int((df["temperature_c"] >= 70).sum()),
    }

    # Time-based analysis (last 24 hours vs previous)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    latest_time = df["timestamp"].max()
    last_24h = latest_time - timedelta(hours=24)

    recent_df = df[df["timestamp"] >= last_24h]
    previous_df = df[(df["timestamp"] < last_24h) & (df["timestamp"] >= last_24h - timedelta(hours=48))]

    if len(recent_df) > 0 and len(previous_df) > 0:
        load_trend = recent_df["load_percent"].mean() - previous_df["load_percent"].mean()
        temp_trend = recent_df["temperature_c"].mean() - previous_df["temperature_c"].mean()
        risk_trend = recent_df["risk_score"].mean() - previous_df["risk_score"].mean()
    else:
        load_trend = 0
        temp_trend = 0
        risk_trend = 0

    health_metrics = {
        "total_records": total_records,
        "total_transformers": total_transformers,
        "total_substations": total_substations,
        "total_regions": total_regions,
        "status_distribution": {
            "Normal": normal_count,
            "Low": low_count,
            "Warning": warning_count,
            "High Risk": high_risk_count,
            "Critical": critical_count,
        },
        "health_percentage": health_percentage,
        "total_faults": int(total_faults),
        "fault_rate": fault_rate,
        "avg_load_percent": avg_load,
        "avg_temperature_c": avg_temperature,
        "avg_voltage_kv": avg_voltage,
        "avg_power_factor": avg_power_factor,
        "avg_risk_score": avg_risk,
        "avg_anomaly_score": avg_anomaly_score,
        "max_load_percent": max_load,
        "max_temperature_c": max_temperature,
        "max_risk_score": max_risk,
        "total_energy_generated_mwh": total_generation,
        "total_energy_consumed_mwh": total_consumption,
        "avg_efficiency": avg_efficiency,
        "anomaly_count": int(anomaly_count),
        "anomaly_rate": anomaly_rate,
        "avg_latency_ms": avg_latency,
        "max_latency_ms": max_latency,
        "load_distribution": load_distribution,
        "temperature_distribution": temp_distribution,
        "load_trend": load_trend,
        "temp_trend": temp_trend,
        "risk_trend": risk_trend,
        "latest_timestamp": latest_time,
        "time_range_start": df["timestamp"].min(),
    }

    return health_metrics


def calculate_transformer_health(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate health score for each transformer.

    Health Score Components:
    - Reliability: Based on fault history
    - Stability: Based on voltage and frequency stability
    - Efficiency: Based on power factor
    - Safety: Based on temperature and risk

    Returns:
        DataFrame with transformer health metrics
    """
    transformer_health = df.groupby(["transformer_id", "substation_id", "region"]).agg(
        # Basic metrics
        record_count=("event_id", "count"),
        avg_load_percent=("load_percent", "mean"),
        max_load_percent=("load_percent", "max"),
        min_load_percent=("load_percent", "min"),
        load_std=("load_percent", "std"),

        avg_temperature_c=("temperature_c", "mean"),
        max_temperature_c=("temperature_c", "max"),
        temp_std=("temperature_c", "std"),

        avg_voltage_kv=("voltage_kv", "mean"),
        voltage_std=("voltage_kv", "std"),
        min_voltage_kv=("voltage_kv", "min"),
        max_voltage_kv=("voltage_kv", "max"),

        avg_frequency_hz=("frequency_hz", "mean"),
        freq_std=("frequency_hz", "std"),

        avg_power_factor=("power_factor", "mean"),
        min_power_factor=("power_factor", "min"),

        avg_power_mw=("power_mw", "mean"),
        total_energy_generated=("energy_generated_mwh", "sum"),
        total_energy_consumed=("energy_consumed_mwh", "sum"),

        # Risk metrics
        avg_risk_score=("risk_score", "mean"),
        max_risk_score=("risk_score", "max"),
        risk_std=("risk_score", "std"),

        # Anomaly metrics
        avg_anomaly_score=("anomaly_score", "mean"),
        max_anomaly_score=("anomaly_score", "max"),
        anomaly_count=("risk_score", lambda x: (x > 50).sum()),

        # Fault metrics
        fault_count=("fault_indicator", "sum"),

        # Communication metrics
        avg_latency_ms=("communication_latency_ms", "mean"),
        max_latency_ms=("communication_latency_ms", "max"),

        # Status tracking
        normal_count=("status", lambda x: (x == "Normal").sum()),
        warning_count=("status", lambda x: (x == "Warning").sum()),
        high_risk_count=("status", lambda x: (x == "High Risk").sum()),
        critical_count=("status", lambda x: (x == "Critical").sum()),

        # Anomaly type diversity
        distinct_anomaly_types=("anomaly_type", lambda x: x[x != "Normal"].nunique()),

        # Last seen timestamp
        last_seen=("timestamp", "max"),
        first_seen=("timestamp", "min"),

    ).reset_index()

    # Fill NaN values
    transformer_health = transformer_health.fillna(0)

    # Calculate health score (0-100)
    # Higher is better

    # Reliability score (0-25): Based on fault rate
    max_faults = transformer_health["fault_count"].max()
    if max_faults > 0:
        transformer_health["reliability_score"] = 25 * (1 - transformer_health["fault_count"] / max_faults)
    else:
        transformer_health["reliability_score"] = 25

    # Stability score (0-25): Based on voltage and frequency std
    voltage_stability = 25 * (1 - transformer_health["voltage_std"] / transformer_health["voltage_std"].max() if transformer_health["voltage_std"].max() > 0 else 0)
    freq_stability = 25 * (1 - transformer_health["freq_std"] / transformer_health["freq_std"].max() if transformer_health["freq_std"].max() > 0 else 0)

    transformer_health["stability_score"] = (voltage_stability + freq_stability) / 2

    # Efficiency score (0-25): Based on power factor
    transformer_health["efficiency_score"] = 25 * (transformer_health["avg_power_factor"] - 0.7) / 0.3
    transformer_health["efficiency_score"] = transformer_health["efficiency_score"].clip(0, 25)

    # Safety score (0-25): Based on max temperature and max risk
    temp_safety = 25 * (1 - transformer_health["max_temperature_c"] / 85)
    risk_safety = 25 * (1 - transformer_health["max_risk_score"] / 100)

    transformer_health["safety_score"] = (temp_safety + risk_safety) / 2

    # Total health score
    transformer_health["health_score"] = (
        transformer_health["reliability_score"] +
        transformer_health["stability_score"] +
        transformer_health["efficiency_score"] +
        transformer_health["safety_score"]
    )

    transformer_health["health_score"] = transformer_health["health_score"].clip(0, 100)

    # Health classification
    transformer_health["health_status"] = pd.cut(
        transformer_health["health_score"],
        bins=[0, 40, 60, 80, 100],
        labels=["Critical", "Poor", "Fair", "Good"]
    )

    # Sort by health score
    transformer_health = transformer_health.sort_values("health_score", ascending=False)

    return transformer_health


def calculate_substation_health(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate health metrics per substation.
    """
    substation_health = df.groupby(["substation_id", "region"]).agg(
        transformer_count=("transformer_id", "nunique"),
        record_count=("event_id", "count"),

        avg_load_percent=("load_percent", "mean"),
        max_load_percent=("load_percent", "max"),
        avg_temperature_c=("temperature_c", "mean"),
        max_temperature_c=("temperature_c", "max"),

        avg_voltage_kv=("voltage_kv", "mean"),
        avg_power_factor=("power_factor", "mean"),

        avg_risk_score=("risk_score", "mean"),
        max_risk_score=("risk_score", "max"),

        fault_count=("fault_indicator", "sum"),
        anomaly_count=("risk_score", lambda x: (x > 50).sum()),

        normal_count=("status", lambda x: (x == "Normal").sum()),
        warning_count=("status", lambda x: (x == "Warning").sum()),
        high_risk_count=("status", lambda x: (x == "High Risk").sum()),
        critical_count=("status", lambda x: (x == "Critical").sum()),

        total_energy_generated=("energy_generated_mwh", "sum"),
        total_energy_consumed=("energy_consumed_mwh", "sum"),

    ).reset_index()

    substation_health = substation_health.fillna(0)

    # Classify substation health
    substation_health["health_status"] = substation_health["max_risk_score"].apply(
        lambda x: "Critical" if x >= 85 else
                  "High Risk" if x >= 70 else
                  "Warning" if x >= 50 else
                  "Normal"
    )

    substation_health = substation_health.sort_values("max_risk_score", ascending=False)

    return substation_health


def calculate_region_health(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate health metrics per region.
    """
    region_health = df.groupby("region").agg(
        substation_count=("substation_id", "nunique"),
        transformer_count=("transformer_id", "nunique"),
        record_count=("event_id", "count"),

        avg_load_percent=("load_percent", "mean"),
        max_load_percent=("load_percent", "max"),
        avg_temperature_c=("temperature_c", "mean"),
        max_temperature_c=("temperature_c", "max"),

        avg_voltage_kv=("voltage_kv", "mean"),
        avg_power_factor=("power_factor", "mean"),

        avg_risk_score=("risk_score", "mean"),
        max_risk_score=("risk_score", "max"),

        total_faults=("fault_indicator", "sum"),
        anomaly_count=("risk_score", lambda x: (x > 50).sum()),

        normal_count=("status", lambda x: (x == "Normal").sum()),
        warning_count=("status", lambda x: (x == "Warning").sum()),
        high_risk_count=("status", lambda x: (x == "High Risk").sum()),
        critical_count=("status", lambda x: (x == "Critical").sum()),

        total_generation=("energy_generated_mwh", "sum"),
        total_consumption=("energy_consumed_mwh", "sum"),

        avg_efficiency=("transmission_efficiency", "mean") if "transmission_efficiency" in df.columns else 0,

    ).reset_index()

    region_health = region_health.fillna(0)

    # Classification
    region_health["health_status"] = region_health["max_risk_score"].apply(
        lambda x: "Critical" if x >= 85 else
                  "High Risk" if x >= 70 else
                  "Warning" if x >= 50 else
                  "Normal"
    )

    region_health = region_health.sort_values("avg_risk_score", ascending=False)

    # Calculate health percentage
    region_health["health_percentage"] = (region_health["normal_count"] / region_health["record_count"]) * 100

    return region_health


def main():
    """Main grid health analysis."""
    base_path = get_base_path()

    print(f"\n{'='*60}")
    print("GRIDPULSE - GRID HEALTH ANALYSIS")
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

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    print(f"Loaded {len(df):,} records")

    # Calculate grid health
    print("\nCalculating grid health...")
    health_metrics = calculate_grid_health(df)

    print(f"\n{'='*60}")
    print("GRID HEALTH SUMMARY")
    print(f"{'='*60}")

    print(f"\nInfrastructure:")
    print(f"  Regions:        {health_metrics['total_regions']}")
    print(f"  Substations:    {health_metrics['total_substations']}")
    print(f"  Transformers:   {health_metrics['total_transformers']:,}")
    print(f"  Total Records:  {health_metrics['total_records']:,}")

    print(f"\nStatus Distribution:")
    for status, count in health_metrics["status_distribution"].items():
        pct = (count / health_metrics["total_records"]) * 100
        print(f"  {status:12s}: {count:>8,} ({pct:5.1f}%)")

    print(f"\nHealth Metrics:")
    print(f"  Overall Health:    {health_metrics['health_percentage']:.1f}%")
    print(f"  Avg Load:          {health_metrics['avg_load_percent']:.1f}%")
    print(f"  Avg Temperature:   {health_metrics['avg_temperature_c']:.1f}°C")
    print(f"  Avg Voltage:       {health_metrics['avg_voltage_kv']:.2f} kV")
    print(f"  Avg Power Factor:  {health_metrics['avg_power_factor']:.3f}")
    print(f"  Avg Risk Score:    {health_metrics['avg_risk_score']:.1f}")
    print(f"  Avg Anomaly Score: {health_metrics['avg_anomaly_score']:.4f}")

    print(f"\nFault Statistics:")
    print(f"  Total Faults:      {health_metrics['total_faults']:,}")
    print(f"  Fault Rate:        {health_metrics['fault_rate']:.2f}%")

    print(f"\nEnergy Metrics:")
    print(f"  Total Generation:  {health_metrics['total_energy_generated_mwh']:,.0f} MWh")
    print(f"  Total Consumption: {health_metrics['total_energy_consumed_mwh']:,.0f} MWh")
    print(f"  Avg Efficiency:    {health_metrics['avg_efficiency']:.1f}%")

    print(f"\nTrends (Last 24h vs Previous):")
    print(f"  Load Trend:    {health_metrics['load_trend']:+.1f}%")
    print(f"  Temp Trend:    {health_metrics['temp_trend']:+.1f}°C")
    print(f"  Risk Trend:    {health_metrics['risk_trend']:+.1f}")

    # Calculate transformer health
    print(f"\n{'='*60}")
    print("TRANSFORMER HEALTH ANALYSIS")
    print(f"{'='*60}")

    transformer_health = calculate_transformer_health(df)
    transformer_health.to_csv(
        os.path.join(exports_path, "transformer_health.csv"),
        index=False
    )
    print(f"\nSaved: transformer_health.csv ({len(transformer_health):,} transformers)")

    print(f"\nHealth Score Distribution:")
    print(f"  Good (80-100):    {(transformer_health['health_score'] >= 80).sum():,} transformers")
    print(f"  Fair (60-79):     {((transformer_health['health_score'] >= 60) & (transformer_health['health_score'] < 80)).sum():,} transformers")
    print(f"  Poor (40-59):     {((transformer_health['health_score'] >= 40) & (transformer_health['health_score'] < 60)).sum():,} transformers")
    print(f"  Critical (<40):   {(transformer_health['health_score'] < 40).sum():,} transformers")

    print(f"\nTop 5 Healthiest Transformers:")
    for _, row in transformer_health.head(5).iterrows():
        print(f"  {row['transformer_id']:12s} | Health: {row['health_score']:5.1f}% | "
              f"Load: {row['avg_load_percent']:5.1f}% | "
              f"Temp: {row['avg_temperature_c']:4.1f}°C")

    print(f"\nTop 5 Most Stressed Transformers:")
    for _, row in transformer_health.tail(5).iterrows():
        print(f"  {row['transformer_id']:12s} | Health: {row['health_score']:5.1f}% | "
              f"Load: {row['avg_load_percent']:5.1f}% | "
              f"Temp: {row['avg_temperature_c']:4.1f}°C | "
              f"Faults: {int(row['fault_count'])}")

    # Calculate substation health
    print(f"\n{'='*60}")
    print("SUBSTATION HEALTH ANALYSIS")
    print(f"{'='*60}")

    substation_health = calculate_substation_health(df)
    substation_health.to_csv(
        os.path.join(exports_path, "substation_health.csv"),
        index=False
    )
    print(f"\nSaved: substation_health.csv ({len(substation_health):,} substations)")

    print(f"\nSubstation Status Distribution:")
    for status in ["Critical", "High Risk", "Warning", "Normal"]:
        count = (substation_health["health_status"] == status).sum()
        print(f"  {status:12s}: {count} substations")

    # Calculate region health
    print(f"\n{'='*60}")
    print("REGION HEALTH ANALYSIS")
    print(f"{'='*60}")

    region_health = calculate_region_health(df)
    region_health.to_csv(
        os.path.join(exports_path, "region_health.csv"),
        index=False
    )
    print(f"\nSaved: region_health.csv ({len(region_health):,} regions)")

    print(f"\nRegional Health Summary:")
    for _, row in region_health.iterrows():
        print(f"  {row['region']:12s} | Transformers: {int(row['transformer_count']):3d} | "
              f"Substations: {int(row['substation_count']):2d} | "
              f"Avg Risk: {row['avg_risk_score']:5.1f} | "
              f"Health: {row['health_percentage']:5.1f}% | "
              f"Status: {row['health_status']}")

    # Save grid health summary
    import json
    with open(os.path.join(exports_path, "grid_health_summary.json"), "w") as f:
        json.dump(health_metrics, f, indent=2, default=str)
    print(f"\nSaved: grid_health_summary.json")

    print(f"\n{'='*60}")
    print("GRID HEALTH ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
GridPulse Anomaly Detection
Uses Isolation Forest ML algorithm to detect grid anomalies
"""

import os
import sys
import pickle
from datetime import datetime
from pathlib import Path

# Auto-detect local JDK 17
import pipeline  # noqa: F401

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from analytics.risk_scoring import calculate_risk_score


def get_base_path() -> Path:
    """Get the base project path."""
    return Path(__file__).parent.parent


def load_silver_data(path: str) -> pd.DataFrame:
    """Load Silver layer data."""
    if not os.path.exists(path):
        print(f"ERROR: Silver data not found at {path}")
        sys.exit(1)

    df = pd.read_parquet(path) if path.endswith('.parquet') else pd.read_csv(path)

    print(f"Loaded {len(df):,} records from Silver layer")
    return df


def prepare_anomaly_features(df: pd.DataFrame) -> np.ndarray:
    """
    Prepare features for anomaly detection.

    Features:
    - load_percent
    - temperature_c
    - voltage_kv
    - frequency_hz
    - power_factor
    - power_mw
    - energy_consumed_mwh
    - communication_latency_ms
    """
    feature_columns = [
        "load_percent",
        "temperature_c",
        "voltage_kv",
        "frequency_hz",
        "power_factor",
        "power_mw",
        "energy_consumed_mwh",
        "communication_latency_ms"
    ]

    # Check for required columns
    missing_cols = [c for c in feature_columns if c not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns: {missing_cols}")
        sys.exit(1)

    # Select features
    X = df[feature_columns].values

    # Handle any NaN values
    X = np.nan_to_num(X, nan=0.0)

    return X


def train_isolation_forest(X: np.ndarray, contamination: float = 0.15) -> IsolationForest:
    """
    Train Isolation Forest model.

    Args:
        X: Feature matrix
        contamination: Expected proportion of anomalies

    Returns:
        Trained IsolationForest model
    """
    print(f"\nTraining Isolation Forest...")
    print(f"  Samples: {X.shape[0]:,}")
    print(f"  Features: {X.shape[1]}")
    print(f"  Expected contamination: {contamination*100}%")

    model = IsolationForest(
        n_estimators=200,
        max_samples='auto',
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
        bootstrap=False
    )

    model.fit(X)

    return model


def detect_anomalies(
    df: pd.DataFrame,
    model: IsolationForest,
    scaler: StandardScaler
) -> pd.DataFrame:
    """
    Detect anomalies in the dataset.

    Args:
        df: Input dataframe
        model: Trained IsolationForest
        scaler: Fitted StandardScaler

    Returns:
        DataFrame with anomaly scores and flags
    """
    feature_columns = [
        "load_percent",
        "temperature_c",
        "voltage_kv",
        "frequency_hz",
        "power_factor",
        "power_mw",
        "energy_consumed_mwh",
        "communication_latency_ms"
    ]

    # Prepare features
    X = df[feature_columns].values
    X = np.nan_to_num(X, nan=0.0)

    # Scale features
    X_scaled = scaler.transform(X)

    # Predict anomalies (-1 for anomaly, 1 for normal)
    predictions = model.predict(X_scaled)

    # Get anomaly scores (decision function)
    scores = model.decision_function(X_scaled)
    anomaly_scores = 1 - (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)

    # Add predictions to dataframe
    df = df.copy()
    df["anomaly_prediction"] = predictions
    df["anomaly_flag"] = (predictions == -1).astype(int)
    df["anomaly_score_ml"] = np.clip(anomaly_scores, 0, 1)

    # Combine with existing anomaly score
    if "anomaly_score" in df.columns:
        df["anomaly_score"] = (
            df["anomaly_score"] * 0.3 +
            df["anomaly_score_ml"] * 0.7
        )
    else:
        df["anomaly_score"] = df["anomaly_score_ml"]

    # Update anomaly type based on ML detection
    df = update_anomaly_types(df)

    return df


def update_anomaly_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Update anomaly types based on anomaly scores and conditions.
    """
    df = df.copy()

    # Only update for records that are actually anomalous
    mask = df["anomaly_flag"] == 1

    if mask.sum() == 0:
        df["anomaly_type"] = "Normal"
        return df

    df.loc[mask, "anomaly_type"] = df.loc[mask].apply(
        lambda row: determine_anomaly_type(row),
        axis=1
    )

    # Set Normal for non-anomalous records
    df.loc[~mask, "anomaly_type"] = "Normal"

    return df


def determine_anomaly_type(row) -> str:
    """
    Determine the specific anomaly type based on conditions.
    """
    load = row.get("load_percent", 50)
    temp = row.get("temperature_c", 45)
    voltage = row.get("voltage_kv", 40)
    frequency = row.get("frequency_hz", 50)
    pf = row.get("power_factor", 0.95)
    latency = row.get("communication_latency_ms", 5)
    fault = row.get("fault_indicator", 0)

    # Compound conditions
    if load > 90 and temp > 70:
        return "Compound Anomaly"

    # Specific anomalies
    if load > 90:
        return "Overload"

    if temp > 70:
        return "Temperature Spike"

    if abs(voltage - 40) > 4:
        return "Voltage Fluctuation"

    if abs(frequency - 50) > 0.25:
        return "Frequency Deviation"

    if pf < 0.75:
        return "Power Factor Anomaly"

    if latency > 40:
        return "Communication Failure"

    if fault == 1:
        return "Transformer Fault"

    # Random assignment for other anomalies
    anomaly_types = [
        "Voltage Fluctuation",
        "Overload",
        "Temperature Spike",
        "Frequency Deviation",
        "Power Factor Anomaly",
        "Transformer Fault",
        "Communication Failure",
        "Unexpected Consumption",
        "Generation Drop"
    ]

    return np.random.choice(anomaly_types)


def save_model(model: IsolationForest, scaler: StandardScaler, path: str):
    """Save trained model and scaler."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

    model_data = {
        "model": model,
        "scaler": scaler,
        "feature_columns": [
            "load_percent",
            "temperature_c",
            "voltage_kv",
            "frequency_hz",
            "power_factor",
            "power_mw",
            "energy_consumed_mwh",
            "communication_latency_ms"
        ],
        "training_date": datetime.now().isoformat()
    }

    with open(path, 'wb') as f:
        pickle.dump(model_data, f)

    print(f"Model saved to: {path}")


def main():
    """Main anomaly detection execution."""
    base_path = get_base_path()

    print(f"\n{'='*60}")
    print("GRIDPULSE - ANOMALY DETECTION (ISOLATION FOREST)")
    print(f"{'='*60}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load data
    silver_path = os.path.join(base_path, "data", "silver", "grid_silver")
    exports_path = os.path.join(base_path, "data", "exports")

    print(f"\nLoading Silver data...")
    df = load_silver_data(silver_path)

    print(f"\nInitial status distribution:")
    print(df["status"].value_counts().to_string())

    # Prepare features
    print(f"\nPreparing features for anomaly detection...")
    X = prepare_anomaly_features(df)
    print(f"Feature matrix shape: {X.shape}")

    # Standardize features
    print("\nStandardizing features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train Isolation Forest
    model = train_isolation_forest(X_scaled, contamination=0.12)

    # Detect anomalies
    print("\nDetecting anomalies...")
    df_anomalies = detect_anomalies(df, model, scaler)

    # Calculate risk scores
    print("\nCalculating risk scores...")
    df_anomalies = calculate_risk_score(df_anomalies)

    # Update status based on new risk scores
    df_anomalies["status"] = df_anomalies["risk_score"].apply(
        lambda x: "Critical" if x >= 85 else
                  "High Risk" if x >= 70 else
                  "Warning" if x >= 50 else
                  "Low" if x >= 30 else
                  "Normal"
    )

    # Statistics
    print(f"\n{'='*60}")
    print("ANOMALY DETECTION RESULTS")
    print(f"{'='*60}")

    anomaly_count = df_anomalies["anomaly_flag"].sum()
    total_count = len(df_anomalies)
    anomaly_rate = (anomaly_count / total_count) * 100

    print(f"\nTotal Records: {total_count:,}")
    print(f"Anomalies Detected: {anomaly_count:,} ({anomaly_rate:.2f}%)")
    print(f"Normal Records: {total_count - anomaly_count:,}")

    print(f"\nAnomaly Score Statistics:")
    print(f"  Mean: {df_anomalies['anomaly_score'].mean():.4f}")
    print(f"  Std:  {df_anomalies['anomaly_score'].std():.4f}")
    print(f"  Min:  {df_anomalies['anomaly_score'].min():.4f}")
    print(f"  Max:  {df_anomalies['anomaly_score'].max():.4f}")

    print(f"\nAnomaly Type Distribution:")
    anomaly_types = df_anomalies[df_anomalies["anomaly_flag"] == 1]["anomaly_type"].value_counts()
    for anomaly_type, count in anomaly_types.items():
        print(f"  {anomaly_type}: {count:,} ({count/anomaly_count*100:.1f}%)")

    print(f"\nStatus Distribution (Updated):")
    status_counts = df_anomalies["status"].value_counts()
    for status, count in status_counts.items():
        print(f"  {status}: {count:,} ({count/total_count*100:.1f}%)")

    # Save model
    model_path = os.path.join(base_path, "analytics", "anomaly_model.pkl")
    save_model(model, scaler, model_path)

    # Save results
    print(f"\nSaving results...")
    os.makedirs(silver_path, exist_ok=True)
    df_anomalies.to_parquet(silver_path, index=False)
    print(f"  Updated Silver data saved")

    # Export anomaly summary
    anomaly_summary = df_anomalies[df_anomalies["anomaly_flag"] == 1].groupby(
        ["anomaly_type", "status"]
    ).agg(
        count=("event_id", "count"),
        avg_score=("anomaly_score", "mean"),
        avg_risk=("risk_score", "mean"),
        avg_load=("load_percent", "mean"),
        avg_temp=("temperature_c", "mean")
    ).reset_index()

    anomaly_summary.to_csv(
        os.path.join(exports_path, "anomaly_detection_summary.csv"),
        index=False
    )
    print(f"  Anomaly summary exported")

    # Export severity summary
    severity_summary = df_anomalies.groupby("status").agg(
        count=("event_id", "count"),
        avg_risk=("risk_score", "mean"),
        avg_score=("anomaly_score", "mean")
    ).reset_index()

    severity_summary.to_csv(
        os.path.join(exports_path, "severity_summary.csv"),
        index=False
    )
    print(f"  Severity summary exported")

    print(f"\n{'='*60}")
    print("ANOMALY DETECTION COMPLETE")
    print(f"{'='*60}")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()

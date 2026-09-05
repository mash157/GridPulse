#!/usr/bin/env python
"""
GridPulse Analytics Service
Reads processed PySpark data and serves API responses
"""

import os
import sys
import json
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

import numpy as np
import pandas as pd


def classify_risk(score: float) -> str:
    """Canonical 5-band status mapping.

    0-29 Normal, 30-49 Low, 50-69 Warning, 70-84 High Risk, 85-100 Critical.
    """
    if score >= 85:
        return "Critical"
    elif score >= 70:
        return "High Risk"
    elif score >= 50:
        return "Warning"
    elif score >= 30:
        return "Low"
    return "Normal"


class AnalyticsService:
    """Serves analytics data from processed Gold/Silver layers."""

    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / "data"
        self.exports_path = self.data_path / "exports"
        self.gold_path = self.data_path / "gold" / "gold_data"
        self.silver_path = self.data_path / "silver" / "grid_silver"

        self._df = None  # Main dataframe
        self._loaded = False

    @property
    def is_loaded(self):
        return self._loaded

    @property
    def record_count(self):
        return len(self._df) if self._df is not None else 0

    def load_data(self):
        """Load all processed data."""
        try:
            self._load_silver_data()
            self._loaded = True
            print(f"AnalyticsService loaded: {self.record_count:,} records")
        except Exception as e:
            print(f"Warning: Could not load data: {e}")
            self._loaded = False

    def _load_silver_data(self):
        """Load the silver layer data (main dataset)."""
        # Try CSV first (pandas pipeline), then parquet (PySpark pipeline)
        candidates = [
            self.data_path / "silver" / "grid_silver.csv",
            self.silver_path,  # parquet dir
            self.exports_path / "silver_sample.csv",
            self.exports_path / "silver_full.csv",
        ]

        loaded = False
        for path in candidates:
            if os.path.exists(path):
                try:
                    if str(path).endswith(".csv"):
                        self._df = pd.read_csv(path)
                    else:
                        self._df = pd.read_parquet(path)
                    print(f"  Loaded from: {path}")
                    loaded = True
                    break
                except Exception as e:
                    print(f"  Failed to load {path}: {e}")
                    continue

        if not loaded:
            raise FileNotFoundError(f"No silver data found. Checked: {candidates}")

        # Ensure required columns
        if "voltage_deviation_kv" not in self._df.columns:
            self._df["voltage_deviation_kv"] = self._df["voltage_kv"] - 40.0
        if "frequency_deviation_hz" not in self._df.columns:
            self._df["frequency_deviation_hz"] = self._df["frequency_hz"] - 50.0
        if "anomaly_flag" not in self._df.columns:
            self._df["anomaly_flag"] = (self._df["status"] != "Normal").astype(int)

    def _parse_anomaly_types(self, anomaly_type: Optional[str]) -> Optional[List[str]]:
        """Parse anomaly_type filter which can be comma-separated.

        Examples:
          'Overload' -> ['Overload']
          'Overload,Temperature Spike' -> ['Overload', 'Temperature Spike']
          None -> None (no filter)
        """
        if not anomaly_type:
            return None
        types = [t.strip() for t in anomaly_type.split(",") if t.strip()]
        return types if types else None

    def _apply_filters(
        self,
        df: pd.DataFrame,
        region: Optional[str] = None,
        substation: Optional[str] = None,
        transformer: Optional[str] = None,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        anomaly_type: Optional[str] = None,
        time_range: Optional[str] = None,
    ) -> pd.DataFrame:
        """Apply common filters to dataframe.

        anomaly_type supports comma-separated values for multi-select:
          'Overload,Temperature Spike' => filter to either type.
        """
        filtered = df.copy()

        if region:
            filtered = filtered[filtered["region"] == region]
        if substation:
            filtered = filtered[filtered["substation_id"] == substation]
        if transformer:
            filtered = filtered[filtered["transformer_id"] == transformer]
        if status:
            filtered = filtered[filtered["status"] == status]

        # Multi-select anomaly type filter
        anomaly_types = self._parse_anomaly_types(anomaly_type)
        if anomaly_types:
            filtered = filtered[filtered["anomaly_type"].isin(anomaly_types)]

        if risk_level:
            rl = risk_level.lower()
            # 5-band mapping consistent with classify_risk / the Gold dataset:
            # Critical >= 85, High Risk 70-84, Warning 50-69, Low 30-49.
            if rl == "critical":
                filtered = filtered[filtered["risk_score"] >= 85]
            elif rl == "high":
                filtered = filtered[(filtered["risk_score"] >= 70) & (filtered["risk_score"] < 85)]
            elif rl == "warning":
                filtered = filtered[(filtered["risk_score"] >= 50) & (filtered["risk_score"] < 70)]
            elif rl == "low":
                filtered = filtered[(filtered["risk_score"] >= 30) & (filtered["risk_score"] < 50)]
            elif rl == "normal":
                filtered = filtered[filtered["risk_score"] < 30]

        if time_range and "timestamp" in filtered.columns:
            try:
                ts = pd.to_datetime(filtered["timestamp"])
                data_max = ts.max()  # Use latest timestamp in data as reference
                hours_map = {"24h": 24, "7d": 168, "30d": 720, "90d": 2160, "72h": 72, "6h": 6, "12h": 12, "48h": 48}
                hours = hours_map.get(time_range, 2160)  # Default to 90d for historical data
                cutoff = data_max - pd.Timedelta(hours=hours)
                filtered = filtered[ts >= cutoff]
            except Exception:
                pass

        return filtered

    def _calculate_trend(self, df: pd.DataFrame, metric: str, fraction: float = 0.2) -> float:
        """Calculate trend percentage for a metric by comparing recent vs earlier data."""
        if "timestamp" not in df.columns or len(df) < 10:
            return 0.0

        try:
            df_sorted = df.sort_values("timestamp")
            n = len(df_sorted)
            split_idx = int(n * (1 - fraction))

            if split_idx < 1 or split_idx >= n:
                return 0.0

            recent = df_sorted.iloc[split_idx:]
            earlier = df_sorted.iloc[:split_idx]

            if metric not in recent.columns:
                return 0.0

            recent_val = recent[metric].sum() if metric in ("fault_indicator", "anomaly_flag") else recent[metric].mean()
            earlier_val = earlier[metric].sum() if metric in ("fault_indicator", "anomaly_flag") else earlier[metric].mean()

            if earlier_val == 0:
                return 0.0

            trend = ((recent_val - earlier_val) / abs(earlier_val)) * 100
            return round(max(-50, min(50, trend)), 1)
        except Exception:
            return 0.0

    def get_summary(self, region=None, substation=None, transformer=None, status=None, anomaly_type=None, risk_level=None, time_range="24h"):
        """Dashboard summary KPIs."""
        df = self._apply_filters(self._df, region=region, substation=substation, transformer=transformer, status=status, risk_level=risk_level, anomaly_type=anomaly_type, time_range=time_range)

        total_gen = df["energy_generated_mwh"].sum() if "energy_generated_mwh" in df.columns else 0
        total_cons = df["energy_consumed_mwh"].sum() if "energy_consumed_mwh" in df.columns else 0
        avg_load = df["load_percent"].mean() if len(df) > 0 else 0
        total_transformers = df["transformer_id"].nunique() if len(df) > 0 else 0
        active_transformers = df[df["status"] != "Critical"]["transformer_id"].nunique() if len(df) > 0 else 0
        fault_count = df["fault_indicator"].sum() if "fault_indicator" in df.columns else 0
        anomaly_count = df["anomaly_flag"].sum() if "anomaly_flag" in df.columns else 0
        # Critical transformers: records with risk >= 85 (5-band mapping)
        critical_t = (
            len(df[df["risk_score"] >= 85]["transformer_id"].unique())
            if "risk_score" in df.columns and len(df) > 0 else 0
        )

        # Grid health calculation
        health_result = self._calculate_health_score(df)
        health_score = health_result.get("health_score", 50) if isinstance(health_result, dict) else health_result

        # Calculate real trends
        gen_trend = self._calculate_trend(df, "energy_generated_mwh", fraction=0.2)
        cons_trend = self._calculate_trend(df, "energy_consumed_mwh", fraction=0.2)
        load_trend = self._calculate_trend(df, "load_percent", fraction=0.2)
        fault_trend = self._calculate_trend(df, "fault_indicator", fraction=0.2)
        anomaly_trend = self._calculate_trend(df, "anomaly_flag", fraction=0.2)

        try:
            if "timestamp" in df.columns and len(df) >= 10:
                df_sorted = df.sort_values("timestamp")
                split_idx = int(len(df_sorted) * 0.8)
                recent_critical = len(df_sorted.iloc[split_idx:][df_sorted.iloc[split_idx:]["status"] == "Critical"]["transformer_id"].unique())
                earlier_critical = len(df_sorted.iloc[:split_idx][df_sorted.iloc[:split_idx]["status"] == "Critical"]["transformer_id"].unique())
                transformer_trend = round(((recent_critical - earlier_critical) / earlier_critical) * 100, 1) if earlier_critical > 0 else 0.0
            else:
                transformer_trend = 0.0
        except Exception:
            transformer_trend = 0.0

        return {
            "total_generation_mw": round(total_gen, 1),
            "total_consumption_mw": round(total_cons, 1),
            "grid_load_percent": round(avg_load, 1),
            "active_transformers": int(active_transformers),
            "total_transformers": int(total_transformers),
            "faults_detected": int(fault_count),
            "anomalies_detected": int(anomaly_count),
            "critical_transformers": int(critical_t),
            "grid_health_score": round(float(health_score), 1),
            "generation_trend": gen_trend,
            "consumption_trend": cons_trend,
            "load_trend": load_trend,
            "transformer_trend": transformer_trend,
            "fault_trend": fault_trend,
            "anomaly_trend": anomaly_trend,
            "records_today": int(len(df)),
        }

    def get_regions(self, region=None, substation=None, transformer=None, status=None, anomaly_type=None, risk_level=None, time_range=None):
        """Region-level aggregation."""
        df = self._apply_filters(self._df, region=region, substation=substation, transformer=transformer, status=status, risk_level=risk_level, anomaly_type=anomaly_type, time_range=time_range)
        if len(df) == 0:
            return []
        agg = df.groupby("region").agg(
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
        ).reset_index()

        return agg.to_dict("records")

    def get_transformers(self, region=None, substation=None, transformer=None, status=None, anomaly_type=None, risk_level=None, time_range=None):
        """Transformer summaries.

        Returns every transformer entity in the filtered dataset. Each row
        carries its aggregated/representative parameters:
          - avg_risk_score  -> representative state (status via classify_risk)
          - max_risk_score  -> worst record seen (worst_status)
          - dominant_anomaly_type / distinct_anomaly_types
        """
        df = self._apply_filters(self._df, region=region, substation=substation, transformer=transformer, status=status, risk_level=risk_level, anomaly_type=anomaly_type, time_range=time_range)

        agg = df.groupby(["transformer_id", "substation_id", "region"]).agg(
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
        ).reset_index()

        agg["worst_status"] = agg["max_risk_score"].apply(classify_risk)
        agg["status"] = agg["avg_risk_score"].apply(classify_risk)

        # Dominant anomaly type (mode of non-Normal records) per transformer
        anom_df = df[df["status"] != "Normal"]
        if len(anom_df) > 0:
            dominant = anom_df.groupby("transformer_id")["anomaly_type"].agg(
                lambda s: s.value_counts().index[0]
            ).rename("dominant_anomaly_type")
            agg = agg.merge(dominant, on="transformer_id", how="left")
            agg["dominant_anomaly_type"] = agg["dominant_anomaly_type"].fillna("Normal")
        else:
            agg["dominant_anomaly_type"] = "Normal"

        agg = agg.sort_values("avg_risk_score", ascending=False)

        # Return ALL transformers so the map, table, and counters show every
        # asset in the filtered dataset (not just the top 100).
        return agg.to_dict("records")

    def get_anomalies(self, region=None, substation=None, transformer=None, anomaly_type=None, status=None, risk_level=None, time_range=None):
        """Anomaly type summary."""
        df = self._apply_filters(
            self._df[self._df["anomaly_flag"] == 1],
            region=region, substation=substation, transformer=transformer, status=status, risk_level=risk_level,
            anomaly_type=anomaly_type, time_range=time_range,
        )

        if len(df) == 0:
            return []

        agg = df.groupby(["anomaly_type", "status"]).agg(
            anomaly_count=("event_id", "count"),
            avg_risk_score=("risk_score", "mean"),
            avg_load_percent=("load_percent", "mean"),
            avg_temperature_c=("temperature_c", "mean"),
            avg_voltage_kv=("voltage_kv", "mean"),
        ).reset_index()

        agg = agg.sort_values("anomaly_count", ascending=False)
        return agg.to_dict("records")

    def get_alerts(self, region=None, substation=None, transformer=None, anomaly_type=None, status=None, risk_level=None, time_range=None):
        """Recent alerts (anomalies sorted by severity)."""
        df = self._apply_filters(
            self._df[self._df["anomaly_flag"] == 1],
            region=region, substation=substation, transformer=transformer, status=status, risk_level=risk_level,
            anomaly_type=anomaly_type, time_range=time_range,
        )

        df = df.sort_values("risk_score", ascending=False).head(20)

        alerts = []
        for _, row in df.iterrows():
            alerts.append({
                "event_id": row.get("event_id", ""),
                "timestamp": str(row.get("timestamp", "")),
                "transformer_id": row.get("transformer_id", ""),
                "substation_id": row.get("substation_id", ""),
                "region": row.get("region", ""),
                "anomaly_type": row.get("anomaly_type", ""),
                "risk_score": int(row.get("risk_score", 0)),
                "status": row.get("status", "Normal"),
                "voltage_kv": round(float(row.get("voltage_kv", 0)), 2),
                "temperature_c": round(float(row.get("temperature_c", 0)), 2),
                "load_percent": round(float(row.get("load_percent", 0)), 2),
            })

        return alerts

    def get_energy(self, region=None, substation=None, transformer=None, anomaly_type=None, time_range="24h"):
        """Energy analytics with hourly breakdown."""
        df = self._apply_filters(self._df, region=region, substation=substation, transformer=transformer, anomaly_type=anomaly_type, time_range=time_range)

        if "timestamp" in df.columns:
            df_copy = df.copy()
            try:
                df_copy["hour_of_day"] = pd.to_datetime(df_copy["timestamp"]).dt.hour
            except Exception:
                df_copy["hour_of_day"] = 12

            hourly = df_copy.groupby("hour_of_day").agg(
                total_power_mw=("power_mw", "sum"),
                avg_load_percent=("load_percent", "mean"),
                avg_temperature_c=("temperature_c", "mean"),
                avg_energy_generated_mwh=("energy_generated_mwh", "mean"),
                avg_energy_consumed_mwh=("energy_consumed_mwh", "mean"),
                total_faults=("fault_indicator", "sum"),
                record_count=("event_id", "count"),
                avg_risk_score=("risk_score", "mean"),
            ).reset_index()
            hourly = hourly.sort_values("hour_of_day")
        else:
            hourly = pd.DataFrame()

        return {
            "hourly": hourly.to_dict("records") if len(hourly) > 0 else [],
            "total_generated": round(df["energy_generated_mwh"].sum(), 1) if "energy_generated_mwh" in df.columns else 0,
            "total_consumed": round(df["energy_consumed_mwh"].sum(), 1) if "energy_consumed_mwh" in df.columns else 0,
        }

    def get_grid_health(self, region=None, substation=None, transformer=None, anomaly_type=None, risk_level=None, status=None, time_range=None):
        """Grid health score (0-100)."""
        df = self._apply_filters(self._df, region=region, substation=substation, transformer=transformer, anomaly_type=anomaly_type, risk_level=risk_level, status=status, time_range=time_range)
        health = self._calculate_health_score(df)
        return health

    def _calculate_health_score(self, df):
        """Calculate grid health score from actual data."""
        if len(df) == 0:
            return {"health_score": 50, "status": "Unknown", "total_transformers": 0, "active_transformers": 0, "critical_transformers": 0, "normal_count": 0, "warning_count": 0, "high_risk_count": 0, "critical_count": 0, "low_count": 0, "avg_voltage_stability": 0, "avg_frequency_stability": 0, "overload_rate": 0, "communication_failure_rate": 0}

        total = len(df)

        status_counts = df["status"].value_counts()
        normal_rate = status_counts.get("Normal", 0) / total
        critical_rate = status_counts.get("Critical", 0) / total
        warning_rate = status_counts.get("Warning", 0) / total

        if "voltage_deviation_kv" in df.columns:
            v_stability = max(0, 1 - abs(df["voltage_deviation_kv"].mean()) / 5)
        else:
            v_stability = 0.85

        if "frequency_deviation_hz" in df.columns:
            f_stability = max(0, 1 - abs(df["frequency_deviation_hz"].mean()) / 0.5)
        else:
            f_stability = 0.9

        overload_rate = len(df[df["load_percent"] > 90]) / total if total > 0 else 0
        overload_health = max(0, 1 - overload_rate * 5)

        if "temperature_c" in df.columns:
            temp_risk = len(df[df["temperature_c"] > 70]) / total
            temp_health = max(0, 1 - temp_risk * 5)
        else:
            temp_health = 0.85

        if "communication_latency_ms" in df.columns:
            comm_fail = len(df[df["communication_latency_ms"] > 50]) / total
            comm_health = max(0, 1 - comm_fail * 10)
        else:
            comm_health = 0.9

        health = (
            normal_rate * 30 +
            (1 - critical_rate) * 20 +
            (1 - warning_rate) * 10 +
            v_stability * 12 +
            f_stability * 10 +
            overload_health * 8 +
            temp_health * 5 +
            comm_health * 5
        )

        health = max(0, min(100, health))

        if health >= 80:
            status = "Excellent"
        elif health >= 65:
            status = "Healthy"
        elif health >= 50:
            status = "Warning"
        else:
            status = "Critical"

        total_t = df["transformer_id"].nunique()
        critical_t = df[df["risk_score"] >= 85]["transformer_id"].nunique() if "risk_score" in df.columns else 0
        active_t = df[df["status"] != "Critical"]["transformer_id"].nunique()

        return {
            "health_score": round(health, 1),
            "status": status,
            "total_transformers": int(total_t),
            "active_transformers": int(active_t),
            "critical_transformers": int(critical_t),
            "normal_count": int(status_counts.get("Normal", 0)),
            "warning_count": int(status_counts.get("Warning", 0)),
            "high_risk_count": int(status_counts.get("High Risk", 0)),
            "critical_count": int(status_counts.get("Critical", 0)),
            "low_count": int(status_counts.get("Low", 0)),
            "avg_voltage_stability": round(v_stability * 100, 1),
            "avg_frequency_stability": round(f_stability * 100, 1),
            "overload_rate": round(overload_rate * 100, 2),
            "communication_failure_rate": round(
                (len(df[df["communication_latency_ms"] > 50]) / total * 100) if "communication_latency_ms" in df.columns and total > 0 else 0, 2
            ),
        }

    def get_risk(self, region=None, substation=None, transformer=None, anomaly_type=None, risk_level=None):
        """Risk distribution data."""
        df = self._apply_filters(self._df, region=region, substation=substation, transformer=transformer, risk_level=risk_level, anomaly_type=anomaly_type)

        risk_dist = {}
        for level in ["Normal", "Low", "Warning", "High Risk", "Critical"]:
            risk_dist[level] = int(len(df[df["status"] == level]))

        return {
            "distribution": risk_dist,
            "avg_risk_score": round(df["risk_score"].mean(), 1) if "risk_score" in df.columns and len(df) > 0 else 0,
            "max_risk_score": int(df["risk_score"].max()) if "risk_score" in df.columns and len(df) > 0 else 0,
        }

    def get_substations(self, region=None):
        """Substation data with aggregated metrics."""
        df = self._apply_filters(self._df, region=region)
        if len(df) == 0:
            return []

        agg = df.groupby(["substation_id", "region"]).agg(
            total_power_mw=("power_mw", "sum"),
            avg_load_percent=("load_percent", "mean"),
            avg_temperature_c=("temperature_c", "mean"),
            avg_risk_score=("risk_score", "mean"),
            max_risk_score=("risk_score", "max"),
            total_faults=("fault_indicator", "sum"),
            transformer_count=("transformer_id", "nunique"),
            avg_energy_generated=("energy_generated_mwh", "mean"),
            avg_energy_consumed=("energy_consumed_mwh", "mean"),
        ).reset_index()

        agg["status"] = agg["max_risk_score"].apply(classify_risk)
        return agg.to_dict("records")

    def get_3d_analytics(self, region=None, substation=None, transformer=None, anomaly_type=None, risk_level=None, status=None):
        """3D analytical chart data (sampled/aggregated for performance)."""
        df = self._apply_filters(self._df, region=region, substation=substation, transformer=transformer, status=status, risk_level=risk_level, anomaly_type=anomaly_type)

        n = min(1000, len(df))
        if n > 0:
            sampled = df.sample(n=n, random_state=42) if len(df) > n else df
        else:
            sampled = df

        def make_trace(x, y, z, colors, hover_text, name=""):
            return {
                "x": x,
                "y": y,
                "z": z,
                "color": colors,
                "text": hover_text,
                "sizes": [4] * len(x),
                "name": name,
            }

        color_map = {"Normal": "#22c55e", "Low": "#3b82f6", "Warning": "#f59e0b", "High Risk": "#f97316", "Critical": "#ef4444"}

        # Grid Risk Landscape: voltage × temperature × risk
        grid_risk = make_trace(
            x=sampled["voltage_kv"].round(2).tolist(),
            y=sampled["temperature_c"].round(2).tolist(),
            z=sampled["risk_score"].tolist() if "risk_score" in sampled.columns else [0] * len(sampled),
            colors=[color_map.get(s, "#94a3b8") for s in sampled["status"]],
            hover_text=[
                f"Transformer: {r.get('transformer_id', '')}<br>"
                f"Region: {r.get('region', '')}<br>"
                f"Voltage: {r.get('voltage_kv', 0):.1f} kV<br>"
                f"Temperature: {r.get('temperature_c', 0):.1f}°C<br>"
                f"Risk: {r.get('risk_score', 0)}<br>"
                f"Status: {r.get('status', '')}<br>"
                f"Anomaly: {r.get('anomaly_type', '')}"
                for _, r in sampled.iterrows()
            ],
        )

        # Load Performance: load × power_factor × temperature
        load_perf = make_trace(
            x=sampled["load_percent"].round(2).tolist(),
            y=sampled["power_factor"].round(4).tolist(),
            z=sampled["temperature_c"].round(2).tolist(),
            colors=[color_map.get(s, "#94a3b8") for s in sampled["status"]],
            hover_text=[
                f"Transformer: {r.get('transformer_id', '')}<br>"
                f"Region: {r.get('region', '')}<br>"
                f"Load: {r.get('load_percent', 0):.1f}%<br>"
                f"Power Factor: {r.get('power_factor', 0):.3f}<br>"
                f"Temperature: {r.get('temperature_c', 0):.1f}°C<br>"
                f"Risk: {r.get('risk_score', 0)}<br>"
                f"Status: {r.get('status', '')}"
                for _, r in sampled.iterrows()
            ],
        )

        return {
            "grid_risk": grid_risk,
            "load_performance": load_perf,
            "sample_size": n,
            "total_records": len(df),
        }

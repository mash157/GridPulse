#!/usr/bin/env python
"""
GridPulse Data Loader
Cached data loading for dashboard components
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from dashboard.config import (
    BASE_PATH, EXPORTS_PATH, SILVER_SAMPLE_FILE,
    TRANSFORMER_SUMMARY_FILE, SUBSTATION_SUMMARY_FILE,
    REGION_SUMMARY_FILE, HOURLY_SUMMARY_FILE, DAILY_SUMMARY_FILE,
    ANOMALY_SUMMARY_FILE, SEVERITY_SUMMARY_FILE,
    CRITICAL_TRANSFORMERS_FILE, TRANSFORMER_RISK_FILE,
    TRANSFORMER_HEALTH_FILE, SUBSTATION_HEALTH_FILE,
    REGION_HEALTH_FILE, GRID_HEALTH_FILE
)


@st.cache_data(ttl=300, show_spinner="Loading main dataset...")
def load_silver_sample() -> Optional[pd.DataFrame]:
    """
    Load the silver sample dataset for dashboard.

    Returns:
        DataFrame with telemetry data or None if not found
    """
    if not SILVER_SAMPLE_FILE.exists():
        print(f"Silver sample file not found: {SILVER_SAMPLE_FILE}")
        return None

    try:
        df = pd.read_csv(SILVER_SAMPLE_FILE)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except Exception as e:
        print(f"Error loading silver sample: {e}")
        return None


@st.cache_data(ttl=300, show_spinner="Loading transformer summary...")
def load_transformer_summary() -> Optional[pd.DataFrame]:
    """Load transformer summary data."""
    if not TRANSFORMER_SUMMARY_FILE.exists():
        return None

    try:
        return pd.read_csv(TRANSFORMER_SUMMARY_FILE)
    except Exception as e:
        print(f"Error loading transformer summary: {e}")
        return None


@st.cache_data(ttl=300, show_spinner="Loading substation summary...")
def load_substation_summary() -> Optional[pd.DataFrame]:
    """Load substation summary data."""
    if not SUBSTATION_SUMMARY_FILE.exists():
        return None

    try:
        return pd.read_csv(SUBSTATION_SUMMARY_FILE)
    except Exception as e:
        print(f"Error loading substation summary: {e}")
        return None


@st.cache_data(ttl=300, show_spinner="Loading region summary...")
def load_region_summary() -> Optional[pd.DataFrame]:
    """Load region summary data."""
    if not REGION_SUMMARY_FILE.exists():
        return None

    try:
        return pd.read_csv(REGION_SUMMARY_FILE)
    except Exception as e:
        print(f"Error loading region summary: {e}")
        return None


@st.cache_data(ttl=300, show_spinner="Loading severity summary...")
def load_severity_summary() -> Optional[pd.DataFrame]:
    """Load severity/status distribution data."""
    if not SEVERITY_SUMMARY_FILE.exists():
        return None

    try:
        return pd.read_csv(SEVERITY_SUMMARY_FILE)
    except Exception as e:
        print(f"Error loading severity summary: {e}")
        return None


@st.cache_data(ttl=300, show_spinner="Loading anomaly summary...")
def load_anomaly_summary() -> Optional[pd.DataFrame]:
    """Load anomaly type summary data."""
    if not ANOMALY_SUMMARY_FILE.exists():
        return None

    try:
        return pd.read_csv(ANOMALY_SUMMARY_FILE)
    except Exception as e:
        print(f"Error loading anomaly summary: {e}")
        return None


@st.cache_data(ttl=300, show_spinner="Loading critical transformers...")
def load_critical_transformers() -> Optional[pd.DataFrame]:
    """Load critical transformers data."""
    if not CRITICAL_TRANSFORMERS_FILE.exists():
        return None

    try:
        return pd.read_csv(CRITICAL_TRANSFORMERS_FILE)
    except Exception as e:
        print(f"Error loading critical transformers: {e}")
        return None


@st.cache_data(ttl=300, show_spinner="Loading transformer risk...")
def load_transformer_risk() -> Optional[pd.DataFrame]:
    """Load transformer risk summary data."""
    if not TRANSFORMER_RISK_FILE.exists():
        return None

    try:
        return pd.read_csv(TRANSFORMER_RISK_FILE)
    except Exception as e:
        print(f"Error loading transformer risk: {e}")
        return None


@st.cache_data(ttl=300, show_spinner="Loading hourly summary...")
def load_hourly_summary() -> Optional[pd.DataFrame]:
    """Load hourly summary data."""
    if not HOURLY_SUMMARY_FILE.exists():
        return None

    try:
        return pd.read_csv(HOURLY_SUMMARY_FILE)
    except Exception as e:
        print(f"Error loading hourly summary: {e}")
        return None


@st.cache_data(ttl=300, show_spinner="Loading daily summary...")
def load_daily_summary() -> Optional[pd.DataFrame]:
    """Load daily summary data."""
    if not DAILY_SUMMARY_FILE.exists():
        return None

    try:
        return pd.read_csv(DAILY_SUMMARY_FILE)
    except Exception as e:
        print(f"Error loading daily summary: {e}")
        return None


@st.cache_data(ttl=300, show_spinner="Loading transformer health...")
def load_transformer_health() -> Optional[pd.DataFrame]:
    """Load transformer health data."""
    if not TRANSFORMER_HEALTH_FILE.exists():
        return None

    try:
        return pd.read_csv(TRANSFORMER_HEALTH_FILE)
    except Exception as e:
        print(f"Error loading transformer health: {e}")
        return None


@st.cache_data(ttl=300, show_spinner="Loading substation health...")
def load_substation_health() -> Optional[pd.DataFrame]:
    """Load substation health data."""
    if not SUBSTATION_HEALTH_FILE.exists():
        return None

    try:
        return pd.read_csv(SUBSTATION_HEALTH_FILE)
    except Exception as e:
        print(f"Error loading substation health: {e}")
        return None


@st.cache_data(ttl=300, show_spinner="Loading region health...")
def load_region_health() -> Optional[pd.DataFrame]:
    """Load region health data."""
    if not REGION_HEALTH_FILE.exists():
        return None

    try:
        return pd.read_csv(REGION_HEALTH_FILE)
    except Exception as e:
        print(f"Error loading region health: {e}")
        return None


@st.cache_data(ttl=60, show_spinner="Loading grid health summary...")
def load_grid_health_summary() -> Optional[Dict[str, Any]]:
    """Load grid health summary JSON."""
    if not GRID_HEALTH_FILE.exists():
        return None

    try:
        import json
        with open(GRID_HEALTH_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading grid health summary: {e}")
        return None


@st.cache_data(ttl=300, show_spinner="Loading all dataframes...")
def load_all_data() -> Dict[str, Optional[pd.DataFrame]]:
    """
    Load all required dataframes in one call.

    Returns:
        Dictionary with all dataframes
    """
    return {
        "silver_sample": load_silver_sample(),
        "transformer_summary": load_transformer_summary(),
        "substation_summary": load_substation_summary(),
        "region_summary": load_region_summary(),
        "severity_summary": load_severity_summary(),
        "anomaly_summary": load_anomaly_summary(),
        "critical_transformers": load_critical_transformers(),
        "transformer_risk": load_transformer_risk(),
        "hourly_summary": load_hourly_summary(),
        "daily_summary": load_daily_summary(),
        "transformer_health": load_transformer_health(),
        "substation_health": load_substation_health(),
        "region_health": load_region_health(),
    }


def get_data_status() -> Dict[str, bool]:
    """
    Check which data files exist.

    Returns:
        Dictionary with file existence status
    """
    files = {
        "silver_sample": SILVER_SAMPLE_FILE,
        "transformer_summary": TRANSFORMER_SUMMARY_FILE,
        "substation_summary": SUBSTATION_SUMMARY_FILE,
        "region_summary": REGION_SUMMARY_FILE,
        "hourly_summary": HOURLY_SUMMARY_FILE,
        "daily_summary": DAILY_SUMMARY_FILE,
        "anomaly_summary": ANOMALY_SUMMARY_FILE,
        "severity_summary": SEVERITY_SUMMARY_FILE,
        "critical_transformers": CRITICAL_TRANSFORMERS_FILE,
        "transformer_risk": TRANSFORMER_RISK_FILE,
        "transformer_health": TRANSFORMER_HEALTH_FILE,
        "substation_health": SUBSTATION_HEALTH_FILE,
        "region_health": REGION_HEALTH_FILE,
        "grid_health": GRID_HEALTH_FILE,
    }

    status = {}
    for name, path in files.items():
        status[name] = path.exists()

    return status


def get_last_data_update() -> Optional[datetime]:
    """Get the last modification time of the silver sample file."""
    if SILVER_SAMPLE_FILE.exists():
        mtime = SILVER_SAMPLE_FILE.stat().st_mtime
        return datetime.fromtimestamp(mtime)
    return None


def get_stream_status() -> dict:
    """
    Determine whether the telemetry stream is currently ONLINE or OFFLINE.

    Reads ``data/streaming/heartbeat.json`` written by the stream generator.
    The stream is considered ONLINE when the heartbeat was updated within the
    last 30 seconds AND the generator has not marked itself as ``stopped``.

    Returns:
        dict with keys: online (bool), status_text (str),
        events_generated (int|None), anomalies_detected (int|None),
        last_update (str|None)
    """
    import json as _json

    hb_path = BASE_PATH / "data" / "streaming" / "heartbeat.json"
    default = {
        "online": False,
        "status_text": "STREAM OFFLINE",
        "events_generated": None,
        "anomalies_detected": None,
        "last_update": None,
    }

    if not hb_path.exists():
        return default

    try:
        with open(hb_path) as f:
            hb = _json.load(f)

        gen_status = hb.get("status", "unknown")
        last_update_str = hb.get("last_update")

        if last_update_str is None:
            return default

        if gen_status == "stopped":
            return {
                "online": False,
                "status_text": "STREAM OFFLINE",
                "events_generated": hb.get("events_generated"),
                "anomalies_detected": hb.get("anomalies_detected"),
                "last_update": last_update_str,
            }

        last_update_dt = datetime.fromisoformat(last_update_str)
        age_seconds = (datetime.now() - last_update_dt).total_seconds()

        online = age_seconds < 30  # heartbeat is fresh

        return {
            "online": online,
            "status_text": "STREAM ONLINE" if online else "STREAM OFFLINE",
            "events_generated": hb.get("events_generated"),
            "anomalies_detected": hb.get("anomalies_detected"),
            "last_update": last_update_str,
        }
    except Exception:
        return default

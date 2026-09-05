#!/usr/bin/env python
"""
GridPulse Dashboard Configuration
Application settings and constants
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

# Project base path
BASE_PATH = Path(__file__).parent.parent

# Data paths
DATA_PATH = BASE_PATH / "data"
RAW_PATH = DATA_PATH / "raw"
BRONZE_PATH = DATA_PATH / "bronze"
SILVER_PATH = DATA_PATH / "silver"
GOLD_PATH = DATA_PATH / "gold"
STREAMING_PATH = DATA_PATH / "streaming"
EXPORTS_PATH = DATA_PATH / "exports"

# Ensure directories exist
for path in [RAW_PATH, BRONZE_PATH, SILVER_PATH, GOLD_PATH, STREAMING_PATH, EXPORTS_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# Data files
RAW_DATA_FILE = RAW_PATH / "grid_telemetry_raw.csv"
SILVER_SAMPLE_FILE = EXPORTS_PATH / "silver_sample.csv"
TRANSFORMER_SUMMARY_FILE = EXPORTS_PATH / "transformer_summary.csv"
SUBSTATION_SUMMARY_FILE = EXPORTS_PATH / "substation_summary.csv"
REGION_SUMMARY_FILE = EXPORTS_PATH / "region_summary.csv"
HOURLY_SUMMARY_FILE = EXPORTS_PATH / "hourly_summary.csv"
DAILY_SUMMARY_FILE = EXPORTS_PATH / "daily_summary.csv"
ANOMALY_SUMMARY_FILE = EXPORTS_PATH / "anomaly_summary.csv"
SEVERITY_SUMMARY_FILE = EXPORTS_PATH / "severity_summary.csv"
CRITICAL_TRANSFORMERS_FILE = EXPORTS_PATH / "critical_transformers.csv"
TRANSFORMER_RISK_FILE = EXPORTS_PATH / "transformer_risk_summary.csv"
TRANSFORMER_HEALTH_FILE = EXPORTS_PATH / "transformer_health.csv"
SUBSTATION_HEALTH_FILE = EXPORTS_PATH / "substation_health.csv"
REGION_HEALTH_FILE = EXPORTS_PATH / "region_health.csv"
GRID_HEALTH_FILE = EXPORTS_PATH / "grid_health_summary.json"


# Regions
REGIONS = ["North", "South", "East", "West", "Central", "North-East"]

# Substation coordinates (India-focused geographic data)
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

# Status values
STATUS_VALUES = ["Normal", "Low", "Warning", "High Risk", "Critical"]

# Anomaly types
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
    "Normal",
]

# Time range options
TIME_RANGE_OPTIONS = [
    ("Last 1 Hour", timedelta(hours=1)),
    ("Last 6 Hours", timedelta(hours=6)),
    ("Last 12 Hours", timedelta(hours=12)),
    ("Last 24 Hours", timedelta(hours=24)),
    ("Last 7 Days", timedelta(days=7)),
    ("Last 30 Days", timedelta(days=30)),
    ("All Time", None),
]

# Default time range
DEFAULT_TIME_RANGE = "Last 24 Hours"

# Application settings
APP_TITLE = "GridPulse"
APP_SUBTITLE = "Smart Energy Grid Monitoring"
APP_ICON = "⚡"

# Map configuration
DEFAULT_MAP_CENTER = {"lat": 22.0, "lon": 78.0}  # India center
DEFAULT_MAP_ZOOM = 5

# 3D visualization settings
MAX_3D_POINTS = 2500
DEFAULT_3D_SAMPLE_SIZE = 2000

# Pagination settings
TRANSFORMERS_PAGE_SIZE = 25
ALERTS_PAGE_SIZE = 15

# Animation duration (ms)
ANIMATION_DURATION = 300

# Refresh interval (seconds)
REFRESH_INTERVAL = 60

# Cache timeout (seconds)
CACHE_TIMEOUT = 300

# Spark settings
SPARK_MEMORY = "2g"
SPARK_SHUFFLE_PARTITIONS = 8


def get_file_path(filename: str) -> Path:
    """Get full path to a data file."""
    if filename in EXPORTS_PATH.iterdir():
        return EXPORTS_PATH / filename
    return None


def check_data_exists() -> bool:
    """Check if required data files exist."""
    required_files = [
        SILVER_SAMPLE_FILE,
        TRANSFORMER_SUMMARY_FILE,
        SUBSTATION_SUMMARY_FILE,
        REGION_SUMMARY_FILE,
        SEVERITY_SUMMARY_FILE,
        CRITICAL_TRANSFORMERS_FILE,
    ]

    missing = []
    for file in required_files:
        if not file.exists():
            missing.append(file.name)

    if missing:
        print(f"Missing files: {missing}")
        return False

    return True


def get_latest_timestamp(df) -> datetime:
    """Get the latest timestamp from dataframe."""
    if "timestamp" in df.columns:
        if pd_is_datetime(df["timestamp"]):
            return df["timestamp"].max()
        else:
            try:
                return pd.to_datetime(df["timestamp"]).max()
            except:
                return datetime.now()

    return datetime.now()


def pd_is_datetime(series) -> bool:
    """Check if pandas series is datetime type."""
    try:
        return pd.api.types.is_datetime64_any_dtype(series)
    except:
        return False


# Import pandas here to avoid circular imports
import pandas as pd

"""GridPulse API Schemas"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DashboardSummary(BaseModel):
    total_generation_mw: float = 0
    total_consumption_mw: float = 0
    grid_load_percent: float = 0
    active_transformers: int = 0
    total_transformers: int = 0
    faults_detected: int = 0
    anomalies_detected: int = 0
    grid_health_score: float = 0


class GridHealth(BaseModel):
    health_score: float = 0
    status: str = "Unknown"
    total_transformers: int = 0
    active_transformers: int = 0
    critical_transformers: int = 0
    normal_count: int = 0
    warning_count: int = 0
    high_risk_count: int = 0
    critical_count: int = 0


class LiveEvent(BaseModel):
    event_id: str
    timestamp: str
    region: str
    substation_id: str
    transformer_id: str
    voltage_kv: float = 0
    current_amp: float = 0
    power_mw: float = 0
    frequency_hz: float = 50.0
    load_percent: float = 0
    power_factor: float = 0.95
    temperature_c: float = 45
    fault_indicator: int = 0
    anomaly_score: float = 0
    risk_score: int = 0
    status: str = "Normal"
    anomaly_type: str = "Normal"
    message: str = ""


class Alert(BaseModel):
    event_id: str
    timestamp: str
    transformer_id: str
    substation_id: str
    region: str
    anomaly_type: str
    risk_score: int
    status: str
    voltage_kv: float
    temperature_c: float
    load_percent: float

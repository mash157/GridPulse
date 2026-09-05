#!/usr/bin/env python
"""
GridPulse FastAPI Backend
Serves processed analytics data via REST API and WebSocket
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.analytics_service import AnalyticsService
from backend.services.streaming_service import StreamingService

app = FastAPI(
    title="GridPulse API",
    description="Smart Energy Grid Monitoring & Predictive Failure Analytics",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
analytics = AnalyticsService()
streaming = StreamingService()


@app.on_event("startup")
async def startup():
    """Load data on startup."""
    analytics.load_data()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/summary")
async def get_summary(
    region: Optional[str] = None,
    substation: Optional[str] = None,
    transformer: Optional[str] = None,
    status: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    time_range: Optional[str] = "24h",
):
    """Dashboard summary KPIs."""
    return analytics.get_summary(
        region=region, substation=substation, transformer=transformer,
        status=status, anomaly_type=anomaly_type, risk_level=risk_level,
        time_range=time_range,
    )


@app.get("/api/regions")
async def get_regions(
    region: Optional[str] = None,
    substation: Optional[str] = None,
    transformer: Optional[str] = None,
    status: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    time_range: Optional[str] = None,
):
    """Region-level aggregation."""
    return analytics.get_regions(
        region=region, substation=substation, transformer=transformer,
        status=status, anomaly_type=anomaly_type, risk_level=risk_level,
        time_range=time_range,
    )


@app.get("/api/transformers")
async def get_transformers(
    region: Optional[str] = None,
    substation: Optional[str] = None,
    transformer: Optional[str] = None,
    status: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    time_range: Optional[str] = None,
):
    """Transformer summaries with filtering."""
    return analytics.get_transformers(
        region=region, substation=substation, transformer=transformer,
        status=status, anomaly_type=anomaly_type, risk_level=risk_level,
        time_range=time_range,
    )


@app.get("/api/anomalies")
async def get_anomalies(
    region: Optional[str] = None,
    substation: Optional[str] = None,
    transformer: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    time_range: Optional[str] = None,
    alerts: Optional[bool] = False,
):
    """Anomaly data and summary."""
    if alerts:
        return analytics.get_alerts(
            region=region, substation=substation, transformer=transformer,
            anomaly_type=anomaly_type, status=status, risk_level=risk_level,
            time_range=time_range,
        )
    return analytics.get_anomalies(
        region=region, substation=substation, transformer=transformer,
        anomaly_type=anomaly_type, status=status, risk_level=risk_level,
        time_range=time_range,
    )


@app.get("/api/energy")
async def get_energy(
    region: Optional[str] = None,
    substation: Optional[str] = None,
    transformer: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    time_range: Optional[str] = "24h",
):
    """Energy generation vs consumption analytics."""
    return analytics.get_energy(
        region=region, substation=substation, transformer=transformer,
        anomaly_type=anomaly_type, time_range=time_range,
    )


@app.get("/api/grid-health")
async def get_grid_health(
    region: Optional[str] = None,
    substation: Optional[str] = None,
    transformer: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    time_range: Optional[str] = None,
):
    """Grid health score and metrics."""
    return analytics.get_grid_health(
        region=region, substation=substation, transformer=transformer,
        anomaly_type=anomaly_type, risk_level=risk_level, status=status,
        time_range=time_range,
    )


@app.get("/api/risk")
async def get_risk(
    region: Optional[str] = None,
    substation: Optional[str] = None,
    transformer: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    risk_level: Optional[str] = None,
):
    """Risk scoring data."""
    return analytics.get_risk(
        region=region, substation=substation, transformer=transformer,
        anomaly_type=anomaly_type, risk_level=risk_level,
    )


@app.get("/api/analytics/3d")
async def get_analytics_3d(
    region: Optional[str] = None,
    substation: Optional[str] = None,
    transformer: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
):
    """3D analytical chart data (aggregated/sampled)."""
    return analytics.get_3d_analytics(
        region=region, substation=substation, transformer=transformer,
        anomaly_type=anomaly_type, risk_level=risk_level, status=status,
    )


@app.get("/api/substations")
async def get_substations(
    region: Optional[str] = None,
):
    """Substation locations and status."""
    return analytics.get_substations(region=region)


@app.get("/api/status")
async def get_status():
    """System status."""
    return {
        "status": "operational",
        "pipeline": "running",
        "timestamp": datetime.now().isoformat(),
        "data_loaded": analytics.is_loaded,
        "record_count": analytics.record_count,
    }


@app.websocket("/ws/grid")
async def websocket_grid(websocket: WebSocket):
    """WebSocket endpoint for live grid events."""
    await websocket.accept()
    try:
        while True:
            event = streaming.generate_live_event()
            await websocket.send_json(event)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

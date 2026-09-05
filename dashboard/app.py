#!/usr/bin/env python
"""
GridPulse - Smart Energy Grid Monitoring & Predictive Analytics
Main Streamlit Dashboard Application
"""

import os
import sys
from pathlib import Path

import streamlit as st
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.theme import get_theme, LIGHT_THEME, DARK_THEME
from dashboard.data_loader import (
    load_all_data,
    load_silver_sample,
    load_transformer_summary,
    load_critical_transformers,
    get_data_status,
    get_last_data_update,
    get_stream_status,
)
from dashboard.filters import (
    render_filters,
    apply_filters,
    clear_filters,
    get_filter_options,
)
from dashboard.config import REGIONS, TIME_RANGE_OPTIONS
from dashboard.components import (
    render_header,
    render_sidebar,
    render_kpi_cards,
    render_grid_map,
    render_grid_health_donut,
    render_energy_by_region,
    render_top_anomaly_types,
    render_power_gen_consumption,
    render_3d_analytics,
    render_recent_alerts,
    render_top_risk_transformers,
    render_critical_transformers,
    render_transformer_table,
)


def main():
    """Main dashboard application."""
    
    # Configure page
    st.set_page_config(
        page_title="GridPulse - Smart Energy Grid Monitoring",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Initialize session state
    if "is_dark" not in st.session_state:
        st.session_state.is_dark = False
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Overview"
    
    if "filters" not in st.session_state:
        st.session_state.filters = {
            "region": "All",
            "substation_id": "All",
            "transformer_id": "All",
            "time_range": "Last 24 Hours",
        }
    
    if "last_stream_update" not in st.session_state:
        st.session_state.last_stream_update = None
    
    # Get theme
    is_dark = st.session_state.is_dark
    theme = get_theme(is_dark)
    
    # Inject base CSS
    _inject_base_css(theme)
    
    # Load data
    with st.spinner("Loading dashboard data..."):
        data = load_all_data()
        df_silver = data.get("silver_sample")
        df_transformer = data.get("transformer_summary")
        df_critical = data.get("critical_transformers")
        df_anomaly = data.get("anomaly_summary")
        df_severity = data.get("severity_summary")
    
    # Check streaming data
    streaming_dir = Path(__file__).parent.parent / "data" / "streaming"
    stream_files = list(streaming_dir.glob("stream_telemetry_*.csv"))
    has_streaming = len(stream_files) > 0
    
    if has_streaming:
        # Load latest streaming data
        latest_stream = max(stream_files, key=os.path.getmtime)
        try:
            df_stream = pd.read_csv(latest_stream)
            df_stream["timestamp"] = pd.to_datetime(df_stream["timestamp"])
            st.session_state.last_stream_update = df_stream["timestamp"].max()
        except:
            st.session_state.last_stream_update = None
    
    # Get filter options from data
    if df_silver is not None and len(df_silver) > 0:
        filter_options = get_filter_options(df_silver, st.session_state.filters)
    else:
        filter_options = {
            "region": ["All"] + REGIONS,
            "substation_id": ["All"],
            "transformer_id": ["All"],
            "time_range": [opt[0] for opt in TIME_RANGE_OPTIONS],
        }
    
    # Current filters
    current_filters = st.session_state.filters
    
    # Render header
    stream_status = get_stream_status()
    render_header(is_dark=is_dark, stream_status=stream_status)
    
    # Render sidebar using the component
    with st.sidebar:
        render_sidebar(
            is_dark=is_dark,
            current_page=st.session_state.current_page,
            df=df_silver,
            current_filters=current_filters
        )
    
    # Main content area - page title
    if st.session_state.current_page != "Overview":
        st.markdown(f"""
        <div style="
            font-size: 24px;
            font-weight: 700;
            color: {theme.text};
            margin-bottom: 8px;
        ">
            {st.session_state.current_page}
        </div>
        """, unsafe_allow_html=True)
    
    # Render current page
    if st.session_state.current_page == "Overview":
        _render_overview_page(
            df_silver, df_critical, is_dark, theme, current_filters,
            has_streaming
        )
    elif st.session_state.current_page == "Grid Monitoring":
        _render_grid_monitoring_page(
            df_silver, df_transformer, is_dark, theme, current_filters
        )
    elif st.session_state.current_page == "Transformers":
        _render_transformers_page(
            df_silver, is_dark, theme, current_filters
        )
    elif st.session_state.current_page == "3D Analytics":
        _render_3d_page(df_silver, is_dark, theme, current_filters)
    elif st.session_state.current_page == "Anomalies":
        _render_anomalies_page(
            df_silver, df_anomaly, is_dark, theme, current_filters
        )
    elif st.session_state.current_page == "Forecasting":
        _render_forecasting_page(
            df_silver, is_dark, theme, current_filters
        )
    elif st.session_state.current_page == "Reports":
        _render_reports_page(
            df_silver, is_dark, theme, current_filters
        )
    
    # Live feed ticker at bottom
    _render_live_feed(df_silver, is_dark, theme, current_filters)
    
    # Footer
    st.markdown(f"""
    <div style="
        background: {theme.surface};
        border-top: 1px solid {theme.border};
        padding: 12px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11px;
        color: {theme.text_muted};
        margin-top: 20px;
    ">
        <span>© 2025 GridPulse - Smart Energy Grid Monitoring Platform</span>
        <span>Data last updated: {get_last_data_update().strftime('%Y-%m-%d %H:%M:%S') if get_last_data_update() else 'Never'}</span>
    </div>
    """, unsafe_allow_html=True)


def _render_overview_page(
    df_silver, df_critical, is_dark, theme, filters, has_streaming
):
    """Render Overview page matching reference design."""
    
    if df_silver is None or len(df_silver) == 0:
        st.warning("No data available. Please run the data pipeline first.", icon="⚠️")
        return
    
    # KPI Cards Row
    st.markdown(f"""
    <div style="
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 12px;
        margin-bottom: 16px;
    ">
    """, unsafe_allow_html=True)
    
    render_kpi_cards(df_silver, is_dark, filters)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Row 2: Map + Charts (2/3 + 1/3 split)
    col_map, col_charts = st.columns([2, 1])
    
    with col_map:
        render_grid_map(df_silver, is_dark, filters)
    
    with col_charts:
        # Grid Health Donut
        render_grid_health_donut(df_silver, is_dark, filters)
        
        st.markdown(f"<div style='height: 12px;'></div>", unsafe_allow_html=True)
        
        # Energy by Region
        render_energy_by_region(df_silver, is_dark, filters, filters.get("time_range", "Last 24 Hours"))
    
    # Row 3: Anomaly Types + Top Risk Transformers + Power Chart (3 columns)
    col_anomaly, col_risk, col_power = st.columns([1, 1, 1])
    
    with col_anomaly:
        render_top_anomaly_types(df_silver, is_dark, filters)
    
    with col_risk:
        render_top_risk_transformers(df_silver, is_dark, filters)
    
    with col_power:
        render_power_gen_consumption(df_silver, is_dark, filters, filters.get("time_range", "Last 24 Hours"))
    
    # Row 4: Recent Alerts + Critical Transformers
    col_alerts, col_critical = st.columns([1, 1])
    
    with col_alerts:
        render_recent_alerts(df_silver, is_dark, filters)
    
    with col_critical:
        render_critical_transformers(df_silver, is_dark, filters)
    
    # 3D overview mini (compact)
    st.markdown(f"<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    col_3d, _ = st.columns([1, 1])
    with col_3d:
        render_3d_analytics(df_silver, is_dark, filters, "3D Grid Risk Landscape")


def _render_grid_monitoring_page(df_silver, df_transformer, is_dark, theme, filters):
    """Render Grid Monitoring page."""
    
    st.markdown(f"""
    <div style="
        font-size: 24px;
        font-weight: 700;
        color: {theme.text};
        margin-bottom: 8px;
    ">
        Grid Monitoring
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="
        font-size: 13px;
        color: {theme.text_muted};
        margin-bottom: 20px;
    ">
        Regional health, substation performance, energy flow, load distribution, faults, and outages.
    </div>
    """, unsafe_allow_html=True)
    
    if df_silver is None or len(df_silver) == 0:
        st.warning("No data available.")
        return
    
    # Apply filters
    df_filtered = apply_filters(df_silver, filters)
    
    if len(df_filtered) == 0:
        st.info("No data for selected filters.")
        return
    
    # Regional health section
    st.markdown(f"""
    <div style="
        background: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    ">
        <div style="
            font-size: 14px;
            font-weight: 700;
            color: {theme.text};
            margin-bottom: 12px;
        ">
            Regional Health Overview
        </div>
    """, unsafe_allow_html=True)
    
    # Region summary cards
    region_summary = df_filtered.groupby("region").agg(
        substation_count=("substation_id", "nunique"),
        transformer_count=("transformer_id", "nunique"),
        avg_load=("load_percent", "mean"),
        max_load=("load_percent", "max"),
        avg_temp=("temperature_c", "mean"),
        avg_risk=("risk_score", "mean"),
        max_risk=("risk_score", "max"),
        fault_count=("fault_indicator", "sum"),
        normal_count=("status", lambda x: (x == "Normal").sum()),
        total_count=("status", "count"),
    ).reset_index()
    
    region_summary["health_pct"] = (region_summary["normal_count"] / region_summary["total_count"]) * 100
    
    cols = st.columns(len(region_summary))
    
    for col, row in zip(cols, region_summary.iterrows()):
        row = row[1]
        region = row["region"]
        
        health_color = _get_health_color(row["health_pct"], theme)
        
        col.markdown(f"""
        <div style="
            background: {theme.surface_secondary};
            border: 1px solid {theme.border};
            border-radius: 6px;
            padding: 12px;
            text-align: center;
        ">
            <div style="
                font-size: 11px;
                color: {theme.text_muted};
                margin-bottom: 4px;
            ">{region}</div>
            <div style="
                font-size: 20px;
                font-weight: 700;
                color: {health_color};
            ">{row['health_pct']:.0f}%</div>
            <div style="
                font-size: 10px;
                color: {theme.text_muted};
                margin-bottom: 8px;
            ">Health</div>
            <div style="
                font-size: 10px;
                color: {theme.text};
                display: flex;
                justify-content: center;
                gap: 8px;
            ">
                <span>{substation_count} subs</span>
                <span>{transformer_count} tr</span>
            </div>
            <div style="
                font-size: 10px;
                color: {theme.text_muted};
            ">
                Load: {avg_load:.1f}% | Risk: {avg_risk:.1f}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Substation performance
    st.markdown(f"""
    <div style="
        background: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    ">
        <div style="
            font-size: 14px;
            font-weight: 700;
            color: {theme.text};
            margin-bottom: 12px;
        ">
            Substation Performance
        </div>
    """, unsafe_allow_html=True)
    
    substation_perf = df_filtered.groupby(["substation_id", "region"]).agg(
        transformers=("transformer_id", "nunique"),
        avg_load=("load_percent", "mean"),
        max_load=("load_percent", "max"),
        avg_temp=("temperature_c", "mean"),
        avg_voltage=("voltage_kv", "mean"),
        avg_risk=("risk_score", "mean"),
        max_risk=("risk_score", "max"),
        faults=("fault_indicator", "sum"),
        records=("event_id", "count"),
    ).reset_index().sort_values("max_risk", ascending=False)
    
    # Table
    perf_html = f"""
    <div style="
        overflow-x: auto;
    ">
        <table style="
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        ">
            <thead>
                <tr style="background: {theme.table_header};">
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid {theme.border};">Substation</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid {theme.border};">Region</th>
                    <th style="padding: 8px; text-align: right; border-bottom: 1px solid {theme.border};">Transformers</th>
                    <th style="padding: 8px; text-align: right; border-bottom: 1px solid {theme.border};">Avg Load</th>
                    <th style="padding: 8px; text-align: right; border-bottom: 1px solid {theme.border};">Max Load</th>
                    <th style="padding: 8px; text-align: right; border-bottom: 1px solid {theme.border};">Avg Temp</th>
                    <th style="padding: 8px; text-align: right; border-bottom: 1px solid {theme.border};">Avg Risk</th>
                    <th style="padding: 8px; text-align: right; border-bottom: 1px solid {theme.border};">Max Risk</th>
                    <th style="padding: 8px; text-align: right; border-bottom: 1px solid {theme.border};">Faults</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for idx, row in substation_perf.head(20).iterrows():
        bg = theme.table_row_even if idx % 2 == 0 else theme.table_row_odd
        
        perf_html += f"""
            <tr style="background: {bg};">
                <td style="padding: 6px 8px; border-bottom: 1px solid {theme.border_light};">{row['substation_id']}</td>
                <td style="padding: 6px 8px; border-bottom: 1px solid {theme.border_light};">{row['region']}</td>
                <td style="padding: 6px 8px; text-align: right; border-bottom: 1px solid {theme.border_light};">{row['transformers']}</td>
                <td style="padding: 6px 8px; text-align: right; border-bottom: 1px solid {theme.border_light}; color: {_get_load_color(row['avg_load'], theme)};">{row['avg_load']:.1f}%</td>
                <td style="padding: 6px 8px; text-align: right; border-bottom: 1px solid {theme.border_light}; color: {_get_load_color(row['max_load'], theme)};">{row['max_load']:.1f}%</td>
                <td style="padding: 6px 8px; text-align: right; border-bottom: 1px solid {theme.border_light}; color: {_get_temp_color(row['avg_temp'], theme)};">{row['avg_temp']:.1f}°C</td>
                <td style="padding: 6px 8px; text-align: right; border-bottom: 1px solid {theme.border_light};">{row['avg_risk']:.1f}</td>
                <td style="padding: 6px 8px; text-align: right; border-bottom: 1px solid {theme.border_light}; color: {_get_risk_color(row['max_risk'], theme)};">{int(row['max_risk'])}</td>
                <td style="padding: 6px 8px; text-align: right; border-bottom: 1px solid {theme.border_light}; color: {theme.critical if row['faults'] > 0 else theme.text};">{int(row['faults'])}</td>
            </tr>
        """
    
    perf_html += """
            </tbody>
        </table>
    </div>
    """
    
    st.markdown(perf_html, unsafe_allow_html=True)


def _render_transformers_page(df_silver, is_dark, theme, filters):
    """Render Transformers page."""
    
    st.markdown(f"""
    <div style="
        font-size: 24px;
        font-weight: 700;
        color: {theme.text};
        margin-bottom: 8px;
    ">
        Transformers
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="
        font-size: 13px;
        color: {theme.text_muted};
        margin-bottom: 20px;
    ">
        All grid transformers with status, load, temperature, voltage, power factor, and risk assessment.
    </div>
    """, unsafe_allow_html=True)
    
    if df_silver is None or len(df_silver) == 0:
        st.warning("No data available.")
        return
    
    # Search bar
    search_term = st.text_input(
        "Search transformer ID",
        placeholder="e.g., TR-001",
        key="transformer_search",
        label_visibility="collapsed",
    )
    
    render_transformer_table(df_silver, is_dark, filters, search_term)


def _render_3d_page(df_silver, is_dark, theme, filters):
    """Render dedicated 3D Analytics page."""
    
    st.markdown(f"""
    <div style="
        font-size: 24px;
        font-weight: 700;
        color: {theme.text};
        margin-bottom: 8px;
    ">
        3D Analytics
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="
        font-size: 13px;
        color: {theme.text_muted};
        margin-bottom: 20px;
    ">
        Real 3D data visualizations showing relationships between grid variables.
    </div>
    """, unsafe_allow_html=True)
    
    if df_silver is None or len(df_silver) == 0:
        st.warning("No data available.")
        return
    
    render_3d_analytics(df_silver, is_dark, filters, "3D Grid Risk Landscape")


def _render_anomalies_page(df_silver, df_anomaly, is_dark, theme, filters):
    """Render Anomalies page."""
    
    st.markdown(f"""
    <div style="
        font-size: 24px;
        font-weight: 700;
        color: {theme.text};
        margin-bottom: 8px;
    ">
        Anomalies
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="
        font-size: 13px;
        color: {theme.text_muted};
        margin-bottom: 20px;
    ">
        Detected anomalies using Isolation Forest ML algorithm.
    </div>
    """, unsafe_allow_html=True)
    
    if df_silver is None or len(df_silver) == 0:
        st.warning("No data available.")
        return
    
    # Anomaly summary stats
    df_filtered = apply_filters(df_silver, filters)
    
    if len(df_filtered) == 0:
        st.info("No data for selected filters.")
        return
    
    anomalous = df_filtered[df_filtered["status"] != "Normal"]
    
    # Summary cards
    col_crit, col_high, col_warn = st.columns(3)
    
    with col_crit:
        st.markdown(f"""
        <div style="
            background: {theme.critical_light};
            border: 1px solid {theme.critical};
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        ">
            <div style="
                font-size: 32px;
                font-weight: 700;
                color: {theme.critical};
            ">{len(anomalous[anomalous['status'] == 'Critical'])}</div>
            <div style="
                font-size: 12px;
                color: {theme.text};
            ">Critical</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_high:
        st.markdown(f"""
        <div style="
            background: {theme.high_risk_light};
            border: 1px solid {theme.high_risk};
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        ">
            <div style="
                font-size: 32px;
                font-weight: 700;
                color: {theme.high_risk};
            ">{len(anomalous[anomalous['status'] == 'High Risk'])}</div>
            <div style="
                font-size: 12px;
                color: {theme.text};
            ">High Risk</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_warn:
        st.markdown(f"""
        <div style="
            background: {theme.warning_light};
            border: 1px solid {theme.warning};
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        ">
            <div style="
                font-size: 32px;
                font-weight: 700;
                color: {theme.warning};
            ">{len(anomalous[anomalous['status'] == 'Warning'])}</div>
            <div style="
                font-size: 12px;
                color: {theme.text};
            ">Warning</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Anomaly detail table
    anomaly_detail = df_filtered[df_filtered["status"] != "Normal"].copy()
    anomaly_detail["timestamp"] = pd.to_datetime(anomaly_detail["timestamp"])
    anomaly_detail = anomaly_detail.sort_values(
        ["timestamp", "risk_score"],
        ascending=[False, False]
    )
    
    if len(anomaly_detail) == 0:
        st.success("No anomalies detected in the selected filters.")
        return
    
    anomaly_html = f"""
    <div style="
        background: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: 8px;
        overflow: hidden;
    ">
        <table style="
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        ">
            <thead>
                <tr style="background: {theme.table_header};">
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid {theme.border};">Timestamp</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid {theme.border};">Transformer</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid {theme.border};">Substation</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid {theme.border};">Anomaly Type</th>
                    <th style="padding: 8px; text-align: right; border-bottom: 1px solid {theme.border};">Anomaly Score</th>
                    <th style="padding: 8px; text-align: right; border-bottom: 1px solid {theme.border};">Risk Score</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid {theme.border};">Status</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for idx, row in anomaly_detail.head(50).iterrows():
        status = row["status"]
        status_bg = _get_status_background(status, theme)
        status_color = _get_status_color(status, theme)
        bg = theme.table_row_even if idx % 2 == 0 else theme.table_row_odd
        
        anomaly_html += f"""
            <tr style="background: {bg};">
                <td style="padding: 8px; border-bottom: 1px solid {theme.border_light};">
                    {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
                </td>
                <td style="padding: 8px; border-bottom: 1px solid {theme.border_light}; font-weight: 600;">
                    {row['transformer_id']}
                </td>
                <td style="padding: 8px; border-bottom: 1px solid {theme.border_light};">
                    {row['substation_id']}
                </td>
                <td style="padding: 8px; border-bottom: 1px solid {theme.border_light};">
                    {row['anomaly_type']}
                </td>
                <td style="padding: 8px; text-align: right; border-bottom: 1px solid {theme.border_light};">
                    {row['anomaly_score']:.4f}
                </td>
                <td style="padding: 8px; text-align: right; border-bottom: 1px solid {theme.border_light}; color: {status_color}; font-weight: 700;">
                    {int(row['risk_score'])}
                </td>
                <td style="padding: 8px; border-bottom: 1px solid {theme.border_light};">
                    <span style="
                        padding: 3px 8px;
                        background: {status_bg};
                        color: {status_color};
                        border-radius: 4px;
                        font-size: 10px;
                        font-weight: 700;
                    ">{status}</span>
                </td>
            </tr>
        """
    
    anomaly_html += """
            </tbody>
        </table>
    </div>
    """
    
    st.markdown(anomaly_html, unsafe_allow_html=True)


def _render_forecasting_page(df_silver, is_dark, theme, filters):
    """Render Forecasting page."""
    
    st.markdown(f"""
    <div style="
        font-size: 24px;
        font-weight: 700;
        color: {theme.text};
        margin-bottom: 8px;
    ">
        Forecasting
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="
        font-size: 13px;
        color: {theme.text_muted};
        margin-bottom: 20px;
    ">
        Simple academic forecasting for energy consumption and grid load. <br>
        <em style="color: {theme.warning};">Note: This uses simple forecasting methods for demonstration purposes.</em>
    </div>
    """, unsafe_allow_html=True)
    
    if df_silver is None or len(df_silver) == 0:
        st.warning("No data available.")
        return
    
    df_filtered = apply_filters(df_silver, filters)
    
    if len(df_filtered) == 0:
        st.info("No data for selected filters.")
        return
    
    df_filtered = df_filtered.copy()
    df_filtered["timestamp"] = pd.to_datetime(df_filtered["timestamp"])
    
    # Hourly aggregation for forecasting
    hourly = df_filtered.copy()
    hourly["hour"] = hourly["timestamp"].dt.floor("h")
    
    hourly_agg = hourly.groupby("hour").agg(
        avg_load=("load_percent", "mean"),
        total_consumption=("energy_consumed_mwh", "sum"),
        avg_temp=("temperature_c", "mean"),
    ).reset_index().sort_values("hour")
    
    if len(hourly_agg) < 6:
        st.warning("Not enough data for forecasting. Need at least 6 data points.")
        return
    
    # Simple linear forecasting
    forecast_col, actual_col = st.columns([1, 1])
    
    with forecast_col:
        st.markdown(f"""
        <div style="
            background: {theme.surface};
            border: 1px solid {theme.border};
            border-radius: 8px;
            padding: 16px;
        ">
            <div style="
                font-size: 14px;
                font-weight: 700;
                color: {theme.text};
                margin-bottom: 12px;
            ">
                Grid Load Forecast
            </div>
        """, unsafe_allow_html=True)
        
        # Use simple linear trend for forecast
        from sklearn.linear_model import LinearRegression
        import numpy as np
        
        # Prepare data
        X = np.arange(len(hourly_agg)).reshape(-1, 1)
        y = hourly_agg["avg_load"].values
        
        # Fit model
        model = LinearRegression()
        model.fit(X, y)
        
        # Forecast next 6 hours
        future_X = np.arange(len(hourly_agg), len(hourly_agg) + 6).reshape(-1, 1)
        forecast = model.predict(future_X)
        forecast = np.clip(forecast, 0, 100)
        
        # Plot
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        # Historical
        fig.add_trace(go.Scatter(
            x=hourly_agg["hour"],
            y=hourly_agg["avg_load"],
            mode='lines+markers',
            name='Historical',
            line=dict(color=theme.primary, width=2),
            marker=dict(size=5),
        ))
        
        # Forecast
        last_hour = hourly_agg["hour"].iloc[-1]
        forecast_hours = pd.date_range(
            last_hour + pd.Timedelta(hours=1),
            periods=6,
            freq='h'
        )
        
        fig.add_trace(go.Scatter(
            x=forecast_hours,
            y=forecast,
            mode='lines+markers',
            name='Forecast',
            line=dict(color=theme.warning, width=2, dash='dash'),
            marker=dict(size=5, symbol='diamond'),
        ))
        
        fig.update_layout(
            title="Grid Load: Historical vs Forecast (next 6 hours)",
            height=300,
            paper_bgcolor=theme.surface,
            plot_bgcolor=theme.chart_background,
            xaxis=dict(
                tickformat='%H:%M',
                gridcolor=theme.chart_grid,
            ),
            yaxis=dict(
                title='Load %',
                gridcolor=theme.chart_grid,
            ),
            legend=dict(x=0.5, y=1.1, orientation='h'),
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(f"""
        <div style="
            margin-top: 8px;
            padding: 8px;
            background: {theme.surface_secondary};
            border-radius: 4px;
            font-size: 11px;
        ">
            <b>Forecast Summary:</b><br>
            Next hour: {forecast[0]:.1f}% | 
            In 3 hours: {forecast[2]:.1f}% | 
            In 6 hours: {forecast[5]:.1f}%
        </div>
        """, unsafe_allow_html=True)
    
    with actual_col:
        st.markdown(f"""
        <div style="
            background: {theme.surface};
            border: 1px solid {theme.border};
            border-radius: 8px;
            padding: 16px;
        ">
            <div style="
                font-size: 14px;
                font-weight: 700;
                color: {theme.text};
                margin-bottom: 12px;
            ">
                Energy Consumption Forecast
            </div>
        """, unsafe_allow_html=True)
        
        # Energy consumption forecast
        y_energy = hourly_agg["total_consumption"].values
        
        model_energy = LinearRegression()
        model_energy.fit(X, y_energy)
        
        forecast_energy = model_energy.predict(future_X)
        forecast_energy = np.clip(forecast_energy, 0, None)
        
        fig2 = go.Figure()
        
        fig2.add_trace(go.Scatter(
            x=hourly_agg["hour"],
            y=hourly_agg["total_consumption"],
            mode='lines+markers',
            name='Historical',
            line=dict(color=theme.generation_color, width=2),
            marker=dict(size=5),
        ))
        
        fig2.add_trace(go.Scatter(
            x=forecast_hours,
            y=forecast_energy,
            mode='lines+markers',
            name='Forecast',
            line=dict(color=theme.consumption_color, width=2, dash='dash'),
            marker=dict(size=5, symbol='diamond'),
        ))
        
        fig2.update_layout(
            title="Energy Consumption: Historical vs Forecast (next 6 hours)",
            height=300,
            paper_bgcolor=theme.surface,
            plot_bgcolor=theme.chart_background,
            xaxis=dict(
                tickformat='%H:%M',
                gridcolor=theme.chart_grid,
            ),
            yaxis=dict(
                title='MWh',
                gridcolor=theme.chart_grid,
            ),
            legend=dict(x=0.5, y=1.1, orientation='h'),
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown(f"""
        <div style="
            margin-top: 8px;
            padding: 8px;
            background: {theme.surface_secondary};
            border-radius: 4px;
            font-size: 11px;
        ">
            <b>Forecast Summary:</b><br>
            Next hour: {forecast_energy[0]:,.0f} MWh | 
            In 3 hours: {forecast_energy[2]:,.0f} MWh | 
            In 6 hours: {forecast_energy[5]:,.0f} MWh
        </div>
        """, unsafe_allow_html=True)


def _render_reports_page(df_silver, is_dark, theme, filters):
    """Render Reports page."""
    
    st.markdown(f"""
    <div style="
        font-size: 24px;
        font-weight: 700;
        color: {theme.text};
        margin-bottom: 8px;
    ">
        Reports
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="
        font-size: 13px;
        color: {theme.text_muted};
        margin-bottom: 20px;
    ">
        Data pipeline statistics, processing times, and export options.
    </div>
    """, unsafe_allow_html=True)
    
    if df_silver is None or len(df_silver) == 0:
        st.warning("No data available.")
        return
    
    # Pipeline flow visualization
    st.markdown(f"""
    <div style="
        background: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    ">
        <div style="
            font-size: 14px;
            font-weight: 700;
            color: {theme.text};
            margin-bottom: 16px;
        ">
            Data Pipeline Architecture
        </div>
        
        <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            flex-wrap: wrap;
        ">
            {''.join([
                f'''
                <div style="
                    background: {theme.primary};
                    color: white;
                    padding: 12px 16px;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 600;
                    text-align: center;
                    min-width: 100px;
                    box-shadow: {theme.shadow};
                ">
                    RAW<br>
                    <span style="font-size: 10px; opacity: 0.8;">{len(df_silver):,} records</span>
                </div>
                <div style="color: {theme.primary}; font-size: 20px;">↓</div>
                '''
                for _ in range(1)
            ])}
            
            <div style="
                background: {theme.success};
                color: white;
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                text-align: center;
                min-width: 100px;
                box-shadow: {theme.shadow};
            ">
                BRONZE
            </div>
            <div style="color: {theme.success}; font-size: 20px;">↓</div>
            
            <div style="
                background: {theme.warning};
                color: white;
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                text-align: center;
                min-width: 100px;
                box-shadow: {theme.shadow};
            ">
                SILVER
            </div>
            <div style="color: {theme.warning}; font-size: 20px;">↓</div>
            
            <div style="
                background: {theme.high_risk};
                color: white;
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                text-align: center;
                min-width: 100px;
                box-shadow: {theme.shadow};
            ">
                ANALYTICS
            </div>
            <div style="color: {theme.high_risk}; font-size: 20px;">↓</div>
            
            <div style="
                background: {theme.critical};
                color: white;
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                text-align: center;
                min-width: 100px;
                box-shadow: {theme.shadow};
            ">
                GOLD
            </div>
            <div style="color: {theme.critical}; font-size: 20px;">↓</div>
            
            <div style="
                background: {theme.primary};
                color: white;
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                text-align: center;
                min-width: 100px;
                box-shadow: {theme.shadow};
            ">
                DASHBOARD
            </div>
        </div>
        
        <div style="
            margin-top: 16px;
            padding: 12px;
            background: {theme.surface_secondary};
            border-radius: 6px;
            font-size: 11px;
            color: {theme.text_muted};
        ">
            <b>Statistics:</b><br>
            Silver records in dashboard: {len(df_silver):,}<br>
            Total transformers: {df_silver['transformer_id'].nunique():,}<br>
            Total substations: {df_silver['substation_id'].nunique()}<br>
            Total regions: {df_silver['region'].nunique()}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Export options
    st.markdown(f"""
    <div style="
        background: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: 8px;
        padding: 16px;
    ">
        <div style="
            font-size: 14px;
            font-weight: 700;
            color: {theme.text};
            margin-bottom: 12px;
        ">
            Export Data
        </div>
        
        <div style="
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        ">
            <div style="
                background: {theme.surface_secondary};
                border: 1px solid {theme.border};
                border-radius: 6px;
                padding: 12px;
                cursor: pointer;
            ">
                <div style="
                    font-size: 12px;
                    font-weight: 600;
                    color: {theme.text};
                    margin-bottom: 4px;
                ">Transformer Summary</div>
                <div style="font-size: 10px; color: {theme.text_muted};">Download CSV</div>
            </div>
            <div style="
                background: {theme.surface_secondary};
                border: 1px solid {theme.border};
                border-radius: 6px;
                padding: 12px;
                cursor: pointer;
            ">
                <div style="
                    font-size: 12px;
                    font-weight: 600;
                    color: {theme.text};
                    margin-bottom: 4px;
                ">Critical Transformers</div>
                <div style="font-size: 10px; color: {theme.text_muted};">Download CSV</div>
            </div>
            <div style="
                background: {theme.surface_secondary};
                border: 1px solid {theme.border};
                border-radius: 6px;
                padding: 12px;
                cursor: pointer;
            ">
                <div style="
                    font-size: 12px;
                    font-weight: 600;
                    color: {theme.text};
                    margin-bottom: 4px;
                ">Anomaly Summary</div>
                <div style="font-size: 10px; color: {theme.text_muted};">Download CSV</div>
            </div>
            <div style="
                background: {theme.surface_secondary};
                border: 1px solid {theme.border};
                border-radius: 6px;
                padding: 12px;
                cursor: pointer;
            ">
                <div style="
                    font-size: 12px;
                    font-weight: 600;
                    color: {theme.text};
                    margin-bottom: 4px;
                ">Severity Distribution</div>
                <div style="font-size: 10px; color: {theme.text_muted};">Download CSV</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_live_feed(df_silver, is_dark, theme, filters):
    """Render live feed ticker at bottom."""
    
    df_filtered = apply_filters(df_silver, filters)
    
    # Get recent alerts for ticker
    if df_filtered is not None and len(df_filtered) > 0:
        anomalous = df_filtered[df_filtered["status"] != "Normal"].copy()
        anomalous["timestamp"] = pd.to_datetime(anomalous["timestamp"])
        anomalous = anomalous.sort_values("timestamp", ascending=False).head(5)
        
        ticker_items = []
        for _, row in anomalous.iterrows():
            time_str = row["timestamp"].strftime("%H:%M")
            event_desc = _get_event_description(row)
            ticker_items.append(f"{time_str} {event_desc}")
    
    if len(ticker_items) == 0:
        ticker_items = [
            "System monitoring active",
            "All systems operational",
            "Grid stable",
        ]
    
    # Build ticker HTML
    ticker_html = f"""
    <div style="
        background: {theme.critical if len(anomalous) > 0 else theme.primary}15;
        border-top: 2px solid {theme.critical if len(anomalous) > 0 else theme.primary};
        padding: 8px 24px;
        display: flex;
        align-items: center;
        gap: 16px;
        overflow: hidden;
    ">
        <div style="
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 700;
            color: {'white' if len(anomalous) > 0 else theme.primary};
            white-space: nowrap;
        ">
            <span style="
                width: 8px;
                height: 8px;
                background: {'#ef4444' if len(anomalous) > 0 else theme.success};
                border-radius: 50%;
                animation: pulse 2s infinite;
            "></span>
            <span>Live Feed</span>
        </div>
        
        <div style="
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
            overflow-x: auto;
            padding: 4px 0;
        ">
    """
    
    for i, item in enumerate(ticker_items):
        ticker_html += f"""
            <span style="
                font-size: 11px;
                color: {theme.text};
                white-space: nowrap;
                padding: 0 8px;
            ">
                {item}
            </span>
            {f'<span style="color: {theme.border}; padding: 0 4px;">|</span>' if i < len(ticker_items) - 1 else ''}
        """
    
    ticker_html += """
        </div>
    </div>
    """
    
    st.markdown(ticker_html, unsafe_allow_html=True)


def _get_event_description(row) -> str:
    """Get human-readable event description."""
    anomaly_type = row["anomaly_type"]
    substation = row["substation_id"]
    
    descriptions = {
        "Overload": f"High load detected at {substation}",
        "Temperature Spike": f"Transformer temperature rising at {substation}",
        "Voltage Fluctuation": f"Voltage fluctuation at {substation}",
        "Frequency Deviation": f"Frequency deviation at {substation}",
        "Power Factor Anomaly": f"Power factor anomaly at {substation}",
        "Transformer Fault": f"Transformer fault at {substation}",
        "Communication Failure": f"Communication failure at {substation}",
    }
    
    return descriptions.get(anomaly_type, f"{anomaly_type} at {substation}")


def _get_health_color(health_pct: float, theme) -> str:
    """Get color based on health percentage."""
    if health_pct >= 80:
        return theme.success
    elif health_pct >= 60:
        return theme.warning
    elif health_pct >= 40:
        return theme.high_risk
    return theme.critical


def _get_load_color(load: float, theme) -> str:
    """Get color based on load."""
    if load >= 85:
        return theme.critical
    elif load >= 70:
        return theme.high_risk
    elif load >= 50:
        return theme.warning
    return theme.success


def _get_temp_color(temp: float, theme) -> str:
    """Get color based on temperature."""
    if temp >= 70:
        return theme.critical
    elif temp >= 60:
        return theme.high_risk
    elif temp >= 50:
        return theme.warning
    return theme.success


def _get_risk_color(risk: float, theme) -> str:
    """Get color based on risk score."""
    if risk >= 85:
        return theme.critical
    elif risk >= 70:
        return theme.high_risk
    elif risk >= 50:
        return theme.warning
    return theme.success


def _get_status_color(status: str, theme) -> str:
    """Get color for status."""
    status_colors = {
        "Critical": theme.critical,
        "High Risk": theme.high_risk,
        "Warning": theme.warning,
        "Normal": theme.success,
        "Low": theme.success,
    }
    return status_colors.get(status, theme.text)


def _get_status_background(status: str, theme) -> str:
    """Get background for status."""
    status_bgs = {
        "Critical": theme.critical_light,
        "High Risk": theme.high_risk_light,
        "Warning": theme.warning_light,
        "Normal": theme.success_light,
        "Low": theme.success_light,
    }
    return status_bgs.get(status, theme.surface_secondary)


def _inject_base_css(theme):
    """Inject base CSS styles."""
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {{
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }}
    
    body {{
        background: {theme.background};
    }}
    
    .stApp {{
        background: {theme.background};
    }}
    
    /* Hide sidebar header */
    [data-testid="stSidebarNav"] {{
        display: none;
    }}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}
    ::-webkit-scrollbar-track {{
        background: transparent;
    }}
    ::-webkit-scrollbar-thumb {{
        background: {theme.scrollbar_thumb};
        border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {theme.text_muted};
    }}
    
    /* Smooth transitions */
    * {{
        transition: background-color 0.2s, border-color 0.2s, color 0.2s;
    }}
    
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }}
        70% {{ box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }}
    }}
    </style>
    """, unsafe_allow_html=True)


def _render_system_status_card(df, theme):
    """Render system status card in sidebar."""
    
    if df is not None and len(df) > 0:
        total_records = len(df)
        latest_time = pd.to_datetime(df["timestamp"]).max()
        
        status_html = f"""
        <div style="
            background: {theme.surface};
            border: 1px solid {theme.border};
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
        ">
            <div style="
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 10px;
            ">
                <div style="
                    width: 28px;
                    height: 28px;
                    background: {theme.primary};
                    border-radius: 6px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                ">
                    🛡️
                </div>
                <div>
                    <div style="
                        font-size: 12px;
                        font-weight: 700;
                        color: {theme.text};
                    ">
                        System Status
                    </div>
                </div>
            </div>
            
            <div style="
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 6px 8px;
                background: {theme.success_light};
                border-radius: 4px;
                margin-bottom: 8px;
            ">
                <span style="
                    width: 8px;
                    height: 8px;
                    background: {theme.success};
                    border-radius: 50%;
                    display: inline-block;
                    animation: pulse 2s infinite;
                "></span>
                <span style="
                    font-size: 12px;
                    font-weight: 600;
                    color: {theme.text};
                ">
                    All Systems Operational
                </span>
            </div>
            
            <div style="
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            ">
                <div style="
                    background: {theme.surface_secondary};
                    padding: 8px;
                    border-radius: 4px;
                ">
                    <div style="
                        font-size: 10px;
                        color: {theme.text_muted};
                        margin-bottom: 4px;
                    ">Data Pipeline</div>
                    <div style="
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                    ">
                        <span style="color: {theme.text}; font-weight: 500;">Running</span>
                        <span style="color: {theme.text_muted}; font-size: 10px;">
                            {latest_time.strftime('%H:%M:%S') if pd.notna(latest_time) else '--:--:--'}
                        </span>
                    </div>
                </div>
                
                <div style="
                    background: {theme.surface_secondary};
                    padding: 8px;
                    border-radius: 4px;
                ">
                    <div style="
                        font-size: 10px;
                        color: {theme.text_muted};
                        margin-bottom: 4px;
                    ">Records (Today)</div>
                    <div style="
                        font-size: 14px;
                        font-weight: 700;
                        color: {theme.text};
                    ">
                        {total_records:,}
                    </div>
                </div>
            </div>
        </div>
        """
    else:
        status_html = f"""
        <div style="
            background: {theme.surface};
            border: 1px solid {theme.border};
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
        ">
            <div style="
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 10px;
            ">
                <div style="
                    width: 28px;
                    height: 28px;
                    background: {theme.warning};
                    border-radius: 6px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                ">
                    🛡️
                </div>
                <div>
                    <div style="
                        font-size: 12px;
                        font-weight: 700;
                        color: {theme.text};
                    ">
                        System Status
                    </div>
                </div>
            </div>
            
            <div style="
                padding: 8px;
                background: {theme.warning_light};
                border-radius: 4px;
                margin-bottom: 8px;
            ">
                <span style="
                    font-size: 12px;
                    font-weight: 600;
                    color: {theme.warning};
                ">
                    No Data Available
                </span>
            </div>
            
            <div style="
                background: {theme.surface_secondary};
                padding: 8px;
                border-radius: 4px;
            ">
                <div style="
                    font-size: 10px;
                    color: {theme.text_muted};
                    margin-bottom: 4px;
                ">Data Pipeline</div>
                <div style="
                    color: {theme.text};
                    font-weight: 500;
                ">Idle</div>
            </div>
        </div>
        """
    
    st.markdown(status_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
GridPulse Recent Alerts Component
Alert table matching reference design
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from dashboard.theme import get_theme
from dashboard.filters import apply_filters


def render_recent_alerts(df: pd.DataFrame, is_dark: bool = False,
                         filters: dict = None, max_alerts: int = 5) -> None:
    """
    Render Recent Alerts table matching reference design.
    
    Columns:
    - Time
    - Event (Anomaly Type)
    - Location (Substation)
    - Severity (Status)
    
    Shows only non-normal records.
    """
    theme = get_theme(is_dark)
    
    if df is None or len(df) == 0:
        st.info("No alerts to display.", icon="🔔")
        return
    
    # Apply filters
    if filters:
        df = apply_filters(df, filters)
    
    if len(df) == 0:
        st.info("No alerts for the selected filters.", icon="🔔")
        return
    
    # Filter to anomalous records
    alerts_df = df[df["status"] != "Normal"].copy()
    
    if len(alerts_df) == 0:
        st.info("No anomalies detected.", icon="✅")
        return
    
    # Sort by timestamp descending, then by risk score descending
    alerts_df["timestamp"] = pd.to_datetime(alerts_df["timestamp"])
    alerts_df = alerts_df.sort_values(
        ["timestamp", "risk_score"],
        ascending=[False, False]
    ).head(max_alerts)
    
    # Render header
    st.markdown(f"""
    <div style="
        font-size: 14px;
        font-weight: 700;
        color: {theme.text};
        margin-bottom: 4px;
    ">
        Recent Alerts
    </div>
    """, unsafe_allow_html=True)
    
    # Create table
    table_html = f"""
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
                <tr style="
                    background: {theme.table_header};
                ">
                    <th style="
                        padding: 8px 12px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Time</th>
                    <th style="
                        padding: 8px 12px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Event</th>
                    <th style="
                        padding: 8px 12px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Location</th>
                    <th style="
                        padding: 8px 12px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Severity</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for idx, row in alerts_df.iterrows():
        status = row["status"]
        status_bg = _get_status_background(status, theme)
        status_color = _get_status_color(status, theme)
        time_str = row["timestamp"].strftime("%H:%M:%S") if pd.notna(row["timestamp"]) else "-"
        
        table_html += f"""
                <tr style="
                    {'background: ' + status_bg if idx % 2 == 0 else ''}
                ">
                    <td style="
                        padding: 8px 12px;
                        color: {theme.text};
                        border-bottom: 1px solid {theme.border_light};
                    ">{time_str}</td>
                    <td style="
                        padding: 8px 12px;
                        color: {theme.text};
                        font-weight: 500;
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['anomaly_type']}</td>
                    <td style="
                        padding: 8px 12px;
                        color: {theme.text};
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['substation_id']}</td>
                    <td style="
                        padding: 8px 12px;
                        border-bottom: 1px solid {theme.border_light};
                    ">
                        <span style="
                            padding: 3px 8px;
                            background: {status_bg};
                            color: {status_color};
                            border-radius: 4px;
                            font-size: 10px;
                            font-weight: 700;
                            text-transform: uppercase;
                        ">{status}</span>
                    </td>
                </tr>
        """
    
    table_html += """
            </tbody>
        </table>
    </div>
    """
    
    st.markdown(table_html, unsafe_allow_html=True)
    
    # View All link
    st.markdown(f"""
    <div style="
        margin-top: 8px;
        text-align: right;
    ">
        <a href="#" style="
            color: {theme.primary};
            font-size: 12px;
            font-weight: 600;
            text-decoration: none;
        ">View All →</a>
    </div>
    """, unsafe_allow_html=True)


def _get_status_color(status: str, theme) -> str:
    """Get text color for status."""
    status_colors = {
        "Critical": theme.critical,
        "High Risk": theme.high_risk,
        "Warning": theme.warning,
        "Normal": theme.success,
        "Low": theme.success,
    }
    return status_colors.get(status, theme.text)


def _get_status_background(status: str, theme) -> str:
    """Get background color for status badge."""
    status_bgs = {
        "Critical": theme.critical_light,
        "High Risk": theme.high_risk_light,
        "Warning": theme.warning_light,
        "Normal": theme.success_light,
        "Low": theme.success_light,
    }
    return status_bgs.get(status, theme.surface_secondary)

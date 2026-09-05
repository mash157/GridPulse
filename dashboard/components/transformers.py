#!/usr/bin/env python
"""
GridPulse Transformers Component
Transformer risk tables matching reference design
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from dashboard.theme import get_theme
from dashboard.filters import apply_filters


def render_top_risk_transformers(df: pd.DataFrame, is_dark: bool = False,
                                 filters: dict = None, max_rows: int = 5) -> None:
    """
    Render Top Risk Transformers table matching reference design.
    
    Columns:
    - ID (Transformer ID)
    - Substation
    - Risk (Risk Score)
    - Status
    
    Sorted by risk descending.
    """
    theme = get_theme(is_dark)
    
    if df is None or len(df) == 0:
        st.info("No transformer data available.", icon="⚡")
        return
    
    # Apply filters
    if filters:
        df = apply_filters(df, filters)
    
    if len(df) == 0:
        st.info("No transformer data for the selected filters.", icon="⚡")
        return
    
    # Get transformer risk summary
    transformer_risk = df.groupby(["transformer_id", "substation_id", "region"]).agg(
        avg_risk=("risk_score", "mean"),
        max_risk=("risk_score", "max"),
        avg_load=("load_percent", "mean"),
        avg_temp=("temperature_c", "mean"),
        avg_voltage=("voltage_kv", "mean"),
        avg_pf=("power_factor", "mean"),
    ).reset_index()
    
    # Get worst status based on max risk
    transformer_risk["status"] = transformer_risk["max_risk"].apply(_classify_risk)
    
    # Sort by max risk descending
    transformer_risk = transformer_risk.sort_values("max_risk", ascending=False).head(max_rows)
    
    # Render header
    st.markdown(f"""
    <div style="
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    ">
        <div style="
            font-size: 14px;
            font-weight: 700;
            color: {theme.text};
        ">
            Top Risk Transformers
        </div>
        <a href="#" style="
            color: {theme.primary};
            font-size: 12px;
            font-weight: 600;
            text-decoration: none;
        ">View All →</a>
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
                    ">ID</th>
                    <th style="
                        padding: 8px 12px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Substation</th>
                    <th style="
                        padding: 8px 12px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Risk</th>
                    <th style="
                        padding: 8px 12px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Status</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for idx, row in transformer_risk.iterrows():
        status = row["status"]
        status_bg = _get_status_background(status, theme)
        status_color = _get_status_color(status, theme)
        
        # Risk color based on level
        risk_color = status_color
        
        table_html += f"""
                <tr style="
                    {'background: ' + theme.table_row_even if idx % 2 == 0 else 'background: ' + theme.table_row_odd}
                ">
                    <td style="
                        padding: 8px 12px;
                        color: {theme.text};
                        font-weight: 600;
                        border-bottom: 1px solid {theme.border};
                    ">{row['transformer_id']}</td>
                    <td style="
                        padding: 8px 12px;
                        color: {theme.text};
                        border-bottom: 1px solid {theme.border};
                    ">{row['substation_id']}</td>
                    <td style="
                        padding: 8px 12px;
                        color: {risk_color};
                        font-weight: 700;
                        border-bottom: 1px solid {theme.border};
                    ">{int(row['max_risk'])}</td>
                    <td style="
                        padding: 8px 12px;
                        border-bottom: 1px solid {theme.border};
                    ">
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
    
    table_html += """
            </tbody>
        </table>
    </div>
    """
    
    st.markdown(table_html, unsafe_allow_html=True)


def render_critical_transformers(df: pd.DataFrame, is_dark: bool = False,
                                  filters: dict = None) -> None:
    """
    Render Critical Transformers section matching reference design.
    
    Only shows transformers with risk_score >= 85.
    Columns:
    - Transformer ID
    - Substation
    - Region
    - Load
    - Temperature
    - Voltage
    - Risk Score
    - Anomaly Type
    """
    theme = get_theme(is_dark)
    
    if df is None or len(df) == 0:
        st.info("No data available.", icon="⚠️")
        return
    
    # Apply filters
    if filters:
        df = apply_filters(df, filters)
    
    if len(df) == 0:
        st.info("No data available for the selected filters.", icon="⚠️")
        return
    
    # Filter to critical
    critical_df = df[df["risk_score"] >= 85].copy()
    
    if len(critical_df) == 0:
        st.success("No critical transformers detected.", icon="✅")
        return
    
    # Get summary by transformer
    critical_summary = critical_df.groupby(
        ["transformer_id", "substation_id", "region"]
    ).agg(
        avg_load=("load_percent", "mean"),
        max_temp=("temperature_c", "max"),
        avg_voltage=("voltage_kv", "mean"),
        avg_risk=("risk_score", "mean"),
        max_risk=("risk_score", "max"),
        anomaly_types=("anomaly_type", lambda x: ", ".join(
            sorted(set(x[x != "Normal"].tolist()))
        ) if len(x[x != "Normal"]) > 0 else "Normal"),
    ).reset_index()
    
    critical_summary = critical_summary.sort_values("max_risk", ascending=False)
    
    # Render header
    st.markdown(f"""
    <div style="
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    ">
        <div style="
            font-size: 14px;
            font-weight: 700;
            color: {theme.critical};
        ">
            ⚠️ Critical Transformers
        </div>
        <span style="
            font-size: 12px;
            color: {theme.text_muted};
        ">
            {len(critical_summary)} transformers at risk
        </span>
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
            font-size: 11px;
        ">
            <thead>
                <tr style="
                    background: {theme.table_header};
                ">
                    <th style="
                        padding: 6px 8px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Transformer ID</th>
                    <th style="
                        padding: 6px 8px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Substation</th>
                    <th style="
                        padding: 6px 8px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Region</th>
                    <th style="
                        padding: 6px 8px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Load %</th>
                    <th style="
                        padding: 6px 8px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Temp °C</th>
                    <th style="
                        padding: 6px 8px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Voltage kV</th>
                    <th style="
                        padding: 6px 8px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Risk</th>
                    <th style="
                        padding: 6px 8px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Anomaly Type</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for idx, row in critical_summary.iterrows():
        table_html += f"""
                <tr style="
                    {'background: ' + theme.critical_light if idx % 2 == 0 else 'background: ' + theme.surface}
                ">
                    <td style="
                        padding: 6px 8px;
                        color: {theme.text};
                        font-weight: 600;
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['transformer_id']}</td>
                    <td style="
                        padding: 6px 8px;
                        color: {theme.text};
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['substation_id']}</td>
                    <td style="
                        padding: 6px 8px;
                        color: {theme.text};
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['region']}</td>
                    <td style="
                        padding: 6px 8px;
                        color: {theme.high_risk};
                        font-weight: 600;
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['avg_load']:.1f}%</td>
                    <td style="
                        padding: 6px 8px;
                        color: {theme.critical};
                        font-weight: 600;
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['max_temp']:.1f}°C</td>
                    <td style="
                        padding: 6px 8px;
                        color: {theme.text};
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['avg_voltage']:.2f}</td>
                    <td style="
                        padding: 6px 8px;
                        color: {theme.critical};
                        font-weight: 700;
                        border-bottom: 1px solid {theme.border_light};
                    ">{int(row['max_risk'])}</td>
                    <td style="
                        padding: 6px 8px;
                        color: {theme.critical};
                        font-weight: 500;
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['anomaly_types']}</td>
                </tr>
        """
    
    table_html += """
            </tbody>
        </table>
    </div>
    """
    
    st.markdown(table_html, unsafe_allow_html=True)


def _classify_risk(score: float) -> str:
    """Classify risk score to status."""
    if score >= 85:
        return "Critical"
    elif score >= 70:
        return "High Risk"
    elif score >= 50:
        return "Warning"
    elif score >= 30:
        return "Low"
    else:
        return "Normal"


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

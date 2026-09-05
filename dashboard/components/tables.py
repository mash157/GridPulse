#!/usr/bin/env python
"""
GridPulse Transformer Table Component
Full transformer listing with search and sorting
"""

import streamlit as st
import pandas as pd
from dashboard.theme import get_theme
from dashboard.filters import apply_filters


def render_transformer_table(df: pd.DataFrame, is_dark: bool = False,
                             filters: dict = None, search_term: str = "") -> None:
    """
    Render full transformer listing table with search and sorting.
    
    Columns:
    - ID (Transformer ID)
    - Region
    - Substation
    - Load %
    - Temperature °C
    - Voltage kV
    - Power Factor
    - Risk
    - Status
    
    Features:
    - Search by transformer ID
    - Sortable columns
    - Status badges
    """
    theme = get_theme(is_dark)
    
    if df is None or len(df) == 0:
        st.info("No transformer data available.", icon="📋")
        return
    
    # Apply filters
    if filters:
        df = apply_filters(df, filters)
    
    if len(df) == 0:
        st.info("No transformer data for the selected filters.", icon="📋")
        return
    
    # Get transformer summary
    transformer_summary = df.groupby(
        ["transformer_id", "region", "substation_id"]
    ).agg(
        avg_load=("load_percent", "mean"),
        avg_temp=("temperature_c", "mean"),
        avg_voltage=("voltage_kv", "mean"),
        avg_pf=("power_factor", "mean"),
        max_risk=("risk_score", "max"),
        avg_risk=("risk_score", "mean"),
        status=("status", lambda x: _get_worst_status(x)),
    ).reset_index()
    
    # Apply search filter
    if search_term:
        transformer_summary = transformer_summary[
            transformer_summary["transformer_id"].str.contains(
                search_term, case=False, na=False
            )
        ]
    
    if len(transformer_summary) == 0:
        st.info("No transformers match the search criteria.", icon="🔍")
        return
    
    # Sort controls
    sort_col = st.selectbox(
        "Sort by",
        options=["ID", "Risk", "Load", "Temperature", "Status"],
        index=1,
        key="transformer_sort",
        label_visibility="collapsed",
    )
    
    sort_order = st.radio(
        "Order",
        options=["Descending", "Ascending"],
        index=0,
        key="transformer_order",
        label_visibility="collapsed",
    )
    
    ascending = sort_order == "Ascending"
    
    sort_mapping = {
        "ID": "transformer_id",
        "Risk": "max_risk",
        "Load": "avg_load",
        "Temperature": "avg_temp",
        "Status": "status",
    }
    
    transformer_summary = transformer_summary.sort_values(
        sort_mapping.get(sort_col, "max_risk"),
        ascending=ascending
    )
    
    # Display info
    st.markdown(f"""
    <div style="
        font-size: 11px;
        color: {theme.text_muted};
        margin-bottom: 8px;
    ">
        Showing <b>{len(transformer_summary):,}</b> transformers
        {f' matching "{search_term}"' if search_term else ''}
    </div>
    """, unsafe_allow_html=True)
    
    # Create table
    table_html = f"""
    <div style="
        background: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: 8px;
        overflow: hidden;
        max-height: 500px;
        overflow-y: auto;
    ">
        <table style="
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
        ">
            <thead>
                <tr style="
                    background: {theme.table_header};
                    position: sticky;
                    top: 0;
                    z-index: 1;
                ">
                    <th style="
                        padding: 8px 10px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                        cursor: pointer;
                    ">ID</th>
                    <th style="
                        padding: 8px 10px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Region</th>
                    <th style="
                        padding: 8px 10px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Substation</th>
                    <th style="
                        padding: 8px 10px;
                        text-align: right;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Load %</th>
                    <th style="
                        padding: 8px 10px;
                        text-align: right;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Temp °C</th>
                    <th style="
                        padding: 8px 10px;
                        text-align: right;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Voltage kV</th>
                    <th style="
                        padding: 8px 10px;
                        text-align: right;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Power Factor</th>
                    <th style="
                        padding: 8px 10px;
                        text-align: right;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Risk</th>
                    <th style="
                        padding: 8px 10px;
                        text-align: left;
                        font-weight: 600;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border};
                    ">Status</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for idx, row in transformer_summary.iterrows():
        status = row["status"]
        status_bg = _get_status_background(status, theme)
        status_color = _get_status_color(status, theme)
        
        risk_color = _get_risk_color(row["max_risk"], theme)
        
        bg = theme.table_row_even if idx % 2 == 0 else theme.table_row_odd
        
        table_html += f"""
                <tr style="
                    background: {bg};
                ">
                    <td style="
                        padding: 6px 10px;
                        color: {theme.text};
                        font-weight: 600;
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['transformer_id']}</td>
                    <td style="
                        padding: 6px 10px;
                        color: {theme.text_muted};
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['region']}</td>
                    <td style="
                        padding: 6px 10px;
                        color: {theme.text};
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['substation_id']}</td>
                    <td style="
                        padding: 6px 10px;
                        color: {_get_load_color(row['avg_load'], theme)};
                        text-align: right;
                        font-weight: 500;
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['avg_load']:.1f}%</td>
                    <td style="
                        padding: 6px 10px;
                        color: {_get_temp_color(row['avg_temp'], theme)};
                        text-align: right;
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['avg_temp']:.1f}</td>
                    <td style="
                        padding: 6px 10px;
                        color: {theme.text};
                        text-align: right;
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['avg_voltage']:.2f}</td>
                    <td style="
                        padding: 6px 10px;
                        color: {_get_pf_color(row['avg_pf'], theme)};
                        text-align: right;
                        border-bottom: 1px solid {theme.border_light};
                    ">{row['avg_pf']:.3f}</td>
                    <td style="
                        padding: 6px 10px;
                        color: {risk_color};
                        text-align: right;
                        font-weight: 700;
                        border-bottom: 1px solid {theme.border_light};
                    ">{int(row['max_risk'])}</td>
                    <td style="
                        padding: 6px 10px;
                        border-bottom: 1px solid {theme.border_light};
                    ">
                        <span style="
                            padding: 2px 6px;
                            background: {status_bg};
                            color: {status_color};
                            border-radius: 3px;
                            font-size: 9px;
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


def _get_worst_status(statuses: pd.Series) -> str:
    """Get worst status from series."""
    priority = {"Critical": 4, "High Risk": 3, "Warning": 2, "Low": 1, "Normal": 0}
    
    worst = "Normal"
    worst_priority = -1
    
    for status in statuses:
        p = priority.get(status, 0)
        if p > worst_priority:
            worst_priority = p
            worst = status
    
    return worst


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


def _get_risk_color(risk: float, theme) -> str:
    """Get color based on risk score."""
    if risk >= 85:
        return theme.critical
    elif risk >= 70:
        return theme.high_risk
    elif risk >= 50:
        return theme.warning
    elif risk >= 30:
        return theme.warning
    return theme.success


def _get_load_color(load: float, theme) -> str:
    """Get color based on load percentage."""
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


def _get_pf_color(pf: float, theme) -> str:
    """Get color based on power factor."""
    if pf < 0.7:
        return theme.critical
    elif pf < 0.8:
        return theme.warning
    elif pf < 0.9:
        return theme.success
    return theme.success

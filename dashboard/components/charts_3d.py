#!/usr/bin/env python
"""
GridPulse 3D Analytics Component
Real 3D data visualizations using Plotly Scatter3d
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dashboard.theme import get_theme, get_3d_scene_config
from dashboard.filters import apply_filters
from dashboard.config import MAX_3D_POINTS


def render_3d_analytics(df: pd.DataFrame, is_dark: bool = False, 
                        filters: dict = None, selected_graph: str = "Risk Landscape") -> None:
    """
    Render 3D analytics page with multiple visualization options.
    
    Graphs:
    1. 3D Grid Risk Landscape - Voltage vs Temperature vs Risk Score
    2. Load Performance Space - Load% vs Power Factor vs Temperature
    3. Energy Consumption Space - Energy Generated vs Energy Consumed vs Load%
    4. Anomaly Detection Space - Voltage Deviation vs Temperature vs Anomaly Score
    """
    theme = get_theme(is_dark)
    
    if df is None or len(df) == 0:
        # Show overview of 3D graphs on main page
        _render_3d_overview(df, is_dark, filters, theme)
        return
    
    # Apply filters
    if filters:
        df = apply_filters(df, filters)
    
    if len(df) == 0:
        st.info("No data available for the selected filters.", icon="🧊")
        return
    
    # Graph selection tabs
    graph_options = [
        "3D Grid Risk Landscape",
        "Load Performance Space",
        "Energy Consumption Space",
        "Anomaly Detection Space",
    ]
    
    selected_idx = 0
    for idx, option in enumerate(graph_options):
        if option == selected_graph:
            selected_idx = idx
            break
    
    selected_graph = st.selectbox(
        "Select 3D Visualization",
        options=graph_options,
        index=selected_idx,
        label_visibility="collapsed",
    )
    
    # Render selected graph
    if selected_graph == "3D Grid Risk Landscape":
        _render_risk_landscape(df, is_dark, theme)
    elif selected_graph == "Load Performance Space":
        _render_load_performance(df, is_dark, theme)
    elif selected_graph == "Energy Consumption Space":
        _render_energy_consumption(df, is_dark, theme)
    elif selected_graph == "Anomaly Detection Space":
        _render_anomaly_detection(df, is_dark, theme)


def _render_3d_overview(df, is_dark, filters, theme):
    """Render compact 3D overview on main page."""
    
    if df is None or len(df) == 0:
        st.info("No data available for the 3D view.", icon="🧊")
        return
    
    if filters:
        df = apply_filters(df, filters)
    
    if len(df) == 0:
        st.info("No data available for the 3D view.", icon="🧊")
        return
    
    # Sample data for 3D
    sampled_df = _sample_for_3d(df)
    
    # Create 3D scatter: Load% vs Temperature vs Risk Score
    # Prioritize critical/high risk records
    
    status_order = {"Critical": 3, "High Risk": 2, "Warning": 1, "Normal": 0, "Low": 0}
    status_colors = {
        "Critical": theme.critical,
        "High Risk": theme.high_risk,
        "Warning": theme.warning,
        "Normal": theme.success,
        "Low": theme.success,
    }
    
    fig = go.Figure()
    
    # Add traces by status to ensure proper layering
    for status in ["Critical", "High Risk", "Warning", "Normal", "Low"]:
        status_df = sampled_df[sampled_df["status"] == status]
        if len(status_df) == 0:
            continue
        
        fig.add_trace(go.Scatter3d(
            x=status_df["load_percent"],
            y=status_df["temperature_c"],
            z=status_df["risk_score"],
            mode='markers',
            marker=dict(
                size=3,
                color=status_colors[status],
                opacity=0.8,
                line=dict(width=0.5, color='white'),
            ),
            name=status,
            text=[
                f"Transformer: {row.transformer_id}<br>"
                f"Substation: {row.substation_id}<br>"
                f"Load: {row.load_percent:.1f}%<br>"
                f"Temperature: {row.temperature_c:.1f}°C<br>"
                f"Risk Score: {row.risk_score}<br>"
                f"Status: {row.status}"
                for row in status_df.itertuples()
            ],
            hoverinfo='text',
        ))
    
    scene_config = get_3d_scene_config(is_dark)
    
    fig.update_layout(
        title=dict(
            text='<b>3D Grid Analytics</b><br><span style="font-size:10px;color:{}">Load (%) vs Temperature (°C) vs Risk Score</span>'.format(theme.text_muted),
            font=dict(size=12, color=theme.text, family='Inter, sans-serif'),
            x=0.5,
            y=0.98,
        ),
        paper_bgcolor=theme.chart_paper_bg,
        plot_bgcolor=theme.scene_background,
        margin=dict(l=20, r=20, t=40, b=20),
        height=350,
        scene=scene_config,
    )
    
    st.plotly_chart(fig, key="3d_overview", use_container_width=True, height=350)
    
    # Legend for 3D overview
    legend_html = f"""
    <div style="
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        padding: 6px 0;
        font-size: 10px;
        color: {theme.text};
    ">
        <div style="display: flex; align-items: center; gap: 4px;">
            <span style="width: 8px; height: 8px; background: {theme.success}; border-radius: 50%; display: inline-block;"></span>
            Normal ({len(sampled_df[sampled_df['status']=='Normal'])})
        </div>
        <div style="display: flex; align-items: center; gap: 4px;">
            <span style="width: 8px; height: 8px; background: {theme.warning}; border-radius: 50%; display: inline-block;"></span>
            Warning ({len(sampled_df[sampled_df['status']=='Warning'])})
        </div>
        <div style="display: flex; align-items: center; gap: 4px;">
            <span style="width: 8px; height: 8px; background: {theme.high_risk}; border-radius: 50%; display: inline-block;"></span>
            High Risk ({len(sampled_df[sampled_df['status']=='High Risk'])})
        </div>
        <div style="display: flex; align-items: center; gap: 4px;">
            <span style="width: 8px; height: 8px; background: {theme.critical}; border-radius: 50%; display: inline-block;"></span>
            Critical ({len(sampled_df[sampled_df['status']=='Critical'])})
        </div>
        <span style="color: {theme.text_muted}; margin-left: auto;">
            Showing {len(sampled_df):,} of {len(df):,} records
        </span>
    </div>
    """
    
    st.markdown(legend_html, unsafe_allow_html=True)


def _render_risk_landscape(df: pd.DataFrame, is_dark: bool, theme) -> None:
    """Render 3D Grid Risk Landscape visualization."""
    
    sampled_df = _sample_for_3d(df)
    
    status_colors = {
        "Critical": theme.critical,
        "High Risk": theme.high_risk,
        "Warning": theme.warning,
        "Normal": theme.success,
        "Low": theme.success,
    }
    
    fig = go.Figure()
    
    for status in ["Critical", "High Risk", "Warning", "Normal", "Low"]:
        status_df = sampled_df[sampled_df["status"] == status]
        if len(status_df) == 0:
            continue
        
        fig.add_trace(go.Scatter3d(
            x=status_df["voltage_kv"],
            y=status_df["temperature_c"],
            z=status_df["risk_score"],
            mode='markers',
            marker=dict(
                size=3.5,
                color=status_colors[status],
                opacity=0.85,
                line=dict(width=0.5, color='white'),
            ),
            name=status,
            text=[
                f"<b>{row.transformer_id}</b><br>"
                f"Substation: {row.substation_id}<br>"
                f"Voltage: {row.voltage_kv:.2f} kV<br>"
                f"Temperature: {row.temperature_c:.1f}°C<br>"
                f"Risk Score: {row.risk_score}<br>"
                f"Status: {row.status}"
                for row in status_df.itertuples()
            ],
            hoverinfo='text',
        ))
    
    scene_config = get_3d_scene_config(is_dark)
    
    fig.update_layout(
        title=dict(
            text='<b>3D Grid Risk Landscape</b>',
            font=dict(size=14, color=theme.text, family='Inter, sans-serif'),
            x=0.5,
            y=0.98,
        ),
        paper_bgcolor=theme.chart_paper_bg,
        plot_bgcolor=theme.scene_background,
        margin=dict(l=20, r=20, t=40, b=20),
        height=500,
        scene={
            **scene_config,
            'xaxis': {
                **scene_config['xaxis'],
                'title': 'Voltage (kV)',
            },
            'yaxis': {
                **scene_config['yaxis'],
                'title': 'Temperature (°C)',
            },
            'zaxis': {
                **scene_config['zaxis'],
                'title': 'Risk Score',
            },
        },
    )
    
    _render_3d_chart(fig, len(sampled_df), len(df), theme)


def _render_load_performance(df: pd.DataFrame, is_dark: bool, theme) -> None:
    """Render Load Performance Space visualization."""
    
    sampled_df = _sample_for_3d(df)
    
    status_colors = {
        "Critical": theme.critical,
        "High Risk": theme.high_risk,
        "Warning": theme.warning,
        "Normal": theme.success,
        "Low": theme.success,
    }
    
    fig = go.Figure()
    
    for status in ["Critical", "High Risk", "Warning", "Normal", "Low"]:
        status_df = sampled_df[sampled_df["status"] == status]
        if len(status_df) == 0:
            continue
        
        fig.add_trace(go.Scatter3d(
            x=status_df["load_percent"],
            y=status_df["power_factor"],
            z=status_df["temperature_c"],
            mode='markers',
            marker=dict(
                size=3.5,
                color=status_colors[status],
                opacity=0.85,
                line=dict(width=0.5, color='white'),
            ),
            name=status,
            text=[
                f"<b>{row.transformer_id}</b><br>"
                f"Substation: {row.substation_id}<br>"
                f"Load: {row.load_percent:.1f}%<br>"
                f"Power Factor: {row.power_factor:.3f}<br>"
                f"Temperature: {row.temperature_c:.1f}°C<br>"
                f"Status: {row.status}"
                for row in status_df.itertuples()
            ],
            hoverinfo='text',
        ))
    
    scene_config = get_3d_scene_config(is_dark)
    
    fig.update_layout(
        title=dict(
            text='<b>Load Performance Space</b>',
            font=dict(size=14, color=theme.text, family='Inter, sans-serif'),
            x=0.5,
            y=0.98,
        ),
        paper_bgcolor=theme.chart_paper_bg,
        plot_bgcolor=theme.scene_background,
        margin=dict(l=20, r=20, t=40, b=20),
        height=500,
        scene={
            **scene_config,
            'xaxis': {
                **scene_config['xaxis'],
                'title': 'Load %',
            },
            'yaxis': {
                **scene_config['yaxis'],
                'title': 'Power Factor',
            },
            'zaxis': {
                **scene_config['zaxis'],
                'title': 'Temperature (°C)',
            },
        },
    )
    
    _render_3d_chart(fig, len(sampled_df), len(df), theme)


def _render_energy_consumption(df: pd.DataFrame, is_dark: bool, theme) -> None:
    """Render Energy Consumption Space visualization."""
    
    sampled_df = _sample_for_3d(df)
    
    region_colors = {
        "North": "#3b82f6",
        "South": "#22c55e",
        "East": "#f97316",
        "West": "#f59e0b",
        "Central": "#8b5cf6",
        "North-East": "#6366f1",
    }
    
    fig = go.Figure()
    
    for region in df["region"].unique():
        region_df = sampled_df[sampled_df["region"] == region]
        if len(region_df) == 0:
            continue
        
        fig.add_trace(go.Scatter3d(
            x=region_df["energy_generated_mwh"],
            y=region_df["energy_consumed_mwh"],
            z=region_df["load_percent"],
            mode='markers',
            marker=dict(
                size=3,
                color=region_colors.get(region, theme.primary),
                opacity=0.8,
                line=dict(width=0.5, color='white'),
            ),
            name=region,
            text=[
                f"<b>{row.transformer_id}</b><br>"
                f"Region: {row.region}<br>"
                f"Substation: {row.substation_id}<br>"
                f"Generated: {row.energy_generated_mwh:,.0f} MWh<br>"
                f"Consumed: {row.energy_consumed_mwh:,.0f} MWh<br>"
                f"Load: {row.load_percent:.1f}%"
                for row in region_df.itertuples()
            ],
            hoverinfo='text',
        ))
    
    scene_config = get_3d_scene_config(is_dark)
    
    fig.update_layout(
        title=dict(
            text='<b>Energy Consumption Space</b>',
            font=dict(size=14, color=theme.text, family='Inter, sans-serif'),
            x=0.5,
            y=0.98,
        ),
        paper_bgcolor=theme.chart_paper_bg,
        plot_bgcolor=theme.scene_background,
        margin=dict(l=20, r=20, t=40, b=20),
        height=500,
        scene={
            **scene_config,
            'xaxis': {
                **scene_config['xaxis'],
                'title': 'Energy Generated (MWh)',
            },
            'yaxis': {
                **scene_config['yaxis'],
                'title': 'Energy Consumed (MWh)',
            },
            'zaxis': {
                **scene_config['zaxis'],
                'title': 'Load %',
            },
        },
    )
    
    _render_3d_chart(fig, len(sampled_df), len(df), theme)


def _render_anomaly_detection(df: pd.DataFrame, is_dark: bool, theme) -> None:
    """Render Anomaly Detection Space visualization."""
    
    sampled_df = _sample_for_3d(df)
    
    # Calculate voltage deviation
    sampled_df = sampled_df.copy()
    sampled_df["voltage_deviation"] = abs(sampled_df["voltage_kv"] - 40.0)
    
    severity_colors = {
        "Critical": theme.critical,
        "High Risk": theme.high_risk,
        "Warning": theme.warning,
        "Normal": theme.success,
        "Low": theme.success,
    }
    
    fig = go.Figure()
    
    for status in ["Critical", "High Risk", "Warning", "Normal", "Low"]:
        status_df = sampled_df[sampled_df["status"] == status]
        if len(status_df) == 0:
            continue
        
        fig.add_trace(go.Scatter3d(
            x=status_df["voltage_deviation"],
            y=status_df["temperature_c"],
            z=status_df["anomaly_score"] if "anomaly_score" in status_df.columns else status_df["risk_score"] / 100,
            mode='markers',
            marker=dict(
                size=3.5,
                color=severity_colors[status],
                opacity=0.85,
                line=dict(width=0.5, color='white'),
            ),
            name=status,
            text=[
                f"<b>{row.transformer_id}</b><br>"
                f"Substation: {row.substation_id}<br>"
                f"Voltage Deviation: {row.voltage_deviation:.2f} kV<br>"
                f"Temperature: {row.temperature_c:.1f}°C<br>"
                f"Anomaly Score: {row.anomaly_score if 'anomaly_score' in row._asdict() else row.risk_score/100:.3f}<br>"
                f"Status: {row.status}"
                for row in status_df.itertuples()
            ],
            hoverinfo='text',
        ))
    
    scene_config = get_3d_scene_config(is_dark)
    
    fig.update_layout(
        title=dict(
            text='<b>Anomaly Detection Space</b>',
            font=dict(size=14, color=theme.text, family='Inter, sans-serif'),
            x=0.5,
            y=0.98,
        ),
        paper_bgcolor=theme.chart_paper_bg,
        plot_bgcolor=theme.scene_background,
        margin=dict(l=20, r=20, t=40, b=20),
        height=500,
        scene={
            **scene_config,
            'xaxis': {
                **scene_config['xaxis'],
                'title': 'Voltage Deviation (kV)',
            },
            'yaxis': {
                **scene_config['yaxis'],
                'title': 'Temperature (°C)',
            },
            'zaxis': {
                **scene_config['zaxis'],
                'title': 'Anomaly Score',
            },
        },
    )
    
    _render_3d_chart(fig, len(sampled_df), len(df), theme)


def _render_3d_chart(fig: go.Figure, shown_count: int, total_count: int, theme) -> None:
    """Render 3D chart with controls and info."""
    
    st.plotly_chart(fig, key="3d_chart", use_container_width=True, height=500)
    
    # Camera controls
    control_buttons = [
        ("Front View", {"eye": {"x": 0, "y": -1.5, "z": 0.5}}),
        ("Top View", {"eye": {"x": 0, "y": 0, "z": 1.5}}),
        ("Side View", {"eye": {"x": 1.5, "y": 0, "z": 0.5}}),
        ("Reset View", {"eye": {"x": 1.5, "y": 1.5, "z": 1.2}}),
    ]
    
    cols = st.columns(len(control_buttons))
    for col, (label, camera) in zip(cols, control_buttons):
        with col:
            st.button(
                label,
                key=f"camera_{label.replace(' ', '_')}",
                use_container_width=True,
                help=f"Set camera to {label.lower()}",
            )
    
    # Show count info
    st.markdown(f"""
    <div style="
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        font-size: 11px;
        color: {theme.text_muted};
    ">
        <span>Showing <b>{shown_count:,}</b> of <b>{total_count:,}</b> records</span>
        <span>Use hover for details | Drag to rotate | Scroll to zoom</span>
    </div>
    """, unsafe_allow_html=True)


def _sample_for_3d(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sample dataframe for 3D visualization.
    
    Prioritize critical/high risk records, then sample normal records.
    Target: ~2000-3000 points total.
    """
    # Split by status priority
    critical = df[df["status"] == "Critical"]
    high_risk = df[df["status"] == "High Risk"]
    warning = df[df["status"] == "Warning"]
    normal = df[df["status"].isin(["Normal", "Low"])]
    
    # Take all critical/high risk
    result_parts = [critical, high_risk, warning]
    
    # Sample normal records to fill up
    target_total = min(MAX_3D_POINTS, 2500)
    already_have = sum(len(p) for p in result_parts)
    remaining = target_total - already_have
    
    if remaining > 0 and len(normal) > 0:
        sampled_normal = normal.sample(n=min(remaining, len(normal)), random_state=42)
        result_parts.append(sampled_normal)
    
    result = pd.concat(result_parts, ignore_index=True)
    
    return result

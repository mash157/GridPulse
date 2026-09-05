#!/usr/bin/env python
"""
GridPulse Live Grid Map Component
Geographic visualization of grid infrastructure
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly import subplots
from dashboard.theme import get_theme
from dashboard.filters import apply_filters


def render_grid_map(df: pd.DataFrame, is_dark: bool = False, filters: dict = None) -> None:
    """
    Render Live Grid Map matching reference design.
    
    Shows:
    - Geographic map of India with substation locations
    - Transmission lines between nodes
    - Status indicators (Normal, High Load, Critical)
    - Map summary box (Regions, Substations, Transformers, Active, Faults)
    - Map legend
    - Map controls
    """
    theme = get_theme(is_dark)
    
    if df is None or len(df) == 0:
        st.info("No data available for the selected filters.", icon="🗺️")
        return
    
    # Apply filters
    if filters:
        df = apply_filters(df, filters)
    
    if len(df) == 0:
        st.info("No data available for the selected filters.", icon="🗺️")
        return
    
    # Calculate map summary stats
    regions_count = df["region"].nunique()
    substations_count = df["substation_id"].nunique()
    transformers_count = df["transformer_id"].nunique()
    active_count = len(df)
    faults_count = int(df["fault_indicator"].sum())
    
    # Get substation coordinates
    from dashboard.config import SUBSTATION_COORDS
    
    # Aggregate by substation
    substation_data = []
    for sub_id in df["substation_id"].unique():
        sub_df = df[df["substation_id"] == sub_id]
        
        # Determine status
        max_risk = sub_df["risk_score"].max()
        avg_load = sub_df["load_percent"].mean()
        
        if max_risk >= 85:
            status = "Critical"
        elif max_risk >= 70 or avg_load >= 80:
            status = "High Load"
        else:
            status = "Normal"
        
        # Get coordinates
        coords = SUBSTATION_COORDS.get(sub_id, {"lat": 22.0, "lon": 78.0})
        
        substation_data.append({
            "substation_id": sub_id,
            "region": sub_df["region"].iloc[0],
            "lat": coords["lat"],
            "lon": coords["lon"],
            "avg_load": avg_load,
            "max_risk": max_risk,
            "status": status,
            "fault_count": int(sub_df["fault_indicator"].sum()),
            "transformer_count": sub_df["transformer_id"].nunique(),
        })
    
    substation_df = pd.DataFrame(substation_data)
    
    # Prepare map traces
    # Nodes (substations)
    node_traces = []
    for status in ["Normal", "High Load", "Critical"]:
        status_df = substation_df[substation_df["status"] == status]
        if len(status_df) == 0:
            continue
        
        status_colors = {
            "Normal": theme.success,
            "High Load": theme.high_risk,
            "Critical": theme.critical,
        }
        
        marker_size = 12 if status == "Normal" else (14 if status == "High Load" else 16)
        
        trace = go.Scattergeo(
            lon=status_df["lon"],
            lat=status_df["lat"],
            mode='markers+text',
            marker=dict(
                size=marker_size,
                color=status_colors[status],
                line=dict(width=2, color='white'),
                symbol='circle',
            ),
            text=status_df["substation_id"],
            textposition='top center',
            textfont=dict(size=9, color=theme.text, family='Inter, sans-serif'),
            name=status,
            hoverinfo='text',
            hovertext=[
                f"<b>{row.substation_id}</b><br>"
                f"Region: {row.region}<br>"
                f"Load: {row.avg_load:.1f}%<br>"
                f"Transformers: {row.transformer_count}<br>"
                f"Status: {row.status}"
                for row in status_df.itertuples()
            ],
        )
        node_traces.append(trace)
    
    # Create transmission lines (connections between nearby substations)
    # For visualization, connect substations within same region
    line_traces = []
    regions = substation_df["region"].unique()
    
    for region in regions:
        region_data = substation_df[substation_df["region"] == region].sort_values("lon")
        
        if len(region_data) > 1:
            # Connect consecutive substations
            line_lons = []
            line_lats = []
            
            for i in range(len(region_data) - 1):
                line_lons.extend([region_data.iloc[i]["lon"], region_data.iloc[i+1]["lon"], None])
                line_lats.extend([region_data.iloc[i]["lat"], region_data.iloc[i+1]["lat"], None])
            
            line_trace = go.Scattergeo(
                lon=line_lons,
                lat=line_lats,
                mode='lines',
                line=dict(
                    width=1.5,
                    color=theme.transmission_color,
                    opacity=0.6,
                ),
                name=f"{region} Lines",
                showlegend=False,
                hoverinfo='skip',
            )
            line_traces.append(line_trace)
    
    # Build map layout
    map_layout = dict(
        title=dict(
            text='<b>Live Grid Map</b><br><span style="font-size:11px;color:{}">Real-time power flow and equipment status</span>'.format(theme.text_muted),
            font=dict(size=14, color=theme.text, family='Inter, sans-serif'),
            x=0.5,
            y=0.95,
        ),
        geo=dict(
            scope='asia',
            projection=dict(type='mercator'),
            center=dict(lat=22.0, lon=78.0),
            resolution=50,
            showland=True,
            landcolor=theme.surface_secondary if is_dark else '#f8fafc',
            subunitcolor=theme.border,
            subunitwidth=1,
            showlakes=False,
            showocean=True,
            oceancolor=theme.surface_secondary if is_dark else '#eef2f6',
            bgcolor=theme.surface if is_dark else '#ffffff',
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        paper_bgcolor=theme.surface,
        plot_bgcolor=theme.surface,
        height=450,
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.02,
            bgcolor='rgba(255,255,255,0.9)' if not is_dark else 'rgba(17,28,56,0.9)',
            bordercolor=theme.border,
            borderwidth=1,
            font=dict(size=10, color=theme.text, family='Inter, sans-serif'),
            orientation='h',
        ),
    )
    
    # Combine all traces
    all_traces = node_traces + line_traces
    
    fig = go.Figure(data=all_traces, layout=map_layout)
    
    # Render map
    st.plotly_chart(fig, key="grid_map", use_container_width=True, height=450)
    
    # Map summary box (right side floating - using columns)
    st.markdown(f"""
    <div style="
        display: flex;
        justify-content: flex-end;
        margin-top: -30px;
        margin-bottom: 10px;
    ">
        <div style="
            background: {theme.surface};
            border: 1px solid {theme.border};
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: {theme.shadow};
            min-width: 140px;
        ">
            <div style="
                font-size: 11px;
                font-weight: 700;
                color: {theme.text};
                margin-bottom: 8px;
                border-bottom: 1px solid {theme.border};
                padding-bottom: 6px;
            ">
                Map Summary
            </div>
            <div style="
                font-size: 11px;
                display: grid;
                grid-template-columns: 1fr auto;
                gap: 4px 12px;
            ">
                <span style="color: {theme.text_muted};">Regions</span>
                <span style="font-weight: 600; color: {theme.text};">{regions_count}</span>
                
                <span style="color: {theme.text_muted};">Substations</span>
                <span style="font-weight: 600; color: {theme.text};">{substations_count}</span>
                
                <span style="color: {theme.text_muted};">Transformers</span>
                <span style="font-weight: 600; color: {theme.text};">{transformers_count}</span>
                
                <span style="color: {theme.text_muted};">Active</span>
                <span style="font-weight: 600; color: {theme.success};">{active_count}</span>
                
                <span style="color: {theme.text_muted};">Faults</span>
                <span style="font-weight: 600; color: {theme.critical};">{faults_count}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Map Legend
    legend_html = f"""
    <div style="
        display: flex;
        gap: 16px;
        padding: 8px 0;
        font-size: 11px;
        color: {theme.text};
    ">
        <div style="display: flex; align-items: center; gap: 4px;">
            <span style="
                width: 10px;
                height: 10px;
                background: {theme.success};
                border-radius: 50%;
                display: inline-block;
            "></span>
            <span>Normal</span>
        </div>
        <div style="display: flex; align-items: center; gap: 4px;">
            <span style="
                width: 10px;
                height: 10px;
                background: {theme.high_risk};
                border-radius: 50%;
                display: inline-block;
            "></span>
            <span>High Load</span>
        </div>
        <div style="display: flex; align-items: center; gap: 4px;">
            <span style="
                width: 10px;
                height: 10px;
                background: {theme.critical};
                border-radius: 50%;
                display: inline-block;
            "></span>
            <span>Critical</span>
        </div>
        <div style="display: flex; align-items: center; gap: 4px;">
            <span style="
                width: 20px;
                height: 2px;
                background: {theme.transmission_color};
                display: inline-block;
                border-radius: 1px;
            "></span>
            <span>Transmission Line</span>
        </div>
    </div>
    """
    
    st.markdown(legend_html, unsafe_allow_html=True)
    
    # Map controls (zoom in/out, reset)
    st.markdown(f"""
    <div style="
        display: flex;
        justify-content: flex-end;
        gap: 4px;
        margin-top: 8px;
    ">
        {[f'''
        <button onclick="window.location.reload()" style="
            padding: 6px 10px;
            background: {theme.surface};
            border: 1px solid {theme.border};
            border-radius: 4px;
            color: {theme.text};
            font-size: 12px;
            cursor: pointer;
        ">
            🔄 Reset
        </button>
        ''' for _ in range(1)]}
    </div>
    """, unsafe_allow_html=True)

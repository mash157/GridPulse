#!/usr/bin/env python
"""
GridPulse Charts Component
Various chart visualizations for the dashboard
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dashboard.theme import get_theme
from dashboard.filters import apply_filters


def render_grid_health_donut(df: pd.DataFrame, is_dark: bool = False, 
                              filters: dict = None, region_filter: str = "All Regions") -> None:
    """
    Render Grid Health Distribution donut chart matching reference design.
    
    Shows:
    - Donut chart with center text (Total Transformers)
    - Segments: Normal, Warning, High Risk, Critical
    - Legend with counts and percentages
    """
    theme = get_theme(is_dark)
    
    if df is None or len(df) == 0:
        st.info("No data available for the selected filters.", icon="📊")
        return
    
    # Apply filters
    if filters:
        df = apply_filters(df, filters)
    
    if len(df) == 0:
        st.info("No data available for the selected filters.", icon="📊")
        return
    
    # Get unique transformers and their worst status
    transformer_status = df.groupby("transformer_id")["status"].agg(
        lambda x: _get_worst_status(x)
    ).reset_index()
    
    # Count by status
    status_counts = transformer_status["status"].value_counts()
    
    status_order = ["Normal", "Warning", "High Risk", "Critical"]
    values = [status_counts.get(s, 0) for s in status_order]
    total_transformers = sum(values)
    
    # Create donut chart
    colors = [
        theme.success,
        theme.warning,
        theme.high_risk,
        theme.critical,
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Pie(
        labels=status_order,
        values=values,
        hole=0.65,
        marker_colors=colors,
        marker_line=dict(color='white', width=2),
        textinfo='none',
        hoverinfo='label+value+percent',
        hovertemplate='%{label}<br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
        name='Health Distribution',
    ))
    
    # Add center text
    fig.add_annotation(
        x=0.5,
        y=0.5,
        text=f"{total_transformers:,}",
        font=dict(size=32, color=theme.text, weight='bold', family='Inter, sans-serif'),
        showarrow=False,
    )
    
    fig.add_annotation(
        x=0.5,
        y=0.42,
        text="Total",
        font=dict(size=12, color=theme.text_muted, family='Inter, sans-serif'),
        showarrow=False,
    )
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f'<b>Grid Health Distribution</b>',
            font=dict(size=14, color=theme.text, family='Inter, sans-serif'),
            x=0.5,
            y=0.95,
        ),
        paper_bgcolor=theme.surface,
        plot_bgcolor=theme.chart_background,
        margin=dict(l=40, r=40, t=50, b=40),
        showlegend=True,
        legend=dict(
            x=1.15,
            y=0.5,
            bgcolor='rgba(255,255,255,0.9)' if not is_dark else 'rgba(17,28,56,0.9)',
            bordercolor=theme.border,
            borderwidth=1,
            font=dict(size=11, color=theme.text, family='Inter, sans-serif'),
            orientation='v',
        ),
        height=320,
    )
    
    st.plotly_chart(fig, key="health_donut", use_container_width=True, height=320)
    
    # Legend (manual for better styling)
    legend_html = f"""
    <div style="
        display: flex;
        flex-direction: column;
        gap: 6px;
        font-size: 11px;
        color: {theme.text};
        margin-top: 8px;
    ">
        {[f'''
        <div style="
            display: flex;
            align-items: center;
            gap: 6px;
        ">
            <span style="
                width: 10px;
                height: 10px;
                background: {colors[i]};
                border-radius: 50%;
                display: inline-block;
                border: 1px solid white;
            "></span>
            <span style="font-weight: 500;">{status_order[i]}</span>
            <span style="color: {theme.text_muted};">{values[i]:,} ({values[i]/total_transformers*100:.0f}%)</span>
        </div>
        ''' for i in range(len(status_order)) if values[i] > 0]}
    </div>
    """
    
    st.markdown(legend_html, unsafe_allow_html=True)


def render_energy_by_region(df: pd.DataFrame, is_dark: bool = False,
                            filters: dict = None, time_range: str = "Last 24 Hours") -> None:
    """
    Render Energy by Region bar chart matching reference design.
    
    Shows:
    - Vertical bar chart
    - Y-axis: Power (MW)
    - X-axis: Regions (North, South, East, West, Central, North-East)
    - Time range filter
    """
    theme = get_theme(is_dark)
    
    if df is None or len(df) == 0:
        st.info("No data available for the selected filters.", icon="📊")
        return
    
    # Apply filters
    if filters:
        df = apply_filters(df, filters)
    
    if len(df) == 0:
        st.info("No data available for the selected filters.", icon="📊")
        return
    
    # Aggregate by region
    region_energy = df.groupby("region").agg(
        total_power_mw=("power_mw", "sum"),
        avg_load=("load_percent", "mean"),
        total_generation=("energy_generated_mwh", "sum"),
        total_consumption=("energy_consumed_mwh", "sum"),
    ).reset_index()
    
    # Sort by total power descending
    region_energy = region_energy.sort_values("total_power_mw", ascending=False)
    
    # Region colors (matching reference)
    region_colors_map = {
        "North": "#3b82f6",      # Blue
        "South": "#22c55e",      # Green  
        "East": "#f97316",       # Orange
        "West": "#f59e0b",       # Yellow-orange
        "Central": "#8b5cf6",    # Purple
        "North-East": "#6366f1", # Indigo
    }
    
    colors = [region_colors_map.get(r, theme.primary) for r in region_energy["region"]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=region_energy["region"],
        y=region_energy["total_power_mw"],
        marker_color=colors,
        marker_line=dict(color='white', width=1),
        marker_line_width=1,
        text=[f"{v:,.0f} MW" for v in region_energy["total_power_mw"]],
        textposition='outside',
        textfont=dict(size=10, color=theme.text, family='Inter, sans-serif'),
        name='Total Power (MW)',
        hovertemplate='<b>%{x}</b><br>Power: %{y:,.0f} MW<br>Load: %{customdata:.1f}%<extra></extra>',
        customdata=region_energy["avg_load"],
    ))
    
    fig.update_layout(
        title=dict(
            text=f'<b>Energy by Region</b><br><span style="font-size:11px;color:{theme.text_muted}">{time_range}</span>',
            font=dict(size=14, color=theme.text, family='Inter, sans-serif'),
            x=0.5,
            y=0.95,
        ),
        paper_bgcolor=theme.surface,
        plot_bgcolor=theme.chart_background,
        margin=dict(l=50, r=20, t=50, b=50),
        xaxis=dict(
            title='Region',
            title_font=dict(size=12, color=theme.text, family='Inter, sans-serif'),
            tickfont=dict(size=11, color=theme.text, family='Inter, sans-serif'),
            gridcolor=theme.chart_grid,
            zerolinecolor=theme.chart_axis_line,
            showline=True,
            linecolor=theme.chart_axis_line,
        ),
        yaxis=dict(
            title='Power (MW)',
            title_font=dict(size=12, color=theme.text, family='Inter, sans-serif'),
            tickfont=dict(size=11, color=theme.text, family='Inter, sans-serif'),
            gridcolor=theme.chart_grid,
            zerolinecolor=theme.chart_axis_line,
            showline=True,
            linecolor=theme.chart_axis_line,
            rangemode='tozero',
        ),
        height=320,
    )
    
    st.plotly_chart(fig, key="energy_by_region", use_container_width=True, height=320)


def render_top_anomaly_types(df: pd.DataFrame, is_dark: bool = False,
                             filters: dict = None) -> None:
    """
    Render Top Anomaly Types horizontal bar chart matching reference design.
    
    Shows:
    - Horizontal bar chart
    - Anomaly types ranked by count
    - Color-coded bars
    """
    theme = get_theme(is_dark)
    
    if df is None or len(df) == 0:
        st.info("No data available for the selected filters.", icon="⚠️")
        return
    
    # Apply filters
    if filters:
        df = apply_filters(df, filters)
    
    if len(df) == 0:
        st.info("No data available for the selected filters.", icon="⚠️")
        return
    
    # Filter to non-normal records
    anomaly_df = df[df["status"] != "Normal"]
    
    if len(anomaly_df) == 0:
        st.info("No anomalies detected.", icon="✅")
        return
    
    # Count by anomaly type
    anomaly_counts = anomaly_df["anomaly_type"].value_counts().head(8)
    
    # Anomaly type colors (matching reference)
    anomaly_colors_map = {
        "Voltage Fluctuation": theme.critical,
        "Overload": "#f97316",
        "Temperature Spike": theme.high_risk,
        "Frequency Deviation": theme.primary,
        "Power Factor Anomaly": "#8b5cf6",
        "Transformer Fault": theme.critical,
        "Communication Failure": "#64748b",
        "Unexpected Consumption": theme.warning,
        "Generation Drop": "#06b6d4",
        "Compound Anomaly": "#ec4899",
    }
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=anomaly_counts.index.tolist(),
        x=anomaly_counts.values,
        orientation='h',
        marker_color=[anomaly_colors_map.get(t, theme.primary) for t in anomaly_counts.index],
        marker_line=dict(color='white', width=1),
        text=[f"{v:,}" for v in anomaly_counts.values],
        textposition='outside',
        textfont=dict(size=11, color=theme.text, family='Inter, sans-serif'),
        name='Anomaly Count',
        hovertemplate='<b>%{y}</b><br>Count: %{x:,}<extra></extra>',
    ))
    
    fig.update_layout(
        title=dict(
            text='<b>Top Anomaly Types</b>',
            font=dict(size=14, color=theme.text, family='Inter, sans-serif'),
            x=0.5,
            y=0.95,
        ),
        paper_bgcolor=theme.surface,
        plot_bgcolor=theme.chart_background,
        margin=dict(l=120, r=20, t=50, b=20),
        xaxis=dict(
            title='Count',
            title_font=dict(size=12, color=theme.text, family='Inter, sans-serif'),
            tickfont=dict(size=11, color=theme.text, family='Inter, sans-serif'),
            gridcolor=theme.chart_grid,
            zerolinecolor=theme.chart_axis_line,
            showline=True,
            linecolor=theme.chart_axis_line,
            rangemode='tozero',
        ),
        yaxis=dict(
            title='',
            tickfont=dict(size=11, color=theme.text, family='Inter, sans-serif'),
            gridcolor='rgba(0,0,0,0)',
            zeroline=False,
        ),
        height=280,
    )
    
    st.plotly_chart(fig, key="anomaly_types", use_container_width=True, height=280)


def render_power_gen_consumption(df: pd.DataFrame, is_dark: bool = False,
                                 filters: dict = None, time_range: str = "Last 24 Hours") -> None:
    """
    Render Power Generation vs Consumption time series chart.
    
    Shows:
    - Two lines: Generation (green) and Consumption (blue)
    - Time on X-axis
    - Power/Energy on Y-axis
    """
    theme = get_theme(is_dark)
    
    if df is None or len(df) == 0:
        st.info("No data available for the selected filters.", icon="📈")
        return
    
    # Apply filters
    if filters:
        df = apply_filters(df, filters)
    
    if len(df) == 0:
        st.info("No data available for the selected filters.", icon="📈")
        return
    
    # Convert timestamp
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # Aggregate by hour
    hourly = df.copy()
    hourly["hour"] = hourly["timestamp"].dt.floor("h")
    
    hourly_agg = hourly.groupby("hour").agg(
        total_generation=("energy_generated_mwh", "sum"),
        total_consumption=("energy_consumed_mwh", "sum"),
        avg_power=("power_mw", "mean"),
    ).reset_index().sort_values("hour")
    
    if len(hourly_agg) == 0:
        st.info("No data for the selected time range.", icon="📈")
        return
    
    # Create area/line chart
    fig = go.Figure()
    
    # Generation area
    fig.add_trace(go.Scatter(
        x=hourly_agg["hour"],
        y=hourly_agg["total_generation"],
        mode='lines+markers',
        name='Generation',
        line=dict(color=theme.generation_color, width=2),
        fill='tozeroy',
        fillcolor=f"rgba(34, 197, 94, 0.2)",
        marker=dict(size=4, color=theme.generation_color),
        hovertemplate='<b>Generation</b><br>Time: %{x|%H:%M}<br>Power: %{y:,.0f} MWh<extra></extra>',
    ))
    
    # Consumption line
    fig.add_trace(go.Scatter(
        x=hourly_agg["hour"],
        y=hourly_agg["total_consumption"],
        mode='lines+markers',
        name='Consumption',
        line=dict(color=theme.consumption_color, width=2),
        fill='tozeroy',
        fillcolor=f"rgba(59, 130, 246, 0.2)",
        marker=dict(size=4, color=theme.consumption_color),
        hovertemplate='<b>Consumption</b><br>Time: %{x|%H:%M}<br>Power: %{y:,.0f} MWh<extra></extra>',
    ))
    
    fig.update_layout(
        title=dict(
            text=f'<b>Power Generation vs Consumption</b><br><span style="font-size:11px;color:{theme.text_muted}">{time_range}</span>',
            font=dict(size=14, color=theme.text, family='Inter, sans-serif'),
            x=0.5,
            y=0.95,
        ),
        paper_bgcolor=theme.surface,
        plot_bgcolor=theme.chart_background,
        margin=dict(l=50, r=20, t=50, b=40),
        xaxis=dict(
            title='Time',
            title_font=dict(size=12, color=theme.text, family='Inter, sans-serif'),
            tickfont=dict(size=10, color=theme.text, family='Inter, sans-serif'),
            gridcolor=theme.chart_grid,
            zerolinecolor=theme.chart_axis_line,
            showline=True,
            linecolor=theme.chart_axis_line,
            tickformat='%H:%M',
        ),
        yaxis=dict(
            title='Power (MW)',
            title_font=dict(size=12, color=theme.text, family='Inter, sans-serif'),
            tickfont=dict(size=11, color=theme.text, family='Inter, sans-serif'),
            gridcolor=theme.chart_grid,
            zerolinecolor=theme.chart_axis_line,
            showline=True,
            linecolor=theme.chart_axis_line,
            rangemode='tozero',
        ),
        legend=dict(
            x=0.5,
            y=1.02,
            xanchor='center',
            yanchor='bottom',
            bgcolor='rgba(255,255,255,0.9)' if not is_dark else 'rgba(17,28,56,0.9)',
            bordercolor=theme.border,
            borderwidth=1,
            font=dict(size=11, color=theme.text, family='Inter, sans-serif'),
            orientation='h',
        ),
        height=320,
    )
    
    st.plotly_chart(fig, key="gen_consumption", use_container_width=True, height=320)


def _get_worst_status(statuses: pd.Series) -> str:
    """Get worst status from a series of statuses."""
    priority = {"Critical": 4, "High Risk": 3, "Warning": 2, "Low": 1, "Normal": 0}
    
    worst = "Normal"
    worst_priority = -1
    
    for status in statuses:
        p = priority.get(status, 0)
        if p > worst_priority:
            worst_priority = p
            worst = status
    
    return worst

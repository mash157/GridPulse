#!/usr/bin/env python
"""
GridPulse KPI Cards Component
Six metric cards matching reference design
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dashboard.theme import get_theme
from dashboard.filters import apply_filters


def render_kpi_cards(df: pd.DataFrame, is_dark: bool = False, filters: dict = None) -> None:
    """
    Render 6 KPI metric cards matching reference design.
    
    Cards:
    1. Total Generation (MW) - green lightning icon
    2. Total Consumption (MW) - blue pulse icon
    3. Grid Load (%) - orange gauge icon
    4. Active Transformers - blue transformer icon
    5. Faults Detected - red warning icon
    6. Anomalies - purple shield icon
    
    Each card with trend line and percentage vs last 24h.
    """
    theme = get_theme(is_dark)
    
    if df is None or len(df) == 0:
        _render_empty_kpis(theme)
        return
    
    # Apply filters if provided
    if filters:
        df = apply_filters(df, filters)
    
    if len(df) == 0:
        _render_empty_kpis(theme)
        return
    
    # Calculate metrics
    metrics = _calculate_kpi_metrics(df)
    
    # Create 6 columns for KPI cards
    cols = st.columns(6)
    
    # Card configurations in order
    card_configs = [
        {
            "title": "Total Generation",
            "value": f"{metrics['total_generation_mw']:,.0f} MW",
            "icon": "⚡",
            "icon_bg": theme.success_light,
            "icon_color": theme.success,
            "trend_text": metrics['generation_trend'],
            "trend_color": _get_trend_color(metrics['generation_trend'], theme),
            "spark_data": metrics['generation_spark'],
            "spark_color": theme.success,
        },
        {
            "title": "Total Consumption",
            "value": f"{metrics['total_consumption_mw']:,.0f} MW",
            "icon": "💓",
            "icon_bg": theme.primary_light,
            "icon_color": theme.primary,
            "trend_text": metrics['consumption_trend'],
            "trend_color": _get_trend_color(metrics['consumption_trend'], theme),
            "spark_data": metrics['consumption_spark'],
            "spark_color": theme.consumption_color,
        },
        {
            "title": "Grid Load",
            "value": f"{metrics['avg_load_percent']:.1f}%",
            "icon": "📊",
            "icon_bg": "#fef3c7",
            "icon_color": "#f59e0b",
            "trend_text": metrics['load_trend'],
            "trend_color": _get_trend_color(metrics['load_trend'], theme),
            "spark_data": metrics['load_spark'],
            "spark_color": "#f59e0b",
        },
        {
            "title": "Active Transformers",
            "value": f"{metrics['active_transformers']:,} / {metrics['total_transformers']:,}",
            "icon": "🔌",
            "icon_bg": theme.primary_light,
            "icon_color": theme.primary,
            "trend_text": metrics['transformers_trend'],
            "trend_color": _get_trend_color(metrics['transformers_trend'], theme),
            "spark_data": metrics['transformers_spark'],
            "spark_color": theme.primary,
        },
        {
            "title": "Faults Detected",
            "value": f"{metrics['total_faults']}",
            "icon": "⚠️",
            "icon_bg": theme.critical_light,
            "icon_color": theme.critical,
            "trend_text": metrics['faults_trend'],
            "trend_color": _get_trend_color(metrics['faults_trend'], theme),
            "spark_data": metrics['faults_spark'],
            "spark_color": theme.critical,
        },
        {
            "title": "Anomalies",
            "value": f"{metrics['anomaly_count']}",
            "icon": "🛡️",
            "icon_bg": "#f3e8ff",
            "icon_color": "#8b5cf6",
            "trend_text": metrics['anomalies_trend'],
            "trend_color": _get_trend_color(metrics['anomalies_trend'], theme),
            "spark_data": metrics['anomalies_spark'],
            "spark_color": "#8b5cf6",
        },
    ]
    
    # Render each card
    for idx, (col, config) in enumerate(zip(cols, card_configs)):
        with col:
            _render_single_kpi_card(config, theme, idx)
    
    # Add sparkline legend
    st.markdown(f"""
    <div style="
        display: flex;
        justify-content: center;
        gap: 24px;
        padding: 8px 0;
        font-size: 10px;
        color: {theme.text_muted};
    ">
        <span>↑ Green = Generation trend</span>
        <span>↑ Blue = Consumption trend</span>
    </div>
    """, unsafe_allow_html=True)


def _render_single_kpi_card(config: dict, theme, idx: int) -> None:
    """Render a single KPI card matching reference design."""
    
    card_html = f"""
    <div style="
        background: {theme.kpi_background};
        border: 1px solid {theme.kpi_border};
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 8px;
        box-shadow: {theme.shadow};
        transition: all 0.2s;
    ">
        <div style="
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 8px;
        ">
            <div style="
                width: 36px;
                height: 36px;
                background: {config['icon_bg']};
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
            ">
                <span style="color: {config['icon_color']};">{config['icon']}</span>
            </div>
            <div style="
                font-size: 10px;
                font-weight: 600;
                color: {config['trend_color']};
                text-align: right;
            ">
                {config['trend_text']}
            </div>
        </div>
        
        <div style="
            font-size: 22px;
            font-weight: 700;
            color: {theme.text};
            line-height: 1.2;
            margin-bottom: 2px;
        ">
            {config['value']}
        </div>
        
        <div style="
            font-size: 11px;
            color: {theme.text_muted};
            font-weight: 500;
        ">
            {config['title']}
        </div>
        
        <div style="
            height: 30px;
            margin-top: 8px;
            position: relative;
        ">
            <div id="sparkline_{idx}" style="width: 100%; height: 100%;"></div>
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Render sparkline after card
    if config['spark_data'] and len(config['spark_data']) > 1:
        _render_sparkline(
            config['spark_data'],
            config['spark_color'],
            idx,
            theme
        )


def _render_sparkline(data: list, color: str, idx: int, theme) -> None:
    """Render a small sparkline chart."""
    if len(data) < 2:
        return
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(data))),
        y=data,
        mode='lines',
        line=dict(color=color, width=2),
        fillcolor=color,
        fill='tozeroy',
        opacity=0.3,
        showlegend=False,
        hoverinfo='skip',
    ))
    
    fig.update_layout(
        xaxis=dict(visible=False, showticklabels=False, showgrid=False),
        yaxis=dict(visible=False, showticklabels=False, showgrid=False, rangemode='tozero'),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=30,
        width=120,
    )
    
    st.plotly_chart(fig, key=f"spark_{idx}", use_container_width=True, height=30)


def _render_empty_kpis(theme) -> None:
    """Render empty state for KPI cards."""
    for _ in range(6):
        st.info("No data available", icon="📊")


def _calculate_kpi_metrics(df: pd.DataFrame) -> dict:
    """Calculate all KPI metrics from dataframe."""
    import numpy as np
    
    # Convert timestamp
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    latest_time = df["timestamp"].max()
    last_24h = latest_time - pd.Timedelta(hours=24)
    last_48h = latest_time - pd.Timedelta(hours=48)
    
    # Current period (last 24h)
    current_df = df[df["timestamp"] >= last_24h]
    
    # Previous period (24-48h ago)
    previous_df = df[(df["timestamp"] >= last_48h) & (df["timestamp"] < last_24h)]
    
    # Total Generation (MW)
    total_generation = current_df["energy_generated_mwh"].sum()
    prev_generation = previous_df["energy_generated_mwh"].sum() if len(previous_df) > 0 else 0
    gen_trend_pct = ((total_generation - prev_generation) / (prev_generation + 1)) * 100 if prev_generation > 0 else 0
    gen_trend = f"↑ {gen_trend_pct:.1f}% vs last 24h" if gen_trend_pct > 0 else f"↓ {abs(gen_trend_pct):.1f}% vs last 24h"
    
    # Total Consumption (MWh)
    total_consumption = current_df["energy_consumed_mwh"].sum()
    prev_consumption = previous_df["energy_consumed_mwh"].sum() if len(previous_df) > 0 else 0
    cons_trend_pct = ((total_consumption - prev_consumption) / (prev_consumption + 1)) * 100 if prev_consumption > 0 else 0
    cons_trend = f"↑ {cons_trend_pct:.1f}% vs last 24h" if cons_trend_pct > 0 else f"↓ {abs(cons_trend_pct):.1f}% vs last 24h"
    
    # Grid Load
    avg_load = current_df["load_percent"].mean()
    prev_load = previous_df["load_percent"].mean() if len(previous_df) > 0 else 0
    load_diff = avg_load - prev_load
    load_trend = f"↑ {load_diff:.1f}% vs last 24h" if load_diff > 0 else f"↓ {abs(load_diff):.1f}% vs last 24h"
    
    # Transformers
    total_transformers = df["transformer_id"].nunique()
    active_transformers = current_df["transformer_id"].nunique() if len(current_df) > 0 else total_transformers
    prev_transformers = previous_df["transformer_id"].nunique() if len(previous_df) > 0 else 0
    tran_trend_pct = ((active_transformers - prev_transformers) / (prev_transformers + 1)) * 100 if prev_transformers > 0 else 0
    tran_trend = f"↑ {tran_trend_pct:.1f}% vs last 24h" if tran_trend_pct > 0 else f"↓ {abs(tran_trend_pct):.1f}% vs last 24h"
    
    # Faults
    total_faults = int(current_df["fault_indicator"].sum())
    prev_faults = int(previous_df["fault_indicator"].sum()) if len(previous_df) > 0 else 0
    faults_diff_pct = ((total_faults - prev_faults) / (prev_faults + 1)) * 100 if prev_faults > 0 else 0
    faults_trend = f"↑ {faults_diff_pct:.0f}% vs last 24h" if faults_diff_pct > 0 else f"↓ {abs(faults_diff_pct):.0f}% vs last 24h"
    
    # Anomalies
    anomaly_count = int((current_df["status"] != "Normal").sum())
    prev_anomalies = int((previous_df["status"] != "Normal").sum()) if len(previous_df) > 0 else 0
    anom_diff_pct = ((anomaly_count - prev_anomalies) / (prev_anomalies + 1)) * 100 if prev_anomalies > 0 else 0
    anom_trend = f"↑ {anom_diff_pct:.0f}% vs last 24h" if anom_diff_pct > 0 else f"↓ {abs(anom_diff_pct):.0f}% vs last 24h"
    
    # Sparkline data (hourly aggregation)
    hourly = current_df.copy()
    hourly["hour"] = hourly["timestamp"].dt.floor("h")
    hourly_agg = hourly.groupby("hour").agg(
        generation=("energy_generated_mwh", "sum"),
        consumption=("energy_consumed_mwh", "sum"),
        load=("load_percent", "mean"),
        faults=("fault_indicator", "sum"),
        anomalies=("status", lambda x: (x != "Normal").sum()),
        transformer_count=("transformer_id", "nunique"),
    ).reset_index()
    
    # Normalize for sparklines
    gen_spark = hourly_agg["generation"].tolist() if len(hourly_agg) > 0 else [0]
    cons_spark = hourly_agg["consumption"].tolist() if len(hourly_agg) > 0 else [0]
    load_spark = (hourly_agg["load"] / 100).tolist() if len(hourly_agg) > 0 else [0]
    faults_spark = (hourly_agg["faults"] / (hourly_agg["faults"].max() + 1)).tolist() if len(hourly_agg) > 0 and hourly_agg["faults"].max() > 0 else [0]
    anom_spark = (hourly_agg["anomalies"] / (hourly_agg["anomalies"].max() + 1)).tolist() if len(hourly_agg) > 0 and hourly_agg["anomalies"].max() > 0 else [0]
    tran_spark = (hourly_agg["transformer_count"] / total_transformers).tolist() if len(hourly_agg) > 0 and total_transformers > 0 else [0]
    
    return {
        "total_generation_mw": total_generation,
        "total_consumption_mwh": total_consumption,
        "avg_load_percent": avg_load,
        "total_transformers": total_transformers,
        "active_transformers": active_transformers,
        "total_faults": total_faults,
        "anomaly_count": anomaly_count,
        "generation_trend": gen_trend,
        "consumption_trend": cons_trend,
        "load_trend": load_trend,
        "transformers_trend": tran_trend,
        "faults_trend": faults_trend,
        "anomalies_trend": anom_trend,
        "generation_spark": gen_spark,
        "consumption_spark": cons_spark,
        "load_spark": load_spark,
        "faults_spark": faults_spark,
        "anomalies_spark": anom_spark,
        "transformers_spark": tran_spark,
    }


def _get_trend_color(trend_text: str, theme) -> str:
    """Get color based on trend direction."""
    if trend_text.startswith("↑"):
        return theme.success
    elif trend_text.startswith("↓"):
        return theme.critical
    return theme.text_muted

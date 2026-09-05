#!/usr/bin/env python
"""
GridPulse Sidebar Component
Left navigation and filter panel matching reference design
"""

import streamlit as st
from datetime import datetime
from dashboard.theme import get_theme
from dashboard.config import REGIONS, SUBSTATION_COORDS, TIME_RANGE_OPTIONS
from dashboard.filters import clear_filters
from dashboard.data_loader import get_stream_status


def render_sidebar(
    is_dark: bool = False,
    current_page: str = "Overview",
    df=None,
    current_filters: dict = None
):
    """
    Render the left sidebar matching reference design.
    
    Reference layout:
    - Navigation buttons (red active state)
    - Available Filters section with dropdowns
    - Clear Filters button (red)
    - System Status panel at bottom
    """
    theme = get_theme(is_dark)
    
    # Build filter options from data
    if df is not None and len(df) > 0:
        filter_options = _get_filter_options_from_df(df, current_filters or {})
    else:
        filter_options = _get_default_filter_options()
    
    # Sidebar content
    with st.sidebar:
        # Set sidebar width via CSS
        st.markdown(f"""
        <style>
        section[data-testid="stSidebar"] {{
            width: 240px !important;
            background: #fcfcfc;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # Navigation buttons
        _render_navigation_ref(current_page, theme)
        
        st.markdown(f"<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        # Available Filters section
        _render_available_filters(
            filter_options, 
            current_filters or {}, 
            theme
        )
        
        # Clear Filters button
        _render_clear_filters_button(theme)
        
        st.markdown(f"<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        # System Status panel
        _render_system_status_panel(df, theme)


def _render_navigation_ref(current_page: str, theme) -> None:
    """Render navigation links with red active state matching reference."""
    
    nav_items = [
        ("Overview", False),
        ("Grid Monitoring", False),
        ("Transformers", False),
        ("3D Analytics", False),
        ("Anomalies", False),
        ("Forecasting", False),
        ("Reports", False),
    ]
    
    nav_icon_map = {
        'Overview': '📁',
        'Grid Monitoring': '🗺️',
        'Transformers': '⚡',
        '3D Analytics': '🧊',
        'Anomalies': '⚠️',
        'Forecasting': '📈',
        'Reports': '📋',
    }
    
    for label, has_badge in nav_items:
        is_active = current_page == label
        icon = nav_icon_map[label]
        
        # Active state uses red background (matching reference image)
        if is_active:
            bg_color = "#ef4444"  # Red for active
            text_color = "#ffffff"
            icon_color = "#ffffff"
            border_radius = "4px"
        else:
            bg_color = "#ffffff"
            text_color = "#64748b"
            icon_color = "#64748b"
            border_radius = "4px"
        
        # Navigation button HTML
        nav_html = f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 14px;
            margin: 3px 0;
            background: {bg_color};
            border-radius: {border_radius};
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid #efefef;
        ">
            <span style="font-size: 16px; color: {icon_color};">
                {icon}
            </span>
            </span>
            <span style="
                font-size: 13px;
                font-weight: 500;
                color: {text_color};
            ">{label}</span>
        </div>
        """
        
        st.markdown(nav_html, unsafe_allow_html=True)


def _render_available_filters(options: dict, current_filters: dict, theme) -> None:
    """Render Available Filters section with dropdown selectors."""
    
    # Section header
    st.markdown(f"""
    <div style="
        font-size: 11px;
        font-weight: 700;
        color: #64748b;
        padding: 8px 12px 6px;
        border-bottom: 1px solid #efefef;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    ">
        Available Filters
    </div>
    """, unsafe_allow_html=True)
    
    # Four stacked dropdown selectors
    filter_config = [
        ("region", "Region", options.get("region", ["All"] + REGIONS), current_filters.get("region", "All")),
        ("substation_id", "Substation", options.get("substation_id", ["All"]), current_filters.get("substation_id", "All")),
        ("transformer_id", "Transformer", options.get("transformer_id", ["All"]), current_filters.get("transformer_id", "All")),
        ("time_range", "Time Range", options.get("time_range", []), current_filters.get("time_range", "Last 24 Hours")),
    ]
    
    for field_key, label, opts, current_val in filter_config:
        selected_idx = opts.index(current_val) if current_val in opts else 0
        
        # Render styled dropdown
        st.markdown(f"""
        <div style="
            margin-bottom: 6px;
        ">
            <label style="
                display: block;
                font-size: 11px;
                color: #64748b;
                margin-bottom: 4px;
                font-weight: 500;
            ">
                {label}
            </label>
            <select style="
                width: 100%;
                padding: 8px 12px;
                padding-right: 32px;
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                font-size: 13px;
                color: #0f172a;
                outline: none;
                cursor: pointer;
                appearance: none;
                background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12"><path fill="%2364748b" d="M6 8L1 3h10z"/></svg>');
                background-repeat: no-repeat;
                background-position: right 10px center;
            ">
                {''.join(f'<option value="{opt}" {"selected" if opt == current_val else ""}>{opt}</option>' for opt in opts)}
            </select>
        </div>
        """, unsafe_allow_html=True)


def _render_clear_filters_button(theme) -> None:
    """Render Clear Filters button matching reference (red button)."""
    st.markdown(f"""
    <div style="
        margin-top: 12px;
        padding: 8px 12px;
        background: #ffffff;
        border: 1px solid #efefef;
        border-radius: 4px;
    ">
        <button style="
            width: 100%;
            padding: 9px 16px;
            background: #ef4444;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        "
            onmouseover="this.style.background='#dc2626'"
            onmouseout="this.style.background='#ef4444'"
        >
            Clear Filters
        </button>
    </div>
    """, unsafe_allow_html=True)


def _render_system_status_panel(df, theme) -> None:
    """Render System Status panel at bottom of sidebar."""

    stream_status = get_stream_status()
    stream_online = stream_status.get("online", False)
    stream_label = stream_status.get("status_text", "STREAM OFFLINE")
    stream_events = stream_status.get("events_generated")
    stream_anomalies = stream_status.get("anomalies_detected")

    if df is not None and len(df) > 0:
        total_records = len(df)
        total_transformers = df["transformer_id"].nunique()

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        latest_time = df["timestamp"].max()

        system_status = "All Systems Operational"
        status_color = "#22c55e"
        pipeline_status = "Running"
        pipeline_time = datetime.now().strftime("%H:%M:%S")
        records_display = f"{total_records:,}"
    else:
        system_status = "No Data Available"
        status_color = "#f59e0b"
        pipeline_status = "Idle"
        pipeline_time = "-"
        records_display = "0"

    # Stream status color
    stream_color = "#22c55e" if stream_online else "#ef4444"
    stream_pulse = 'animation: pulse 2s infinite;' if stream_online else ''
    stream_events_str = f"{stream_events:,}" if stream_events is not None else "—"
    stream_anomalies_str = f"{stream_anomalies:,}" if stream_anomalies is not None else "—"

    # System Status panel
    st.markdown(f"""
    <div style="
        background: #ffffff;
        border: 1px solid #efefef;
        border-radius: 6px;
        padding: 12px;
        margin-top: 8px;
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
                background: #3b82f6;
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
                    color: #0f172a;
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
            background: #f8fafc;
            border-radius: 4px;
            margin-bottom: 8px;
        ">
            <span style="
                width: 8px;
                height: 8px;
                background: {status_color};
                border-radius: 50%;
                display: inline-block;
            "></span>
            <span style="
                font-size: 12px;
                font-weight: 600;
                color: #0f172a;
            ">{system_status}</span>
        </div>

        <!-- Stream status -->
        <div style="
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 8px;
            background: #f8fafc;
            border-radius: 4px;
            margin-bottom: 10px;
        ">
            <span style="
                width: 8px;
                height: 8px;
                background: {stream_color};
                border-radius: 50%;
                display: inline-block;
                {stream_pulse}
            "></span>
            <span style="
                font-size: 12px;
                font-weight: 600;
                color: {stream_color};
            ">{stream_label}</span>
        </div>

        <div style="
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        ">
            <div style="
                background: #f8fafc;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #efefef;
            ">
                <div style="
                    font-size: 10px;
                    color: #64748b;
                    margin-bottom: 4px;
                ">Data Pipeline</div>
                <div style="
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                ">
                    <span style="color: #0f172a; font-weight: 500; font-size: 12px;">{pipeline_status}</span>
                    <span style="color: #64748b; font-size: 11px;">{pipeline_time}</span>
                </div>
            </div>

            <div style="
                background: #f8fafc;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #efefef;
            ">
                <div style="
                    font-size: 10px;
                    color: #64748b;
                    margin-bottom: 4px;
                ">Stream Events</div>
                <div style="
                    font-size: 14px;
                    font-weight: 700;
                    color: #0f172a;
                ">{stream_events_str}</div>
            </div>

            <div style="
                background: #f8fafc;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #efefef;
            ">
                <div style="
                    font-size: 10px;
                    color: #64748b;
                    margin-bottom: 4px;
                ">Anomalies</div>
                <div style="
                    font-size: 14px;
                    font-weight: 700;
                    color: #ef4444;
                ">{stream_anomalies_str}</div>
            </div>

            <div style="
                background: #f8fafc;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #efefef;
            ">
                <div style="
                    font-size: 10px;
                    color: #64748b;
                    margin-bottom: 4px;
                ">Silver Records</div>
                <div style="
                    font-size: 14px;
                    font-weight: 700;
                    color: #0f172a;
                ">{records_display}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _get_filter_options_from_df(df, current_filters: dict) -> dict:
    """Extract filter options from dataframe."""
    options = {}
    
    # Region options
    region_values = sorted(df["region"].unique().tolist())
    options["region"] = ["All"] + region_values
    
    # Substation options (cascade from region)
    current_region = current_filters.get("region", "All")
    if current_region != "All":
        filtered = df[df["region"] == current_region]
        sub_values = sorted(filtered["substation_id"].unique().tolist())
    else:
        sub_values = sorted(df["substation_id"].unique().tolist())
    options["substation_id"] = ["All"] + sub_values
    
    # Transformer options (cascade from substation)
    current_substation = current_filters.get("substation_id", "All")
    current_region = current_filters.get("region", "All")
    
    if current_substation != "All":
        filtered = df[df["substation_id"] == current_substation]
        tran_values = sorted(filtered["transformer_id"].unique().tolist())
    elif current_region != "All":
        filtered = df[df["region"] == current_region]
        tran_values = sorted(filtered["transformer_id"].unique().tolist())
    else:
        tran_values = sorted(df["transformer_id"].unique().tolist())
    options["transformer_id"] = ["All"] + tran_values
    
    # Time range options
    options["time_range"] = [opt[0] for opt in TIME_RANGE_OPTIONS]
    
    return options


def _get_default_filter_options() -> dict:
    """Get default filter options when no data."""
    return {
        "region": ["All"] + REGIONS,
        "substation_id": ["All"],
        "transformer_id": ["All"],
        "time_range": [opt[0] for opt in TIME_RANGE_OPTIONS],
    }

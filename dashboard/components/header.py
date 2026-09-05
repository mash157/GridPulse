#!/usr/bin/env python
"""
GridPulse Header Component
Top navigation bar with branding, search, and controls
"""

import streamlit as st
from datetime import datetime

from dashboard.theme import get_theme


def render_header(is_dark: bool = False, stream_status: dict = None):
    """
    Render the dashboard header.

    Layout:
    - Left: GridPulse branding + subtitle
    - Center: Search bar
    - Right: Stream status, date/time, theme toggle, notifications, user

    Args:
        is_dark: Whether dark theme is active
        stream_status: dict with keys online, status_text, events_generated,
                       anomalies_detected, last_update
    """
    theme = get_theme(is_dark)

    if stream_status is None:
        stream_status = {"online": False, "status_text": "STREAM OFFLINE"}

    is_online = stream_status.get("online", False)
    status_label = stream_status.get("status_text", "STREAM OFFLINE")
    status_dot_color = theme.success if is_online else "#ef4444"

    # Header container with custom CSS
    header_html = f"""
    <div style="
        background: {theme.header_background};
        border-bottom: 1px solid {theme.border};
        padding: 12px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
        position: sticky;
        top: 0;
        z-index: 100;
    ">
        <!-- Left: Branding -->
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="
                width: 40px;
                height: 40px;
                background: {theme.primary};
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 22px;
                box-shadow: {theme.shadow};
            ">
                ⚡
            </div>
            <div>
                <div style="
                    font-size: 18px;
                    font-weight: 700;
                    color: {theme.header_text};
                    letter-spacing: -0.5px;
                    line-height: 1.2;
                ">
                    GridPulse
                </div>
                <div style="
                    font-size: 11px;
                    color: {theme.header_text_muted};
                    font-weight: 500;
                ">
                    Smart Energy Grid Monitoring
                </div>
            </div>
        </div>

        <!-- Center: Search -->
        <div style="
            flex: 1;
            max-width: 400px;
            position: relative;
        ">
            <div style="
                position: absolute;
                left: 12px;
                top: 50%;
                transform: translateY(-50%);
                color: {theme.text_muted};
                font-size: 16px;
            ">
                🔍
            </div>
            <input type="text"
                placeholder="Search transformers, substations, regions..."
                style="
                    width: 100%;
                    padding: 8px 12px 8px 36px;
                    border: 1px solid {theme.border};
                    border-radius: 6px;
                    background: {theme.surface};
                    color: {theme.text};
                    font-size: 13px;
                    outline: none;
                    transition: all 0.2s;
                "
                onfocus="this.borderColor='{theme.primary}'; this.boxShadow='0 0 0 3px {theme.primary_light}'"
                onblur="this.borderColor='{theme.border}'; this.boxShadow='none'"
            />
            <div style="
                position: absolute;
                right: 12px;
                top: 50%;
                transform: translateY(-50%);
                background: {theme.surface_secondary};
                color: {theme.text_muted};
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 600;
            ">
                Ctrl K
            </div>
        </div>

        <!-- Right: Controls -->
        <div style="display: flex; align-items: center; gap: 16px;">
            <!-- Stream Status -->
            <div style="
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 4px 10px;
                background: {theme.surface};
                border: 1px solid {theme.border};
                border-radius: 6px;
            ">
                <span style="
                    width: 8px;
                    height: 8px;
                    background: {status_dot_color};
                    border-radius: 50%;
                    {'animation: pulse 2s infinite;' if is_online else ''}
                "></span>
                <span style="
                    font-size: 12px;
                    font-weight: 600;
                    color: {status_dot_color};
                ">
                    {status_label}
                </span>
            </div>

            <!-- Date/Time -->
            <div style="
                text-align: right;
            ">
                <div style="
                    font-size: 12px;
                    font-weight: 600;
                    color: {theme.text};
                ">
                    {datetime.now().strftime('%b %d, %Y')}
                </div>
                <div style="
                    font-size: 11px;
                    color: {theme.text_muted};
                ">
                    {datetime.now().strftime('%H:%M:%S')}
                </div>
            </div>

            <!-- Theme Toggle -->
            <div style="
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: {theme.surface};
                border: 1px solid {theme.border};
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s;
            ">
                <span style="font-size: 16px;">☀️</span>
            </div>

            <!-- Notifications -->
            <div style="
                position: relative;
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: {theme.surface};
                border: 1px solid {theme.border};
                border-radius: 8px;
                cursor: pointer;
            ">
                <span style="font-size: 16px;">🔔</span>
                <span style="
                    position: absolute;
                    top: -4px;
                    right: -4px;
                    width: 16px;
                    height: 16px;
                    background: {theme.critical};
                    border-radius: 50%;
                    color: white;
                    font-size: 9px;
                    font-weight: 700;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    12
                </span>
            </div>

            <!-- User Avatar -->
            <div style="
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 4px 8px 4px 4px;
                background: {theme.surface};
                border: 1px solid {theme.border};
                border-radius: 8px;
                cursor: pointer;
            ">
                <div style="
                    width: 32px;
                    height: 32px;
                    background: linear-gradient(135deg, {theme.primary}, #8b5cf6);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 13px;
                    font-weight: 700;
                ">
                    AD
                </div>
                <div style="text-align: left;">
                    <div style="
                        font-size: 12px;
                        font-weight: 600;
                        color: {theme.text};
                    ">
                        Admin
                    </div>
                    <div style="
                        font-size: 10px;
                        color: {theme.text_muted};
                    ">
                        Grid Operator
                    </div>
                </div>
                <span style="
                    margin-left: 4px;
                    color: {theme.text_muted};
                    font-size: 12px;
                ">▼</span>
            </div>
        </div>
    </div>
    """

    st.markdown(header_html, unsafe_allow_html=True)

    # Add CSS for pulse animation and other styles
    st.markdown("""
    <style>
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
        70% { box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }
        100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
    }

    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }

    /* Custom select styling */
    select {
        appearance: none;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2364748b' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 8px center;
        padding-right: 28px;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.2s;
    }

    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 6px !important;
    }
    </style>
    """, unsafe_allow_html=True)

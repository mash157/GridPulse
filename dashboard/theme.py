#!/usr/bin/env python
"""
GridPulse Theme System
Centralized theme configuration for Light and Dark modes
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Theme:
    """Theme configuration dataclass."""

    # Background colors
    background: str
    background_gradient_start: str
    background_gradient_end: str

    # Surface colors (cards, panels)
    surface: str
    surface_hover: str
    surface_secondary: str

    # Text colors
    text: str
    text_muted: str
    text_secondary: str
    text_disabled: str

    # Border colors
    border: str
    border_light: str
    border_focus: str

    # Primary accent
    primary: str
    primary_hover: str
    primary_light: str
    primary_text: str

    # Secondary accent
    secondary: str
    secondary_hover: str

    # Semantic colors (Status indicators)
    success: str  # Normal
    success_light: str
    warning: str  # Warning
    warning_light: str
    high_risk: str  # High Risk
    high_risk_light: str
    critical: str  # Critical
    critical_light: str

    # Chart colors
    chart_background: str
    chart_paper_bg: str
    chart_text: str
    chart_grid: str
    chart_axis_line: str

    # Specific chart series colors
    generation_color: str
    consumption_color: str
    transmission_color: str

    # Additional UI elements
    shadow: str
    shadow_strong: str
    scrollbar_track: str
    scrollbar_thumb: str
    input_bg: str
    input_border: str
    button_text: str
    badge_background: str

    # 3D Scene colors
    scene_background: str
    scene_axis_color: str
    scene_grid_color: str

    # Sidebar specific
    sidebar_background: str
    sidebar_text: str
    sidebar_active: str
    sidebar_active_text: str
    sidebar_border: str

    # Header specific
    header_background: str
    header_text: str
    header_text_muted: str

    # KPI card specific
    kpi_background: str
    kpi_border: str
    kpi_icon_background: str

    # Table specific
    table_background: str
    table_row_even: str
    table_row_odd: str
    table_header: str
    table_rowHover: str

    # Dropdown specific
    dropdown_background: str
    dropdown_border: str
    dropdown_text: str
    dropdown_optionHover: str


# Light Theme - Premium enterprise style
LIGHT_THEME = Theme(
    # Background
    background="#f4f6f9",
    background_gradient_start="#f8fafc",
    background_gradient_end="#eef2f6",
    surface="#ffffff",
    surface_hover="#f8fafc",
    surface_secondary="#f1f5f9",

    # Text
    text="#0f172a",
    text_muted="#64748b",
    text_secondary="#475569",
    text_disabled="#94a3b8",

    # Borders
    border="#e2e8f0",
    border_light="#f1f5f9",
    border_focus="#0066ff",

    # Primary
    primary="#0066ff",
    primary_hover="#0052cc",
    primary_light="#e6f0ff",
    primary_text="#ffffff",

    # Secondary
    secondary="#64748b",
    secondary_hover="#475569",

    # Semantic colors
    success="#22c55e",
    success_light="#dcfce7",
    warning="#f59e0b",
    warning_light="#fef3c7",
    high_risk="#f97316",
    high_risk_light="#ffedd5",
    critical="#ef4444",
    critical_light="#fee2e2",

    # Chart
    chart_background="#ffffff",
    chart_paper_bg="#ffffff",
    chart_text="#0f172a",
    chart_grid="#e2e8f0",
    chart_axis_line="#cbd5e1",

    # Series colors
    generation_color="#22c55e",
    consumption_color="#3b82f6",
    transmission_color="#6366f1",

    # UI
    shadow="0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)",
    shadow_strong="0 4px 12px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06)",
    scrollbar_track="#f1f5f9",
    scrollbar_thumb="#cbd5e1",
    input_bg="#ffffff",
    input_border="#e2e8f0",
    button_text="#ffffff",
    badge_background="#e2e8f0",

    # 3D
    scene_background="#ffffff",
    scene_axis_color="#64748b",
    scene_grid_color="#e2e8f0",

    # Sidebar
    sidebar_background="#f8fafc",
    sidebar_text="#475569",
    sidebar_active="#e6f0ff",
    sidebar_active_text="#0066ff",
    sidebar_border="#e2e8f0",

    # Header
    header_background="#ffffff",
    header_text="#0f172a",
    header_text_muted="#64748b",

    # KPI
    kpi_background="#ffffff",
    kpi_border="#e2e8f0",
    kpi_icon_background="#f1f5f9",

    # Table
    table_background="#ffffff",
    table_row_even="#ffffff",
    table_row_odd="#f8fafc",
    table_header="#f1f5f9",
    table_rowHover="#f1f5f9",

    # Dropdown
    dropdown_background="#ffffff",
    dropdown_border="#e2e8f0",
    dropdown_text="#0f172a",
    dropdown_optionHover="#f1f5f9",
)


# Dark Theme - Premium dark mode
DARK_THEME = Theme(
    # Background
    background="#0b1329",
    background_gradient_start="#0f1729",
    background_gradient_end="#091020",
    surface="#111c38",
    surface_hover="#15213d",
    surface_secondary="#1a2744",

    # Text
    text="#ffffff",
    text_muted="#94a3b8",
    text_secondary="#64748b",
    text_disabled="#475569",

    # Borders
    border="#1e3a5f",
    border_light="#1a2744",
    border_focus="#3b82f6",

    # Primary
    primary="#3b82f6",
    primary_hover="#2563eb",
    primary_light="#1e3a5f",
    primary_text="#ffffff",

    # Secondary
    secondary="#64748b",
    secondary_hover="#94a3b8",

    # Semantic colors
    success="#22c55e",
    success_light="#14532d",
    warning="#f59e0b",
    warning_light="#78350f",
    high_risk="#f97316",
    high_risk_light="#7c2d12",
    critical="#ef4444",
    critical_light="#7f1d1d",

    # Chart
    chart_background="#111c38",
    chart_paper_bg="#111c38",
    chart_text="#ffffff",
    chart_grid="#1e3a5f",
    chart_axis_line="#334155",

    # Series colors
    generation_color="#22c55e",
    consumption_color="#3b82f6",
    transmission_color="#818cf8",

    # UI
    shadow="0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2)",
    shadow_strong="0 4px 12px rgba(0,0,0,0.4), 0 2px 4px rgba(0,0,0,0.3)",
    scrollbar_track="#1a2744",
    scrollbar_thumb="#334155",
    input_bg="#1a2744",
    input_border="#334155",
    button_text="#ffffff",
    badge_background="#334155",

    # 3D
    scene_background="#0b1329",
    scene_axis_color="#64748b",
    scene_grid_color="#1e3a5f",

    # Sidebar
    sidebar_background="#0f1729",
    sidebar_text="#94a3b8",
    sidebar_active="#1e3a5f",
    sidebar_active_text="#3b82f6",
    sidebar_border="#1e3a5f",

    # Header
    header_background="#111c38",
    header_text="#ffffff",
    header_text_muted="#94a3b8",

    # KPI
    kpi_background="#111c38",
    kpi_border="#1e3a5f",
    kpi_icon_background="#1a2744",

    # Table
    table_background="#111c38",
    table_row_even="#111c38",
    table_row_odd="#0f1729",
    table_header="#1a2744",
    table_rowHover="#1a2744",

    # Dropdown
    dropdown_background="#111c38",
    dropdown_border="#334155",
    dropdown_text="#ffffff",
    dropdown_optionHover="#1a2744",
)


def get_theme(is_dark: bool = False) -> Theme:
    """Get the appropriate theme based on mode."""
    return DARK_THEME if is_dark else LIGHT_THEME


def get_plotly_theme(is_dark: bool = False) -> Dict[str, Any]:
    """
    Get Plotly theme configuration.

    Returns:
        Dictionary with Plotly configuration
    """
    theme = get_theme(is_dark)

    return {
        "paper_bgcolor": theme.chart_paper_bg,
        "plot_bgcolor": theme.chart_background,
        "font": {
            "color": theme.chart_text,
            "family": "Inter, system-ui, -apple-system, sans-serif",
            "size": 12,
        },
        "xaxis": {
            "gridcolor": theme.chart_grid,
            "zerolinecolor": theme.chart_axis_line,
            "linecolor": theme.chart_axis_line,
            "tickfont": {
                "color": theme.chart_text,
                "size": 11,
            },
            "titlefont": {
                "color": theme.chart_text,
                "size": 12,
            },
        },
        "yaxis": {
            "gridcolor": theme.chart_grid,
            "zerolinecolor": theme.chart_axis_line,
            "linecolor": theme.chart_axis_line,
            "tickfont": {
                "color": theme.chart_text,
                "size": 11,
            },
            "titlefont": {
                "color": theme.chart_text,
                "size": 12,
            },
        },
        "legend": {
            "font": {
                "color": theme.chart_text,
                "size": 11,
            },
            "title": {
                "font": {
                    "color": theme.chart_text,
                    "size": 12,
                },
            },
        },
        "hoverlabel": {
            "bgcolor": theme.surface,
            "font": {
                "color": theme.text,
                "size": 12,
            },
        },
        "margin": {
            "l": 60,
            "r": 20,
            "t": 40,
            "b": 60,
        },
        "height": None,
        "width": None,
    }


def get_3d_scene_config(is_dark: bool = False) -> Dict[str, Any]:
    """
    Get 3D scene configuration for Plotly.

    Returns:
        Dictionary with 3D scene configuration
    """
    theme = get_theme(is_dark)

    return {
        "xaxis": {
            "backgroundcolor": theme.scene_background,
            "gridcolor": theme.scene_grid_color,
            "gridwidth": 0.5,
            "linecolor": theme.scene_axis_color,
            "showbackground": True,
            "showgrid": True,
            "showline": True,
            "showspikes": False,
            "tickfont": {
                "color": theme.chart_text,
                "size": 10,
            },
            "title": "",
            "zeroline": False,
        },
        "yaxis": {
            "backgroundcolor": theme.scene_background,
            "gridcolor": theme.scene_grid_color,
            "gridwidth": 0.5,
            "linecolor": theme.scene_axis_color,
            "showbackground": True,
            "showgrid": True,
            "showline": True,
            "showspikes": False,
            "tickfont": {
                "color": theme.chart_text,
                "size": 10,
            },
            "title": "",
            "zeroline": False,
        },
        "zaxis": {
            "backgroundcolor": theme.scene_background,
            "gridcolor": theme.scene_grid_color,
            "gridwidth": 0.5,
            "linecolor": theme.scene_axis_color,
            "showbackground": True,
            "showgrid": True,
            "showline": True,
            "showspikes": False,
            "tickfont": {
                "color": theme.chart_text,
                "size": 10,
            },
            "title": "",
            "zeroline": False,
        },
        "camera": {
            "eye": {"x": 1.5, "y": 1.5, "z": 1.2},
            "center": {"x": 0, "y": 0, "z": 0},
            "up": {"x": 0, "y": 0, "z": 1},
        },
        "aspectmode": "manual",
        "aspectratio": {"x": 1, "y": 1, "z": 0.8},
    }


def get_status_color(status: str, is_dark: bool = False) -> str:
    """Get color for a status value."""
    theme = get_theme(is_dark)

    status_colors = {
        "Normal": theme.success,
        "Low": theme.success,
        "Warning": theme.warning,
        "High Risk": theme.high_risk,
        "Critical": theme.critical,
    }

    return status_colors.get(status, theme.text_muted)


def get_status_background(status: str, is_dark: bool = False) -> str:
    """Get background color for a status value."""
    theme = get_theme(is_dark)

    status_backgrounds = {
        "Normal": theme.success_light,
        "Low": theme.success_light,
        "Warning": theme.warning_light,
        "High Risk": theme.high_risk_light,
        "Critical": theme.critical_light,
    }

    return status_backgrounds.get(status, theme.surface_secondary)

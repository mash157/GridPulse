#!/usr/bin/env python
"""
GridPulse Filter System
Centralized filter management with cascading dependencies
"""

from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from dashboard.config import REGIONS, TIME_RANGE_OPTIONS


def get_unique_values(
    df: pd.DataFrame,
    column: str,
    filter_value: Optional[str] = None
) -> List[str]:
    """
    Get unique values from a column, respecting filter dependencies.

    Args:
        df: DataFrame to extract values from
        column: Column name
        filter_value: Parent filter value (for cascading)

    Returns:
        Sorted list of unique values
    """
    if df is None or len(df) == 0:
        return []

    # Filter by parent if applicable
    if filter_value and filter_value != "All":
        # Handle cascading filters
        if column == "substation_id" and "region" in df.columns:
            df = df[df["region"] == filter_value]
        elif column == "transformer_id" and "substation_id" in df.columns:
            df = df[df["substation_id"] == filter_value]

    values = df[column].unique().tolist()
    values = sorted(values)

    # Add "All" option at the beginning
    return ["All"] + values


def apply_filters(
    df: pd.DataFrame,
    filters: Dict[str, str],
    timestamp_col: str = "timestamp"
) -> pd.DataFrame:
    """
    Apply all filters to a dataframe.

    Args:
        df: DataFrame to filter
        filters: Dictionary with filter values
        timestamp_col: Name of timestamp column

    Returns:
        Filtered DataFrame
    """
    if df is None or len(df) == 0:
        return df

    filtered_df = df.copy()

    # Apply region filter
    region = filters.get("region", "All")
    if region and region != "All" and "region" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["region"] == region]

    # Apply substation filter
    substation = filters.get("substation_id", "All")
    if substation and substation != "All" and "substation_id" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["substation_id"] == substation]

    # Apply transformer filter
    transformer = filters.get("transformer_id", "All")
    if transformer and transformer != "All" and "transformer_id" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["transformer_id"] == transformer]

    # Apply time range filter
    time_range = filters.get("time_range", "Last 24 Hours")
    if time_range and time_range != "All Time" and timestamp_col in filtered_df.columns:
        # Find the timedelta for the selected range
        range_map = {
            "Last 1 Hour": timedelta(hours=1),
            "Last 6 Hours": timedelta(hours=6),
            "Last 12 Hours": timedelta(hours=12),
            "Last 24 Hours": timedelta(hours=24),
            "Last 7 Days": timedelta(days=7),
            "Last 30 Days": timedelta(days=30),
        }

        delta = range_map.get(time_range)
        if delta:
            # Ensure timestamp is datetime
            if not pd.api.types.is_datetime64_any_dtype(filtered_df[timestamp_col]):
                filtered_df[timestamp_col] = pd.to_datetime(filtered_df[timestamp_col])

            latest_time = filtered_df[timestamp_col].max()
            cutoff_time = latest_time - delta

            filtered_df = filtered_df[filtered_df[timestamp_col] >= cutoff_time]

    return filtered_df


def get_filter_options(
    df: pd.DataFrame,
    current_filters: Dict[str, str]
) -> Dict[str, List[str]]:
    """
    Get filter options based on current data and filters.

    Args:
        df: Full dataset
        current_filters: Current filter selections

    Returns:
        Dictionary with filter options for each category
    """
    options = {}

    # Region options
    if df is not None and "region" in df.columns:
        region_values = get_unique_values(df, "region")
        options["region"] = region_values
    else:
        options["region"] = ["All"] + REGIONS

    # Substation options (cascading from region)
    current_region = current_filters.get("region", "All")
    if df is not None and "substation_id" in df.columns:
        if current_region != "All":
            filtered = df[df["region"] == current_region]
            sub_values = get_unique_values(filtered, "substation_id")
        else:
            sub_values = get_unique_values(df, "substation_id")
        options["substation_id"] = sub_values
    else:
        options["substation_id"] = ["All"]

    # Transformer options (cascading from substation)
    current_substation = current_filters.get("substation_id", "All")
    if df is not None and "transformer_id" in df.columns:
        if current_substation != "All":
            filtered = df[df["substation_id"] == current_substation]
            tran_values = get_unique_values(filtered, "transformer_id")
        elif current_region != "All" and "region" in df.columns:
            filtered = df[df["region"] == current_region]
            tran_values = get_unique_values(filtered, "transformer_id")
        else:
            tran_values = get_unique_values(df, "transformer_id")
        options["transformer_id"] = tran_values
    else:
        options["transformer_id"] = ["All"]

    # Time range options
    options["time_range"] = [opt[0] for opt in TIME_RANGE_OPTIONS]

    return options


def render_filters(
    df: pd.DataFrame,
    current_filters: Dict[str, str],
    key_prefix: str = "filter"
) -> Dict[str, str]:
    """
    Render filter UI components in Streamlit sidebar.

    Args:
        df: Full dataset for populating options
        current_filters: Current filter selections
        key_prefix: Prefix for Streamlit widget keys

    Returns:
        Updated filter dictionary
    """
    options = get_filter_options(df, current_filters)

    # Region filter
    region_options = options.get("region", ["All"] + REGIONS)
    selected_region = st.selectbox(
        "Region",
        options=region_options,
        key=f"{key_prefix}_region",
        index=region_options.index(current_filters.get("region", "All")) if current_filters.get("region", "All") in region_options else 0,
        label_visibility="collapsed"
    )

    # Substation filter
    sub_options = options.get("substation_id", ["All"])
    selected_substation = st.selectbox(
        "Substation",
        options=sub_options,
        key=f"{key_prefix}_substation",
        index=sub_options.index(current_filters.get("substation_id", "All")) if current_filters.get("substation_id", "All") in sub_options else 0,
        label_visibility="collapsed"
    )

    # Transformer filter
    tran_options = options.get("transformer_id", ["All"])
    selected_transformer = st.selectbox(
        "Transformer",
        options=tran_options,
        key=f"{key_prefix}_transformer",
        index=tran_options.index(current_filters.get("transformer_id", "All")) if current_filters.get("transformer_id", "All") in tran_options else 0,
        label_visibility="collapsed"
    )

    # Time range filter
    time_options = options.get("time_range", [opt[0] for opt in TIME_RANGE_OPTIONS])
    selected_time = st.selectbox(
        "Time Range",
        options=time_options,
        key=f"{key_prefix}_time",
        index=time_options.index(current_filters.get("time_range", "Last 24 Hours")) if current_filters.get("time_range", "Last 24 Hours") in time_options else 0,
        label_visibility="collapsed"
    )

    # Build updated filters
    updated_filters = {
        "region": selected_region,
        "substation_id": selected_substation,
        "transformer_id": selected_transformer,
        "time_range": selected_time,
    }

    return updated_filters


def clear_filters() -> Dict[str, str]:
    """Return default (empty) filter values."""
    return {
        "region": "All",
        "substation_id": "All",
        "transformer_id": "All",
        "time_range": "Last 24 Hours",
    }


def get_filter_summary(filters: Dict[str, str]) -> str:
    """
    Get a human-readable summary of active filters.

    Args:
        filters: Filter dictionary

    Returns:
        Summary string
    """
    parts = []

    if filters.get("region") and filters["region"] != "All":
        parts.append(f"Region: {filters['region']}")

    if filters.get("substation_id") and filters["substation_id"] != "All":
        parts.append(f"Substation: {filters['substation_id']}")

    if filters.get("transformer_id") and filters["transformer_id"] != "All":
        parts.append(f"Transformer: {filters['transformer_id']}")

    if filters.get("time_range") and filters["time_range"] != "All Time":
        parts.append(f"Time: {filters['time_range']}")

    if not parts:
        return "No filters applied"

    return " | ".join(parts)


def validate_filter_consistency(
    df: pd.DataFrame,
    filters: Dict[str, str]
) -> Tuple[bool, str]:
    """
    Validate that filters are consistent with available data.

    Args:
        df: Full dataset
        filters: Filter dictionary

    Returns:
        Tuple of (is_valid, message)
    """
    if df is None or len(df) == 0:
        return True, "No data to validate"

    # Check region exists
    if filters.get("region") and filters["region"] != "All":
        if "region" in df.columns and filters["region"] not in df["region"].unique():
            return False, f"Region '{filters['region']}' not found in data"

    # Check substation exists (considering region filter)
    if filters.get("substation_id") and filters["substation_id"] != "All":
        if filters.get("region") and filters["region"] != "All":
            region_df = df[df["region"] == filters["region"]]
        else:
            region_df = df

        if "substation_id" in region_df.columns and filters["substation_id"] not in region_df["substation_id"].unique():
            return False, f"Substation '{filters['substation_id']}' not found in selected region"

    # Check transformer exists (considering substation/region filters)
    if filters.get("transformer_id") and filters["transformer_id"] != "All":
        if filters.get("substation_id") and filters["substation_id"] != "All":
            sub_df = df[df["substation_id"] == filters["substation_id"]]
        elif filters.get("region") and filters["region"] != "All":
            sub_df = df[df["region"] == filters["region"]]
        else:
            sub_df = df

        if "transformer_id" in sub_df.columns and filters["transformer_id"] not in sub_df["transformer_id"].unique():
            return False, f"Transformer '{filters['transformer_id']}' not found in selected scope"

    return True, "Filters are valid"

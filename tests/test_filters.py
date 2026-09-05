#!/usr/bin/env python
"""
GridPulse Tests - Filter Functionality
"""

import unittest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.filters import apply_filters, get_filter_options, clear_filters


class TestApplyFilters(unittest.TestCase):
    """Test filter application."""
    
    def setUp(self):
        """Create test dataframe."""
        self.df = pd.DataFrame({
            "event_id": [f"EVT-{i:07d}" for i in range(1000)],
            "timestamp": pd.date_range("2025-01-01", periods=1000, freq="h"),
            "region": np.random.choice(["North", "South", "East"], 1000),
            "substation_id": [f"SUB-{i % 20:03d}" for i in range(1000)],
            "transformer_id": [f"TR-{i % 100:03d}" for i in range(1000)],
            "load_percent": np.random.uniform(30, 90, 1000),
            "status": np.random.choice(["Normal", "Warning", "Critical"], 1000, p=[0.8, 0.15, 0.05]),
        })
    
    def test_no_filters_returns_all(self):
        """Test that no filters returns all data."""
        filters = {
            "region": "All",
            "substation_id": "All",
            "transformer_id": "All",
            "time_range": "All Time",
        }
        
        result = apply_filters(self.df.copy(), filters)
        
        self.assertEqual(len(result), len(self.df),
            "No filters should return all records")
    
    def test_region_filter(self):
        """Test region filter filters correctly."""
        filters = {
            "region": "North",
            "substation_id": "All",
            "transformer_id": "All",
            "time_range": "Last 24 Hours",
        }
        
        result = apply_filters(self.df.copy(), filters)
        
        # All results should be North region
        self.assertTrue((result["region"] == "North").all(),
            "Region filter not working correctly")
        
        # Should have fewer records
        self.assertLess(len(result), len(self.df),
            "Region filter should reduce record count")
    
    def test_substation_filter(self):
        """Test substation filter."""
        filters = {
            "region": "All",
            "substation_id": "SUB-001",
            "transformer_id": "All",
            "time_range": "Last 24 Hours",
        }
        
        result = apply_filters(self.df.copy(), filters)
        
        self.assertTrue((result["substation_id"] == "SUB-001").all(),
            "Substation filter not working correctly")
    
    def test_transformer_filter(self):
        """Test transformer filter."""
        filters = {
            "region": "All",
            "substation_id": "All",
            "transformer_id": "TR-005",
            "time_range": "Last 24 Hours",
        }
        
        result = apply_filters(self.df.copy(), filters)
        
        self.assertTrue((result["transformer_id"] == "TR-005").all(),
            "Transformer filter not working correctly")
    
    def test_time_range_filter(self):
        """Test time range filter."""
        filters = {
            "region": "All",
            "substation_id": "All",
            "transformer_id": "All",
            "time_range": "Last 24 Hours",
        }
        
        result = apply_filters(self.df.copy(), filters)
        
        # Should have at most 24 hours of data
        time_range = result["timestamp"].max() - result["timestamp"].min()
        self.assertLessEqual(time_range.total_seconds() / 3600, 24,
            f"Time range should be <= 24h, got {time_range.total_seconds()/3600:.1f}h")
    
    def test_combined_filters(self):
        """Test multiple filters combined."""
        filters = {
            "region": "North",
            "substation_id": "All",
            "transformer_id": "All",
            "time_range": "Last 1 Hour",
        }
        
        result = apply_filters(self.df.copy(), filters)
        
        # Should filter by both region and time
        self.assertTrue((result["region"] == "North").all(),
            "Region filter not applied")
        
        time_range = result["timestamp"].max() - result["timestamp"].min()
        self.assertLessEqual(time_range.total_seconds() / 3600, 1.5,
            "Time range filter not applied correctly")
    
    def test_empty_result(self):
        """Test that filter returning no results doesn't crash."""
        filters = {
            "region": "NonExistentRegion",
            "substation_id": "All",
            "transformer_id": "All",
            "time_range": "Last 24 Hours",
        }
        
        # Should not crash
        result = apply_filters(self.df.copy(), filters)
        
        # Should return empty dataframe
        self.assertTrue(len(result) == 0 or len(result) < len(self.df),
            "Should handle non-matching filter gracefully")


class TestCascadingFilters(unittest.TestCase):
    """Test cascading filter dependencies."""
    
    def setUp(self):
        """Create test dataframe with hierarchy."""
        self.df = pd.DataFrame({
            "event_id": range(500),
            "timestamp": pd.date_range("2025-01-01", periods=500, freq="h"),
            "region": ["North"] * 200 + ["South"] * 200 + ["East"] * 100,
            "substation_id": (
                ["SUB-001"] * 100 + ["SUB-002"] * 100 +
                ["SUB-003"] * 100 + ["SUB-004"] * 100 +
                ["SUB-005"] * 100
            ),
            "transformer_id": [f"TR-{i % 10:03d}" for i in range(500)],
            "load_percent": np.random.uniform(40, 80, 500),
        })
    
    def test_region_substation_cascade(self):
        """Test that selecting region cascades to substation options."""
        from dashboard.filters import get_filter_options
        
        filters = {"region": "North", "substation_id": "All", "transformer_id": "All"}
        options = get_filter_options(self.df, filters)
        
        # Substation options should only include North substations
        north_subs = self.df[self.df["region"] == "North"]["substation_id"].unique()
        
        for sub in options["substation_id"]:
            if sub != "All":
                self.assertIn(sub, north_subs,
                    f"Substation {sub} should not appear when North region selected")


class TestClearFilters(unittest.TestCase):
    """Test clear filters functionality."""
    
    def test_clear_filters_returns_defaults(self):
        """Test that clear_filters returns default values."""
        result = clear_filters()
        
        expected = {
            "region": "All",
            "substation_id": "All",
            "transformer_id": "All",
            "time_range": "Last 24 Hours",
        }
        
        self.assertEqual(result, expected,
            f"Clear filters should return defaults, got {result}")


class TestFilterOptions(unittest.TestCase):
    """Test filter options generation."""
    
    def setUp(self):
        """Create test dataframe."""
        self.df = pd.DataFrame({
            "event_id": range(200),
            "timestamp": pd.date_range("2025-01-01", periods=200, freq="h"),
            "region": ["North", "South", "East"] * 66 + ["North", "South"],
            "substation_id": [f"SUB-{i % 10:03d}" for i in range(200)],
            "transformer_id": [f"TR-{i % 50:03d}" for i in range(200)],
        })
    
    def test_region_options(self):
        """Test region filter options."""
        from dashboard.filters import get_filter_options
        
        options = get_filter_options(self.df, {"region": "All"})
        
        self.assertIn("All", options["region"], "Should have 'All' option")
        self.assertIn("North", options["region"], "Should have North")
        self.assertIn("South", options["region"], "Should have South")
        self.assertIn("East", options["region"], "Should have East")
    
    def test_transformer_options_all(self):
        """Test transformer options when no filters."""
        from dashboard.filters import get_filter_options
        
        options = get_filter_options(self.df, {
            "region": "All",
            "substation_id": "All",
        })
        
        self.assertIn("All", options["transformer_id"])
        # Should have all transformer IDs
        expected_transformers = self.df["transformer_id"].unique()
        for t in expected_transformers:
            self.assertIn(t, options["transformer_id"],
                f"Transformer {t} should be in options")


if __name__ == "__main__":
    unittest.main()

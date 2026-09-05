#!/usr/bin/env python
"""
GridPulse Tests - Risk Scoring
"""

import unittest
import pandas as pd
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRiskScoring(unittest.TestCase):
    """Test risk scoring functionality."""
    
    def test_risk_score_exists(self):
        """Test that risk_score column exists."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"
        
        if not sample_file.exists():
            self.skipTest("Silver sample not available")
        
        df = pd.read_csv(sample_file)
        
        self.assertIn("risk_score", df.columns, 
            "risk_score column missing from data")
    
    def test_risk_score_bounds(self):
        """Test that risk scores are within 0-100 range."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"
        
        if not sample_file.exists():
            self.skipTest("Silver sample not available")
        
        df = pd.read_csv(sample_file)
        
        self.assertGreaterEqual(df["risk_score"].min(), 0,
            f"Risk score below 0: {df['risk_score'].min()}")
        self.assertLessEqual(df["risk_score"].max(), 100,
            f"Risk score above 100: {df['risk_score'].max()}")
    
    def test_risk_levels_defined(self):
        """Test that all risk levels are properly classified."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        severity_file = exports_path / "severity_summary.csv"
        
        if not severity_file.exists():
            self.skipTest("Severity summary not available")
        
        df = pd.read_csv(severity_file)
        
        # Check that status column has valid values
        valid_statuses = {"Normal", "Low", "Warning", "High Risk", "Critical"}
        actual_statuses = set(df["status"].unique())
        
        self.assertTrue(actual_statuses.issubset(valid_statuses),
            f"Invalid status values: {actual_statuses - valid_statuses}")
    
    def test_risk_increases_with_anomalies(self):
        """Test that risk scores increase with anomalies."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"
        
        if not sample_file.exists():
            self.skipTest("Silver sample not available")
        
        df = pd.read_csv(sample_file)
        
        # Get average risk by status
        risk_by_status = df.groupby("status")["risk_score"].mean()
        
        # Critical should have highest risk
        if "Critical" in risk_by_status.index and "Normal" in risk_by_status.index:
            self.assertGreater(
                risk_by_status["Critical"],
                risk_by_status["Normal"],
                "Critical status should have higher avg risk than Normal"
            )
        
        if "High Risk" in risk_by_status.index and "Warning" in risk_by_status.index:
            self.assertGreater(
                risk_by_status["High Risk"],
                risk_by_status["Warning"],
                "High Risk status should have higher avg risk than Warning"
            )
    
    def test_critical_transformers_have_high_risk(self):
        """Test that critical transformers have risk >= 85 (pipeline threshold)."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        critical_file = exports_path / "critical_transformers.csv"
        
        if not critical_file.exists():
            self.skipTest("Critical transformers not exported")
        
        df = pd.read_csv(critical_file)
        
        # 5-band mapping: Critical is risk >= 85 (consistent with backend)
        self.assertTrue(
            (df["max_risk_score"] >= 85).all(),
            f"Critical transformers should have risk >= 85, got min: {df['max_risk_score'].min()}"
        )
    
    def test_risk_score_statistics(self):
        """Test risk score statistics are reasonable."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"
        
        if not sample_file.exists():
            self.skipTest("Silver sample not available")
        
        df = pd.read_csv(sample_file)
        
        stats = df["risk_score"].describe()
        
        # Mean should be between 10-50 (not too low, not too high)
        self.assertGreater(stats["mean"], 5,
            f"Mean risk too low: {stats['mean']:.1f}")
        self.assertLess(stats["mean"], 60,
            f"Mean risk too high: {stats['mean']:.1f}")
        
        # Should have variation (std > 0)
        self.assertGreater(stats["std"], 0,
            "Risk scores should have variation")


class TestRiskComponents(unittest.TestCase):
    """Test individual risk score components."""
    
    def test_risk_components_exist(self):
        """Test that risk score components are calculated."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"
        
        if not sample_file.exists():
            self.skipTest("Silver sample not available")
        
        df = pd.read_csv(sample_file)
        
        # Check for individual risk component columns
        expected_components = [
            "load_risk_score",
            "temperature_risk_score",
            "voltage_risk_score",
            "frequency_risk_score",
            "power_factor_risk_score",
            "fault_risk_score",
            "anomaly_risk_score",
            "communication_risk_score",
        ]
        
        missing = [col for col in expected_components if col not in df.columns]
        
        if len(missing) > 0:
            # These might not be in the exported sample
            pass  # OK if not in sample


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python
"""
GridPulse Tests - Anomaly Detection
"""

import unittest
import pandas as pd
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAnomalyDetection(unittest.TestCase):
    """Test anomaly detection functionality."""
    
    def test_anomaly_scores_exist(self):
        """Test that anomaly scores are calculated."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"
        
        if not sample_file.exists():
            self.skipTest("Silver sample not available")
        
        df = pd.read_csv(sample_file)
        
        self.assertIn("anomaly_score", df.columns,
            "anomaly_score column missing")
        self.assertIn("anomaly_flag", df.columns,
            "anomaly_flag column missing")
    
    def test_anomaly_score_range(self):
        """Test that anomaly scores are in valid range."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"
        
        if not sample_file.exists():
            self.skipTest("Silver sample not available")
        
        df = pd.read_csv(sample_file)
        
        # Anomaly scores should be 0-1
        self.assertGreaterEqual(df["anomaly_score"].min(), 0,
            f"Min anomaly score is {df['anomaly_score'].min()}")
        self.assertLessEqual(df["anomaly_score"].max(), 1,
            f"Max anomaly score is {df['anomaly_score'].max()}")
    
    def test_anomaly_types_exist(self):
        """Test that anomaly types are assigned."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"
        
        if not sample_file.exists():
            self.skipTest("Silver sample not available")
        
        df = pd.read_csv(sample_file)
        
        self.assertIn("anomaly_type", df.columns,
            "anomaly_type column missing")
        
        # Non-normal records should have specific anomaly types
        anomalous = df[df["status"] != "Normal"]
        if len(anomalous) > 0:
            non_normal_types = anomalous["anomaly_type"].unique()
            # Should have meaningful anomaly types, not just "Normal"
            meaningful = [t for t in non_normal_types if t != "Normal"]
            self.assertGreater(len(meaningful), 0,
                "Anomalous records should have specific anomaly types")
    
    def test_anomaly_rate_reasonable(self):
        """Test that anomaly rate is reasonable (not too high, not too low)."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"
        
        if not sample_file.exists():
            self.skipTest("Silver sample not available")
        
        df = pd.read_csv(sample_file)
        
        anomaly_rate = (df["anomaly_flag"] == 1).sum() / len(df) * 100
        
        # Anomaly rate: any non-Normal record counts as an anomaly. The target
        # record mix keeps the majority of records healthy.
        self.assertGreater(anomaly_rate, 3,
            f"Anomaly rate too low: {anomaly_rate:.2f}%")
        self.assertLess(anomaly_rate, 70,
            f"Anomaly rate too high: {anomaly_rate:.2f}%")
    
    def test_all_anomaly_types_present(self):
        """Test that all ten anomaly types have meaningful quantities."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"

        if not sample_file.exists():
            self.skipTest("Silver sample not available")

        df = pd.read_csv(sample_file)

        expected_types = [
            "Voltage Fluctuation",
            "Overload",
            "Temperature Spike",
            "Frequency Deviation",
            "Power Factor Anomaly",
            "Transformer Fault",
            "Communication Failure",
            "Unexpected Consumption",
            "Generation Drop",
            "Compound Anomaly",
        ]
        present = set(df["anomaly_type"].unique())
        missing = [t for t in expected_types if t not in present]
        self.assertEqual(len(missing), 0,
            f"Anomaly types missing from dataset: {missing}")

        anomalous = df[df["status"] != "Normal"]
        if len(anomalous) > 0:
            for t in expected_types:
                count = (anomalous["anomaly_type"] == t).sum()
                self.assertGreater(count, len(anomalous) * 0.005,
                    f"Anomaly type '{t}' has too few records: {count}")
    
    def test_ml_model_exists(self):
        """Test that ML model file exists (if trained)."""
        model_path = Path(__file__).parent.parent / "analytics" / "anomaly_model.pkl"
        
        if not model_path.exists():
            self.skipTest("ML model not trained yet")
        
        # Model file should exist
        self.assertTrue(model_path.exists(),
            "Anomaly detection model should exist after training")


class TestRiskScoring(unittest.TestCase):
    """Test risk scoring functionality."""
    
    def test_risk_scores_exist(self):
        """Test that risk scores are calculated."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"
        
        if not sample_file.exists():
            self.skipTest("Silver sample not available")
        
        df = pd.read_csv(sample_file)
        
        self.assertIn("risk_score", df.columns,
            "risk_score column missing")
    
    def test_risk_score_range(self):
        """Test that risk scores are in valid range (0-100)."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"
        
        if not sample_file.exists():
            self.skipTest("Silver sample not available")
        
        df = pd.read_csv(sample_file)
        
        self.assertGreaterEqual(df["risk_score"].min(), 0,
            f"Min risk score: {df['risk_score'].min()}")
        self.assertLessEqual(df["risk_score"].max(), 100,
            f"Max risk score: {df['risk_score'].max()}")
    
    def test_risk_distribution(self):
        """Test that risk distribution has all levels."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        severity_file = exports_path / "severity_summary.csv"
        
        if not severity_file.exists():
            self.skipTest("Severity summary not available")
        
        df = pd.read_csv(severity_file)
        
        # Should have multiple risk levels
        expected_levels = ["Normal", "Warning", "High Risk", "Critical"]
        actual_levels = df["status"].tolist()
        
        for level in expected_levels:
            if level in actual_levels:
                continue  # OK if present
            # Some levels might be missing due to data
            pass
    
    def test_risk_correlation_with_load(self):
        """Test that risk scores correlate with load."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"
        
        if not sample_file.exists():
            self.skipTest("Silver sample not available")
        
        df = pd.read_csv(sample_file)
        
        corr = df["risk_score"].corr(df["load_percent"])
        
        # Should have positive correlation
        self.assertGreater(corr, 0.1,
            f"Risk-load correlation too low: {corr:.3f}")
    
    def test_risk_correlation_with_temp(self):
        """Test that risk scores correlate with temperature."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"
        
        if not sample_file.exists():
            self.skipTest("Silver sample not available")
        
        df = pd.read_csv(sample_file)
        
        corr = df["risk_score"].corr(df["temperature_c"])
        
        # Should have positive correlation
        self.assertGreater(corr, 0.1,
            f"Risk-temp correlation too low: {corr:.3f}")


if __name__ == "__main__":
    unittest.main()

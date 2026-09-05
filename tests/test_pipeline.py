#!/usr/bin/env python
"""
GridPulse Tests - Pipeline Stages
"""

import unittest
import pandas as pd
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_generation.generate_dataset import (
    SUBSTATION_COORDS,
    REGIONS,
    generate_transformer_ids,
)


class TestBronzeLayer(unittest.TestCase):
    """Test Bronze layer ingestion."""

    def test_bronze_exists(self):
        """Test that Bronze layer data exists."""
        bronze_path = Path(__file__).parent.parent / "data" / "bronze" / "grid_bronze.csv"

        if not bronze_path.exists():
            self.skipTest("Bronze layer not created yet")

        df = pd.read_csv(bronze_path)
        self.assertGreater(len(df), 0, "Bronze CSV is empty")

    def test_bronze_record_count(self):
        """Test Bronze layer has the full 150,000 records."""
        bronze_path = Path(__file__).parent.parent / "data" / "bronze" / "grid_bronze.csv"

        if not bronze_path.exists():
            self.skipTest("Bronze layer not created yet")

        df = pd.read_csv(bronze_path)
        self.assertEqual(len(df), 150000,
            f"Bronze layer has {len(df)} records, expected 150,000")

    def test_bronze_has_metadata(self):
        """Test Bronze layer has ingestion metadata columns."""
        bronze_path = Path(__file__).parent.parent / "data" / "bronze" / "grid_bronze.csv"

        if not bronze_path.exists():
            self.skipTest("Bronze layer not created yet")

        df = pd.read_csv(bronze_path)
        self.assertIn("ingestion_time", df.columns)
        self.assertIn("ingestion_batch", df.columns)


class TestSilverLayer(unittest.TestCase):
    """Test Silver layer transformation."""

    def test_silver_exists(self):
        """Test that Silver layer data exists."""
        silver_path = Path(__file__).parent.parent / "data" / "silver" / "grid_silver.csv"

        if not silver_path.exists():
            self.skipTest("Silver layer not created yet")

        df = pd.read_csv(silver_path)
        self.assertGreater(len(df), 0, "Silver CSV is empty")

    def test_silver_record_count(self):
        """Test Silver layer has the full 150,000 records."""
        silver_path = Path(__file__).parent.parent / "data" / "silver" / "grid_silver.csv"

        if not silver_path.exists():
            self.skipTest("Silver layer not created yet")

        df = pd.read_csv(silver_path)
        self.assertEqual(len(df), 150000,
            f"Silver layer has {len(df)} records, expected 150,000")

    def test_silver_columns(self):
        """Test Silver layer has expected columns including engineered features."""
        silver_path = Path(__file__).parent.parent / "data" / "silver" / "grid_silver.csv"

        if not silver_path.exists():
            self.skipTest("Silver layer not created yet")

        df = pd.read_csv(silver_path)

        expected_columns = [
            "voltage_deviation_kv",
            "frequency_deviation_hz",
            "power_quality_score",
            "voltage_stability_score",
            "calculated_power_mw",
            "transmission_efficiency",
            "anomaly_flag",
        ]

        for col in expected_columns:
            self.assertIn(col, df.columns,
                f"Missing engineered column: {col}")

    def test_silver_full_coverage(self):
        """Test every transformer/substation/region survived transformation."""
        silver_path = Path(__file__).parent.parent / "data" / "silver" / "grid_silver.csv"

        if not silver_path.exists():
            self.skipTest("Silver layer not created yet")

        df = pd.read_csv(silver_path)

        expected_trans = set(generate_transformer_ids())
        missing = expected_trans - set(df["transformer_id"].unique())
        self.assertEqual(len(missing), 0,
            f"Transformers missing from silver: {sorted(missing)[:10]}")

        missing_subs = set(SUBSTATION_COORDS.keys()) - set(df["substation_id"].unique())
        self.assertEqual(len(missing_subs), 0,
            f"Substations missing from silver: {sorted(missing_subs)}")


class TestGoldLayer(unittest.TestCase):
    """Test Gold layer aggregation."""

    def test_gold_exists(self):
        """Test that Gold layer data exists."""
        gold_path = Path(__file__).parent.parent / "data" / "gold" / "gold_data"

        if not gold_path.exists():
            self.skipTest("Gold layer not created yet")

        files = list(gold_path.glob("*.csv"))
        self.assertGreater(len(files), 0, "No CSV files in Gold layer")

    def test_transformer_summary(self):
        """Test transformer summary exists and has correct structure."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        transformer_file = exports_path / "transformer_summary.csv"

        if not transformer_file.exists():
            self.skipTest("Transformer summary not exported yet")

        df = pd.read_csv(transformer_file)

        self.assertEqual(len(df), len(SUBSTATION_COORDS) * 20,
            f"Transformer summary has {len(df)} rows, expected "
            f"{len(SUBSTATION_COORDS) * 20} (every transformer)")

        required_cols = ["transformer_id", "substation_id", "region", "avg_risk_score", "status"]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Missing column: {col}")

    def test_region_summary(self):
        """Test region summary covers every region."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        region_file = exports_path / "region_summary.csv"

        if not region_file.exists():
            self.skipTest("Region summary not exported yet")

        df = pd.read_csv(region_file)

        self.assertEqual(set(df["region"].unique()), set(REGIONS),
            f"Region summary should cover all {len(REGIONS)} regions")

    def test_critical_transformers(self):
        """Test critical transformers export."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        critical_file = exports_path / "critical_transformers.csv"

        if not critical_file.exists():
            self.skipTest("Critical transformers not exported yet")

        df = pd.read_csv(critical_file)

        if len(df) > 0:
            self.assertIn("transformer_id", df.columns)
            self.assertIn("max_risk_score", df.columns)

            # 5-band mapping: Critical is risk >= 85 (consistent with backend)
            self.assertTrue((df["max_risk_score"] >= 85).all(),
                "Critical transformers should have risk >= 85")


class TestExports(unittest.TestCase):
    """Test data exports."""

    def test_silver_sample_exists(self):
        """Test silver sample export exists."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        sample_file = exports_path / "silver_sample.csv"

        if not sample_file.exists():
            self.skipTest("Silver sample not exported yet")

        df = pd.read_csv(sample_file)
        self.assertGreater(len(df), 10000,
            f"Silver sample has {len(df)} records, expected >= 10,000")

    def test_severity_summary(self):
        """Test severity summary export."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        severity_file = exports_path / "severity_summary.csv"

        if not severity_file.exists():
            self.skipTest("Severity summary not exported yet")

        df = pd.read_csv(severity_file)

        self.assertIn("status", df.columns)
        self.assertIn("count", df.columns)

        # Should have multiple status levels
        self.assertGreaterEqual(len(df), 2,
            "Severity summary should have at least 2 status levels")

    def test_energy_distribution_export(self):
        """Test region energy distribution export matches the dataset."""
        exports_path = Path(__file__).parent.parent / "data" / "exports"
        region_file = exports_path / "region_summary.csv"

        if not region_file.exists():
            self.skipTest("Region summary not exported yet")

        df = pd.read_csv(region_file)

        self.assertIn("total_energy_generated_mwh", df.columns)
        self.assertIn("total_energy_consumed_mwh", df.columns)
        self.assertGreater(df["total_energy_generated_mwh"].sum(), 0,
            "Total generated energy should be positive")
        self.assertGreater(df["total_energy_consumed_mwh"].sum(), 0,
            "Total consumed energy should be positive")


if __name__ == "__main__":
    unittest.main()
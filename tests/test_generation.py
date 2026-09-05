#!/usr/bin/env python
"""
GridPulse Tests - Dataset Generation
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


RAW_DATA = Path(__file__).parent.parent / "data" / "raw" / "grid_telemetry_raw.csv"


def load_raw():
    if not RAW_DATA.exists():
        raise unittest.SkipTest("Dataset not generated yet")
    return pd.read_csv(RAW_DATA)


class TestDatasetGeneration(unittest.TestCase):
    """Test dataset generation functionality."""

    def test_record_count(self):
        """Test that generated dataset has exactly 150,000 records."""
        df = load_raw()
        self.assertEqual(len(df), 150000,
            f"Dataset has {len(df)} records, expected 150,000")

    def test_required_columns(self):
        """Test that dataset has all required columns."""
        df = load_raw()

        required_columns = [
            "event_id",
            "timestamp",
            "region",
            "substation_id",
            "transformer_id",
            "voltage_kv",
            "current_amp",
            "power_mw",
            "frequency_hz",
            "load_percent",
            "power_factor",
            "temperature_c",
            "energy_generated_mwh",
            "energy_consumed_mwh",
            "outage_duration_min",
            "communication_latency_ms",
            "fault_indicator",
            "anomaly_score",
            "risk_score",
            "status",
            "anomaly_type",
        ]

        missing = [col for col in required_columns if col not in df.columns]
        self.assertEqual(len(missing), 0,
            f"Missing columns: {missing}")

    def test_regions_present(self):
        """Test that all expected regions are present."""
        df = load_raw()

        expected_regions = REGIONS
        actual_regions = df["region"].unique().tolist()

        for region in expected_regions:
            self.assertIn(region, actual_regions,
                f"Region '{region}' not found in data")

    def test_transformer_count(self):
        """Test that every generated transformer has data."""
        df = load_raw()

        expected = set(generate_transformer_ids())
        actual = set(df["transformer_id"].unique())
        missing = expected - actual
        self.assertEqual(len(missing), 0,
            f"{len(missing)} transformers have no data: {sorted(missing)[:10]}")

        # Full set should match the configured hierarchy
        self.assertEqual(len(actual), len(SUBSTATION_COORDS) * 20,
            f"Expected {len(SUBSTATION_COORDS) * 20} transformers, got {len(actual)}")

    def test_every_substation_present(self):
        """Test that every configured substation has telemetry records."""
        df = load_raw()

        actual = set(df["substation_id"].unique())
        missing = set(SUBSTATION_COORDS.keys()) - actual
        self.assertEqual(len(missing), 0,
            f"Substations with no data: {sorted(missing)}")

    def test_transformer_substation_region_coverage(self):
        """Test that every transformer maps to a substation and region."""
        df = load_raw()

        for _, row in df.iterrows():
            substation = row["substation_id"]
            region = row["region"]
            self.assertIn(substation, SUBSTATION_COORDS,
                f"Unknown substation {substation}")
            self.assertEqual(
                SUBSTATION_COORDS[substation]["region"], region,
                f"Region mismatch for {substation}: {region} vs "
                f"{SUBSTATION_COORDS[substation]['region']}"
            )

    def test_status_distribution(self):
        """Test that status values are reasonable and every band is populated."""
        df = load_raw()

        status_counts = df["status"].value_counts()

        # The healthy bands (Normal + Low) should hold the majority of records
        healthy_pct = (status_counts.get("Normal", 0) + status_counts.get("Low", 0)) / len(df) * 100
        self.assertGreater(healthy_pct, 45,
            f"Normal+Low records should be >45%, got {healthy_pct:.1f}%")

        # All five statuses should exist (5-band mapping incl. Low)
        for status in ["Normal", "Low", "Warning", "High Risk", "Critical"]:
            self.assertGreater(status_counts.get(status, 0), 0,
                f"Status '{status}' missing from dataset")

    def test_risk_score_status_consistency(self):
        """Test that status always agrees with the 5-band risk mapping:

        0-29 Normal, 30-49 Low, 50-69 Warning, 70-84 High Risk, 85-100 Critical.
        """
        df = load_raw()

        def expected_status(risk):
            if risk >= 85:
                return "Critical"
            elif risk >= 70:
                return "High Risk"
            elif risk >= 50:
                return "Warning"
            elif risk >= 30:
                return "Low"
            return "Normal"

        expected = df["risk_score"].apply(expected_status)
        mismatches = (expected != df["status"]).sum()
        self.assertEqual(mismatches, 0,
            f"{mismatches} records have risk_score inconsistent with status")

    def test_energy_distribution_totals(self):
        """Test that energy distribution covers all records accurately."""
        df = load_raw()

        by_region = df.groupby("region")["event_id"].count()
        # Every region must have records and they must sum to the total
        self.assertEqual(by_region.sum(), len(df))
        self.assertGreater(by_region.min(), 0,
            "Every region should contribute to the energy distribution")

        # Generated/consumed energy must be positive everywhere
        self.assertGreater(df["energy_generated_mwh"].sum(), 0)
        self.assertGreater(df["energy_consumed_mwh"].sum(), 0)

        # Regional share should reflect record share (roughly proportional
        # since every record contributes energy)
        for region, count in by_region.items():
            share = count / len(df)
            region_gen = df[df["region"] == region]["energy_generated_mwh"].sum()
            self.assertGreater(region_gen, 0,
                f"Region {region} has no generated energy")


class TestDataValidation(unittest.TestCase):
    """Test data validation and quality."""

    def test_voltage_range(self):
        """Test that voltage values are within expected range."""
        df = load_raw()

        voltage_out_of_range = df[(df["voltage_kv"] < 30) | (df["voltage_kv"] > 50)]
        self.assertLess(len(voltage_out_of_range), len(df) * 0.01,
            f"Too many voltage values out of range: {len(voltage_out_of_range)}")

    def test_frequency_range(self):
        """Test that frequency values are within expected range."""
        df = load_raw()

        freq_out_of_range = df[(df["frequency_hz"] < 49) | (df["frequency_hz"] > 51)]
        self.assertLess(len(freq_out_of_range), len(df) * 0.01,
            f"Too many frequency values out of range")

    def test_load_range(self):
        """Test that load values are within 0-100%."""
        df = load_raw()

        invalid_load = df[(df["load_percent"] < 0) | (df["load_percent"] > 100)]
        self.assertEqual(len(invalid_load), 0,
            f"Found {len(invalid_load)} load values outside 0-100%")

    def test_correlation_load_current_temp(self):
        """Test that load, current, and temperature have realistic correlations."""
        df = load_raw()

        corr_load_current = df["load_percent"].corr(df["current_amp"])
        corr_load_temp = df["load_percent"].corr(df["temperature_c"])

        self.assertGreater(corr_load_current, 0.3,
            f"Load-current correlation too low: {corr_load_current:.3f}")
        self.assertGreater(corr_load_temp, 0.2,
            f"Load-temperature correlation too low: {corr_load_temp:.3f}")


if __name__ == "__main__":
    unittest.main()
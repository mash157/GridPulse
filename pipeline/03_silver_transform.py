#!/usr/bin/env python
"""
GridPulse Silver Layer - Data Transformation
Removes duplicates, handles missing values, validates ranges, normalizes fields
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure project root on path and set up local JDK 17
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

LOCAL_JDK = Path(_PROJECT_ROOT) / "jdk-17.0.12"
if LOCAL_JDK.exists() and (LOCAL_JDK / "bin" / "java.exe").exists():
    os.environ["JAVA_HOME"] = str(LOCAL_JDK)
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    _bin = str(LOCAL_JDK / "bin")
    if _bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _bin + ";" + os.environ["PATH"]

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, avg, stddev, count, lit, row_number,
    round as spark_round, sqrt
)
from pyspark.sql.window import Window


def get_base_path() -> Path:
    """Get the base project path."""
    return Path(__file__).parent.parent


def transform_silver(spark: SparkSession, bronze_path: str, silver_path: str) -> int:
    """
    Transform Bronze data to Silver layer.

    Args:
        spark: SparkSession
        bronze_path: Path to Bronze Parquet data
        silver_path: Destination path for Silver data

    Returns:
        Number of records in Silver layer
    """
    print(f"\n{'='*60}")
    print("GRIDPULSE - SILVER LAYER TRANSFORMATION")
    print(f"{'='*60}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nBronze Source: {bronze_path}")
    print(f"Silver Destination: {silver_path}")

    # Read Bronze data
    print("\n[1/7] Reading Bronze data...")
    df_bronze = spark.read.parquet(bronze_path)
    bronze_count = df_bronze.count()
    print(f"  Bronze records: {bronze_count:,}")

    # Remove duplicates based on event_id
    print("\n[2/7] Removing duplicates...")
    window_spec = Window.partitionBy("event_id").orderBy(col("ingestion_time").desc())
    df_deduped = df_bronze.withColumn("rn", row_number().over(window_spec))
    df_deduped = df_deduped.filter(col("rn") == 1).drop("rn")

    duplicates_removed = bronze_count - df_deduped.count()
    print(f"  Duplicates removed: {duplicates_removed:,}")
    print(f"  Records after dedup: {df_deduped.count():,}")

    # Handle missing values
    print("\n[3/7] Handling missing values...")

    # Fill numeric columns with median values
    numeric_cols = [
        "voltage_kv", "current_amp", "power_mw", "frequency_hz",
        "load_percent", "power_factor", "temperature_c",
        "energy_generated_mwh", "energy_consumed_mwh",
        "outage_duration_min", "communication_latency_ms",
        "anomaly_score"
    ]

    for col_name in numeric_cols:
        if col_name in df_deduped.columns:
            median_val = df_deduped.agg(
                spark_round(
                    col(col_name).cast("double").approxQuantile(col_name, [0.5], 0.01)[0],
                    2
                ).alias("median")
            ).collect()[0]["median"]

            df_deduped = df_deduped.withColumn(
                col_name,
                when(col(col_name).isNull(), lit(median_val)).otherwise(col(col_name))
            )

    # Fill categorical columns
    df_deduped = df_deduped.withColumn(
        "status",
        when(col("status").isNull(), lit("Normal")).otherwise(col("status"))
    )
    df_deduped = df_deduped.withColumn(
        "anomaly_type",
        when(col("anomaly_type").isNull(), lit("Normal")).otherwise(col("anomaly_type"))
    )
    df_deduped = df_deduped.withColumn(
        "fault_indicator",
        when(col("fault_indicator").isNull(), lit(0)).otherwise(col("fault_indicator"))
    )

    print(f"  Missing values handled")

    # Validate ranges
    print("\n[4/7] Validating ranges...")

    # Voltage range: 35-45 kV
    voltage_before = df_deduped.filter(
        (col("voltage_kv") < 35) | (col("voltage_kv") > 45)
    ).count()
    df_deduped = df_deduped.withColumn(
        "voltage_kv",
        when(col("voltage_kv") < 35, lit(35.0))
        .when(col("voltage_kv") > 45, lit(45.0))
        .otherwise(col("voltage_kv"))
    )
    if voltage_before > 0:
        print(f"  Voltage clipped: {voltage_before} records")

    # Frequency range: 49.5-50.5 Hz
    freq_before = df_deduped.filter(
        (col("frequency_hz") < 49.5) | (col("frequency_hz") > 50.5)
    ).count()
    df_deduped = df_deduped.withColumn(
        "frequency_hz",
        when(col("frequency_hz") < 49.5, lit(49.5))
        .when(col("frequency_hz") > 50.5, lit(50.5))
        .otherwise(col("frequency_hz"))
    )
    if freq_before > 0:
        print(f"  Frequency clipped: {freq_before} records")

    # Load percent: 0-100%
    load_before = df_deduped.filter(
        (col("load_percent") < 0) | (col("load_percent") > 100)
    ).count()
    df_deduped = df_deduped.withColumn(
        "load_percent",
        when(col("load_percent") < 0, lit(0.0))
        .when(col("load_percent") > 100, lit(100.0))
        .otherwise(col("load_percent"))
    )
    if load_before > 0:
        print(f"  Load percent clipped: {load_before} records")

    # Power factor: 0.6-1.0
    pf_before = df_deduped.filter(
        (col("power_factor") < 0.6) | (col("power_factor") > 1.0)
    ).count()
    df_deduped = df_deduped.withColumn(
        "power_factor",
        when(col("power_factor") < 0.6, lit(0.6))
        .when(col("power_factor") > 1.0, lit(1.0))
        .otherwise(col("power_factor"))
    )
    if pf_before > 0:
        print(f"  Power factor clipped: {pf_before} records")

    # Temperature: 35-85°C
    temp_before = df_deduped.filter(
        (col("temperature_c") < 35) | (col("temperature_c") > 85)
    ).count()
    df_deduped = df_deduped.withColumn(
        "temperature_c",
        when(col("temperature_c") < 35, lit(35.0))
        .when(col("temperature_c") > 85, lit(85.0))
        .otherwise(col("temperature_c"))
    )
    if temp_before > 0:
        print(f"  Temperature clipped: {temp_before} records")

    print(f"  Range validation: COMPLETED")

    # Feature engineering - calculate derived fields
    print("\n[5/7] Feature engineering...")

    # Voltage deviation from nominal (40kV)
    df_silver = df_deduped.withColumn(
        "voltage_deviation_kv",
        spark_round(col("voltage_kv") - lit(40.0), 2)
    )

    # Frequency deviation from nominal (50Hz)
    df_silver = df_silver.withColumn(
        "frequency_deviation_hz",
        spark_round(col("frequency_hz") - lit(50.0), 3)
    )

    # Power quality score (based on power factor)
    df_silver = df_silver.withColumn(
        "power_quality_score",
        spark_round(
            (col("power_factor") - lit(0.6)) / lit(0.4) * lit(100),
            1
        )
    )

    # Efficiency score (based on voltage stability)
    df_silver = df_silver.withColumn(
        "voltage_stability_score",
        spark_round(
            lit(100) - abs(col("voltage_deviation_kv")) * lit(5),
            1
        )
    )

    # Calculate actual power from V, I, PF (for verification)
    df_silver = df_silver.withColumn(
        "calculated_power_mw",
        spark_round(
            col("voltage_kv") * col("current_amp") * col("power_factor") / lit(1000),
            2
        )
    )

    # Transmission efficiency (generated vs consumed)
    df_silver = df_silver.withColumn(
        "transmission_efficiency",
        spark_round(
            when(col("energy_consumed_mwh") > 0,
                 col("energy_generated_mwh") / col("energy_consumed_mwh") * lit(100))
            .otherwise(lit(100)),
            1
        )
    )

    print(f"  Features engineered: voltage_deviation, frequency_deviation, power_quality, efficiency")

    # Normalize fields (Z-score normalization for key metrics)
    print("\n[6/7] Normalizing fields...")

    # Calculate Z-scores for key metrics
    for metric in ["load_percent", "temperature_c", "power_mw"]:
        mean_val = df_silver.agg(avg(col(metric))).collect()[0][0]
        std_val = df_silver.agg(stddev(col(metric))).collect()[0][0]

        if std_val and std_val > 0:
            z_col = f"{metric}_zscore"
            df_silver = df_silver.withColumn(
                z_col,
                spark_round(
                    (col(metric) - lit(mean_val)) / lit(std_val),
                    3
                )
            )

    print(f"  Z-scores calculated for load_percent, temperature_c, power_mw")

    # Add transformation metadata
    print("\n[7/7] Adding metadata...")
    df_silver = df_silver.withColumn("transformation_time", lit(datetime.now().isoformat()))
    df_silver = df_silver.withColumn("silver_version", lit("1.0"))

    # Select final columns
    final_columns = [
        "event_id", "timestamp", "region", "substation_id", "transformer_id",
        "latitude", "longitude", "voltage_kv", "current_amp", "power_mw",
        "frequency_hz", "load_percent", "power_factor", "temperature_c",
        "energy_generated_mwh", "energy_consumed_mwh", "outage_duration_min",
        "communication_latency_ms", "fault_indicator", "anomaly_score",
        "risk_score", "status", "anomaly_type",
        "voltage_deviation_kv", "frequency_deviation_hz",
        "power_quality_score", "voltage_stability_score",
        "calculated_power_mw", "transmission_efficiency",
        "load_percent_zscore", "temperature_c_zscore", "power_mw_zscore",
        "transformation_time", "silver_version"
    ]

    df_silver = df_silver.select([c for c in final_columns if c in df_silver.columns])

    # Write to Silver layer
    print("\nWriting to Silver layer...")
    df_silver.write.mode("overwrite").parquet(silver_path)

    silver_count = df_silver.count()
    print(f"  Silver records written: {silver_count:,}")

    # Verify
    df_verify = spark.read.parquet(silver_path)
    print(f"  Verification count: {df_verify.count():,}")

    print(f"\n{'='*60}")
    print("SILVER TRANSFORMATION COMPLETE")
    print(f"{'='*60}")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Bronze Records: {bronze_count:,}")
    print(f"Silver Records: {silver_count:,}")
    print(f"Output: {silver_path}")

    return silver_count


def main():
    """Main execution function."""
    base_path = get_base_path()

    # Define paths
    bronze_path = os.path.join(base_path, "data", "bronze", "grid_bronze")
    silver_path = os.path.join(base_path, "data", "silver", "grid_silver")

    # Check if Bronze exists
    if not os.path.exists(bronze_path):
        print(f"\nERROR: Bronze data not found at {bronze_path}")
        print("Please run 01_bronze_batch_ingest.py first.")
        sys.exit(1)

    # Create Spark session
    spark = (
        SparkSession.builder
        .appName("GridPulse-Silver")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )

    try:
        record_count = transform_silver(spark, bronze_path, silver_path)
        print(f"\n✓ Silver layer transformation successful: {record_count:,} records")
    except Exception as e:
        print(f"\n✗ Silver layer transformation failed: {str(e)}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

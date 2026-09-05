#!/usr/bin/env python
"""
GridPulse Bronze Layer - Batch Ingestion
Ingests raw data, validates schema, converts timestamps
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

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, lit
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    IntegerType, TimestampType, FloatType
)


def get_base_path() -> Path:
    """Get the base project path."""
    return Path(__file__).parent.parent


def get_bronze_schema() -> StructType:
    """Define the Bronze layer schema."""
    return StructType([
        StructField("event_id", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("region", StringType(), True),
        StructField("substation_id", StringType(), True),
        StructField("transformer_id", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("voltage_kv", DoubleType(), True),
        StructField("current_amp", DoubleType(), True),
        StructField("power_mw", DoubleType(), True),
        StructField("frequency_hz", DoubleType(), True),
        StructField("load_percent", DoubleType(), True),
        StructField("power_factor", DoubleType(), True),
        StructField("temperature_c", DoubleType(), True),
        StructField("energy_generated_mwh", DoubleType(), True),
        StructField("energy_consumed_mwh", DoubleType(), True),
        StructField("outage_duration_min", DoubleType(), True),
        StructField("communication_latency_ms", DoubleType(), True),
        StructField("fault_indicator", IntegerType(), True),
        StructField("anomaly_score", DoubleType(), True),
        StructField("risk_score", IntegerType(), True),
        StructField("status", StringType(), True),
        StructField("anomaly_type", StringType(), True),
    ])


def validate_schema(df, schema: StructType) -> bool:
    """Validate that the dataframe matches the expected schema."""
    expected_fields = {field.name for field in schema.fields}
    actual_fields = set(df.columns)

    missing = expected_fields - actual_fields
    extra = actual_fields - expected_fields

    if missing:
        print(f"WARNING: Missing fields: {missing}")
        return False

    if extra:
        print(f"INFO: Extra fields found (will be ignored): {extra}")

    return True


def ingest_bronze(spark: SparkSession, raw_path: str, bronze_path: str) -> int:
    """
    Ingest raw data into Bronze layer.

    Args:
        spark: SparkSession
        raw_path: Path to raw CSV data
        bronze_path: Destination path for Bronze data

    Returns:
        Number of records ingested
    """
    print(f"\n{'='*60}")
    print("GRIDPULSE - BRONZE LAYER INGESTION")
    print(f"{'='*60}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nRaw Data Source: {raw_path}")
    print(f"Bronze Destination: {bronze_path}")

    # Check if raw data exists
    if not os.path.exists(raw_path):
        print(f"\nERROR: Raw data not found at {raw_path}")
        print("Please run data_generation first.")
        sys.exit(1)

    # Read raw data with schema validation
    print("\n[1/4] Reading raw data...")
    df_raw = spark.read.csv(raw_path, header=True, inferSchema=True)

    record_count = df_raw.count()
    print(f"  Raw records loaded: {record_count:,}")

    # Validate schema
    print("\n[2/4] Validating schema...")
    schema = get_bronze_schema()
    if validate_schema(df_raw, schema):
        print("  Schema validation: PASSED")
    else:
        print("  Schema validation: Completed with warnings")

    # Convert timestamp column
    print("\n[3/4] Converting timestamps...")
    df_bronze = df_raw.withColumn(
        "timestamp",
        to_timestamp(col("timestamp"), "yyyy-%m-%d %H:%M:%S.%f")
    )

    # Add ingestion metadata
    df_bronze = df_bronze.withColumn("ingestion_time", lit(datetime.now().isoformat()))
    df_bronze = df_bronze.withColumn("ingestion_batch", lit("batch_001"))

    print(f"  Timestamp conversion: COMPLETED")

    # Write to Bronze layer (Parquet format)
    print("\n[4/4] Writing to Bronze layer...")
    df_bronze.write.mode("overwrite").parquet(bronze_path)

    bronze_count = df_bronze.count()
    print(f"  Bronze records written: {bronze_count:,}")

    # Verify write
    df_verify = spark.read.parquet(bronze_path)
    print(f"  Verification count: {df_verify.count():,}")

    print(f"\n{'='*60}")
    print("BRONZE INGESTION COMPLETE")
    print(f"{'='*60}")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Records: {bronze_count:,}")
    print(f"Output: {bronze_path}")

    return bronze_count


def main():
    """Main execution function."""
    base_path = get_base_path()

    # Define paths
    raw_path = os.path.join(base_path, "data", "raw", "grid_telemetry_raw.csv")
    bronze_path = os.path.join(base_path, "data", "bronze", "grid_bronze")

    # Create Spark session
    spark = (
        SparkSession.builder
        .appName("GridPulse-Bronze")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )

    try:
        record_count = ingest_bronze(spark, raw_path, bronze_path)
        print(f"\n✓ Bronze layer ingestion successful: {record_count:,} records")
    except Exception as e:
        print(f"\n✗ Bronze layer ingestion failed: {str(e)}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

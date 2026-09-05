#!/usr/bin/env python
"""
GridPulse Gold Layer - Data Aggregation
Creates transformer, substation, region, hourly, daily, and anomaly summaries
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
        os.environ["PATH"] = _bin + ";" + os.environ.get("PATH", "")

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, sum as spark_sum, avg, max as spark_max, min as spark_min,
    count, countDistinct, round as spark_round, lit, hour, date,
    to_date, window, when
)
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType


def get_base_path() -> Path:
    """Get the base project path."""
    return Path(__file__).parent.parent


def aggregate_gold(spark, silver_path, gold_path, exports_path):
    """Aggregate Silver data to Gold layer."""
    print(f"\n{'='*60}")
    print("GRIDPULSE - GOLD LAYER AGGREGATION")
    print(f"{'='*60}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nSilver Source: {silver_path}")
    print(f"Gold Destination: {gold_path}")
    print(f"Exports Path: {exports_path}")

    # Read Silver data
    print("\n[1/8] Reading Silver data...")
    df_silver = spark.read.parquet(silver_path)
    silver_count = df_silver.count()
    print(f"  Silver records: {silver_count:,}")

    stats = {
        "silver_records": silver_count,
        "transformer_summary": 0,
        "substation_summary": 0,
        "region_summary": 0,
        "hourly_summary": 0,
        "daily_summary": 0,
        "anomaly_summary": 0,
        "severity_summary": 0,
        "critical_summary": 0,
    }

    # 1. Transformer Summary
    print("\n[2/8] Creating transformer summary...")
    transformer_summary = (
        df_silver.groupBy("transformer_id", "substation_id", "region")
        .agg(
            spark_sum("power_mw").alias("total_power_mw"),
            spark_round(avg("voltage_kv"), 2).alias("avg_voltage_kv"),
            spark_round(avg("current_amp"), 2).alias("avg_current_amp"),
            spark_round(avg("power_mw"), 2).alias("avg_power_mw"),
            spark_round(avg("frequency_hz"), 2).alias("avg_frequency_hz"),
            spark_round(avg("load_percent"), 2).alias("avg_load_percent"),
            spark_round(avg("power_factor"), 4).alias("avg_power_factor"),
            spark_round(avg("temperature_c"), 2).alias("avg_temperature_c"),
            spark_round(max("temperature_c"), 2).alias("max_temperature_c"),
            spark_round(avg("energy_generated_mwh"), 2).alias("total_energy_generated_mwh"),
            spark_round(avg("energy_consumed_mwh"), 2).alias("total_energy_consumed_mwh"),
            spark_round(avg("communication_latency_ms"), 2).alias("avg_latency_ms"),
            spark_sum("fault_indicator").alias("total_faults"),
            spark_max("risk_score").alias("max_risk_score"),
            spark_round(avg("risk_score"), 1).alias("avg_risk_score"),
            count("*").alias("record_count"),
            spark_max("status").alias("worst_status"),
        )
        .orderBy(col("avg_risk_score").desc())
    )
    transformer_count = transformer_summary.count()
    stats["transformer_summary"] = transformer_count
    print(f"  Transformers summarized: {transformer_count:,}")

    # 2. Substation Summary
    print("\n[3/8] Creating substation summary...")
    substation_summary = (
        df_silver.groupBy("substation_id", "region")
        .agg(
            spark_sum("power_mw").alias("total_power_mw"),
            spark_round(avg("voltage_kv"), 2).alias("avg_voltage_kv"),
            spark_round(avg("load_percent"), 2).alias("avg_load_percent"),
            spark_round(avg("temperature_c"), 2).alias("avg_temperature_c"),
            spark_round(avg("power_factor"), 4).alias("avg_power_factor"),
            spark_round(avg("energy_generated_mwh"), 2).alias("total_energy_generated_mwh"),
            spark_round(avg("energy_consumed_mwh"), 2).alias("total_energy_consumed_mwh"),
            spark_sum("fault_indicator").alias("total_faults"),
            countDistinct("transformer_id").alias("transformer_count"),
            spark_max("risk_score").alias("max_risk_score"),
            spark_round(avg("risk_score"), 1).alias("avg_risk_score"),
            count("*").alias("record_count"),
        )
        .orderBy(col("avg_risk_score").desc())
    )
    substation_count = substation_summary.count()
    stats["substation_summary"] = substation_count
    print(f"  Substations summarized: {substation_count}")

    # 3. Region Summary
    print("\n[4/8] Creating region summary...")
    region_summary = (
        df_silver.groupBy("region")
        .agg(
            spark_sum("power_mw").alias("total_power_mw"),
            spark_round(avg("voltage_kv"), 2).alias("avg_voltage_kv"),
            spark_round(avg("load_percent"), 2).alias("avg_load_percent"),
            spark_round(avg("temperature_c"), 2).alias("avg_temperature_c"),
            spark_round(avg("power_factor"), 4).alias("avg_power_factor"),
            spark_round(avg("energy_generated_mwh"), 2).alias("total_energy_generated_mwh"),
            spark_round(avg("energy_consumed_mwh"), 2).alias("total_energy_consumed_mwh"),
            spark_sum("fault_indicator").alias("total_faults"),
            countDistinct("transformer_id").alias("transformer_count"),
            countDistinct("substation_id").alias("substation_count"),
            spark_max("risk_score").alias("max_risk_score"),
            spark_round(avg("risk_score"), 1).alias("avg_risk_score"),
            count("*").alias("record_count"),
        )
        .orderBy(col("total_power_mw").desc())
    )
    region_count = region_summary.count()
    stats["region_summary"] = region_count
    print(f"  Regions summarized: {region_count}")

    # 4. Hourly Summary
    print("\n[5/8] Creating hourly summary...")
    hourly_summary = (
        df_silver.withColumn("hour_of_day", hour(col("timestamp")))
        .groupBy("hour_of_day")
        .agg(
            spark_sum("power_mw").alias("total_power_mw"),
            spark_round(avg("load_percent"), 2).alias("avg_load_percent"),
            spark_round(avg("temperature_c"), 2).alias("avg_temperature_c"),
            spark_round(avg("energy_generated_mwh"), 2).alias("avg_energy_generated_mwh"),
            spark_round(avg("energy_consumed_mwh"), 2).alias("avg_energy_consumed_mwh"),
            spark_sum("fault_indicator").alias("total_faults"),
            count("*").alias("record_count"),
            spark_round(avg("risk_score"), 1).alias("avg_risk_score"),
        )
        .orderBy("hour_of_day")
    )
    hourly_count = hourly_summary.count()
    stats["hourly_summary"] = hourly_count
    print(f"  Hourly summaries: {hourly_count}")

    # 5. Daily Summary
    print("\n[6/8] Creating daily summary...")
    daily_summary = (
        df_silver.withColumn("date", to_date(col("timestamp")))
        .groupBy("date")
        .agg(
            spark_sum("power_mw").alias("total_power_mw"),
            spark_round(avg("load_percent"), 2).alias("avg_load_percent"),
            spark_round(avg("temperature_c"), 2).alias("avg_temperature_c"),
            spark_round(spark_sum("energy_generated_mwh"), 2).alias("total_energy_generated_mwh"),
            spark_round(spark_sum("energy_consumed_mwh"), 2).alias("total_energy_consumed_mwh"),
            spark_sum("fault_indicator").alias("total_faults"),
            count("*").alias("record_count"),
            spark_round(avg("risk_score"), 1).alias("avg_risk_score"),
        )
        .orderBy("date")
    )
    daily_count = daily_summary.count()
    stats["daily_summary"] = daily_count
    print(f"  Daily summaries: {daily_count}")

    # 6. Anomaly Summary
    print("\n[7/8] Creating anomaly summary...")
    anomaly_summary = (
        df_silver.filter(col("status") != "Normal")
        .groupBy("anomaly_type", "status")
        .agg(
            count("*").alias("anomaly_count"),
            spark_round(avg("risk_score"), 1).alias("avg_risk_score"),
            spark_round(avg("load_percent"), 2).alias("avg_load_percent"),
            spark_round(avg("temperature_c"), 2).alias("avg_temperature_c"),
            spark_round(avg("voltage_kv"), 2).alias("avg_voltage_kv"),
        )
        .orderBy(col("anomaly_count").desc())
    )
    anomaly_count = anomaly_summary.count()
    stats["anomaly_summary"] = anomaly_count
    print(f"  Anomaly types: {anomaly_count}")

    # 7. Severity Summary
    print("\n[8/8] Creating severity summary...")
    severity_summary = (
        df_silver.groupBy("status")
        .agg(
            count("*").alias("count"),
            spark_round(avg("risk_score"), 1).alias("avg_risk_score"),
            spark_round(avg("load_percent"), 2).alias("avg_load_percent"),
            spark_round(avg("temperature_c"), 2).alias("avg_temperature_c"),
        )
        .orderBy(
            when(col("status") == "Critical", lit(1))
            .when(col("status") == "High Risk", lit(2))
            .when(col("status") == "Warning", lit(3))
            .when(col("status") == "Normal", lit(4))
            .otherwise(lit(5))
        )
    )
    severity_count = severity_summary.count()
    stats["severity_summary"] = severity_count
    print(f"  Severity levels: {severity_count}")

    # Critical Transformers
    print("\n[bonus] Creating critical transformer summary...")
    critical_summary = (
        df_silver.filter(col("risk_score") >= 85)
        .groupBy("transformer_id", "substation_id", "region")
        .agg(
            spark_round(avg("load_percent"), 2).alias("avg_load_percent"),
            spark_round(avg("temperature_c"), 2).alias("avg_temperature_c"),
            spark_round(avg("voltage_kv"), 2).alias("avg_voltage_kv"),
            spark_round(avg("power_factor"), 4).alias("avg_power_factor"),
            spark_round(avg("risk_score"), 1).alias("avg_risk_score"),
            spark_max("risk_score").alias("max_risk_score"),
            countDistinct("anomaly_type").alias("distinct_anomaly_types"),
            spark_sum("fault_indicator").alias("total_faults"),
        )
        .orderBy(col("max_risk_score").desc())
    )
    critical_count = critical_summary.count()
    stats["critical_summary"] = critical_count
    print(f"  Critical transformers: {critical_count}")

    # Write Gold data
    print(f"\n{'='*60}")
    print("WRITING GOLD DATA")
    print(f"{'='*60}")

    gold_output = os.path.join(gold_path, "gold_data")
    os.makedirs(gold_output, exist_ok=True)

    transformer_summary.write.mode("overwrite").parquet(os.path.join(gold_output, "transformer_summary"))
    substation_summary.write.mode("overwrite").parquet(os.path.join(gold_output, "substation_summary"))
    region_summary.write.mode("overwrite").parquet(os.path.join(gold_output, "region_summary"))
    hourly_summary.write.mode("overwrite").parquet(os.path.join(gold_output, "hourly_summary"))
    daily_summary.write.mode("overwrite").parquet(os.path.join(gold_output, "daily_summary"))
    anomaly_summary.write.mode("overwrite").parquet(os.path.join(gold_output, "anomaly_summary"))
    severity_summary.write.mode("overwrite").parquet(os.path.join(gold_output, "severity_summary"))
    critical_summary.write.mode("overwrite").parquet(os.path.join(gold_output, "critical_transformers"))

    # Export to CSV
    print(f"\n{'='*60}")
    print("EXPORTING TO CSV")
    print(f"{'='*60}")

    os.makedirs(exports_path, exist_ok=True)

    transformer_summary.toPandas().to_csv(os.path.join(exports_path, "transformer_summary.csv"), index=False)
    print(f"  transformer_summary.csv  ({transformer_count:,} rows)")

    substation_summary.toPandas().to_csv(os.path.join(exports_path, "substation_summary.csv"), index=False)
    print(f"  substation_summary.csv   ({substation_count:,} rows)")

    region_summary.toPandas().to_csv(os.path.join(exports_path, "region_summary.csv"), index=False)
    print(f"  region_summary.csv       ({region_count:,} rows)")

    hourly_summary.toPandas().to_csv(os.path.join(exports_path, "hourly_summary.csv"), index=False)
    print(f"  hourly_summary.csv       ({hourly_count:,} rows)")

    daily_summary.toPandas().to_csv(os.path.join(exports_path, "daily_summary.csv"), index=False)
    print(f"  daily_summary.csv        ({daily_count:,} rows)")

    anomaly_summary.toPandas().to_csv(os.path.join(exports_path, "anomaly_summary.csv"), index=False)
    print(f"  anomaly_summary.csv      ({anomaly_count:,} rows)")

    severity_summary.toPandas().to_csv(os.path.join(exports_path, "severity_summary.csv"), index=False)
    print(f"  severity_summary.csv     ({severity_count:,} rows)")

    critical_summary.toPandas().to_csv(os.path.join(exports_path, "critical_transformers.csv"), index=False)
    print(f"  critical_transformers.csv ({critical_count:,} rows)")

    # Silver sample for dashboard API
    print(f"\n  Exporting sample data for dashboard...")
    silver_sample = df_silver.orderBy(col("timestamp").desc()).limit(50000).toPandas()
    silver_sample.to_csv(os.path.join(exports_path, "silver_sample.csv"), index=False)
    print(f"  silver_sample.csv        ({len(silver_sample):,} rows)")

    print(f"\n{'='*60}")
    print("GOLD AGGREGATION COMPLETE")
    print(f"{'='*60}")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return stats


def main():
    """Main execution function."""
    base_path = get_base_path()

    silver_path = os.path.join(base_path, "data", "silver", "grid_silver")
    gold_path = os.path.join(base_path, "data", "gold")
    exports_path = os.path.join(base_path, "data", "exports")

    if not os.path.exists(silver_path):
        print(f"\nERROR: Silver data not found at {silver_path}")
        print("Please run 03_silver_transform.py first.")
        sys.exit(1)

    spark = (
        SparkSession.builder
        .appName("GridPulse-Gold")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )

    try:
        stats = aggregate_gold(spark, silver_path, gold_path, exports_path)
        print(f"\n✓ Gold aggregation complete!")
        print(f"\nSummary:")
        for key, value in stats.items():
            print(f"  {key}: {value:,}")
    except Exception as e:
        print(f"\n✗ Gold aggregation failed: {str(e)}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

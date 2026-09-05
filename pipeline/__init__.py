#!/usr/bin/env python
"""
GridPulse Pipeline — shared configuration.
Auto-detects Oracle JDK 17 in the project folder and sets JAVA_HOME.
"""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Try to find local JDK 17
LOCAL_JDK = PROJECT_ROOT / "jdk-17.0.12"
if LOCAL_JDK.exists() and (LOCAL_JDK / "bin" / "java.exe").exists():
    os.environ["JAVA_HOME"] = str(LOCAL_JDK)
    bin_dir = str(LOCAL_JDK / "bin")
    if bin_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = bin_dir + ";" + os.environ.get("PATH", "")
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    print(f"[pipeline] Using local JDK 17: {LOCAL_JDK}")


def create_spark_session(app_name: str = "GridPulse"):
    """Create Spark session using local JDK 17."""
    from pyspark.sql import SparkSession
    return (
        SparkSession.builder
        .appName(app_name)
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "2g")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.python.worker.reuse", "true")
        .getOrCreate()
    )

"""
RetailMart Analytics Platform - Master Pipeline Runner
==========================================================
Runs the core Bronze -> Silver -> Gold pipeline end-to-end
(the PySpark and Delta Lake jobs are run separately -- see README.md --
since they need a JDK and, for Delta, internet access to Maven Central).

Run:
    python run_pipeline.py
"""

import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("Generating synthetic raw data", "src/generate_data.py"),
    ("Bronze: raw ingestion", "src/bronze/ingest_bronze.py"),
    ("Silver: cleaning & standardization", "src/silver/clean_silver.py"),
    ("Gold: SQL business aggregates (DuckDB)", "src/gold/build_gold.py"),
]


def run_step(label, script):
    print("\n" + "=" * 70)
    print(f"STEP: {label}")
    print("=" * 70)
    result = subprocess.run([sys.executable, os.path.join(BASE_DIR, script)])
    if result.returncode != 0:
        print(f"\n[FAILED] {label} (exit code {result.returncode})")
        sys.exit(result.returncode)


def main():
    for label, script in STEPS:
        run_step(label, script)

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print("""
Core pipeline finished. Gold-layer CSVs are in data/gold/

Optional next steps (run manually - need extra setup):
  python src/delta/scd2_pandas_demo.py       # SCD2 logic demo (no Spark needed)
  python src/spark/revenue_at_scale.py       # needs: pip install pyspark
  python src/delta/scd2_product_catalog.py   # needs: pip install pyspark delta-spark
                                              #        + internet access (Maven Central)
""")


if __name__ == "__main__":
    main()

#!/bin/bash
# ======================================
# Auto start SparkSession + JupyterLab
# Compatible: macOS / Linux
# ======================================

source ~/anaconda3/bin/activate spark_env

export PYSPARK_PYTHON=$(which python)
export PYSPARK_DRIVER_PYTHON=jupyter
export PYSPARK_DRIVER_PYTHON_OPTS="lab"

echo "Using JAVA_HOME=${JAVA_HOME}"
echo "Starting PySpark + JupyterLab..."

pyspark --master local[*]
echo "PySpark + JupyterLab session ended."
# --- IGNORE ---
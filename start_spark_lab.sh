#!/bin/bash
# ===================================================================
# Start Spark Lab (macOS / Linux)
# ===================================================================

# Exit on errors
set -e

echo "=== Activating Conda environment: spark_env ==="
# Detect conda base
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate spark_env

# ===================================================================
# Set environment variables
# ===================================================================
export JAVA_HOME="/Users/$(whoami)/WorkSpace/Java/jdk-23.0.2"   # chỉnh path nếu khác
export SPARK_HOME="/Users/$(whoami)/WorkSpace/Python/spark-4.0.1-bin-hadoop3"
export HADOOP_HOME="$SPARK_HOME"
export PATH="$JAVA_HOME/bin:$SPARK_HOME/bin:$HADOOP_HOME/bin:$PATH"

echo "JAVA_HOME=$JAVA_HOME"
echo "SPARK_HOME=$SPARK_HOME"
echo "HADOOP_HOME=$HADOOP_HOME"

# ===================================================================
# Start Docker containers
# ===================================================================
echo "=== Starting Airflow container ==="
docker-compose -f "$(pwd)/spark-airflow-demo/docker-compose.yml" up -d

echo "=== Starting Atlas container ==="
if ! docker ps -a --format '{{.Names}}' | grep -q '^atlas$'; then
    docker run -d -p 21000:21000 --name atlas local/atlas:2.3.0
else
    docker start atlas || true
fi

echo "=== Starting Ranger container ==="
if ! docker ps -a --format '{{.Names}}' | grep -q '^ranger$'; then
    docker run -d -p 6080:6080 --name ranger local/ranger:2.3.0
else
    docker start ranger || true
fi

# ===================================================================
# Start Jupyter Lab
# ===================================================================
echo "=== Starting Jupyter Lab ==="
jupyter lab

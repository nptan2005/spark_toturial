@echo off
REM ==============================================
REM Start SparkSession + JupyterLab (Windows)
REM ==============================================

CALL conda activate spark_env

@echo off
echo === Starting Spark Environment ===
call conda activate spark_env

echo Starting Docker containers...
docker-compose -f spark-airflow-demo\docker-compose.yml up -d
docker start atlas || docker run -d -p 21000:21000 --name atlas local/atlas:2.3.0
docker start ranger || docker run -d -p 6080:6080 --name ranger local/ranger:2.3.0

echo Starting Jupyter Notebook...
jupyter lab
echo Jupyter Notebook started.
echo Starting PySpark Shell...
pyspark --master local[*]

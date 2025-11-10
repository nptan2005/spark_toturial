@echo off
REM ==============================================
REM Start SparkSession + JupyterLab (Windows)
REM ==============================================

CALL conda activate spark_env

SET JAVA_HOME=%CONDA_PREFIX%
SET PATH=%JAVA_HOME%\bin;%PATH%
SET PYSPARK_PYTHON=%CONDA_PREFIX%\python.exe
SET PYSPARK_DRIVER_PYTHON=jupyter
SET PYSPARK_DRIVER_PYTHON_OPTS="lab"

echo JAVA_HOME=%JAVA_HOME%
echo Starting Spark 4.0.1 with Python 3.10...

pyspark --master local[*]

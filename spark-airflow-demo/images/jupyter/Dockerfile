# FROM jupyter/pyspark-notebook:latest
FROM local/spark:3.5.1-full

USER root

# Cài Python + Jupyter + pyspark client
RUN apt-get update && apt-get install -y python3 python3-pip && \
    pip3 install --no-cache-dir jupyterlab findspark pyspark==3.5.1

# Set biến môi trường chuẩn
ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$PATH
ENV PYSPARK_PYTHON=python3
ENV PYTHONPATH=$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.10.9.7-src.zip

# Tạo workspace
RUN mkdir -p /workspace && chown -R 185:185 /workspace
WORKDIR /workspace

# Jupyter config
EXPOSE 8888

USER 185
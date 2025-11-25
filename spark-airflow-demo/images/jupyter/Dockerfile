# Base từ Spark đã có Python 3.12
FROM local/spark:3.5.1-full

USER root

# -------------------------------------------------
# Install minimal deps for Jupyter
# (python3.12 đã được build trong image spark rồi)
# -------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-distutils \
    python3-apt \
    curl \
    wget \
    git && \
    rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# Jupyter + PySpark + libs (cài vào python3.12)
# -------------------------------------------------
RUN python3.12 -m pip install --no-cache-dir \
    jupyterlab \
    findspark \
    pyspark==3.5.1 \
    pandas \
    numpy \
    pyarrow

# -------------------------------------------------
# Spark env
# -------------------------------------------------
ENV SPARK_HOME=/opt/spark
ENV PATH="$SPARK_HOME/bin:$PATH"

# Force Spark dùng Python 3.12
ENV PYSPARK_PYTHON=/usr/local/bin/python3.12
ENV PYSPARK_DRIVER_PYTHON=/usr/local/bin/python3.12

# py4j version auto-detect
ENV PYTHONPATH="$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j*.zip"

# Tạo thư mục config riêng
RUN mkdir -p /home/jovyan/conf

# Copy Spark config
# COPY jars/*.jar /opt/spark/jars/
COPY conf/spark-defaults.conf /home/jovyan/conf/spark-defaults.conf
RUN chown -R 185:185 /home/jovyan/conf

# -------------------------------------------------
# Workspace
# -------------------------------------------------
RUN mkdir -p /workspace && chown -R 185:185 /workspace
WORKDIR /workspace

EXPOSE 8888

USER 185
ENV SPARK_CONF_DIR=/home/jovyan/conf
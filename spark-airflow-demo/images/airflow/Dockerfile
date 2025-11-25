# -------------------------------------------------
# Stage 1 – Spark 3.5.1 (Python 3.12)
# -------------------------------------------------
FROM local/spark:3.5.1-full AS spark-dist

# -------------------------------------------------
# Stage 2 – Airflow base (Python 3.12)
# -------------------------------------------------
FROM apache/airflow:2.10.5-python3.12

USER root

# -------------------------------------------------
# Copy Spark từ stage 1
# -------------------------------------------------
COPY --from=spark-dist /opt/spark /opt/spark
RUN chown -R airflow:root /opt/spark

ENV SPARK_HOME=/opt/spark
ENV PATH="/opt/spark/bin:${PATH}"

# -------------------------------------------------
# Install Java 17 + system libs (ARM64 auto-detect)
# -------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk \
    libaio1 libpq-dev build-essential gcc g++ make unzip procps \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# -------------------------------------------------
# Oracle Instant Client (ARM64)
# -------------------------------------------------
COPY instantclient/*.zip /tmp/
RUN unzip /tmp/*.zip -d /opt/oracle && rm /tmp/*.zip

# EXACT path based on your tree
ENV ORACLE_HOME=/opt/oracle/instantclient-basic-linux.arm64-23.26.0.0.0/instantclient_23_26
ENV LD_LIBRARY_PATH="$ORACLE_HOME:$LD_LIBRARY_PATH"

# -------------------------------------------------
# Python dependencies
# -------------------------------------------------
USER airflow
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt && \
    pip install --no-cache-dir \
    cx_Oracle \
    pyspark==3.5.1 \
    pyarrow \
    pandas \
    numpy

RUN pip install --no-cache-dir \
    apache-airflow-providers-openlineage==1.8.0 \
    openlineage-python==1.27.0


# -------------------------------------------------
# Spark dùng Python 3.12
# -------------------------------------------------
USER root
RUN which python3 && ln -sf "$(which python3)" /usr/local/bin/python3.12 || true
ENV PYSPARK_PYTHON=/usr/local/bin/python3.12
ENV PYSPARK_DRIVER_PYTHON=/usr/local/bin/python3.12

# ENV PYTHONPATH="$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j*.zip"
ENV PYTHONPATH="/opt/airflow:$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j*.zip"

# -------------------------------------------------
# OpenTelemetry Java Agent
# -------------------------------------------------
RUN mkdir -p /opt/otel && \
    curl -L \
    -o /opt/otel/opentelemetry-javaagent.jar \
    https://repo1.maven.org/maven2/io/opentelemetry/javaagent/opentelemetry-javaagent/2.4.0/opentelemetry-javaagent-2.4.0.jar && \
    chmod 644 /opt/otel/opentelemetry-javaagent.jar

# -------------------------------------------------
# Switch về airflow user
# -------------------------------------------------
USER airflow
WORKDIR /opt/airflow

ENV PATH="${SPARK_HOME}/bin:${JAVA_HOME}/bin:${PATH}"
# ENV AIRFLOW__LINEAGE__BACKEND=openlineage.airflow.backend.OpenLineageBackend
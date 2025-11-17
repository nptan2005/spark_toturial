# Stage 1: Lấy Spark distribution chuẩn (đã build sẵn)
FROM local/spark:3.5.1-full AS spark-dist

# Stage 2: Airflow base image
FROM apache/airflow:2.10.5-python3.12

USER root

# Copy Spark từ stage 1 vào đúng chỗ
COPY --from=spark-dist /opt/spark /opt/spark

# Thiết lập biến môi trường Spark
ENV SPARK_HOME=/opt/spark
ENV PATH=/opt/spark/bin:/home/airflow/.local/bin:/usr/local/bin:/usr/bin:/bin

# Fix permission cho airflow user nếu cần
RUN chown -R airflow:root /opt/spark

RUN apt-get update && apt-get install -y --no-install-recommends \
    libaio1 libpq-dev gcc g++ make unzip procps openjdk-17-jdk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Oracle client
COPY instantclient/*.zip /tmp/
RUN unzip /tmp/*.zip -d /opt/oracle && rm /tmp/*.zip

ENV ORACLE_HOME=/opt/oracle/instantclient*
ENV LD_LIBRARY_PATH=$ORACLE_HOME:$LD_LIBRARY_PATH

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Symlink python
RUN ln -s /usr/local/bin/python3 /usr/local/bin/python || true

# install python packages

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
RUN pip install --no-cache-dir cx_Oracle pyspark==3.5.1 pyarrow pandas numpy

USER airflow

ENV PATH="/home/airflow/.local/bin:${PATH}"

WORKDIR /opt/airflow
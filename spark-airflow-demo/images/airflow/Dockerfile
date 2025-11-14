# --------------------------------------------------------------------
# AIRFLOW BASE IMAGE
# --------------------------------------------------------------------
FROM apache/airflow:2.10.5-python3.12

USER root

# --------------------------------------------------------------------
# System packages (gọn, đủ dùng)
# --------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl unzip ca-certificates libaio1 \
    build-essential gcc g++ make \
    libpq-dev libssl-dev default-libmysqlclient-dev \
    zsh git fonts-powerline \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------------------------
# ORACLE INSTANT CLIENT (ARM64 COMPATIBLE)
# --------------------------------------------------------------------
# Bạn phải tải đúng ARM64:
# https://download.oracle.com/otn_software/linux/instantclient/219000/instantclient-basiclite-linux.arm64-21.9.0.0.0.zip

COPY instantclient/*.zip /tmp/ic.zip

RUN unzip /tmp/ic.zip -d /opt/oracle && \
    rm /tmp/ic.zip

ENV ORACLE_HOME=/opt/oracle/instantclient_23_6
ENV LD_LIBRARY_PATH=$ORACLE_HOME:$LD_LIBRARY_PATH

# --------------------------------------------------------------------
# Install Python dependencies
# --------------------------------------------------------------------
COPY requirements.txt /requirements.txt

# Chuyển sang user airflow để cài pip theo khuyến cáo
USER airflow

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /requirements.txt && \
    pip install --no-cache-dir cx_Oracle

# --------------------------------------------------------------------
# Install PySpark for SparkSubmitOperator
# --------------------------------------------------------------------
RUN pip install --no-cache-dir pyspark==3.5.1 pyarrow numpy pandas


# Tạo đường dẫn ~/.local/bin vào PATH (nếu image không đã làm)
ENV PATH=/home/airflow/.local/bin:$PATH


# --------------------------------------------------------------------
# Optional: ZSH + STARSHIP (cho đẹp)
# --------------------------------------------------------------------
USER root
RUN curl -fsSL https://starship.rs/install.sh -o /tmp/starship.sh && \
    sh /tmp/starship.sh -y && \
    rm /tmp/starship.sh

COPY configs/zshrc /etc/zsh/zshrc
COPY configs/starship.toml /etc/starship.toml
ENV SHELL=/bin/zsh

# --------------------------------------------------------------------
# Prepare scripts & Airflow home
# --------------------------------------------------------------------
USER root
COPY scripts/ /opt/airflow/scripts/
RUN chmod +x /opt/airflow/scripts/* || true

RUN chown -R airflow: /opt/airflow

USER airflow
WORKDIR /opt/airflow
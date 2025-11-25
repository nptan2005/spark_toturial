FROM apache/spark:3.5.1-python3

USER root

# -------------------------------------------------
# Install system packages
# -------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget curl unzip ca-certificates procps git zsh \
    libxml2 libxslt1-dev locales fonts-powerline \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# Install OpenJDK 17
# -------------------------------------------------
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# -------------------------------------------------
# Build Python 3.12 from source 
# -------------------------------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    libssl-dev \
    zlib1g-dev \
    libncurses5-dev \
    libnss3-dev \
    libreadline-dev \
    libffi-dev \
    libsqlite3-dev \
    libbz2-dev

RUN cd /tmp && \
    wget https://www.python.org/ftp/python/3.12.1/Python-3.12.1.tgz && \
    tar -xf Python-3.12.1.tgz && \
    cd Python-3.12.1 && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && \
    make altinstall

# Symlink python3.12 globally
RUN ln -sf /usr/local/bin/python3.12 /usr/bin/python3.12 && \
    ln -sf /usr/local/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/local/bin/python3.12 /usr/bin/python

# Install pip for Python 3.12
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# Force Spark to use Python 3.12
ENV PYSPARK_PYTHON=/usr/local/bin/python3.12
ENV PYSPARK_DRIVER_PYTHON=/usr/local/bin/python3.12
ENV PATH="/opt/spark/bin:/usr/local/bin:${PATH}"

# -------------------------------------------------
# THÊM BƯỚC CÀI ĐẶT MAVEN TẠI ĐÂY
# -------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends maven && \
    rm -rf /var/lib/apt/lists/*



# RUN mkdir -p /opt/otel
# COPY opentelemetry_jar/*.jar /opt/otel/

# -------------------------------------------------
# OpenTelemetry Java Agent
# -------------------------------------------------
RUN mkdir -p /opt/otel && \
    curl -L \
    -o /opt/otel/opentelemetry-javaagent.jar \
    https://repo1.maven.org/maven2/io/opentelemetry/javaagent/opentelemetry-javaagent/2.4.0/opentelemetry-javaagent-2.4.0.jar && \
    chmod 644 /opt/otel/opentelemetry-javaagent.jar

# RUN curl -L -o /opt/spark/jars/jackson-databind-2.16.1.jar \
#     "https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-databind/2.16.1/jackson-databind-2.16.1.jar"

# Xóa Maven sau khi dùng để giữ image gọn nhẹ (nếu muốn)
# RUN rm -rf /tmp/atlas-deps
RUN apt-get purge -y maven && apt-get autoremove -y && rm -rf /root/.m2

# -------------------------------------------------
# UTF-8 locale
# -------------------------------------------------
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# -------------------------------------------------
# Python dependencies
# -------------------------------------------------
RUN python3.12 -m pip install --no-cache-dir \
    pandas numpy pyarrow fastparquet kafka-python



# -------------------------------------------------
# JDBC + Kafka Jars
# -------------------------------------------------
COPY jars/*.jar /opt/spark/jars/
ENV SPARK_CLASSPATH="/opt/spark/jars/*"

# -------------------------------------------------
# Log4j2 configs
# -------------------------------------------------
COPY configs/log4j2.properties /opt/spark/conf/log4j2.properties
COPY configs/log4j2.xml        /opt/spark/conf/log4j2.xml

# -------------------------------------------------
# Spark Metrics Configs
# -------------------------------------------------
COPY configs/metrics.properties /opt/spark/conf/metrics.properties
COPY configs/spark-defaults.conf /opt/spark/conf/spark-defaults.conf

# -------------------------------------------------
# Spark History Server
# -------------------------------------------------
RUN mkdir -p /opt/spark/history && \
    chown -R 185:185 /opt/spark/history
ENV SPARK_HISTORY_OPTS="-Dspark.history.fs.logDirectory=/opt/spark/history \
    -Dspark.history.ui.port=18080"

# -------------------------------------------------
# ZSH + Starship
# -------------------------------------------------
RUN curl -fsSL https://starship.rs/install.sh -o /tmp/starship.sh && \
    sh /tmp/starship.sh -y && \
    rm /tmp/starship.sh

RUN mkdir -p /home/spark/.config && \
    chown -R 185:185 /home/spark

COPY configs/starship.toml /home/spark/.config/starship.toml
COPY configs/zshrc         /home/spark/.zshrc

RUN chown -R 185:185 /home/spark

ENV HOME=/home/spark
ENV SHELL=/bin/zsh

COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

# Drop privileges
USER 185
WORKDIR /home/spark
ENTRYPOINT ["/opt/entrypoint.sh"]
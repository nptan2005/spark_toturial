FROM apache/spark:3.5.1-python3

USER root

# -------------------------------------------------
# System packages
# -------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget curl unzip ca-certificates procps git zsh \
    libxml2 libxslt1-dev locales fonts-powerline \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# Install OpenJDK 17 (upgrade from default Java 11)
# -------------------------------------------------
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# -------------------------------------------------
# UTF-8 locale
# -------------------------------------------------
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# -------------------------------------------------
# Install Python dependencies
# (auto-select compatible versions)
# -------------------------------------------------
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    pyarrow \
    fastparquet \
    kafka-python

# -------------------------------------------------
# JDBC + Kafka jars
# -------------------------------------------------
COPY jars/*.jar /opt/spark/jars/
ENV SPARK_CLASSPATH="/opt/spark/jars/*"

# -------------------------------------------------
# Log4j2 configs
# -------------------------------------------------
COPY configs/log4j2.properties /opt/spark/conf/log4j2.properties
COPY configs/log4j2.xml        /opt/spark/conf/log4j2.xml

# -------------------------------------------------
# Spark History Server
# -------------------------------------------------
RUN mkdir -p /opt/spark/history && \
    chown -R 185:185 /opt/spark/history
ENV SPARK_HISTORY_OPTS="-Dspark.history.fs.logDirectory=/opt/spark/history \
    -Dspark.history.ui.port=18080"

# -------------------------------------------------
# Setup ZSH + Starship
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
# -------------------------------------------------
# Drop privileges
# -------------------------------------------------
USER 185
WORKDIR /home/spark
ENTRYPOINT ["/opt/entrypoint.sh"]
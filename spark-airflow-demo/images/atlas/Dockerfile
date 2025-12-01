FROM eclipse-temurin:17-jdk

USER root
WORKDIR /opt/atlas

# Install tools
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    net-tools procps curl wget unzip jq dos2unix vim \
    && rm -rf /var/lib/apt/lists/*

# Copy Atlas binary
COPY apache-atlas-2.3.0 /opt/atlas

# Fix permissions ONLY IF folder exists
RUN if [ -d "/opt/atlas/bin" ]; then chmod +x /opt/atlas/bin/*; fi

# Copy JDBC driver
RUN mkdir -p /opt/atlas/server/webapp/WEB-INF/lib
COPY postgresql-42.7.7.jar /opt/atlas/server/webapp/WEB-INF/lib/postgresql.jar

ENV ATLAS_HOME=/opt/atlas
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=$JAVA_HOME/bin:$PATH

EXPOSE 21000

CMD ["/opt/atlas/bin/atlas_start.py"]
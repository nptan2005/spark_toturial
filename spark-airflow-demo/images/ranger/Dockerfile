FROM eclipse-temurin:11-jdk

USER root
WORKDIR /opt/ranger

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    net-tools procps curl wget unzip zip \
    jq dos2unix vim \
    && rm -rf /var/lib/apt/lists/*

# Copy extracted Ranger source distribution
COPY apache-ranger-2.3.0 /opt/ranger

# Fix permissions for all scripts
RUN find /opt/ranger -name "*.sh" -exec chmod +x {} \;

# Correct location for PostgreSQL JDBC driver
COPY postgresql-42.7.7.jar /opt/ranger/admin/ews/webapp/WEB-INF/lib/postgresql.jar

# JAVA_HOME (correct path for Temurin)
ENV JAVA_HOME=/usr/lib/jvm/temurin-11-jdk
ENV PATH=$JAVA_HOME/bin:$PATH

# Create Ranger DB for PostgreSQL
RUN python3 /opt/ranger/admin/db/postgres/createdb.py \
    -h postgres \
    -u ranger \
    -p ranger123 \
    -d ranger \
    || true

EXPOSE 6080

# Correct start script for Ranger Admin
CMD ["/opt/ranger/admin/ews/ranger-admin-services.sh"]
# Dockerfile for Apache Atlas (cross-platform)
FROM eclipse-temurin:11-jdk
WORKDIR /opt/atlas

# Copy Atlas binaries vào container
COPY apache-atlas-2.3.0 /opt/atlas

EXPOSE 21000

CMD ["./bin/atlas_start.sh"]
# Dockerfile: Ranger 2.3.0 binary (cross-platform)
FROM eclipse-temurin:11-jdk
WORKDIR /opt/ranger

# Copy Ranger binary vào container
COPY apache-ranger-2.3.0 /opt/ranger
COPY postgresql-42.7.7.jar /usr/share/java/postgresql.jar

# Expose Ranger Admin port
EXPOSE 6080

# Start Ranger Admin khi container run
CMD ["./bin/ranger-admin-start.sh"]
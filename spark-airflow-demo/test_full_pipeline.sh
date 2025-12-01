#!/bin/bash

echo "=== CHECK SPARK MASTER ==="
curl -I http://localhost:8080

echo "=== CHECK SPARK WORKER ==="
curl -I http://localhost:8081

echo "=== CHECK KAFKA BROKER ==="
docker exec -i kafka nc -z localhost 29092 && echo "Kafka OK"

echo "=== PRODUCE MESSAGE ==="
echo "hello $(date)" | docker exec -i kafka /opt/kafka/bin/kafka-console-producer.sh \
  --broker-list localhost:29092 \
  --topic test-topic

echo "=== CONSUME MESSAGE ==="
docker exec -i kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:29092 \
  --topic test-topic \
  --from-beginning \
  --max-messages 1

echo "=== TEST SPARK JOB ==="
docker exec -i spark-master \
  /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  /opt/spark/jobs/sample_job.py

echo "=== CHECK MINIO ==="
curl -I http://localhost:9000/minio/health/ready

echo "=== CHECK LOKI LOG ROUTING ==="
curl -I http://localhost:3100/ready

echo "=== CHECK GRAFANA ==="
curl -I http://localhost:3000
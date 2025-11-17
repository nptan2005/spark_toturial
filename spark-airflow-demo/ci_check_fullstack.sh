#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker-compose.yml"
NETWORK="spark-net"

echo "1) Start up (detached) selected services..."
docker compose -f ${COMPOSE_FILE} up -d zookeeper kafka postgres prometheus loki promtail grafana jupyterlab spark-master spark-worker minio redis

echo
echo "2) Wait for containers to be running (30s loop, max 120s)..."
RETRIES=20
for i in $(seq 1 $RETRIES); do
  RUNNING=$(docker compose -f ${COMPOSE_FILE} ps --services --filter "status=running" | wc -l)
  TOTAL=$(docker compose -f ${COMPOSE_FILE} ps --services | wc -l)
  echo "   Attempt $i - running services: $RUNNING / $TOTAL"
  if [ "$RUNNING" -ge 6 ]; then
    break
  fi
  sleep 6
done

echo
echo "3) Show docker compose ps summary:"
docker compose -f ${COMPOSE_FILE} ps

echo
echo "4) Quick health checks (curl endpoints). Results (HTTP code / text):"
check_url() {
  local url=$1
  local name=$2
  if curl -sS -m 5 -o /dev/null -w "%{http_code}" "$url" >/tmp/curlcode 2>/dev/null; then
    CODE=$(cat /tmp/curlcode)
    echo "   $name -> $url  HTTP:$CODE"
  else
    echo "   $name -> $url  (no response)"
  fi
}
check_url "http://localhost:8080" "Spark Master UI"
check_url "http://localhost:8081" "Spark Worker UI"
check_url "http://localhost:3000" "Grafana"
check_url "http://localhost:3100/ready" "Loki"
check_url "http://localhost:9090" "Prometheus"
check_url "http://localhost:9000/minio/health/ready" "MinIO"

echo
echo "5) Check logs briefly (last 30 lines) for core services:"
for svc in spark-master kafka zookeeper loki promtail grafana prometheus; do
  echo "---- ${svc} ----"
  docker compose -f ${COMPOSE_FILE} logs --tail 30 $svc || true
done

echo
echo "6) Kafka smoke test: create topic and produce/consume one message"
# create topic if kafka supports it; using kafka container cli if exists
docker exec -i kafka bash -c 'echo "test-message-$(date +%s)" | /opt/kafka/bin/kafka-console-producer.sh --broker-list localhost:29092 --topic ci_test_topic' || echo "producer command failed (maybe cli not present)"

echo "Consume last message (10s max):"
docker exec -i kafka bash -c '/opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:29092 --topic ci_test_topic --from-beginning --max-messages 1' || echo "consumer failed (maybe cli not present)"

echo
echo "7) Spark smoke test: run simple wordcount job from mounted jobs folder"
# ensure test file exists: ../spark/jobs/pyspark_wordcount.py on host
if docker exec -it spark-master test -f /opt/spark/jobs/pyspark_wordcount.py >/dev/null 2>&1; then
  echo " Running spark-submit..."
  docker exec -i spark-master bash -c "/opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/spark/jobs/pyspark_wordcount.py" || echo "spark-submit failed"
else
  echo " No pyspark job found at /opt/spark/jobs/pyspark_wordcount.py - create it and re-run."
fi

echo
echo "8) Airflow health (if running):"
docker compose -f ${COMPOSE_FILE} ps | grep airflow || true
check_url "http://localhost:8082/health" "Airflow Webserver (port 8082)"

echo
echo "9) Grafana: ensure Loki datasource (via API). Will attempt create (idempotent)."
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="admin"
DS_PAYLOAD='{"name":"loki-local","type":"loki","access":"proxy","url":"http://loki:3100","isDefault":true}'
curl -s -S -u ${GRAFANA_USER}:${GRAFANA_PASS} -H "Content-Type: application/json" -X POST ${GRAFANA_URL}/api/datasources -d "$DS_PAYLOAD" || echo "(create-datasource maybe already exists)"

echo
echo "10) Summary - running containers:"
docker ps --filter "name=$(basename $(pwd))" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

echo
echo "DONE. If any step failed, check detailed logs with 'docker compose logs -f <service>'."
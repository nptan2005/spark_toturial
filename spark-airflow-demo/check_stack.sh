#!/usr/bin/env bash
set -euo pipefail

echo "1) Build & up (attach logs separated)..."
docker compose up -d --build

echo
echo "2) Show compose ps:"
docker compose ps

echo
echo "3) Show local images (quick):"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}"

echo
echo "4) Quick endpoint checks (curl return code shown):"
check() {
  url=$1; name=$2
  echo -n "  - $name: $url -> "
  if curl -sSf --max-time 5 "$url" >/dev/null 2>&1; then
    echo "OK"
  else
    echo "FAILED"
  fi
}

check "http://localhost:8080" "Spark Master UI (may redirect)"
check "http://localhost:8081" "Spark Worker UI"
check "http://localhost:8888" "JupyterLab"
check "http://localhost:8082/health" "Airflow Webserver health"
check "http://localhost:9000/minio/health/ready" "MinIO"
check "http://localhost:9090" "Prometheus"
check "http://localhost:3000" "Grafana"
check "http://localhost:3100/ready" "Loki"
check "http://localhost:8085/realms/master" "Keycloak realm (may take time)"

echo
echo "5) Tail logs for problematic containers (spark-master, keycloak, zookeeper):"
echo "  - spark-master logs (last 200 lines):"
docker compose logs --no-color --tail=200 spark-master || true
echo
echo "  - keycloak logs (last 200 lines):"
docker compose logs --no-color --tail=200 keycloak || true
echo
echo "  - zookeeper logs (last 200 lines):"
docker compose logs --no-color --tail=200 zookeeper || true

echo
echo "6) Quick Spark submit smoke test (run inside jupyter image):"
echo "   This will run a small pyspark job to count numbers (non-blocking)."
# docker compose exec -T jupyterlab bash -lc "
# python3 - <<'PY'
# from pyspark.sql import SparkSession
# spark = SparkSession.builder.master('spark://spark-master:7077').appName('smoke-test').getOrCreate()
# df = spark.range(0, 1000)
# print('count=', df.count())
# spark.stop()
# PY
# " || echo "spark submit test failed (check logs)"

docker compose exec jupyterlab bash -c "
/opt/spark/bin/spark-submit --master spark://spark-master:7077 /workspace/tests/jupyter_test.py
" || echo "spark submit test failed (check logs)"

echo
echo "7) Summary docker stats (no-stream, short):"
docker stats --no-stream --no-trunc | sed -n '1,20p' || true

echo
echo "If any service FAILED above, check its logs with: docker compose logs -f <service>"
echo "To stop everything: docker compose down -v"
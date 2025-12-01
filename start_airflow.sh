#!/bin/bash
# -------------------------------
# 🧠 Script khởi động Airflow Webserver + Scheduler
# -------------------------------

AIRFLOW_HOME="$HOME/WorkSpace/Python/spark-airflow-demo"
PORT=8080

echo "🚀 Starting Airflow environment at: $AIRFLOW_HOME"

# Kích hoạt environment nếu cần
source /opt/homebrew/anaconda3/bin/activate spark_env

# Kiểm tra và khởi tạo DB nếu chưa có
if [ ! -f "$AIRFLOW_HOME/airflow.db" ]; then
  echo "🗄 Initializing Airflow database..."
  airflow db migrate
fi

# Kiểm tra port 8080 có bị chiếm không
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
  echo "⚠️ Port $PORT is already in use. Kill old process first."
  exit 1
fi

# Chạy webserver và scheduler trong background
echo "🌐 Starting Airflow webserver on port $PORT..."
airflow webserver -p $PORT > "$AIRFLOW_HOME/log_webserver.txt" 2>&1 &

echo "⏰ Starting Airflow scheduler..."
airflow scheduler > "$AIRFLOW_HOME/log_scheduler.txt" 2>&1 &

echo "✅ Airflow started successfully!"
echo "   🌍 Web UI: http://localhost:$PORT"
echo "   🧾 Logs: $AIRFLOW_HOME/log_webserver.txt , log_scheduler.txt"

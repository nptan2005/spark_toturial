#!/bin/bash
echo "🛑 Stopping Airflow..."
pkill -f "airflow webserver"
pkill -f "airflow scheduler"
sleep 1
echo "✅ Airflow stopped."

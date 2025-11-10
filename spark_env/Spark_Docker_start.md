# 🐳 Docker + Spark + Airflow: Hướng dẫn tổng hợp
## 1️⃣ Quản lý Docker
Start / Stop containers

```bash
# Start tất cả service trong docker-compose
docker compose up -d

# Stop tất cả service
docker compose down

# Restart service
docker compose restart <service_name>

# Start 1 service riêng lẻ
docker compose up -d <service_name>

# Stop 1 service riêng lẻ
docker compose stop <service_name>
```

Kiểm tra trạng thái

```bash
# Xem trạng thái tất cả containers
docker compose ps

# Xem logs của container
docker compose logs -f <service_name>

# Xem logs của tất cả containers
docker compose logs -f
```

Quản lý image & container

```bash
# Liệt kê image đã pull
docker images

# Pull 1 image mới
docker pull <image_name>

# Remove container
docker rm <container_name>

# Remove image
docker rmi <image_name>
```

## 2️⃣ Truy cập các service

| Service             | URL / Command                                             | Port |
| ------------------- | --------------------------------------------------------- | ---- |
| **Spark Master UI** | [http://localhost:8080](http://localhost:8080)            | 8080 |
| **Spark Worker UI** | [http://localhost:8081](http://localhost:8081)            | 8081 |
| **JupyterLab**      | [http://localhost:8888](http://localhost:8888)            | 8888 |
| **Airflow Web UI**  | [http://localhost:8082](http://localhost:8082)            | 8082 |
| **Kafka (cli)**     | `docker exec -it kafka /bin/bash` → `kafka-topics.sh ...` | 9092 |
| **ZooKeeper (cli)** | `docker exec -it zookeeper /bin/bash` → `zkCli.sh`        | 2181 |
| **MinIO Console**   | [http://localhost:9001](http://localhost:9001)            | 9001 |
| **Postgres (cli)**  | `docker exec -it postgres psql -U airflow -d airflow`     | 5432 |

* 🔹 Lưu ý: nếu dùng Windows, bạn cần đảm bảo các cổng chưa bị chiếm trước đó.

## 3️⃣ Demo flow Spark + Airflow

## A. Spark + PySpark trong JupyterLab

1. Truy cập: http://localhost:8888

2. Trong notebook:

```python
import pyspark
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("DemoSpark") \
    .master("spark://spark-master:7077") \
    .getOrCreate()

# Tạo DataFrame demo
data = [("Alice", 30), ("Bob", 25)]
columns = ["name", "age"]
df = spark.createDataFrame(data, columns)

df.show()

```

3. Kiểm tra job trên Spark UI → http://localhost:8080

## B. Airflow DAG demo

1. Truy cập: http://localhost:8082

2. Tạo DAG dags/demo_spark_dag.py:

```python
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

def demo_task():
    print("Hello Airflow + Spark!")

with DAG("demo_spark_dag",
         start_date=datetime(2025, 1, 1),
         schedule_interval=None,
         catchup=False) as dag:

    t1 = PythonOperator(
        task_id="hello_spark",
        python_callable=demo_task
    )
```

3. Trigger DAG → xem log → kiểm tra output Hello Airflow + Spark!

## C. Kafka + Spark Streaming:

```python
from pyspark.sql import SparkSession
from pyspark.sql.types import StringType

spark = SparkSession.builder \
    .appName("KafkaDemo") \
    .master("spark://spark-master:7077") \
    .getOrCreate()

df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "test-topic") \
    .load()

df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)").writeStream \
    .format("console") \
    .start() \
    .awaitTermination()
```

## 4️⃣ Bonus: chạy Spark + Airflow ngoài Docker

Nếu muốn chạy trên Conda:

## A. Spark:

```bash
conda activate spark_env
export JAVA_HOME=<path_to_java>
export PATH=$JAVA_HOME/bin:$PATH

# Start Spark Master
$SPARK_HOME/sbin/start-master.sh
# Start Spark Worker
$SPARK_HOME/sbin/start-worker.sh spark://localhost:7077
```

## B. Jupyter + PySpark

```bash
export PYSPARK_PYTHON=python
jupyter lab
```

## C. Airflow

```bash
# Init DB
airflow db init

# Start scheduler & webserver
airflow scheduler &
airflow webserver -p 8082

```

* 🔹 Lợi ích: không cần Docker, có thể debug trực tiếp, dùng Python + pip.
* 🔹 Hạn chế: phải cài đủ Java, Spark, Hadoop, Postgres, Kafka thủ công.

# ✅ Tổng kết

Docker giúp bạn chạy đầy đủ stack Spark + Hadoop + Kafka + Airflow + MinIO + Postgres chỉ bằng 1 câu lệnh.

JupyterLab + PySpark cho dev/test notebook nhanh.

Airflow quản lý task & DAG workflow.

Ngoài Docker, Conda + native install giúp debug & develop trực tiếp.


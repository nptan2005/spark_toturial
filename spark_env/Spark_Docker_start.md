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


# Docker kiểm tra:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

full

```bash
docker compose ps
```
# Docker cleanup
## 🔥 1️⃣ Xoá toàn bộ log của container (tự động giảm file JSON log)

Docker log nằm ở:
```
/var/lib/docker/containers/<container-id>/<container-id>-json.log
```
Lệnh dọn:
```bash
docker ps -aq | xargs -I {} sh -c 'truncate -s 0 /var/lib/docker/containers/{}/{}-json.log 2>/dev/null'
```
### ⚠️ Note:
Trên macOS, đường dẫn thực tế nằm trong VM, nhưng Docker Desktop hỗ trợ truncate qua CLI.

* ✔ Log sẽ trở về 0 byte
* ✔ Container không restart
* ✔ Không mất dữ liệu volume

## 🔥 2️⃣ Xóa container đã dừng:

```bash
docker container prune -f
```

## 🔥 3️⃣ Xóa image không dùng (dangling + orphan)

```bash
docker image prune -a -f
```
Nếu muốn xem trước khi xoá:
```bash
docker image prune -a
```
## 🔥 4️⃣ Xoá network rác (docker-compose up/down nhiều sẽ sinh ra)
```bash
docker network prune -f
```
## 🔥 5️⃣ Xoá volume rác (không còn gắn vào container nào)

```bash
docker volume prune -f
```
>⚠️ Lưu ý: volume prune chỉ xoá volume không sử dụng → an toàn.

## 🔥 6️⃣ Xoá toàn bộ build cache (rất nặng, 2–20GB)
```bash
docker builder prune -a -f
```
## 🔥 7️⃣ Xóa mọi thứ không dùng (CLEAN FULL)
```bash
docker system prune -a --volumes -f
```
>### ⚠️ Cẩn trọng:
>*	Xoá tất cả container STOPPED
>*	Xoá mọi image không được container nào dùng
>*	Xoá network rác
>*	Xoá build cache
>*	Xoá volume không dùng
>> Nhưng sẽ không xoá volume đang mount cho project.

## 🔥 8️⃣ Kiểm tra dung lượng Docker sau khi dọn
```bash
docker system df
```
chạy lệnh này trước → để xem cái gì đang chiếm dung lượng:

output ví dụ:
```
> docker system df
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          21        21        18.51GB   3.829GB (20%)
Containers      26        18        597.5MB   99.27MB (16%)
Local Volumes   50        7         390.2MB   321.5MB (82%)
Build Cache     55        0         2.936GB   2.936GB
```
## 🔥 9️⃣ Docker Desktop GUI cũng có nút dọn cache
Settings → Troubleshoot → Clean/Purge Data
Nhưng CLI chính xác hơn và tuỳ chỉnh được.
## ⭐ Gợi ý dọn dẹp

Vì Project đang build rất nhiều docker image big-size (Spark, Airflow, Keycloak, Ranger, Atlas, Prometheus, Loki…), nên khuyên chạy:

Gói dọn tiêu chuẩn nên dùng hằng ngày:
```bash
docker system prune -f
docker builder prune -f
docker volume prune -f
```
Gói dọn toàn bộ (1 tuần/lần)
```bash
docker system prune -a --volumes -f
```


# ✅ Tổng kết

Docker giúp bạn chạy đầy đủ stack Spark + Hadoop + Kafka + Airflow + MinIO + Postgres chỉ bằng 1 câu lệnh.

JupyterLab + PySpark cho dev/test notebook nhanh.

Airflow quản lý task & DAG workflow.

Ngoài Docker, Conda + native install giúp debug & develop trực tiếp.


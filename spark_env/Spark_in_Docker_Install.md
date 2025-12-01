# 🧱 I. Docker Compose hoàn chỉnh (docker-compose.yml)

```yaml
version: "3.9"

services:
  # ------------------- SPARK -------------------
  spark-master:
    image: bde2020/spark-master:3.3.0-hadoop3.3
    container_name: spark-master
    ports:
      - "8080:8080"
      - "7077:7077"
    environment:
      - SPARK_MODE=master
      - SPARK_PUBLIC_DNS=spark-master
    networks:
      - spark-net

  spark-worker:
    image: bde2020/spark-worker:3.3.0-hadoop3.3
    container_name: spark-worker
    depends_on:
      - spark-master
    environment:
      - SPARK_MASTER=spark://spark-master:7077
    ports:
      - "8081:8081"
    networks:
      - spark-net

  # ------------------- KAFKA -------------------
  zookeeper:
    image: bitnami/zookeeper:3.8
    container_name: zookeeper
    environment:
      - ALLOW_ANONYMOUS_LOGIN=yes
    ports:
      - "2181:2181"
    networks:
      - spark-net

  kafka:
    image: wurstmeister/kafka:2.13-2.8.1
    container_name: kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    networks:
      - spark-net

  # ------------------- MINIO (Data Lake) -------------------
  minio:
    image: minio/minio
    container_name: minio
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=admin
      - MINIO_ROOT_PASSWORD=admin123
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - ./data/minio:/data
    networks:
      - spark-net

  # ------------------- POSTGRES (Metadata / Airflow DB) -------------------
  postgres:
    image: postgres:13
    container_name: postgres
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    networks:
      - spark-net

  # ------------------- AIRFLOW -------------------
  airflow:
    image: apache/airflow:2.10.5-python3.12
    container_name: airflow
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
      - AIRFLOW__CORE__FERNET_KEY=C1Cg8QaV6rUzSZlQ9OCAFHVv-IWMBQuSvnfcMfnuEAg=
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
      - AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=True
    ports:
      - "8082:8080"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
    depends_on:
      - postgres
    networks:
      - spark-net

  # ------------------- JUPYTER -------------------
  jupyterlab:
    image: jupyter/pyspark-notebook:latest
    container_name: jupyterlab
    ports:
      - "8888:8888"
    volumes:
      - ./data:/home/jovyan/data
    environment:
      - SPARK_MASTER=spark://spark-master:7077
      - PYSPARK_PYTHON=python3
    networks:
      - spark-net

networks:
  spark-net:
    driver: bridge

```

## Cách chạy:

```bash
# Khởi động toàn bộ stack
docker compose up -d

# Xem log
docker compose logs -f airflow
docker compose logs -f spark-master

# Dừng toàn bộ
docker compose down

```

## Access:

| Service      | URL                                            | Ghi chú                   |
| ------------ | ---------------------------------------------- | ------------------------- |
| Spark Master | [http://localhost:8080](http://localhost:8080) | UI cluster Spark          |
| Spark Worker | [http://localhost:8081](http://localhost:8081) | Worker UI                 |
| JupyterLab   | [http://localhost:8888](http://localhost:8888) | Notebook dev              |
| Airflow      | [http://localhost:8082](http://localhost:8082) | UI quản lý DAG            |
| MinIO        | [http://localhost:9001](http://localhost:9001) | Giao diện quản lý file S3 |
| Kafka        | localhost:9092                                 | Dùng producer/consumer    |
| Postgres     | localhost:5432                                 | Database metadata         |

## Gợi ý DAG mẫu Airflow để chạy Spark Job:

```python
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime

with DAG(
    dag_id="spark_wordcount_demo",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:

    wordcount = SparkSubmitOperator(
        task_id="run_wordcount",
        application="/opt/airflow/dags/jobs/wordcount.py",
        conn_id="spark_default",
        executor_memory="2g",
        driver_memory="2g",
        verbose=True,
    )

```

# 🚀 II. Hướng dẫn khởi động môi trường
## 1️⃣ Tạo cấu trúc thư mục
```bash
mkdir -p spark_env/{data,notebooks,postgres_data,minio_data}
cd spark_env
```

Sao chép file docker-compose.yml vào thư mục này.

## 2️⃣ Khởi động toàn bộ cluster
```bash
docker compose up -d
```

⏱️ Quá trình khởi động mất khoảng 1–2 phút cho lần đầu (tải image).

## 3️⃣ Kiểm tra trạng thái container
```bash
docker ps
```

Bạn sẽ thấy danh sách container đang chạy:

| Container    | Purpose             | Port                  |
| ------------ | ------------------- | --------------------- |
| spark-master | Spark Master Web UI | 8080                  |
| spark-worker | Spark Worker Web UI | 8081                  |
| jupyterlab   | JupyterLab Notebook | 8888                  |
| kafka        | Message Broker      | 9092                  |
| zookeeper    | Kafka dependency    | 2181                  |
| postgres     | Metadata / ETL      | 5432                  |
| minio        | Object Storage      | 9000 (API), 9001 (UI) |


# 🧠 III. Cách truy cập & test nhanh
## 🔹 Spark Master UI

👉 http://localhost:8080

## 🔹 JupyterLab Notebook

👉 http://localhost:8888

## 🔹 MinIO Web Console

👉 http://localhost:9001

```text
Đăng nhập:

Username: admin  
Password: admin123
```

## 🔹 PostgreSQL

Kết nối qua DBeaver, Azure Data Studio, hoặc psql:

```text
Host: localhost
Port: 5432
User: sparkuser
Password: sparkpass
Database: sparkdb
```

# 💡 IV. Giải thích từng cấu phần
## Thành phần	Vai trò	Ghi chú
| Thành phần                | Vai trò                                    | Ghi chú                                     |
| ------------------------- | ------------------------------------------ | ------------------------------------------- |
| **Spark Master / Worker** | Xử lý batch, ETL, streaming                | Có thể scale thêm worker                    |
| **JupyterLab**            | Giao diện phát triển & chạy notebook Spark | Có sẵn pyspark, pandas, scikit-learn        |
| **Kafka / Zookeeper**     | Thu thập & phát realtime data stream       | Dùng cho CDC, event-driven ETL              |
| **PostgreSQL**            | Metadata Store / Transaction logs          | Dùng cho Airflow, Spark checkpoint          |
| **MinIO**                 | Object storage (như S3)                    | Dùng để lưu Delta Table hoặc output parquet |
| **spark-net**             | Docker network bridge                      | Giúp các service truy cập lẫn nhau          |


# 🧰 V. Một số lệnh hữu ích
Dừng toàn bộ container
```bash
docker compose down
```

## Xóa toàn bộ container + volume
```bash
docker compose down -v
```
## Xem log của từng service
```bash
docker logs -f spark-master
```
#📗 VI. Tùy chọn mở rộng (cho ngân hàng)

Bạn có thể dễ dàng bổ sung thêm:

Airflow (ETL orchestration)

Ranger + Atlas (Governance & Data Masking)

Keycloak (SSO + IAM cho Jupyter / Spark UI)

#📦 VII. Kết hợp với Conda Local (Dual Mode)

Bạn hoàn toàn có thể chạy:

Local Mode: Conda env (spark_env)

Cluster Mode: Docker Compose (multi-node Spark, Kafka, MinIO)

Hai môi trường này có thể chia sẻ chung thư mục data/ và notebooks/.

# 🌐 5. Truy cập giao diện:

| Service      | URL                                            | Ghi chú                   |
| ------------ | ---------------------------------------------- | ------------------------- |
| Spark Master | [http://localhost:8080](http://localhost:8080) | UI cluster Spark          |
| Spark Worker | [http://localhost:8081](http://localhost:8081) | Worker UI                 |
| JupyterLab   | [http://localhost:8888](http://localhost:8888) | Notebook dev              |
| Airflow      | [http://localhost:8082](http://localhost:8082) | UI quản lý DAG            |
| MinIO        | [http://localhost:9001](http://localhost:9001) | Giao diện quản lý file S3 |
| Kafka        | localhost:9092                                 | Dùng producer/consumer    |
| Postgres     | localhost:5432                                 | Database metadata         |


# 🧩 6. Gợi ý DAG mẫu Airflow để chạy Spark Job:

```python
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime

with DAG(
    dag_id="spark_wordcount_demo",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:

    wordcount = SparkSubmitOperator(
        task_id="run_wordcount",
        application="/opt/airflow/dags/jobs/wordcount.py",
        conn_id="spark_default",
        executor_memory="2g",
        driver_memory="2g",
        verbose=True,
    )

```

# 💾 7. Hướng dẫn tạo file .env cho Docker Compose

```env
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=admin123
AIRFLOW_UID=50000
AIRFLOW_GID=0
FERNET_KEY=C1Cg8QaV6rUzSZlQ9OCAFHVv-IWMBQuSvnfcMfnuEAg=

```


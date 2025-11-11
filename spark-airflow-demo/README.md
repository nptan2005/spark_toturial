# Spark Environment Docker Compose

File [docker-compose.yml](docker-compose.yml) trong sub-project spark-airflow-demo cấu hình một môi trường **Spark + Kafka + MinIO + Postgres + Airflow + Atlas + Ranger + JupyterLab** đầy đủ, **_cross-platform_** (Windows/Mac/Linux) với khả năng chạy trên Mac ARM thông qua platform: linux/amd64.
**_Note_**: là bảng bổ sung thành phần Governance so với sub project spark_env

## Spark Environment Architecture:
```css
                       +------------------+
                       |     Keycloak     |
                       |      SSO         |
                       |     (8085)       |
                       +--------+---------+
                                |
                                | OAuth2 / OIDC
                                v
+------------------+       +------------------+       +------------------+
|   Spark UI Proxy |<----->|  Spark Master    |<----->|  Spark Worker(s) |
|      (8084)      |       |  (8080/7077)     |       |     (8081)       |
+------------------+       +------------------+       +------------------+
        ^                          ^
        | OAuth2 + Submit Job      | Spark Job / Task
        |                          |
+-------+--------------------------+--------+
|                 Spark Cluster               |
|--------------------------------------------|
|  JupyterLab (8888)                         |
|  - Interactive Notebooks                    |
|  - PySpark submit to cluster                |
|--------------------------------------------|
|  Airflow (8082)                             |
|  - DAG Scheduling                           |
|  - Triggers Spark / MinIO jobs              |
+------------------+-------------------------+
                   |
                   | Reads/Writes
                   v
          +-------------------+
          |      MinIO        |
          |   Object Storage  |
          |   (9000/9001)    |
          +-------------------+
                   ^
                   |
                   | Streaming / Batch
+------------------+-------------------+
|                  Kafka                 |
| +-------------+    +---------------+  |
| | Zookeeper   |<-->| Kafka Broker  |  |
| | (2181)      |    | (9092)        |  |
| +-------------+    +---------------+  |
+---------------------------------------+
                   ^
                   |
                   | Metadata
                   v
          +-------------------+
          |    Postgres       |
          |  Airflow / Atlas  |
          |  Metadata DB      |
          |  (5432)           |
          +-------------------+
                   ^
                   |
                   |
+------------------+-------------------+
|            Governance Layer          |
|-------------------------------------|
| Atlas (21000)                        |
| - Metadata Catalog / Data Lineage    |
| Ranger (6080)                        |
| - Policy-based Access Control (ABAC) |
| Token Service (5001)                 |
| - JWT token provider for Spark / UI  |
+-------------------------------------+


```

## Các thành phần được cấu hình:
### 1. Spark
#### 1.1. spark-master

* **Image:** bde2020/spark-master:3.3.0-hadoop3.3
* **Container Name:** spark-master
* **Ports:**
>>* 8080: Web UI của Spark Master
>>* 7077: Port giao tiếp Spark Worker
* **Môi trường:**
>>* SPARK_MODE=master → Chỉ định container là Master
>>* SPARK_PUBLIC_DNS=spark-master → DNS nội bộ
* **Mạng:** spark-net
#### **Vai trò:** Spark Master quản lý cluster, nhận job từ client, phân phối tới các Spark Worker.
#### **Ứng dụng:** Dùng cho chạy các job Spark (batch/streaming) nội bộ cluster.

#### 1.2. spark-worker

* **Image:** bde2020/spark-worker:3.3.0-hadoop3.3
* **Container Name:** spark-worker
* **Ports:**
>>* 8081: Web UI của Spark Worker
* **Môi trường:**
>>* SPARK_MASTER=spark://spark-master:7077 → Kết nối tới Spark Master
>>* Dependencies: depends_on: spark-master
* **Mạng:** spark-net
#### **Vai trò:** Thực thi job được phân phối từ Spark Master.
#### **Ứng dụng:** Chạy các task Spark, hỗ trợ tính toán phân tán.

### Spark cluster:
#### **Master (8080/7077):** Điều phối các job tới Worker
#### **Worker(s) (8081):** Thực thi job
#### **Luồng dữ liệu:** Nhận job từ JupyterLab hoặc Airflow, đọc/ghi dữ liệu từ/đến MinIO hoặc Kafka.


### 2. Kafka
#### 2.1. zookeeper

* **Image:** zookeeper:3.7.1
* **Container Name:** zookeeper
* **Ports:**
>>* 2181: Port client Zookeeper
* **Môi trường:**
>>* ALLOW_ANONYMOUS_LOGIN=yes → Cho phép client kết nối không cần user/password
* **Mạng:** spark-net
#### **Vai trò:** Quản lý cluster Kafka, lưu trữ metadata về topics, offsets.
#### **Ứng dụng:** Cơ sở hạ tầng cho message broker của Spark Streaming.

#### 2.2. kafka

* **Image:** wurstmeister/kafka:2.13-2.8.1
* **Container Name:** kafka
* **Ports:**
>>* 9092: Port client Kafka
* **Môi trường:**
>>* KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 → Kafka client kết nối qua localhost
>>* KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 → Kết nối Zookeeper
>>* KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 → Replication factor
* **Dependencies:** depends_on: zookeeper
* **Mạng:** spark-net
#### **Vai trò:** Message broker, truyền dữ liệu streaming tới Spark.
#### **Ứng dụng:** Thí nghiệm real-time data pipeline với Spark Streaming.

### 3. MinIO (Data Lake)

* **Image:** minio/minio
* **Container Name:** minio
* **Ports:**
>>* 9000: REST API
>>* 9001: Web Console
* **Volumes:** ./data/minio:/data
* **Command:** server /data --console-address ":9001"
* **Môi trường:**
>>* MINIO_ROOT_USER=admin
>>* MINIO_ROOT_PASSWORD=admin123
* **Mạng:** spark-net
#### **Vai trò:** 
>>* Object storage giống S3 để lưu trữ dữ liệu thí nghiệm.
>>* Data Lake lưu trữ dataset, output Spark jobs.
#### **Ứng dụng:** Lưu trữ input/output Spark, dataset lớn.
#### **Luồng dữ liệu:**
>>* Spark đọc/ghi dữ liệu batch/streaming
>>* JupyterLab đọc dữ liệu mẫu để demo

### 4. Postgres (Airflow Metadata DB)

* **Image:** postgres:13
* **Container Name:** postgres
* **Ports:** 5432 → Port DB
* **Volumes:** ./data/postgres:/var/lib/postgresql/data
* **Môi trường:**
>>* POSTGRES_USER=airflow
>>* POSTGRES_PASSWORD=airflow
>>* POSTGRES_DB=airflow
* **Mạng:** spark-net
#### **Vai trò:** 
>>* Lưu trữ metadata Airflow (DAGs, task status).
>>* Metadata DB cho Airflow, lưu trạng thái DAG và task logs.
#### **Ứng dụng:** Quản lý lịch trình workflow.

### 5. Airflow

* **Image:** apache/airflow:2.10.5-python3.12
* **Container Name:** airflow
* **Ports:** 8082:8080 → Airflow web UI
* **Volumes:**
>>* ./dags:/opt/airflow/dags
>>* ./logs:/opt/airflow/logs
>>* ./plugins:/opt/airflow/plugins
* **Môi trường:**
>>* AIRFLOW__CORE__EXECUTOR=LocalExecutor
>>* AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
>>* AIRFLOW__CORE__FERNET_KEY=...
>>* AIRFLOW__CORE__LOAD_EXAMPLES=False
>>* AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=True
* **Dependencies:** depends_on: postgres
* **Mạng:** spark-net
#### **Vai trò:** 
>>* Orchestration workflow, chạy DAG, điều phối jobs.
>>* Orchestrator workflow, chạy DAGs, schedule jobs.
#### **Ứng dụng:** Kết hợp Spark + Kafka + MinIO pipeline.
#### **Luồng dữ liệu:** Tương tác với Spark cluster, lưu metadata task status vào Postgres.

### 6. JupyterLab

* **Image:** jupyter/pyspark-notebook:latest
* **Container Name:** jupyterlab
* **Ports:** 8888:8888 → Web Notebook
* **Volumes:** ./data:/home/jovyan/data
* **Môi trường:**
>>* SPARK_MASTER=spark://spark-master:7077
>>* PYSPARK_PYTHON=python3
* **Mạng:** spark-net
#### **Vai trò:** 
>>* Notebook môi trường tương tác cho PySpark.
>>* Notebook tương tác cho PySpark, chạy thử code batch/streaming.
#### **Ứng dụng:** Thực hành, demo, viết code Spark, Kafka streaming, MinIO.
#### **Luồng dữ liệu:** Gửi Spark job tới cluster (spark://spark-master:7077) và đọc/ghi dữ liệu tới MinIO.

### 7. Network

* **Name:** spark-net
* **Driver:** bridge
#### **Vai trò:** Cho phép tất cả container giao tiếp nội bộ, đảm bảo Spark Master/Worker, Kafka, Airflow, JupyterLab kết nối liền mạch.

### 8. Governance Layer

* **Atlas** (21000)
>* Metadata catalog, lineage tracking cho data pipeline.
>* Tích hợp với Spark & Airflow.
* **Ranger** (6080)
>* Policy-based access control (ABAC)
>* Quản lý quyền truy cập data lake, Spark jobs.
* **Token Service** (5001)
>* JWT token provider cho Spark UI Proxy và các service khác.

### 9. Luồng dữ liệu tổng quát
### 1. Batch/Interactive:
> JupyterLab → Spark Master → Spark Worker → MinIO
### 2. Streaming:
> External Producer → Kafka Broker → Spark Streaming → MinIO
### 3. Workflow scheduling:
> Airflow → Spark jobs → Worker → MinIO/Postgres
### 4.Governance
> Atlas thu thập lineage từ Spark & Airflow
> Ranger áp dụng quyền truy cập
> Token Service cấp JWT cho Spark UI Proxy và các service khác
### 5.SSO
> Keycloak quản lý người dùng, OAuth2 cho Spark UI Proxy
### 6. Monitoring:
>* Spark Master UI (8080)
>* Spark Worker UI (8081)
>* Airflow Web UI (8082)
>* MinIO Console (9001)
>* Jupyter Notebook (8888)

### 10. Lưu ý vận hành

* **Cross-platform:** platform: linux/amd64 đảm bảo chạy được trên Mac ARM và Windows.
* **Volume mapping:** giữ dữ liệu persistent (Postgres, MinIO, Airflow logs, Jupyter data).
* **Start containers:**
```bash
docker-compose up -d
```
* **Stop containers:**
```bash
docker-compose down
```
* **Kiểm tra logs:**
```bash
docker logs -f <container_name>
```

## Truy cập Web UI:

1. Spark Master: [http://localhost:8080](http://localhost:8080)
2. Spark Worker: [http://localhost:8081](http://localhost:8081)
3. Airflow: [http://localhost:8082](http://localhost:8082)
4. MinIO Console: [http://localhost:9001](http://localhost:9001)
5. JupyterLab: [http://localhost:8888](http://localhost:8888)

## Tài liệu cài đặt và demo:

1. Hướng dẫn [cài đặt và demo](Spark_governance.md)
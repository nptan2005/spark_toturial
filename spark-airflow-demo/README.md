# Spark Environment Docker Compose

File [docker-compose.yml](docker-compose.yml) trong sub-project spark-airflow-demo cấu hình một môi trường **Spark + Kafka + MinIO + Postgres + Airflow + Atlas + Ranger + JupyterLab** đầy đủ, **_cross-platform_** (Windows/Mac/Linux) với khả năng chạy trên Mac ARM thông qua platform: linux/amd64.
**_Note_**: là bảng bổ sung thành phần Governance so với sub project spark_env

## Spark Environment Architecture:
```txt
                                   +-----------------------+
                                   |       Keycloak        |
                                   |   SSO / OAuth2 (8085) |
                                   +-----------+-----------+
                                               |
                                               | OIDC Auth
                                               v
+-----------------------+        +-----------------------+        +------------------------+
|    Spark UI Proxy     |<------>|     Spark Master      |<------>|     Spark Worker(s)    |
|     OAuth2 (8084)     |        |   8080 (UI) / 7077    |        |        (8081)          |
+-----------+-----------+        +-----------+-----------+        +-----------+------------+
            ^                                ^                                ^
            |                                |                                |
            |                                | Spark Tasks                    |
            | OAuth2 Redirect                |                                |
            |                                |                                |
+-----------+-----------+          +----------+------------+       +-----------+------------+
|        JupyterLab     |          |      Airflow Web      |       |       Airflow Scheduler |
|       Notebook (8888) |          |     UI (8082)         |       |     + DAG Processor     |
+-----------+-----------+          +----------+------------+       +-----------+------------+
            |                                |                                |
            +-----------+--------------------+--------------+------------------+
                        |                                   |
                        |  Submit jobs / Read-Write data    |
                        v                                   v
                 +-------------------+               +-------------------+
                 |      MinIO        |               |     Postgres      |
                 |   S3 Storage      |               |  Metadata DB (5432)|
                 +---------+---------+               +----------+----------+
                           ^                                     ^
                           |                                     |
                           | Batch/Stream Data                   | Metadata
                           |                                     |
+--------------------------+-------------------------------------+--------------------------+
|                                         Kafka                                                      |
|                       +----------------+       +-------------------+                             |
|                       |   Zookeeper    |<----->|   Kafka Broker    |                             |
|                       |     (2181)     |       |  (9092 / 29092)   |                             |
+--------------------------+-------------------------------------+----------------------------------+
                           |
                           v
          +----------------+-------------------+
          |               Governance           |
          |-----------------------------------|
          | Ranger (6080) — Policy / ABAC     |
          | Atlas  (21000) — Data Lineage     |
          | Token Service (5001) — JWT        |
          +-----------------------------------+

==================================================================================================
                        🔍  Monitoring + Observability Stack
==================================================================================================

+-------------------+       +--------------------+       +---------------------+
|     Prometheus    |<----->|    cAdvisor        |       | Nginx Exporter      |
|     (9090)        |       | Docker Metrics     |       | Internal Metrics    |
+---------+---------+       +---------+----------+       +----------+----------+
          |                           |                             |
          v                           v                             v
+-----------------------------------------------------------------------------------------------+
|                                           Loki                                                 |
|                                      (Logs Backend, 3100)                                      |
+-------------------------------------------+---------------------------------------------------+
                                            |
                                            v
                                   +----------------+
                                   |    Grafana     |
                                   |  Dashboards    |
                                   |     (3000)     |
                                   +----------------+
```
## Kiến trúc hệ thống

![CDP Architecture](docs/images/architecture-visual.svg)


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

### 9. Monitoring
#### 9.1. Prometheus
>* Image: prom/prometheus:latest
>* Container Name: prometheus
>* Ports: 9090:9090 → Prometheus UI
>* Volumes: ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
>* Mạng: spark-net

**Vai trò:**
* Thu thập metrics từ Spark, Kafka, Nginx exporter, cAdvisor.
* Lưu time-series metrics cho Grafana.

**Ứng dụng:**
* Giám sát CPU, RAM, network của container.
* Tracking Spark executor usage, Kafka broker, Airflow scheduler metrics.

**Luồng dữ liệu:**
* Prometheus pull metrics từ exporters → push sang Grafana dashboards.

⸻

#### 9.2 Loki (Log Backend)
>* Image: grafana/loki:2.8.2
>* Container Name: loki
>* Ports: 3100:3100
>* Volumes: ./monitoring/loki-config.yml:/etc/loki/local-config.yml

**Vai trò:**
* Lưu trữ toàn bộ log ứng dụng: Spark, Kafka, Airflow, Nginx, Token Service, Docker logs.

**Ứng dụng:**
* Truy vấn log bằng LogQL.
* Là backend log cho Grafana Explore.

**Luồng dữ liệu:**
* Promtail → gửi log đến Loki → Grafana đọc từ Loki.


#### 9.3 Promtail (Log Collector)
>* Image: grafana/promtail:2.8.2
>* Container Name: promtail
>* Volumes:
>>* ./monitoring/promtail-config.yml:/etc/promtail/config.yml
>>* ../logs:/logs (toàn bộ log trên host)

**Vai trò:**
* Agent thu thập log từ host và container.
* Parse log theo job (spark, kafka, nginx, airflow…).

**Ứng dụng:**
* Chuyển qua Loki để hiển thị trong Grafana.

**Luồng dữ liệu:**
* Log → Promtail → Loki → Grafana.

#### 9.4  Grafana
>* Image: grafana/grafana:9.5.0
>* Container Name: grafana
>* Ports: 3000:3000
>* Volumes:
>>* grafana-storage:/var/lib/grafana
>>* ./monitoring/grafana/provisioning:/etc/grafana/provisioning
>>* ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards

**Vai trò:**
* Dashboard giám sát toàn hệ thống.
* Hiển thị metrics + log + health của mọi service.

**Ứng dụng:**
* Dashboard Spark, Kafka, Airflow, MinIO, Token Service.
* Live log stream từ Loki.

**Luồng dữ liệu:**
* Prometheus → Metrics → Grafana
* Loki → Logs → Grafana

#### 9.5  cAdvisor (Docker Metrics)
>* Image: gcr.io/google-containers/cadvisor:latest
>* Container Name: cadvisor
>* Expose: 8080
>* Volumes:
>>* /var/lib/docker (Docker engine)
>>* /sys, /var/run…

**Vai trò:**
* Thu thập metrics container-level:
* CPU
* RAM
* Disk I/O
* Network I/O

**Ứng dụng:**
* Xem real-time performance toàn bộ stack Spark → Airflow → Kafka.

**Luồng dữ liệu:**
* cAdvisor → Prometheus → Grafana.

#### 9.6 Nginx Prometheus Exporter
>* Image: nginx/nginx-prometheus-exporter
>* Container Name: nginx-prometheus-exporter
>* Ports: 9113:9113
>* Scrape URI: http://access-host-proxy:8081/nginx_status

**Vai trò:**
* Xuất metrics Nginx:
* request rate
* active connections
* dropped connections

**Ứng dụng:**
* Theo dõi database proxy load, traffic đến Airflow/Spark.

**Luồng dữ liệu:**
* Exporter → Prometheus → Grafana dashboard Nginx.

#### Monitoring Dashboard (JSON + Provisioning):
🔹 1. Airflow Dashboard
	•	Scheduler delay
	•	DAG execution time
	•	Task duration
	•	Worker load

🔹 2. Spark Dashboard
	•	Executors
	•	Jobs / Stages
	•	Task durations
	•	CPU/RAM usage

🔹 3. Kafka Dashboard
	•	Broker health
	•	Consumer lag
	•	ISR / Under-replicated partitions

🔹 4. Nginx Dashboard
	•	Requests per second
	•	Active connections
	•	Upstream latency

🔹 5. Token Service Dashboard
	•	Response time
	•	Error rate

🔹 6. Docker System Dashboard
	•	Per-container CPU, RAM
	•	Disk I/O
	•	Network usage

### 10. Luồng dữ liệu tổng quát
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

### 11. Lưu ý vận hành

* **Cross-platform:** platform: linux/amd64 đảm bảo chạy được trên Mac ARM và Windows.
* **Volume mapping:** giữ dữ liệu persistent (Postgres, MinIO, Airflow logs, Jupyter data).
* **Start containers:**
  
#### Cách lệnh docker cơ bản: 

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

#### Docker kiểm tra:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

full

```bash
docker compose ps
```
### 12. Docker cleanup
#### 🔥 1️⃣ Xoá toàn bộ log của container (tự động giảm file JSON log)

Docker log nằm ở:
```
/var/lib/docker/containers/<container-id>/<container-id>-json.log
```
Lệnh dọn:
```bash
docker ps -aq | xargs -I {} sh -c 'truncate -s 0 /var/lib/docker/containers/{}/{}-json.log 2>/dev/null'
```
##### ⚠️ Note:
Trên macOS, đường dẫn thực tế nằm trong VM, nhưng Docker Desktop hỗ trợ truncate qua CLI.

* ✔ Log sẽ trở về 0 byte
* ✔ Container không restart
* ✔ Không mất dữ liệu volume

#### 🔥 2️⃣ Xóa container đã dừng:

```bash
docker container prune -f
```

#### 🔥 3️⃣ Xóa image không dùng (dangling + orphan)

```bash
docker image prune -a -f
```
Nếu muốn xem trước khi xoá:
```bash
docker image prune -a
```
#### 🔥 4️⃣ Xoá network rác (docker-compose up/down nhiều sẽ sinh ra)
```bash
docker network prune -f
```
#### 🔥 5️⃣ Xoá volume rác (không còn gắn vào container nào)

```bash
docker volume prune -f
```
>⚠️ Lưu ý: volume prune chỉ xoá volume không sử dụng → an toàn.

#### 🔥 6️⃣ Xoá toàn bộ build cache (rất nặng, 2–20GB)
```bash
docker builder prune -a -f
```
#### 🔥 7️⃣ Xóa mọi thứ không dùng (CLEAN FULL)
```bash
docker system prune -a --volumes -f
```
>##### ⚠️ Cẩn trọng:
>*	Xoá tất cả container STOPPED
>*	Xoá mọi image không được container nào dùng
>*	Xoá network rác
>*	Xoá build cache
>*	Xoá volume không dùng
>> Nhưng sẽ không xoá volume đang mount cho project.

#### 🔥 8️⃣ Kiểm tra dung lượng Docker sau khi dọn
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
#### 🔥 9️⃣ Docker Desktop GUI cũng có nút dọn cache
Settings → Troubleshoot → Clean/Purge Data
Nhưng CLI chính xác hơn và tuỳ chỉnh được.
#### ⭐ Gợi ý dọn dẹp

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


## Truy cập Web UI:

1. Spark Master: [http://localhost:8080](http://localhost:8080)
2. Spark Worker: [http://localhost:8081](http://localhost:8081)
3. Airflow: [http://localhost:8082](http://localhost:8082)
4. MinIO Console: [http://localhost:9001](http://localhost:9001)
5. JupyterLab: [http://localhost:8888](http://localhost:8888)

## Tài liệu cài đặt và demo:

1. Hướng dẫn [cài đặt và demo](Spark_governance.md)
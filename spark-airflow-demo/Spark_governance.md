# 🚀 Full Demo Stack: Spark + Airflow + Governance + SSO
## 1️⃣ Mục tiêu setup

* Data processing / compute: Spark Master/Worker, Hadoop, Kafka
* Workflow orchestration: Airflow + DAG demo
* Storage: MinIO (Data Lake)
* Metadata DB: Postgres
* Notebook: JupyterLab + PySpark
* Governance & Masking: Apache Ranger + Apache Atlas
* Authentication: Keycloak (SSO cho Spark UI / Jupyter / Airflow)

## 2️⃣ Folder structure (Docker + Conda ready):

```arduino

spark-airflow-demo/
├─ docker-compose.yml
├─ dags/
│   └─ demo_spark_dag.py
├─ notebooks/
│   └─ demo_spark_notebook.ipynb
├─ data/
├─ logs/
├─ plugins/
├─ config/
├─ conda_env.yml
├─ keycloak/
│   └─ realm-export.json

```

## 3️⃣ Docker Compose (docker-compose.yml)

```yaml
version: "3.9"

services:
  # ---------------- SPARK ----------------
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

  # ---------------- KAFKA ----------------
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

  # ---------------- MinIO ----------------
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

  # ---------------- Postgres ----------------
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

  # ---------------- Airflow ----------------
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

  # ---------------- JupyterLab ----------------
  jupyterlab:
    image: jupyter/pyspark-notebook:latest
    container_name: jupyterlab
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/home/jovyan/notebooks
    environment:
      - SPARK_MASTER=spark://spark-master:7077
      - PYSPARK_PYTHON=python3
    networks:
      - spark-net

  # ---------------- Ranger + Atlas ----------------
  ranger:
    image: apache/ranger:2.3.0
    container_name: ranger
    ports:
      - "6080:6080"
    networks:
      - spark-net

  atlas:
    image: apache/atlas:2.2.0
    container_name: atlas
    ports:
      - "21000:21000"
    networks:
      - spark-net

  # ---------------- Keycloak ----------------
  keycloak:
    image: quay.io/keycloak/keycloak:21.1.1
    container_name: keycloak
    command: start-dev
    environment:
      - KEYCLOAK_ADMIN=admin
      - KEYCLOAK_ADMIN_PASSWORD=admin
    ports:
      - "8083:8080"
    volumes:
      - ./keycloak:/opt/keycloak/data/import
    networks:
      - spark-net

networks:
  spark-net:
    driver: bridge

```

## 4️⃣ Demo DAG (Airflow)

dags/demo_spark_dag.py:

```python
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
from pyspark.sql import SparkSession

def spark_job():
    spark = SparkSession.builder \
        .appName("AirflowSparkDemo") \
        .master("spark://spark-master:7077") \
        .getOrCreate()
    data = [("Alice", 30), ("Bob", 25)]
    df = spark.createDataFrame(data, ["name", "age"])
    df.show()

with DAG(
    dag_id="demo_spark_dag",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag:
    t1 = PythonOperator(
        task_id="run_spark_job",
        python_callable=spark_job
    )

```

## 5️⃣ Demo Notebook (JupyterLab)

notebooks/demo_spark_notebook.ipynb:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("DemoNotebook") \
    .master("spark://spark-master:7077") \
    .getOrCreate()

data = [("John", 28), ("Jane", 32)]
columns = ["name", "age"]

df = spark.createDataFrame(data, columns)
df.show()
```

## 6️⃣ Conda environment (conda_env.yml):

```yaml
name: spark_env
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.12
  - jupyterlab
  - pyspark=3.3.0
  - pandas
  - numpy
  - matplotlib
  - airflow=2.10.5
  - psycopg2
  - requests
  - kafka-python

```
* Khởi tạo:

```bash
conda env create -f conda_env.yml
conda activate spark_env
```

* Chạy Spark + Airflow + Jupyter trực tiếp:

```bash
# Spark master/worker
$SPARK_HOME/sbin/start-master.sh
$SPARK_HOME/sbin/start-worker.sh spark://localhost:7077

# Airflow
airflow db init
airflow scheduler &
airflow webserver -p 8082

# Jupyter
jupyter lab
```

## 7️⃣ Truy cập UI:

| Service         | URL                                              | Port  |
| --------------- | ------------------------------------------------ | ----- |
| Spark Master UI | [http://localhost:8080](http://localhost:8080)   | 8080  |
| Spark Worker UI | [http://localhost:8081](http://localhost:8081)   | 8081  |
| JupyterLab      | [http://localhost:8888](http://localhost:8888)   | 8888  |
| Airflow         | [http://localhost:8082](http://localhost:8082)   | 8080  |
| MinIO           | [http://localhost:9001](http://localhost:9001)   | 9001  |
| Ranger          | [http://localhost:6080](http://localhost:6080)   | 6080  |
| Atlas           | [http://localhost:21000](http://localhost:21000) | 21000 |
| Keycloak        | [http://localhost:8083](http://localhost:8083)   | 8080  |


## 8️⃣ Notes & Tips:

1. Ranger + Atlas:

Ranger dùng policy để mask dữ liệu, authorize các user.

Atlas dùng metadata lineage, tracking job, data catalog.

2. Keycloak:

Bạn có thể tạo realm và user, sau đó config Spark / Jupyter / Airflow dùng OAuth2 login.

3. Local test:

Chạy docker compose up -d → check logs → test notebook → trigger DAG.

4. Outside Docker:

Conda env + native install Java + Spark + Hadoop, chỉ cần thay đổi master=localhost:7077.

## 9️⃣ Keycloak Realm + User Config:

Tạo một realm Keycloak, có sẵn user demo và client OAuth2 cho Spark, Jupyter, Airflow.

File: keycloak/realm-export.json

```json
{
  "realm": "spark-demo-realm",
  "enabled": true,
  "users": [
    {
      "username": "demo_user",
      "enabled": true,
      "emailVerified": true,
      "credentials": [
        {
          "type": "password",
          "value": "demo123",
          "temporary": false
        }
      ]
    }
  ],
  "clients": [
    {
      "clientId": "spark-ui",
      "enabled": true,
      "protocol": "openid-connect",
      "redirectUris": ["http://localhost:8080/*"],
      "publicClient": true,
      "directAccessGrantsEnabled": true
    },
    {
      "clientId": "jupyterlab",
      "enabled": true,
      "protocol": "openid-connect",
      "redirectUris": ["http://localhost:8888/*"],
      "publicClient": true,
      "directAccessGrantsEnabled": true
    },
    {
      "clientId": "airflow",
      "enabled": true,
      "protocol": "openid-connect",
      "redirectUris": ["http://localhost:8082/*"],
      "publicClient": true,
      "directAccessGrantsEnabled": true
    }
  ]
}
```

## 10 Cấu hình OAuth2 Spark UI:

Spark Master / Worker có thể bật authentication bằng OAuth2 Proxy hoặc config trực tiếp Ranger plugin.

Cách đơn giản cho demo:

1. Cài thêm Spark Ranger Plugin (nếu muốn enforce policy, nhưng demo có thể bỏ qua).

2. Sử dụng keycloak-proxy để bảo vệ UI:

```yaml
spark-ui-proxy:
  image: quay.io/oauth2-proxy/oauth2-proxy:latest
  container_name: spark-ui-proxy
  environment:
    - OAUTH2_PROXY_CLIENT_ID=spark-ui
    - OAUTH2_PROXY_CLIENT_SECRET=demo-secret
    - OAUTH2_PROXY_COOKIE_SECRET=randomsecret123
    - OAUTH2_PROXY_PROVIDER=keycloak
    - OAUTH2_PROXY_OIDC_ISSUER_URL=http://keycloak:8080/realms/spark-demo-realm
    - OAUTH2_PROXY_REDIRECT_URL=http://localhost:8084/oauth2/callback
    - OAUTH2_PROXY_UPSTREAMS=http://spark-master:8080
  ports:
    - "8084:4180"
  depends_on:
    - keycloak
    - spark-master
  networks:
    - spark-net
```

* Truy cập Spark UI: http://localhost:8084 → bạn sẽ thấy login Keycloak.

## 11 Cấu hình OAuth2 JupyterLab

JupyterLab hỗ trợ OAuth2 login bằng extension jupyter-server-oauth.
Demo nhanh:

1. Cài đặt extension trong container Jupyter:

```bash
docker exec -it jupyterlab pip install jupyter-server-oauth
```

2. Thêm config jupyter_notebook_config.py:

```python
c.ServerApp.oauth2_provider_class = 'jupyter_server_oauth.providers.keycloak.KeycloakOAuthProvider'
c.KeycloakOAuthProvider.client_id = 'jupyterlab'
c.KeycloakOAuthProvider.client_secret = 'demo-secret'
c.KeycloakOAuthProvider.openid_url = 'http://keycloak:8080/realms/spark-demo-realm/.well-known/openid-configuration'
```

3. Restart JupyterLab → truy cập http://localhost:8888 → login Keycloak.

## 12. Cấu hình OAuth2 Airflow:

Airflow hỗ trợ OAuth2 login qua Flask AppBuilder:

1. Cài đặt package:

```bash
docker exec -it airflow pip install apache-airflow[oauth]
```

2. Trong airflow.cfg hoặc ENV:

```ini
[webserver]
rbac = True
authenticate = True
auth_backend = airflow.providers.oauth2.auth_backend.oauth_auth
```

3. ENV variables:

```yaml
AIRFLOW__WEBSERVER__OAUTH_PROVIDERS=[{'name':'keycloak','token_key':'access_token','icon':'fa-key','remote_app':{'client_id':'airflow','client_secret':'demo-secret','api_base_url':'http://keycloak:8080/realms/spark-demo-realm/protocol/openid-connect','access_token_url':'http://keycloak:8080/realms/spark-demo-realm/protocol/openid-connect/token','authorize_url':'http://keycloak:8080/realms/spark-demo-realm/protocol/openid-connect/auth','client_kwargs':{'scope':'openid profile email'}}}]
```

* Truy cập http://localhost:8082 → login Keycloak.

## 13. Bonus Tips:
* Ranger + Atlas có thể dùng demo user để tạo policy & metadata.
* Khi muốn demo data masking / governance, dùng Spark đọc từ MinIO → Ranger plugin enforce → Atlas track lineage.
* Keycloak dễ dàng mở rộng: thêm user, group, role → mapping cho Spark/Airflow/Jupyter.


# bản Docker Compose hoàn chỉnh demo full stack với:

* Spark Master / Worker
* JupyterLab + PySpark Notebook
* Airflow (LocalExecutor)
* MinIO (Data Lake)
* Postgres (Airflow Metadata DB)
* Zookeeper + Kafka
* Keycloak (SSO)
* OAuth2 Proxy bảo vệ Spark UI & JupyterLab
* Ranger + Atlas (Governance / Data Masking)

```yaml
# docker-compose.yml
# Demo full stack: Spark + Jupyter + Airflow + Kafka + MinIO + Governance (Ranger/Atlas) + Keycloak SSO
# ----------------------------------------------------------
services:
  # ------------------- SPARK -------------------
  spark-master:
    image: bde2020/spark-master:3.3.0-hadoop3.3
    container_name: spark-master
    environment:
      - SPARK_MODE=master
      - SPARK_PUBLIC_DNS=spark-master
    ports:
      - "8080:8080"  # Spark UI
      - "7077:7077"  # Spark Master port
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
      - "8081:8081"  # Spark Worker UI
    networks:
      - spark-net

  # ------------------- JUPYTERLAB -------------------
  jupyterlab:
    image: jupyter/pyspark-notebook:latest
    container_name: jupyterlab
    environment:
      - SPARK_MASTER=spark://spark-master:7077
      - PYSPARK_PYTHON=python3
    ports:
      - "8888:8888"  # JupyterLab Web
    volumes:
      - ./data:/home/jovyan/data
    networks:
      - spark-net

  # ------------------- AIRFLOW -------------------
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

  # ------------------- MINIO -------------------
  minio:
    image: minio/minio
    container_name: minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: admin123
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - ./data/minio:/data
    networks:
      - spark-net

  # ------------------- KAFKA / ZOOKEEPER -------------------
  zookeeper:
    image: wurstmeister/zookeeper:3.4.6
    container_name: zookeeper
    environment:
      ALLOW_ANONYMOUS_LOGIN: "yes"
    ports:
      - "2181:2181"
    networks:
      - spark-net

  kafka:
    image: wurstmeister/kafka:2.13-2.8.1
    container_name: kafka
    depends_on:
      - zookeeper
    environment:
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - "9092:9092"
    networks:
      - spark-net

  # ------------------- KEYCLOAK (SSO) -------------------
  keycloak:
    image: quay.io/keycloak/keycloak:21.1.1
    container_name: keycloak
    command: start-dev
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
    ports:
      - "8085:8080"  # Keycloak Web UI
    networks:
      - spark-net
    volumes:
      - ./keycloak/realm-export.json:/opt/keycloak/data/import/realm-export.json
    entrypoint:
      - "/opt/keycloak/bin/kc.sh"
      - "start-dev"
      - "--import-realm"

  # ------------------- SPARK UI OAuth2 Proxy -------------------
  spark-ui-proxy:
    image: quay.io/oauth2-proxy/oauth2-proxy:latest
    container_name: spark-ui-proxy
    environment:
      - OAUTH2_PROXY_CLIENT_ID=spark-ui
      - OAUTH2_PROXY_CLIENT_SECRET=demo-secret
      - OAUTH2_PROXY_COOKIE_SECRET=randomsecret123
      - OAUTH2_PROXY_PROVIDER=keycloak
      - OAUTH2_PROXY_OIDC_ISSUER_URL=http://keycloak:8080/realms/spark-demo-realm
      - OAUTH2_PROXY_REDIRECT_URL=http://localhost:8084/oauth2/callback
      - OAUTH2_PROXY_UPSTREAMS=http://spark-master:8080
    ports:
      - "8084:4180"
    depends_on:
      - keycloak
      - spark-master
    networks:
      - spark-net

  # ------------------- RANGER & ATLAS (Governance / Masking) -------------------
  ranger:
    image: apache/ranger:2.3.0
    container_name: ranger
    environment:
      - RANGER_ADMIN_PASSWORD=admin
    ports:
      - "6080:6080"
    networks:
      - spark-net

  atlas:
    image: apache/atlas:2.2.0
    container_name: atlas
    ports:
      - "21000:21000"
    networks:
      - spark-net

networks:
  spark-net:
    driver: bridge
```

## 🔹 Giải thích flow demo

* Spark Master/Worker: chạy cluster, Spark UI: http://localhost:8080 → OAuth2 proxy: http://localhost:8084
* JupyterLab: http://localhost:8888 → kết nối Spark cluster
* Airflow: http://localhost:8082 → DAG quản lý Spark Job / Kafka / MinIO workflows
* MinIO: Data Lake → Spark đọc/ghi dữ liệu
* Kafka + Zookeeper: message broker cho real-time demo
* Keycloak: quản lý user, login SSO cho Spark UI, JupyterLab, Airflow
* Ranger + Atlas: quản lý policy, data lineage, masking demo

## ✅ Sử dụng nhanh:

```bash
docker compose pull
docker compose up -d
# Kiểm tra logs
docker compose logs -f keycloak
docker compose logs -f spark-master
```

* Spark UI qua OAuth2 Proxy: http://localhost:8084 → login Keycloak: demo_user/demo123
* JupyterLab login Keycloak: http://localhost:8888
* Airflow login Keycloak: http://localhost:8082

# DEMO:

1. Notebook PySpark: đọc dữ liệu từ MinIO, thực hiện Spark job (ví dụ transform dữ liệu), ghi kết quả lại vào MinIO.
2. DAG Airflow: quản lý job này, gồm task trigger, SparkSubmitOperator, sensor kiểm tra kết quả.
3. Comment chi tiết từng bước flow, để bạn mở lên là test ngay.

## 1️⃣ Thư mục demo
```text
spark-airflow-demo/
│
├─ dags/
│   └─ spark_minio_demo_dag.py
├─ notebooks/
│   └─ spark_minio_demo.ipynb
├─ data/
│   ├─ input/       # dữ liệu gốc MinIO
│   └─ output/      # kết quả
├─ docker-compose.yml

```
## 2️⃣ Notebook demo: notebooks/spark_minio_demo.ipynb:

MinIO (input CSV) → Spark (transform) → MinIO (output CSV)

```python
# PySpark + MinIO demo notebook

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# 1. Khởi tạo SparkSession
spark = SparkSession.builder \
    .appName("Spark MinIO Demo") \
    .master("spark://spark-master:7077") \
    .getOrCreate()

# 2. Cấu hình kết nối MinIO (S3 API)
spark._jsc.hadoopConfiguration().set("fs.s3a.access.key", "admin")
spark._jsc.hadoopConfiguration().set("fs.s3a.secret.key", "admin123")
spark._jsc.hadoopConfiguration().set("fs.s3a.endpoint", "http://minio:9000")
spark._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")

input_path = "s3a://demo-bucket/input/sample.csv"
output_path = "s3a://demo-bucket/output/result.csv"

# 3. Đọc dữ liệu từ MinIO
df = spark.read.option("header", "true").csv(input_path)
print("Input Data:")
df.show()

# 4. Transform dữ liệu (ví dụ: chọn cột, đổi tên, tính toán)
df_transformed = df.select(
    col("id"),
    col("value").cast("double"),
    (col("value").cast("double") * 2).alias("value_double")
)

# 5. Ghi kết quả về MinIO
df_transformed.write.mode("overwrite").option("header", "true").csv(output_path)
print(f"Output saved to {output_path}")
```

## 3️⃣ DAG Airflow: dags/spark_minio_demo_dag.py:

Airflow DAG → SparkSubmitOperator → Sensor kiểm tra kết quả MinIO → hoàn tất

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.python import PythonOperator
import boto3

# 1. Hàm kiểm tra file trên MinIO
def check_minio_file():
    s3 = boto3.client(
        "s3",
        endpoint_url="http://minio:9000",
        aws_access_key_id="admin",
        aws_secret_access_key="admin123"
    )
    result = s3.list_objects_v2(Bucket="demo-bucket", Prefix="output/result.csv")
    if "Contents" not in result:
        raise ValueError("Result not found yet!")
    print("Result file found in MinIO.")

# 2. DAG definition
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

dag = DAG(
    "spark_minio_demo",
    default_args=default_args,
    description="Demo DAG: Spark job + MinIO",
    schedule_interval=None,
    start_date=datetime(2025, 11, 10),
    catchup=False,
)

# 3. SparkSubmitOperator
spark_task = SparkSubmitOperator(
    task_id="spark_minio_task",
    application="/opt/airflow/dags/notebooks/spark_minio_demo.py",  # convert notebook -> py hoặc dùng .py script
    name="spark_minio_demo",
    conn_id="spark_default",
    verbose=True,
    dag=dag,
)

# 4. PythonOperator: kiểm tra kết quả trên MinIO
check_task = PythonOperator(
    task_id="check_minio_result",
    python_callable=check_minio_file,
    dag=dag
)

spark_task >> check_task
```

**Notes**:
* DAG trigger bằng tay hoặc schedule theo giờ.
* SparkSubmitOperator chạy script .py từ Airflow container. Nếu notebook .ipynb, bạn convert sang .py (ví dụ dùng * jupyter nbconvert).
* check_minio_file kiểm tra kết quả trên MinIO bucket.

## 4️⃣ Test nhanh:

1. Start Docker full stack demo:

```bash
docker compose up -d
```

2. Tạo bucket và upload dữ liệu sample vào MinIO:

```bash
docker exec -it minio mc alias set local http://localhost:9000 admin admin123
docker exec -it minio mc mb local/demo-bucket
docker exec -it minio mc cp ./sample.csv local/demo-bucket/input/
```

3. Truy cập Airflow UI: http://localhost:8082 → trigger DAG spark_minio_demo.
4. Spark job sẽ chạy, kết quả lưu MinIO → PythonOperator kiểm tra file → DAG hoàn tất.
5. Kiểm tra MinIO output: http://localhost:9001 (login admin/admin123).

# Compose full stack v2:
* Spark Master / Worker
* MinIO
* Airflow + DAG + Notebook convert sẵn .py
* Postgres
* Kafka + Zookeeper
* Keycloak 21.1.1 + OAuth2 Proxy cho Spark/Jupyter
* Ranger / Atlas (version ổn định)

```yaml
# docker-compose-fullstack.yml
# ----------------------------------------------------------
# Demo Full Stack: Spark + Jupyter + Airflow + Kafka + MinIO
# + Governance (Ranger / Atlas)
# + Keycloak SSO + OAuth2 Proxy cho Spark UI
# ----------------------------------------------------------

version: "3.9"

services:
  # ------------------- SPARK -------------------
  spark-master:
    image: bde2020/spark-master:3.3.0-hadoop3.3
    container_name: spark-master
    environment:
      - SPARK_MODE=master
      - SPARK_PUBLIC_DNS=spark-master
    ports:
      - "8080:8080"   # Spark Master Web UI
      - "7077:7077"   # Spark Master port
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
      - "8081:8081"   # Spark Worker Web UI
    networks:
      - spark-net

  # ------------------- JUPYTERLAB -------------------
  jupyterlab:
    image: jupyter/pyspark-notebook:latest
    container_name: jupyterlab
    environment:
      - SPARK_MASTER=spark://spark-master:7077
      - PYSPARK_PYTHON=python3
    ports:
      - "8888:8888"  # JupyterLab Web UI
    volumes:
      - ./data:/home/jovyan/data
    networks:
      - spark-net

  # ------------------- AIRFLOW + POSTGRES -------------------
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
      - "8082:8080"  # Airflow Web UI
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
    depends_on:
      - postgres
    networks:
      - spark-net

  # ------------------- MINIO (Data Lake) -------------------
  minio:
    image: minio/minio
    container_name: minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: admin123
    ports:
      - "9000:9000"  # MinIO API
      - "9001:9001"  # MinIO Console
    volumes:
      - ./data/minio:/data
    networks:
      - spark-net

  # ------------------- KAFKA / ZOOKEEPER -------------------
  zookeeper:
    image: wurstmeister/zookeeper:3.4.6
    container_name: zookeeper
    environment:
      ALLOW_ANONYMOUS_LOGIN: "yes"
    ports:
      - "2181:2181"
    networks:
      - spark-net

  kafka:
    image: wurstmeister/kafka:2.13-2.8.1
    container_name: kafka
    depends_on:
      - zookeeper
    environment:
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - "9092:9092"
    networks:
      - spark-net

  # ------------------- KEYCLOAK (SSO) -------------------
  keycloak:
    image: quay.io/keycloak/keycloak:21.1.1
    container_name: keycloak
    command: start-dev
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
    ports:
      - "8085:8080"  # Keycloak Web UI
    networks:
      - spark-net
    volumes:
      - ./keycloak/realm-export.json:/opt/keycloak/data/import/realm-export.json
    entrypoint:
      - "/opt/keycloak/bin/kc.sh"
      - "start-dev"
      - "--import-realm"

  # ------------------- SPARK UI OAuth2 Proxy -------------------
  spark-ui-proxy:
    image: quay.io/oauth2-proxy/oauth2-proxy:latest
    container_name: spark-ui-proxy
    environment:
      OAUTH2_PROXY_CLIENT_ID: spark-ui
      OAUTH2_PROXY_CLIENT_SECRET: demo-secret
      OAUTH2_PROXY_COOKIE_SECRET: randomsecret123
      OAUTH2_PROXY_PROVIDER: keycloak
      OAUTH2_PROXY_OIDC_ISSUER_URL: http://keycloak:8080/realms/spark-demo-realm
      OAUTH2_PROXY_REDIRECT_URL: http://localhost:8084/oauth2/callback
      OAUTH2_PROXY_UPSTREAMS: http://spark-master:8080
    ports:
      - "8084:4180"  # OAuth2 Proxy for Spark UI
    depends_on:
      - keycloak
      - spark-master
    networks:
      - spark-net

  # ------------------- RANGER & ATLAS -------------------
  ranger:
    image: sabrinapark/apache-ranger:2.3.0
    container_name: ranger
    environment:
      RANGER_ADMIN_PASSWORD: admin
    ports:
      - "6080:6080"  # Ranger Admin UI
    networks:
      - spark-net

  atlas:
    image: sburn/apache-atlas:2.3.0
    container_name: atlas
    ports:
      - "21000:21000"
    networks:
      - spark-net
    depends_on:
      - postgres

# ------------------- NETWORK -------------------
networks:
  spark-net:
    driver: bridge
```

# Demo flow: MinIO → Spark Job → Result → Airflow Track:

## A. Notebook PySpark: notebooks/spark_minio_demo.ipynb

(ở đây là phiên bản .py bạn có thể convert dễ dàng)

```python
# spark_minio_demo.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

def main():
    spark = SparkSession.builder \
        .appName("Spark MinIO Demo") \
        .master("spark://spark-master:7077") \
        .getOrCreate()

    # cấu hình MinIO (S3 API)
    spark._jsc.hadoopConfiguration().set("fs.s3a.access.key", "admin")
    spark._jsc.hadoopConfiguration().set("fs.s3a.secret.key", "admin123")
    spark._jsc.hadoopConfiguration().set("fs.s3a.endpoint", "http://minio:9000")
    spark._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")

    input_path = "s3a://demo-bucket/input/sample.csv"
    output_path = "s3a://demo-bucket/output/result"

    df = spark.read.option("header", "true").csv(input_path)
    print("== Input Data ==")
    df.show()

    # transform
    df2 = df.select(
        col("id"),
        col("value").cast("double").alias("value_num"),
        (col("value").cast("double") * 2).alias("value_double")
    )

    print("== Transformed Data ==")
    df2.show()

    # write back
    df2.write.mode("overwrite").option("header", "true").csv(output_path)
    print(f"Output saved to {output_path}")

    spark.stop()

if __name__ == "__main__":
    main()
```

## B. DAG Airflow: dags/spark_minio_demo_dag.py:

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.python import PythonOperator
import boto3

def check_minio_file():
    s3 = boto3.client(
        "s3",
        endpoint_url="http://minio:9000",
        aws_access_key_id="admin",
        aws_secret_access_key="admin123"
    )
    resp = s3.list_objects_v2(Bucket="demo-bucket", Prefix="output/")
    if "Contents" not in resp or len(resp["Contents"]) == 0:
        raise ValueError("Result file not found in MinIO")
    print("Result file exists in MinIO")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    "spark_minio_demo",
    default_args=default_args,
    description="Demo Spark job via Airflow, input from MinIO, output to MinIO",
    schedule_interval=None,
    start_date=datetime(2025,1,1),
    catchup=False
) as dag:

    spark_task = SparkSubmitOperator(
        task_id="spark_task",
        application="/opt/airflow/dags/spark_minio_demo.py",
        name="spark_minio_demo",
        conn_id="spark_default",
        verbose=True
    )

    check_task = PythonOperator(
        task_id="check_minio",
        python_callable=check_minio_file
    )

    spark_task >> check_task
```

## C. File cấu hình docker‑compose.yml (có sẵn, chỉ cần đảm bảo volumes và paths đúng)

Bạn đã có phần lớn. Bạn cần đảm bảo:

* Tạo bucket demo-bucket trong MinIO trước khi chạy DAG
* Copy file sample.csv vào MinIO path input/sample.csv
* Volume ./notebooks chứa script .py và notebook nếu cần
* Volume ./dags chứa DAG và script .py

## 🔍 3. Hướng dẫn vận hành nhanh:

1. Start toàn bộ stack:

```bash
docker compose up -d
```

2. Truy cập MinIO console: http://localhost:9001, login admin/admin123.
Tạo bucket demo-bucket. Upload sample.csv vào input/.

3. Truy cập Airflow UI: http://localhost:8082, user nếu chưa SSO thì mặc định.
Có thấy DAG spark_minio_demo. Click Trigger.

4. Job chạy: Spark cluster sẽ thực hiện transform.
Sau đó PythonOperator kiểm tra MinIO ra output/.

5. Truy cập http://localhost:9001 lại, kiểm tra bucket demo-bucket/output/ có thư mục chứa kết quả.

6. Bạn có thể mở JupyterLab http://localhost:8888, load notebook hoặc script và chơi thử.


# 1️⃣ Build image Atlas / Ranger local:

## Atlas:

```bash
# 1. Clone source Atlas
git clone https://github.com/apache/atlas.git
cd atlas
# Checkout version bạn muốn (ví dụ 2.2.0)
git checkout rel/2.2.0

# error: tiep
git fetch --all --tags

# Xem danh sách tag
git tag -l

# Ví dụ, tag 2.2.0 có tên 'apache-atlas-2.2.0'
git checkout release-2.2.0-rc0  
# 2. Tạo docker file trong folder: spark-airflow-demo\images\atlas> nội dung như bên dưới:
Download và giải nén file atlas từ apache
# 3. Build Docker image
docker build -t local/atlas:2.2.0 .
```
* Docker file
```Dockerfile
# ===============================
# Apache Atlas 2.3.0 - Dockerfile
# ===============================

# Dockerfile for Apache Atlas (cross-platform)
FROM eclipse-temurin:11-jdk
WORKDIR /opt/atlas

# Copy Atlas binaries vào container
COPY apache-atlas-2.3.0 /opt/atlas

EXPOSE 21000

CMD ["./bin/atlas_start.sh"]

```

* Bước 2: Tạo file entrypoint.sh cùng thư mục:

```bash
#!/bin/bash
echo "Starting Apache Atlas Server..."
$ATLAS_HOME/bin/atlas_start.py

# Giữ container chạy để bạn có thể attach logs
tail -f $ATLAS_HOME/logs/atlas.log

```

* 👉 Bước 3: Build lại image:

```bash
docker build -t local/atlas:2.3.0 . 
```

* Lưu ý: Apache Atlas có yêu cầu Java + Maven, build image sẽ mất vài phút.

## Ranger:
Tương tự atlas cũng cần download source >>> docker file và build
```Dockerfile
# Dockerfile: Ranger 2.3.0 binary (cross-platform)
FROM eclipse-temurin:11-jdk
WORKDIR /opt/ranger

# Copy Ranger binary vào container
COPY apache-ranger-2.3.0 /opt/ranger

# Expose Ranger Admin port
EXPOSE 6080

# Start Ranger Admin khi container run
CMD ["./bin/ranger-admin-start.sh"]
```

```bash
docker build -t local/ranger:2.3.0 .
```


```bash
# 1. Clone source Ranger
git clone https://github.com/apache/ranger.git
cd ranger
# Checkout version 2.3.0
git checkout rel/2.3.0

# 2. Build Docker image
docker build -t local/ranger:2.3.0 .
```

* Ranger cũng cần Java + Maven, build image xong bạn sẽ có image local.

## Tokenization Service:

1. Cấu trúc:

```css
images/token-service/
├── Dockerfile
└── app.py
```

2. Dockerfile token-service
   
```Dockerfile
# Dockerfile token-service
FROM python:3.12-slim

WORKDIR /app

# Copy code vào
COPY app.py /app

# Cài Flask
RUN pip install flask

# Expose port
EXPOSE 5000

# Start service
CMD ["python", "app.py"]
```

3. app.py

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

# Simple token store
store = {}

@app.route("/token", methods=["POST"])
def generate_token():
    data = request.json
    val = data.get("value")
    if not val:
        return jsonify({"error": "missing value"}), 400
    token = f"TOKEN-{len(store)+1}"
    store[token] = val
    return jsonify({"token": token})

@app.route("/token/<token>", methods=["GET"])
def get_token(token):
    val = store.get(token)
    if not val:
        return jsonify({"error": "token not found"}), 404
    return jsonify({"value": val})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

4. Build:

```bash
cd images/token-service
docker build -t local/token-service:latest .
```
* Kiểm tra:

```bash
cd images/token-service
docker build -t local/token-service:latest .
```

5. Cập nhật Docker Compose:

```yaml
token-service:
  build: ./images/token-service
  image: local/token-service:latest
  container_name: token-service
  ports:
    - "5001:5000"
  networks:
    - spark-net
```

6. Test:

```bash
# Tạo token
curl -X POST -H "Content-Type: application/json" -d '{"value":"mydata"}' http://localhost:5001/token

# Lấy giá trị token
curl http://localhost:5001/token/TOKEN-1
```

## 2️⃣ Sửa docker-compose.yml:

* Dùng image local:

```yaml
atlas:
  image: local/atlas:2.2.0
ranger:
  image: local/ranger:2.3.0
```

* Keycloak vẫn dùng public image:

```yaml
keycloak:
  image: quay.io/keycloak/keycloak:21.1.1
```

* Zookeeper: zookeeper:3.7.1 (pull được)
* Kafka, Spark, Jupyter, MinIO, Postgres, Airflow: giữ nguyên.

## Build custom Spark:
```bash
cd images/spark
docker build --platform=linux/arm64 -t local/spark:3.5.1-full .
```

Test nhanh:

```bash
# chạy container interactive
docker run --rm -it --entrypoint /bin/zsh local/spark:3.5.1-full -l
# hoặc exec vào running container
docker exec -it spark-master /bin/zsh -l
```

## Airflow custom image:
```bash
docker build --platform=linux/arm64 -t local/airflow:2.10.5-custom .
```

### 🔍 Kiểm tra Airflow image
#### ✔ Kiểm tra Airflow version
```bash
docker run --rm local/airflow:2.10.5-custom airflow version
```
#### ✔ Kiểm tra cx_Oracle load Instant Client đúng
```bash
docker run -it --rm local/airflow:2.10.5-custom python3 - <<EOF
import cx_Oracle
print("cx_Oracle OK")
EOF
```
Nếu lỗi DPI-1047, nghĩa là Instant Client đặt sai đường dẫn.

#### ✔ Kiểm tra ORACLE_HOME & LD_LIBRARY_PATH
```bash
docker run --rm local/airflow:2.10.5-custom sh -c "echo ORACLE_HOME=$ORACLE_HOME; echo LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
```
### 🟧 Lệnh kiểm tra DAG import pyspark
(DAG không chạy Spark job, chỉ kiểm tra import)
```bash
docker run -it --rm local/airflow:2.10.5-custom python3 - <<EOF
import pyspark
print("pyspark import OK")
EOF
```
### 🟪 Kiểm tra Instant Client Oracle

```bash
docker run -it --rm local/airflow:2.10.5-custom ls /opt/oracle
docker run -it --rm local/airflow:2.10.5-custom ls /opt/oracle/instantclient_23_6
```

### 🟥 Kiểm tra Airflow Providers đã cài

```bash
docker run -it --rm local/airflow:2.10.5-custom pip show apache-airflow-providers-oracle
docker run -it --rm local/airflow:2.10.5-custom pip show apache-airflow-providers-postgres
docker run -it --rm local/airflow:2.10.5-custom pip show apache-airflow-providers-docker
```

### 🟦 Kiểm tra SparkSubmitOperator từ Airflow container
```bash
docker run -it --rm local/airflow:2.10.5-custom pyspark --version
```
### 🟩 Kiểm tra DAG folder đã mount chính xác khi chạy docker-compose
sau khi bạn chạy compose:
```bash
docker exec -it airflow-webserver ls /opt/airflow/dags
docker exec -it airflow-webserver airflow dags list
```
## Build Kafka client:
```bash
docker build --platform=linux/arm64 -t local/kafka-client:latest .
```
Test
```bash
docker run --rm \
  --network spark-net \
  -v $(pwd)/logs:/app/logs \
  local/kafka-client:latest
```

## 3️⃣ Flow full luồng:

1. MinIO: lưu input dữ liệu CSV / Parquet.
2. Spark job (submit từ notebook hoặc Airflow DAG):
* đọc dữ liệu MinIO,
* xử lý tính toán,
* lưu kết quả về MinIO.
3. Airflow DAG:
* Trigger job Spark,
* Sensor check file result trong MinIO,
* Log kết quả / tracking.
4. Ranger / Atlas:
* Ranger quản lý quyền truy cập data,
* Atlas quản lý metadata, lineage.
5. Keycloak + OAuth2 Proxy:
* SSO cho Spark UI / Jupyter / Airflow.

## 💡 Tóm tắt:
* Không có image public cho Atlas / Ranger, phải build local.
* Keycloak public image còn dùng được.
* Khi build xong, docker-compose sẽ chạy full stack.

```yaml
access-host-proxy:
    image: nginx:latest
    container_name: access-host-proxy
    mem_limit: ${NGINX_MEM}
    cpus: ${NGINX_CPU}
    # REMOVED: network_mode: host
    ports:
      - "5432:5432" # Expose PostgreSQL proxy port
      - "1521:1521" # Expose Oracle proxy port
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl
    networks:
      - spark-net # Quan trọng: Phải thuộc mạng chung để dùng tên dịch vụ
    depends_on:
      postgres:
        condition: service_healthy
    restart: always
```
### B. Dịch vụ Airflow (`flower`, `redis`, `dag-processor`)

| Dịch vụ | Vấn đề/Điều chỉnh | Lý do |
| :--- | :--- | :--- |
| **Network Name** | Dịch vụ đang sử dụng `airflow-network`. | **Phải hợp nhất!** Tất cả các dịch vụ (Spark, Kafka, MinIO, Airflow) nên sử dụng một mạng chung, ví dụ: **`spark-net`**, để Airflow có thể gọi Spark Submit hoặc Kafka Producer/Consumer. |
| **`flower`** | Cấu hình tốt, sử dụng `service_completed_successfully` cho `airflow-init`. | Đảm bảo đổi `airflow-network` thành `spark-net`. |
| **`redis`** | Cấu hình tốt. | Đảm bảo đổi `airflow-network` thành `spark-net`. |
| **`airflow-dag-processor`** | Cần đảm bảo rằng `airflow-common-depends-on` bao gồm cả `redis` và `postgres` healthy trước khi khởi động. | `dag-processor` cần DB (Postgres) và Broker (Redis) hoạt động. |

### C. Bổ sung Dịch vụ Airflow (Để có "Full Stack")

Mô hình Airflow của bạn đang thiếu hai dịch vụ bắt buộc để hoạt động:

1.  **`airflow-webserver`**: Cung cấp giao diện Web UI (đã có port 8082:8080 trong dịch vụ `airflow` ở phần trước, nhưng cần tách ra).
2.  **`airflow-scheduler`**: Lập lịch và kiểm tra trạng thái DAGs.

Bạn nên tách dịch vụ `airflow` (Web UI/Scheduler) thành các thành phần riêng biệt nếu bạn đang sử dụng `LocalExecutor` hoặc `CeleryExecutor` (như Flower chỉ ra).

---

## 3. Cấu hình Cập nhật (Mô phỏng)

Tôi giả định bạn muốn dùng **`spark-net`** làm mạng chung.


http://googleusercontent.com/immersive_entry_chip/1

### Tóm tắt các điều chỉnh chính:

1.  **Sửa `nginx.conf`**: Thay thế các IP cứng bằng tên dịch vụ (`postgres`, `oracle-db`).
2.  **Hợp nhất Network**: Đã đổi tất cả các dịch vụ liên quan đến Airflow/Redis từ `airflow-network` sang **`spark-net`** để đơn giản hóa giao tiếp với Spark, Kafka, và MinIO.
3.  **Tách Airflow**: Đã tách Airflow thành `airflow-webserver` và `airflow-scheduler` (và đổi tên dịch vụ Airflow cũ thành `airflow-webserver` và `airflow-scheduler`) để có một triển khai production-ready hơn.
-------------END SETUP-------------
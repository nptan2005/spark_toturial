# Spark Toturial:
```css
spark_workspace/
│
├─ environment.yml
├─ start_spark_lab.bat      ← dùng trên Windows
├─ start_spark_lab.sh       ← dùng trên macOS/Linux
│
├─ notebooks/               ← nơi chứa Jupyter notebooks
│    ├─ spark_intro.ipynb
│    ├─ streaming_kafka.ipynb
│
└─ data/                    ← data mẫu / input
        ├─ sample_data.csv
        ├─ kafka_messages.txt
```

# Tạo môi trường tên "spark_env" với Python 3.10
```bash
conda create -n spark_env python=3.10 -y
```

# Kích hoạt môi trường
```bash
conda activate spark_env
```

# Cài Spark và các thư viện cần thiết
```bash
pip install pyspark findspark jupyterlab pandas numpy pyarrow
```

# delta tables hoặc streaming:
```bash
pip install delta-spark kafka-python
```

# Kiểm tra cài đặt Spark

```bash
python -c "import pyspark; print(pyspark.__version__)"
```

# Test session
```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("TestSpark") \
    .getOrCreate()

print("Spark version:", spark.version)
spark.stop()
```

# Thiết lập biến môi trường

```bash
export PYSPARK_PYTHON=$(which python)
export PYSPARK_DRIVER_PYTHON=jupyter
export PYSPARK_DRIVER_PYTHON_OPTS="lab"
```


# Tạo biến môi trường bằng file environment.yml:
```yaml
name: spark_env
channels:
  - conda-forge
  - defaults
dependencies:
  # --- Python core ---
  - python=3.10
  - pip
  - numpy
  - pandas
  - pyarrow
  - openjdk=11        # cần cho Spark local mode (Java runtime)
  - jupyterlab
  - ipykernel
  - requests
  - tqdm
  - setuptools
  - wheel

  # --- PIP packages ---
  - pip:
      - pyspark==3.5.1
      - findspark
      - delta-spark
      - kafka-python
      - boto3
      - google-cloud-storage
      - azure-storage-blob
      - sqlalchemy
      - pyodbc
      - oracledb
      - pymysql
```

## 💡 Ghi chú:

* openjdk=11: Spark 3.5 yêu cầu Java 11.
* delta-spark: nếu bạn có dùng Delta Lake (cho realtime/CDC).
* kafka-python: để kết nối Apache Kafka topic.
* oracledb + pyodbc: để đọc/ghi dữ liệu với Oracle, SQL Server.
* azure-storage-blob, google-cloud-storage, boto3: để đọc ghi file trên Cloud (Azure, GCP, AWS).

## Cách sử dụng file:
```makefile
D:\WorkSpace\Python\spark_toturial\environment.yml
```
## Tạo môi trường Conda
```bash
conda env create -f environment.yml
```
## Kích hoạt môi trường
```bash
conda activate spark_env
```
## Kiểm tra
```bash
python -c "import pyspark; print(pyspark.__version__)"
```

# 🧠 3️⃣ (Tuỳ chọn) Chạy Spark với JupyterLab:

## đăng ký kernel để dùng trong Jupyter
```bash
python -m ipykernel install --user --name spark_env --display-name "Spark (PySpark 4.0.1)"
```
## khởi động JupyterLab
```bash
jupyter lab
```

# 🔒 4️⃣ Bảo mật & tương thích (nếu bạn đang trong môi trường ngân hàng)

* Dữ liệu nhạy cảm → nên disable internet access của Conda environment (dùng mirror nội bộ).

* Nếu cluster Spark dùng Kerberos / LDAP → cài thêm:

```bash
pip install requests-kerberos pyspnego
```

* Nếu cần giao tiếp SFTP hoặc SSH:
```bash
pip install paramiko pysftp  
```

# Delta Lake hoặc Kafka Streaming
```bash
pip install "delta-spark>=3.2.0" "kafka-python>=2.0.2"
```

# Khi chạy trên Windows, để tránh lỗi “WinUtils not found”, có thể cài thêm gói giả lập:
```bash
pip install winutils
```

## Window - Java bằng pip (cách dự phòng):

```bash
pip install jdk4spark
```
→ Thư viện này chứa JRE 11 tối giản, tự động giải nén vào .local/jdk trong user folder.

Sau đó thêm biến:

```bat
SET JAVA_HOME=%USERPROFILE%\.local\jdk
SET PATH=%JAVA_HOME%\bin;%PATH%
```

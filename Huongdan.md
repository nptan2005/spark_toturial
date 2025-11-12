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

## Git merge:
### 🚀 local lên GitHub:
```bash
git push origin main
```
### 💡 Kiểm tra nhanh branch tracking:
```bash
git branch -vv
```
### ⚙️ 1️⃣ Thiết lập branch main tracking đúng origin/main
```bash
git branch --set-upstream-to=origin/main main
```
### ⚙️ 2️⃣ Thiết lập hành vi pull chuẩn
1. Để git pull luôn tự động rebase thay vì merge (giữ lịch sử gọn gàng), bạn nên bật:
Thay vì merge, Git đưa các commit local lên đầu của nhánh remote mới nhất:
```css
A---B---C (local)
     \
      D---E (remote)
```
Sau git pull --rebase, Git “chuyển” commit local lên sau E:
```css
A---B---D---E---C'
```
#### 🟢 Ưu điểm:
	*	Lịch sử thẳng hàng, sạch đẹp (linear history).
	*	Dễ đọc, dễ tìm lỗi khi review hoặc bisect.

#### 🔴 Nhược điểm:
	*	Không nên rebase commit đã “push” công khai (vì sẽ thay đổi hash commit).
```bash
git config --global pull.rebase true
```
1. Nếu bạn thích kiểu merge  (ít thay đổi hơn), thì dùng:

```css
A---B---C (local)
     \
      D---E (remote)
```

sau git pull (merge) sẽ thành:

```css
A---B---C--------M
     \          /
      D---E----/
```
#### 🟢 Ưu điểm:
	* Giữ nguyên lịch sử thực tế (bao gồm cả nhánh merge).
	* Dễ xem ai merge, khi nào merge.
#### 🔴 Nhược điểm:
	*	Lịch sử lộn xộn, khó đọc với nhiều “merge commit” dư thừa.
	*	Khi làm teamwork, log nhìn sẽ “rối” (nhiều nhánh giao nhau).


```bash
git config --global pull.rebase false
```
1. ⚙️ 3️⃣ Thiết lập “push default” để Git tự động đẩy đúng nhánh
```bash
git config --global push.default current
```
>Nghĩa là: nếu bạn đang ở main → git push sẽ tự push lên origin/main.

### ✅ Kiểm tra lại cấu hình
Bạn có thể xem toàn bộ config:
```bash
git config --list --show-origin
```
Hoặc chỉ xem các dòng liên quan:
```bash
git config --global --get pull.rebase
git config --global --get push.default
```
### ⚙️ Sử dụng:
#### Nếu làm một mình hoặc code cá nhân → nên dùng:
```bash
git config --global pull.rebase true
```
>(giúp lịch sử gọn, dễ hiểu)

#### Nếu làm team có merge request / pull request rõ ràng → nên dùng:
```bash
git config --global pull.rebase false
```
>(giữ nguyên merge commit để trace dễ dàng)


# Airflow:

## Start:

```bash
airflow webserver -p 8080
```

```bash
airflow scheduler
```

chạy nền

```bash
airflow standalone
```

## 🛑 Dừng tất cả tiến trình Airflow:

```bash
pkill -f "airflow webserver"
pkill -f "airflow scheduler"
```
Hoặc nếu bạn muốn dừng toàn bộ:

```bash
pkill -f airflow
```
✅ Sau đó, kiểm tra lại:

```bash
ps aux | grep airflow
```

## 🧼 (Tuỳ chọn) Dọn log & DB nếu muốn reset sạch

```bash
rm -rf /Users/nptan2005/airflow/airflow.db
rm -rf /Users/nptan2005/airflow/logs/*
```

## Tạo connection Spark trong Airflow
```bash
airflow connections add 'spark_default' \
    --conn-type 'spark' \
    --conn-host 'local[*]' \
    --conn-extra '{"queue":"default"}'
```
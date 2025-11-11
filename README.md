# Spark Toturial:

## learning about spark - hadoop - CDP ##

```css
spark_toturial/             ← this level: run on your pc
│
├─ environment.yml          ← config env for run on your pc
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
|
└─ spark_env/               ← sub project: docker với các thành phần
│
└─ spark-airflow-demo/      ← sub project for example: gonvernance
```
## Giải thích Chi tiết Môi trường Phát triển PySpark (Conda)

Tệp cấu hình [environment.yml](environment.yml) này định nghĩa một môi trường phát triển mạnh mẽ, được tối ưu hóa cho việc phát triển và thử nghiệm các ứng dụng Data Lakehouse (SOT) bằng PySpark trên máy tính cá nhân.

### 1. Vai trò của Conda và các Thư viện

#### Conda (Quản lý Môi trường):

|**Khái niệm**            |  **Vai trò trong Dự án**                 |
|:------------------------|:-----------------------------------------|
|Conda                    |Là hệ thống quản lý môi trường và gói tin (package manager). Conda đảm bảo rằng tất cả các thư viện cần thiết cho Spark (bao gồm Python, Java, và các connectors) được cài đặt trong một môi trường cô lập (spark_env), tránh xung đột với các dự án Python khác trên máy tính của bạn.|
|Channels                  |Các kênh (conda-forge, defaults) là nơi Conda tìm kiếm các gói tin. conda-forge cung cấp các phiên bản cập nhật và đa nền tảng hơn, rất tốt cho các công cụ như openjdk.|

#### Các Thư viện Cốt lõi và Tác dụng

| **Thư viện**            | **Tác dụng**                             | **Liên quan đến Kiến trúc Ngân hàng**       |
|:------------------------|:-----------------------------------------|:--------------------------------------------|
|python=3.10              |Phiên bản ngôn ngữ lập trình chính cho PySpark.|Cung cấp ngôn ngữ cho các job xử lý ELT và ML.|
|openjdk=11|Cung cấp Java Runtime Environment (JRE). Spark được viết bằng Scala/Java, vì vậy nó bắt buộc phải có JRE để chạy (JVM - Java Virtual Machine).|Bắt buộc phải có để khởi động Spark Master/Worker.
|pyspark==4.0.1|Cung cấp giao diện Python cho Apache Spark.|Cung cấp API để viết logic xử lý dữ liệu phân tán (ELT, Masking, SOT).|
|delta-spark|Hỗ trợ định dạng Delta Lake.|Cực kỳ quan trọng. Cho phép bạn xây dựng kiến trúc Lakehouse (SOT) với các tính năng: ACID Transactions, Schema Enforcement, Time Travel.|
|findspark|Giúp các ứng dụng Python dễ dàng tìm thấy thư mục cài đặt Spark.|Tiện ích giúp khởi động nhanh Spark Session trong Jupyter.|
|pyarrow, pandas, numpy|Các thư viện khoa học dữ liệu. PyArrow cải thiện đáng kể tốc độ trao đổi dữ liệu giữa Spark (JVM) và Python (PySpark).|Cải thiện hiệu suất xử lý dữ liệu và tích hợp với các công cụ Data Science.|

#### Các Connector và Tác dụng (Phần pip)

| **Thư viện**                | **Tác dụng**                          | **Liên quan đến Kiến trúc Hybrid**         |
|:----------------------------|:--------------------------------------|:-------------------------------------------|
|kafka-python|Kết nối với Apache Kafka (Cloudera Kafka On-prem).|**Real-time:** Cho phép PySpark đọc/ghi dữ liệu luồng từ Kafka.|
|boto3, google-cloud-storage, azure-storage-blob|Các SDK cho AWS S3, Google Cloud Storage (GCS), và Azure Blob Storage.|**Cloud Storage:** Cho phép PySpark kết nối và đọc/ghi dữ liệu từ Cloud Data Lake trong mô hình Hybrid.|
|sqlalchemy, pyodbc, oracledb, pymysql|Các Driver kết nối đến Cơ sở Dữ liệu.|**Ingestion/Egress:** Cho phép Spark đọc dữ liệu từ các hệ thống lõi truyền thống của ngân hàng.|
|paramiko, pysftp|Kết nối an toàn qua SSH/SFTP.|**Ingestion Batch:** Cần thiết để Spark/các công cụ phụ trợ đọc các file Batch từ các server *On-prem*.|
|requests-kerberos, cryptography, pyspnego|Các thư viện liên quan đến xác thực bảo mật.|**Security/Governance:** Cần thiết để Spark có thể xác thực (ví dụ: Kerberos) và truy cập an toàn vào các tài nguyên của Cloudera CDP On-prem.|

### 2. Apache Spark: Chức năng và Tác dụng

**_Apache Spark_** là một khung tính toán phân tán nguồn mở, được thiết kế để xử lý dữ liệu lớn (Big Data) một cách nhanh chóng.

#### Tác dụng của Spark:

1. **Tốc độ:** Xử lý nhanh hơn gấp 100 lần so với Hadoop MapReduce truyền thống nhờ sử dụng RAM (bộ nhớ trong).
2. **Thống nhất:** Cung cấp một nền tảng duy nhất cho mọi nhu cầu dữ liệu: Batch, Streaming, SQL, và Machine Learning (ML).
3. **Khả năng mở rộng:** Dễ dàng mở rộng từ một máy tính cá nhân lên hàng ngàn node trong môi trường Cloud.

#### Các Thành phần Chức năng Chính của Spark

| **Thành phần**              | **Chức năng**                          | **Ứng dụng trong Ngân hàng**              |
|:----------------------------|:---------------------------------------|:------------------------------------------|
|Spark Core|Nền tảng cơ sở. Quản lý RDDs, phân bổ tác vụ, và I/O.|Cung cấp khả năng tính toán song song, nền tảng cho mọi hoạt động khác.|
|Spark SQL|Xử lý dữ liệu có cấu trúc bằng SQL. Bao gồm DataFrame/Dataset API.|Thực hiện các job ELT (Extract, Load, Transform), tạo ra các bảng SOT (Golden Layer).|
|Spark Streaming|Xử lý dữ liệu luồng.|Real-time: Phát hiện gian lận thẻ, cảnh báo giao dịch.|
|MLlib|Thư viện Machine Learning phân tán.|Huấn luyện các mô hình AI/ML quy mô lớn (Credit Scoring, Customer Churn).|
|GraphX|Thư viện xử lý đồ thị.|Phân tích các mối quan hệ phức tạp (Fraud Ring Detection).|

### 3. Apache Hadoop: Chức năng và Tác dụng

**_Apache Hadoop_** là khung nền tảng cho phép lưu trữ và xử lý dữ liệu lớn trên các cụm máy tính phân tán.
*Lưu ý quan trọng:* Spark vẫn sử dụng các thư viện cốt lõi của Hadoop để thực hiện các chức năng về File System và khả năng tương thích.

#### Tác dụng và Vai trò của Hadoop (ở cấp độ kiến trúc)

1. **Lưu trữ Phân tán:** Cung cấp giải pháp lưu trữ dữ liệu lớn, giá rẻ và chịu lỗi (Fault-tolerant).
2. **Quản lý Tài nguyên:** Quản lý tài nguyên tính toán giữa các ứng dụng khác nhau.
3. **Tương thích:** Đảm bảo Spark có thể đọc và ghi các định dạng file phổ biến trong thế giới Big Data (Parquet, ORC, CSV).

#### Các Thành phần Chức năng Chính của Hadoop

| **Thành phần**                | **Chức năng**                  |**Liên quan đến Spark/Kiến trúc của project này**|
|:------------------------------|:-------------------------------|:------------------------------------------------|
|**HDFS** (Hadoop Distributed File System)|Hệ thống file phân tán, chịu lỗi.|**Storage Abstraction:** Trong môi trường Hybrid, HDFS là nơi lưu trữ dữ liệu Raw (Bronze Layer) On-prem. Spark tương tác với cả HDFS và Cloud Storage thông qua các API tương thích Hadoop.|
|**YARN** (Yet Another Resource Negotiator)|Lớp quản lý tài nguyên (CPU, RAM) của cụm.|**Resource Manager:** Trong môi trường Cloudera, YARN quản lý việc cấp phát tài nguyên cho các ứng dụng Spark (và các job khác).|
|MapReduce|Khung tính toán Batch truyền thống.|**Legacy:** Spark đã thay thế MapReduce.|


## Xem hướng dẫn tại: 
1. Hướng dẫn cấu hình chạy trên PC tại [đây](Huongdan.md)
2. Sub Project: [sub project spark](spark_env/README)
3. sub Project: spark-airflow-demo [gorvernance](spark-airflow-demo/Spark_governance.md)
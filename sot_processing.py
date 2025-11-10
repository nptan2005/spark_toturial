from pyspark.sql import SparkSession
from pyspark.sql.functions import (
                                   col,
                                   concat_ws,
                                   current_timestamp,
                                   lit,
                                   row_number,
                                   sha2,
)
from pyspark.sql.window import Window

# Khởi tạo Spark Session
# SOT_App là tên ứng dụng mô phỏng
spark = SparkSession.builder \
    .appName("SOT_App") \
    .getOrCreate()

# --- 1. BRONZE LAYER (Dữ liệu Thô) ---
print("\n--- BƯỚC 1: XỬ LÝ DỮ LIỆU BRONZE (RAW) ---")

# Dữ liệu khách hàng từ 2 nguồn khác nhau, có sự trùng lặp và thiếu sót
# Nguồn 1: Core Banking (CB) - Dữ liệu Tài khoản/Số dư
data_source_cb = [
    (1, "NGUYEN VAN A", "123456", "nguyena@mail.com", "Hanoi", 10000000),
    (2, "TRAN THI B", "654321", "tranb@mail.com", "HCMC", 5000000),
    (3, "NGUYEN VAN A", "123456", "nguyena@mail.com", "HN", 12000000), # Trùng lặp A
]
columns_cb = ["customer_id", "full_name", "phone", "email", "address", "balance"]
df_cb = spark.createDataFrame(data_source_cb, columns_cb)
df_cb = df_cb.withColumn("source", lit("CoreBanking")).withColumn("load_time", current_timestamp())

# Nguồn 2: CRM - Dữ liệu liên hệ/Trạng thái
data_source_crm = [
    (101, "NGUYEN VAN AN", "123456", "nguyena@mail.net", "Hanoi, Dist 1", "Active"), # A bị sai tên 
    (102, "TRAN THI B", "654321", "tranb@mail.com", "HCM, Dist 3", "Active"),
    (103, "LE VAN C", "111222", "levanc@mail.com", "Danang", "Inactive"),
]
columns_crm = ["crm_id", "full_name", "phone", "email", "full_address", "status"]
df_crm = spark.createDataFrame(data_source_crm, columns_crm)
df_crm = df_crm.withColumn("source", lit("CRM")).withColumn("load_time", current_timestamp())

# Hợp nhất dữ liệu thô
df_bronze = df_cb.select("full_name", "phone", "email", "address", "source", "load_time") \
    .unionByName(
        df_crm.select(
            col("full_name"), 
            col("phone"), 
            col("email"), 
            col("full_address").alias("address"), # Ánh xạ cột địa chỉ
            col("source"), 
            col("load_time")
        )
    )

df_bronze.printSchema()
df_bronze.show(truncate=False)


# --- 2. SILVER LAYER (Làm sạch và Chuẩn hóa) ---
print("\n--- BƯỚC 2: XỬ LÝ DỮ LIỆU SILVER (LÀM SẠCH) ---")

# a) Tạo một khóa nhất quán (Consistent Key) cho việc de-duplication: Hash(Email + Phone)
df_silver = df_bronze.withColumn(
    "unique_key",
    sha2(concat_ws("_", col("email"), col("phone")), 256) # Dùng SHA256 để tạo mã hash
)

# b) Chuẩn hóa tên (ví dụ: Chuyển về chữ hoa, loại bỏ khoảng trắng thừa)
df_silver = df_silver.withColumn("full_name_clean", 
    col("full_name")
)

# c) Loại bỏ các bản ghi trùng lặp (giữ lại bản ghi được nạp gần nhất)
window_spec = Window.partitionBy("unique_key").orderBy(col("load_time").desc())

df_silver_dedup = df_silver.withColumn("row_num", row_number().over(window_spec)) \
                           .filter(col("row_num") == 1) \
                           .drop("row_num", "load_time", "source")

print("Đã làm sạch và loại bỏ trùng lặp (de-duplication):")
df_silver_dedup.show(truncate=False)


# --- 3. GOLD LAYER (SOT - Single Source of Truth) ---
print("\n--- BƯỚC 3: TẠO GOLDEN RECORD (SOT) ---")

# Áp dụng logic SOT: Tạo Golden Record bằng cách hợp nhất các thuộc tính
# Trong SOT, chúng ta chọn thuộc tính tin cậy nhất cho mỗi unique_key
# Ở đây, ta giả định 'full_name_clean', 'phone', 'email' là các thuộc tính SOT
df_sot = df_silver_dedup.select(
    "unique_key",
    "full_name_clean",
    "phone",
    "email",
    "address" # Giữ địa chỉ cuối cùng
)

# Giả định: Dữ liệu SOT phải có TÊN và SĐT
df_sot_final = df_sot.filter(col("full_name_clean").isNotNull() & col("phone").isNotNull()) \
                     .withColumnRenamed("full_name_clean", "SOT_CustomerName") \
                     .withColumn("SOT_CreationDate", current_timestamp())

print("Dữ liệu GOLDEN RECORD (SOT):")
df_sot_final.show(truncate=False)

# Lưu kết quả SOT (Mô phỏng lưu vào Delta Lake/BigQuery)
# Trong môi trường thực tế, bạn sẽ lưu vào Delta Lake hoặc BigQuery.
# Ở đây ta lưu tạm vào một file CSV.
output_path = "data/sot_customer_master"
df_sot_final.write.mode("overwrite").csv(output_path, header=True)
print(f"\n[HOÀN THÀNH] Đã lưu Golden Record (SOT) vào thư mục: {output_path}")

spark.stop()
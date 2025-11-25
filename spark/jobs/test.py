from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("TestOL").getOrCreate()

df = spark.createDataFrame([(1,"A"),(2,"B")], ["id","val"])
df.write.mode("overwrite").parquet("/data/test_ol")

spark.stop()
from pyspark.sql import SparkSession
spark = SparkSession.builder.master("spark://spark-master:7077").appName("smoke-test").getOrCreate()
print("count=", spark.range(1000).count())
spark.stop()
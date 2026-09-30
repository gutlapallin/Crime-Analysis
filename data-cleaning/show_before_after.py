from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("ShowBeforeAfter").getOrCreate()

print("=== Figure 1a – Before cleaning (first 5 rows) ===")
before = spark.read.option("header", True).csv("/home/cs179g/features.csv.gz")
before.show(5)

print("=== Figure 1b – After cleaning (first 5 rows) ===")
after = spark.read.parquet("/home/cs179g/project/CS179G/clean_chicago_crime")
after.show(5)

spark.stop()

# EXECUTE FILE (clean data) spark-submit test.py

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, trim, lower, try_to_timestamp, lit
import time

start = time.time()

spark = SparkSession.builder \
    .appName("ChicagoCrimeClean") \
    .getOrCreate()


crime_df = spark.read.option("header", True).csv("/home/cs179g/features.csv.gz")
#crime_df.printSchema()
#crime_df.show(5)

original_rows = crime_df.count()
original_cols = len(crime_df.columns)

crime_df = crime_df.toDF(
        *[c.lower().replace(" ", "_") for c in crime_df.columns]
)

crime_df = crime_df.dropna(
    subset=["date", "primary_type", "x", "y"]
)

crime_df = crime_df.withColumn(
    "date",
    try_to_timestamp(col("date"), lit("MM/dd/yyyy hh:mm:ss a"))
)

crime_df = crime_df.withColumn(
    "updated_on",
    try_to_timestamp(col("updated_on"), lit("MM/dd/yyyy hh:mm:ss a"))
)


crime_df = crime_df.withColumn(
    "arrest",
    when(lower(trim(col("arrest"))) == "true", True)
    .when(lower(trim(col("arrest"))) == "false", False)
    .otherwise(None)
)

crime_df = crime_df.withColumn(
    "domestic",
    when(lower(trim(col("domestic"))) == "true", True)
    .when(lower(trim(col("domestic"))) == "false", False)
    .otherwise(None)
)


crime_df = crime_df.dropDuplicates(["id"])

#additional words to exclude
keywords = "(?i).*(FISTS|MOTOR VEHICLE|SCOOTER|NON-VEH|NEW STAND).*"
crime_df = crime_df.filter(~col("location_description").rlike(keywords))

crime_df = crime_df.drop(
        "case_number", "block", "iucr", "beat", "district", "ward",
        "fbi_code", "x_coordinate", "y_coordinate", "updated_on", "location"
)

crime_df.write \
     .mode("overwrite") \
    .parquet("/home/cs179g/project/CS179G/clean_chicago_crime")

clean_rows = crime_df.count()
clean_cols = len(crime_df.columns)
print("Rows before:", original_rows)
print("Rows after:", clean_rows)
print("Columns before:", original_cols)
print("Columns after:", clean_cols)
end = time.time()
print("Cleaning runtime:", end-start, "seconds")


crime_df.describe(["x","y"]).show()
crime_df.groupBy("arrest").count().show()
crime_df.groupBy("domestic").count().show()
crime_df.select("primary_type").distinct().count()
spark.stop()


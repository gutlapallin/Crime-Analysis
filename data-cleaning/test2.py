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

print("\nThe Last Row in the Original Dataset is: ")
start_og = time.time(); 
orignal_last_row = crime_df.tail(1)
end_og = time.time()
difference_og = end_og - start_og
print("\nOriginal  Data - Time to Access last row: ", difference_og, " seconds")



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

crime_df = crime_df.drop(
        "case_number", "block", "iucr", "beat", "district", "ward",
        "fbi_code", "x_coordinate", "y_coordinate", "updated_on", "location"
)


print("\nThe Last Row in the New Dataset is: ")
start = time.time()
last_data = crime_df.tail(1)
end = time.time()
difference_new = end - start
print(last_data)
print("\nCleaned Data - Time to Access last row: ", difference_new, " seconds")


print("\nAccessing Time Change: ")
time_improvement = ((difference_og - difference_new) / difference_og) * 100
if time_improvement > 0:
    print(time_improvement, "% faster")

elif time_improvement < 0:
    print(abs(time_improvement), "% slower")

else:
    print("\n- Accessing Time: No significant change")







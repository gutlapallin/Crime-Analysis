from pyspark.sql import SparkSession
from pyspark.sql.functions import col, hour, month, dayofmonth, count, when, date_format

# Start Spark
spark = SparkSession.builder \
    .appName("ChicagoCrimeAnalysis") \
    .getOrCreate()

# Load the cleaned Parquet dataset
crime_df = spark.read.parquet("/home/cs179g/project/CS179G/clean_chicago_crime")
print("Data Loaded Successfully")

# -------------------------
# 1. Time-of-Day Analysis
# -------------------------
crime_df = crime_df.withColumn("hour", hour(col("date")))

daytime_count = crime_df.filter((col("hour") >= 8) & (col("hour") < 16)).count()
evening_count = crime_df.filter((col("hour") >= 16) & (col("hour") < 24)).count()
overnight_count = crime_df.filter((col("hour") >= 0) & (col("hour") < 8)).count()

print("\nAverage hourly crime counts:")
print(f"Daytime (8AM-3:59PM): {daytime_count}")
print(f"Evening (4PM-11:59PM): {evening_count}")
print(f"Overnight (12AM-7:59AM): {overnight_count}")

# -------------------------
# 2. Seasonal / Monthly Trends
# -------------------------
crime_df = crime_df.withColumn("month", month(col("date")))
crime_df = crime_df.withColumn("day", dayofmonth(col("date")))

# Monthly counts
monthly_counts = crime_df.groupBy("month").count().orderBy("month")
print("\nMonthly crime counts:")
monthly_counts.show(12)

# -------------------------
# 3. Holiday Analysis Examples
# -------------------------
# Define holiday filters
christmas = crime_df.filter((col("month") == 12) & (col("day").between(24,26)))
halloween = crime_df.filter((col("month") == 10) & (col("day") == 31))
thanksgiving = crime_df.filter((col("month") == 11) & (col("day").between(22,28)))

# Most common crime type per holiday
print("\nMost common crimes on holidays:")
print("Christmas:")
christmas.groupBy("primary_type").count().orderBy(col("count").desc()).show(1)

print("Halloween:")
halloween.groupBy("primary_type").count().orderBy(col("count").desc()).show(1)

print("Thanksgiving:")
thanksgiving.groupBy("primary_type").count().orderBy(col("count").desc()).show(1)

# -------------------------
# 4. Federal Holidays (example: lower crime)
# -------------------------
# Sample list of federal holidays (month-day format)
federal_holidays = [("01-01"), ("07-04"), ("12-25"), ("11-11")]  # New Year's, Independence, Christmas, Veterans

crime_df = crime_df.withColumn("month_day", date_format(col("date"), "MM-dd"))

holiday_counts = crime_df.filter(col("month_day").isin(federal_holidays)) \
                         .groupBy("month_day").count()
non_holiday_counts = crime_df.filter(~col("month_day").isin(federal_holidays)) \
                             .groupBy("month_day").count()

print("\nCrime counts on federal holidays:")
holiday_counts.show()
print("Crime counts on non-holidays:")
non_holiday_counts.show(5)

# -------------------------
# 5. Great Recession (2007-2009)
# -------------------------
recession_crimes = crime_df.filter((col("year").between("2007","2009")))
most_common_recession_crime = recession_crimes.groupBy("primary_type") \
                                               .count() \
                                               .orderBy(col("count").desc())
print("\nMost common crime during Great Recession (2007-2009):")
most_common_recession_crime.show(1)

# Stop Spark
spark.stop()


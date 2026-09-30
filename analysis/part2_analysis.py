from pyspark.sql import SparkSession
from pyspark.sql import Row
from pyspark.sql.functions import (
    col, when, hour, month, dayofmonth, count, to_date, year,
)
import time
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number
from pyspark.sql.functions import col, count, regexp_replace, trim, upper 

PARQUET_PATH = "/home/cs179g/project/CS179G/clean_chicago_crime"
JDBC_URL = "jdbc:mysql://127.0.0.1:3306/cs179g"
JDBC_USER = "root"
JDBC_PASSWORD = ""
JDBC_DRIVER = "com.mysql.cj.jdbc.Driver"

def normalize_location(location_col):
    n = trim(upper(location_col))

    n = regexp_replace(n, r'\s*/\s*', '/')
    n = regexp_replace(n, r'\s*-\s*', '-')
    n = regexp_replace(n, r'\s*\(\s*', ' (')
    n = regexp_replace(n, r'\s*\)\s*', ')')
    n = regexp_replace(n, r'\.', '')

    n = regexp_replace(n, r'RESIDENCE PORCH/HALLWAY', 'RESIDENCE-PORCH/HALLWAY')
    n = regexp_replace(n, r'RESIDENCE-YARD \(FRONT/BACK\)|RESIDENTIAL YARD \(FRONT/BACK\)', 'RESIDENCE-YARD')
    n = regexp_replace(n, r'VEHICLE NON-COMMERCIAL', 'VEHICLE-NON-COMMERCIAL')
    n = regexp_replace(n, r'OTHER RAILROAD PROP/TRAIN DEPOT|OTHER RAILROAD PROPERTY/TRAIN DEPOT', 'OTHER RAILROAD/TRAIN DEPOT')
    n = regexp_replace(n, r'VEHICLE-OTHER RIDE SHARE.*', 'VEHICLE-RIDE SHARE')
    n = regexp_replace(n, r'AIRPORT TERMINAL.*NON-SECURE.*|AIRPORT TERMINAL MEZZANINE.*', 'AIRPORT TERMINAL-NON-SECURE')
    n = regexp_replace(n, r'AIRPORT TERMINAL.*SECURE.*', 'AIRPORT TERMINAL-SECURE')
    n = regexp_replace(n, r'AIRPORT BUILDING NON-TERMINAL.*', 'AIRPORT BUILDING NON-TERMINAL')
    n = regexp_replace(n, r'AIRPORT EXTERIOR.*|AIRPORT TRANSPORTATION SYSTEM.*', 'AIRPORT EXTERIOR')
    n = regexp_replace(n, r'AIRPORT PARKING LOT', 'PARKING LOT/GARAGE-NON-RESIDENTIAL')
    n = regexp_replace(n, r'SCHOOL-PUBLIC BUILDING|SCHOOL-PUBLIC GROUNDS', 'SCHOOL-PUBLIC')
    n = regexp_replace(n, r'SCHOOL-PRIVATE BUILDING|SCHOOL-PRIVATE GROUNDS', 'SCHOOL-PRIVATE')
    n = regexp_replace(n, r'VEHICLE-COMMERCIAL-ENTERTAINMENT/PARTY BUS|VEHICLE-COMMERCIAL-TROLLEY BUS|VEHICLE-DELIVERY TRUCK|DELIVERY TRUCK', 'VEHICLE-COMMERCIAL-SPECIALTY')
    n = regexp_replace(n, r'SAVINGS AND LOAN|CREDIT UNION', 'BANK/CREDIT UNION')
    n = regexp_replace(n, r'^BANK$', 'BANK/CREDIT UNION')
    n = regexp_replace(n, r'COIN OPERATED MACHINE|AIRPORT VENDING ESTABLISHMENT|NEWSSTAND', 'VENDING/COIN MACHINE/NEWSSTAND')
    n = regexp_replace(n, r'APPLIANCE STORE|PAWN SHOP|CLEANING STORE|BARBERSHOP|CAR WASH', 'SPECIALTY RETAIL/SERVICE')
    n = regexp_replace(n, r'POOL ROOM|BOWLING ALLEY|ATHLETIC CLUB', 'RECREATION FACILITY')
    n = regexp_replace(n, r'CEMETARY|FOREST PRESERVE|FARM|KENNEL|ANIMAL HOSPITAL|HORSE STABLE', 'NATURE/FARM/ANIMAL FACILITY')
    n = regexp_replace(n, r'^BOAT/WATERCRAFT$|^AIRCRAFT$', 'BOAT/AIRCRAFT')
    n = regexp_replace(n, r'FIRE STATION|JAIL/LOCK-UP FACILITY|FEDERAL BUILDING|GOVERNMENT BUILDING/PROPERTY', 'GOVERNMENT FACILITY')
    n = regexp_replace(n, r'DAY CARE CENTER', 'SCHOOL-OTHER/DAY CARE')
    n = regexp_replace(n, r'COLLEGE/UNIVERSITY RESIDENCE HALL', 'COLLEGE/UNIVERSITY-GROUNDS')
    n = regexp_replace(n, r'CTA TRACKS-RIGHT OF WAY|^CTA PLATFORM$', 'CTA PLATFORM/TRACKS')
    n = regexp_replace(n, r'CTA GARAGE/OTHER PROPERTY', 'CTA PARKING LOT/GARAGE')
    n = regexp_replace(n, r'DRIVEWAY-RESIDENTIAL', 'RESIDENCE-YARD')
    n = regexp_replace(n, r'VACANT LOT/LAND|ABANDONED BUILDING', 'ABANDONED BUILDING/VACANT LOT')
    n = regexp_replace(n, r'OTHER \(SPECIFY\)', 'OTHER')

    return n



def main():
    start_total = time.time()

    spark = SparkSession.builder \
        .appName("ChicagoCrimePart2") \
        .getOrCreate()

    print("Reading cleaned data from Parquet...")
    df = spark.read.parquet(PARQUET_PATH)
    df = df.withColumn("hour", hour(col("date")))
    df = df.withColumn("month", month(col("date")))
    df = df.withColumn("day", dayofmonth(col("date")))
    df = df.withColumn("date_only", to_date(col("date")))
    df = df.withColumn("year", year(col("date")).cast("int"))

    hourly_crimes = df.groupBy("hour").agg(count("*").alias("crime_count")).orderBy("hour")
    write_to_mysql(hourly_crimes, "hourly_crimes", spark)

    time_period_crimes = df.withColumn(
        "time_period",
        when((col("hour") >= 8) & (col("hour") <= 15), "Daytime")
        .when((col("hour") >= 16) & (col("hour") <= 23), "Evening")
        .otherwise("Overnight")
    ).groupBy("time_period").agg(count("*").alias("total_crimes"))
    write_to_mysql(time_period_crimes, "time_period_crimes", spark)

    monthly_crimes = df.groupBy("month").agg(count("*").alias("total_crimes")).orderBy("month")
    write_to_mysql(monthly_crimes, "monthly_crimes", spark)

    season_crimes = df.withColumn(
        "season",
        when(col("month").isin(6, 7, 8), "Summer")
        .when(col("month").isin(1, 2), "Late Winter")
        .otherwise("Other")
    ).groupBy("season").agg(count("*").alias("total_crimes"))
    write_to_mysql(season_crimes, "season_crimes", spark)

    christmas = df.filter(col("month") == 12).groupBy("primary_type").agg(count("*").alias("total")).orderBy(col("total").desc())
    write_to_mysql(christmas, "christmas_by_type", spark)
    
    df_with_christmas_flag = df.withColumn("day_type",when(col("month") == 12, "Christmas").otherwise("Non-Christmas"))

    property_crimes = ["THEFT", "BURGLARY", "ROBBERY"]
    df_property = df_with_christmas_flag.filter(col("primary_type").isin(property_crimes))

    christmas_distribution = df_property.groupBy("day_type", "primary_type") \
                                        .agg(count("*").alias("total"))

    write_to_mysql(christmas_distribution, "christmas_vs_nonchristmas_by_type", spark)

    halloween = df.filter((col("month") == 10) & (col("day") == 31)).groupBy("primary_type").agg(count("*").alias("total")).orderBy(col("total").desc())
    write_to_mysql(halloween, "halloween_by_type", spark)
    
    df_with_halloween_flag = df.withColumn(
        "day_type",
        when((col("month") == 10) & (col("day") == 31), "Halloween").otherwise("Non-Halloween")
    )
    top_halloween_crimes = ["ASSAULT", "BATTERY", "PUBLIC PEACE VIOLATION"]
    df_top_crimes = df_with_halloween_flag.filter(col("primary_type").isin(top_halloween_crimes))
    halloween_distribution = df_top_crimes.groupBy("day_type", "primary_type").agg(count("*").alias("total"))
    write_to_mysql(halloween_distribution, "halloween_vs_nonhalloween_by_type", spark)

    thanksgiving_dates = ["2020-11-26","2019-11-28","2018-11-22","2017-11-23","2016-11-24","2015-11-26","2014-11-27","2013-11-28","2012-11-22","2011-11-24","2010-11-25","2009-11-26","2008-11-27","2007-11-22","2006-11-23","2005-11-24","2004-11-25","2003-11-27","2002-11-28","2001-11-22","2000-11-23"]
    thanksgiving = df.filter(col("date_only").cast("string").isin(thanksgiving_dates)).groupBy("primary_type").agg(count("*").alias("total")).orderBy(col("total").desc())
    write_to_mysql(thanksgiving, "thanksgiving_by_type", spark)
    
    df_with_thanksgiving_flag = df.withColumn(
        "day_type",
        when(col("date_only").cast("string").isin(thanksgiving_dates), "Thanksgiving")
        .otherwise("Non-Thanksgiving")
    )

    top_thanksgiving_crimes = ["BATTERY", "THEFT", "CRIMINAL DAMAGE", "ASSAULT"]
    df_top_thanksgiving_crimes = df_with_thanksgiving_flag.filter(col("primary_type").isin(top_thanksgiving_crimes))

    thanksgiving_distribution = df_top_thanksgiving_crimes.groupBy("day_type", "primary_type") \
        .agg(count("*").alias("total"))

    write_to_mysql(thanksgiving_distribution, "thanksgiving_vs_nonthanksgiving_by_type", spark)
    from pyspark.sql.functions import regexp_replace, trim

    df = df.withColumn(
        "location_description",
        trim(regexp_replace(col("location_description"), r"\s*/\s*", "/"))
    )

    sport_locations_df = df.filter(
    (col("location_description").isNotNull()) &
    (col("location_description") != "") &
    (col("location_description").rlike(r"(?i)\bsports?\b"))
    )

    sport_locations_df = sport_locations_df.withColumn(
    "crime_category",
    when(col("primary_type").isin("THEFT", "MOTOR VEHICLE THEFT", "BURGLARY"), "Theft")
    .when(col("primary_type").isin("ASSAULT", "BATTERY"), "Assault & Battery")
    .when(col("primary_type").isin("ROBBERY", "KIDNAPPING"), "Robbery & Kidnapping")
    .when(col("primary_type").isin("CRIM SEXUAL ASSAULT", "SEX OFFENSE", "INTIMIDATION", "STALKING"), "Violent Crime")
    .when(col("primary_type").isin("CRIMINAL DAMAGE", "ARSON"), "Property Damage")
    .when(col("primary_type").isin("NARCOTICS", "LIQUOR LAW VIOLATION", "PUBLIC INDECENCY", "PROSTITUTION"), "Vice & Substances")
    .when(col("primary_type").isin("CRIMINAL TRESPASS", "PUBLIC PEACE VIOLATION", "INTERFERENCE WITH PUBLIC OFFICER", "CONCEALED CARRY LICENSE VIOLATION", "WEAPONS VIOLATION"), "Public Order")
    .when(col("primary_type").isin("DECEPTIVE PRACTICE"), "Fraud & Deception")
    .when(col("primary_type").isin("OFFENSE INVOLVING CHILDREN"), "Crimes Against Children")
    .otherwise("Other")
    )   

    crimes_sport_locations = sport_locations_df.groupby("crime_category").agg(
    count("*").alias("total_crimes")
    ).orderBy(col("total_crimes").desc())

    write_to_mysql(crimes_sport_locations, "sport_location_crimes", spark)

    df_location = (
        df
        .filter(col("location_description").isNotNull() & (col("location_description") != ""))
        .withColumn("location_normalized", normalize_location(col("location_description")))
    )

    theft_counts = (
        df_location
        .filter(col("primary_type") == "THEFT")
        .groupBy("location_normalized")
        .agg(count("*").alias("total_thefts"))
    )

    total_counts = (
        df_location
        .groupBy("location_normalized")
        .agg(count("*").alias("total_crimes"))
    )

    theft_vs_total = (
        theft_counts
        .join(total_counts, on="location_normalized", how="inner")
        .withColumnRenamed("location_normalized", "location_description")
        .orderBy(col("total_thefts").desc())
    )

    write_to_mysql(theft_vs_total, "theft_by_location", spark)

    holidays_df = spark.read \
        .format("jdbc") \
        .option("url", JDBC_URL) \
        .option("dbtable", "holidays") \
        .option("user", JDBC_USER) \
        .option("password", JDBC_PASSWORD) \
        .option("driver", JDBC_DRIVER) \
        .load()
    holidays_df = holidays_df.withColumn("holiday_date", col("holiday_date").cast("date"))
    df_with_holiday = df.join(holidays_df, df["date_only"] == holidays_df["holiday_date"], "left")
    holiday_vs = df_with_holiday.withColumn(
        "day_type", when(col("holiday_date").isNotNull(), "Holiday").otherwise("Non-Holiday")
    ).groupBy("day_type").agg(count("*").alias("total_crimes"))
    write_to_mysql(holiday_vs, "holiday_vs_nonholiday", spark)

    great_recession = df.filter(col("year").isin(2007, 2008, 2009)).groupBy("primary_type").agg(count("*").alias("total")).orderBy(col("total").desc())
    write_to_mysql(great_recession, "great_recession_by_type", spark)

    yearly_crimes = df.groupBy("year").agg(count("*").alias("total_crimes")).orderBy("year")
    write_to_mysql(yearly_crimes, "yearly_crimes", spark)


    keywords = "(?i).*(FISTS|MOTOR VEHICLE|SCOOTER|NON-VEH|NON-MOTOR VEHICLE|NEW STAND).*"

    df_location = df.filter(
    col("location_description").isNotNull() & 
    (col("location_description") != "") &
    ~col("location_description").rlike(keywords)
    ).withColumn("location_category",
    when(col("location_description").rlike("(?i)(RESIDENCE|APARTMENT|HOUSE|ROOMING|DRIVEWAY - RES|RESIDENTIAL YARD|RESIDENCE PORCH|RESIDENCE-GARAGE|CHA )"), "Residential")
    .when(col("location_description").rlike("(?i)(STREET|SIDEWALK|ALLEY|HIGHWAY|EXPRESSWAY|BRIDGE)"), "Street/Outdoors")
    .when(col("location_description").rlike("(?i)(CTA |TRAIN|RAILROAD|TRANSIT|PLATFORM|SUBWAY|BUS)"), "Public Transit")
    .when(col("location_description").rlike("(?i)(AIRPORT|AIRCRAFT)"), "Airport")
    .when(col("location_description").rlike("(?i)(PARKING LOT|PARKING|GARAGE)"), "Parking Lot")
    .when(col("location_description").rlike("(?i)(SCHOOL|COLLEGE|UNIVERSITY|DAY CARE)"), "Education")
    .when(col("location_description").rlike("(?i)(RESTAURANT|BAR|TAVERN|NIGHT CLUB|CAFE)"), "Restraunt Area")
    .when(col("location_description").rlike("(?i)(GROCERY|DRUG STORE|DEPARTMENT STORE|SMALL RETAIL|RETAIL|CONVENIENCE|APPLIANCE|BARBERSHOP)"), "Retail/Stores")
    .when(col("location_description").rlike("(?i)(BANK|CURRENCY EXCHANGE|CREDIT UNION|SAVINGS|ATM)"), "Financial")
    .when(col("location_description").rlike("(?i)(HOSPITAL|MEDICAL|DENTAL|NURSING|CLINIC)"), "Medical")
    .when(col("location_description").rlike("(?i)(PARK|FOREST|LAKEFRONT|BEACH|ATHLETIC|SPORTS|STADIUM|YMCA)"), "Parks/Recreation")
    .when(col("location_description").rlike("(?i)(HOTEL|MOTEL)"), "Hotel/Lodging")
    .when(col("location_description").rlike("(?i)(VACANT|ABANDONED|CONSTRUCTION|WAREHOUSE|FACTORY)"), "Vacant/Industrial")
    .otherwise("Other")
    )

    crimes_by_location = df_location.groupBy("location_category") \
    .agg(count("*").alias("total_crimes")) \
    .orderBy(col("total_crimes").desc())
    write_to_mysql(crimes_by_location, "crimes_by_location", spark)

    crimes_by_location_and_type = df_location.groupBy("location_category", "primary_type") \
    .agg(count("*").alias("total"))

    location_totals = df_location.groupBy("location_category") \
    .agg(count("*").alias("location_total"))

    joined = crimes_by_location_and_type.join(location_totals, on="location_category", how="inner")

    windowSpec = Window.partitionBy("location_category").orderBy(col("total").desc())
    ranked = joined.withColumn("rank", row_number().over(windowSpec))

    top_crime_per_category = ranked.filter(col("rank") == 1).drop("rank")
    write_to_mysql(top_crime_per_category, "crimes_by_location_and_type", spark)
    
    location_type_counts = df_location.groupBy("location_description", "primary_type").agg(count("*").alias("total"))
    location_totals = df_location.groupBy("location_description").agg(count("*").alias("location_total"))
    location_totals_filtered = location_totals.filter(col("location_total") > 100)
    joined = location_type_counts.join(location_totals_filtered,on="location_description",how="inner")
    windowSpec = Window.partitionBy("location_description").orderBy(col("total").desc())
    ranked = joined.withColumn("rank",row_number().over(windowSpec))
    
    df_community = df.filter(col("community_area").isNotNull() & (col("community_area") != ""))
    community_area_crimes = df_community.groupBy("community_area").agg(count("*").alias("total_crimes")).orderBy(col("total_crimes").desc())
    write_to_mysql(community_area_crimes, "community_area_crimes", spark)

    df_area = df.filter(col("community_area").isNotNull() & (col("community_area") != ""))

    downtown_ids = [32, 8, 33, 28]

    df_area = df_area.withColumn(
        "area_type",
        when(col("community_area").isin(downtown_ids), "Downtown")
        .otherwise("Residential")
    )

    area_totals = (
        df_area.groupBy("area_type")
        .agg(count("*").alias("total_crimes"))
    )

    area_tr = (
        df_area.filter(col("primary_type").isin("THEFT", "ROBBERY"))
        .groupBy("area_type")
        .agg(count("*").alias("tr_crimes"))
    )

    downtown_vs_residential = (
        area_tr.join(area_totals, "area_type")
        .withColumn("rate", col("tr_crimes") / col("total_crimes"))
    )

    write_to_mysql(downtown_vs_residential, "downtown_vs_residential_theft_robbery", spark)

    df_loc = df.filter(col("location_description").isNotNull())

   
    locations_categorized = df_loc.withColumn(
        "location_type",
        when(col("location_description").rlike(r"(?i)(TRAIN|BUS|TRANSIT|STATION)"), "Public Transit")
        .when(col("location_description").rlike(r"(?i)(COMMERCIAL|STORE|SHOP|MARKET)"), "Commercial")
        .otherwise("Other")
    )

    robbery_counts = locations_categorized.filter(col("primary_type") == "ROBBERY") \
        .groupBy("location_type") \
        .agg(count("*").alias("robbery_count"))
    
    total_crimes = locations_categorized.groupBy("location_type") \
        .agg(count("*").alias("total_crimes"))

    robbery_by_location = robbery_counts.join(total_crimes, "location_type") \
        .withColumn("robbery_rate", col("robbery_count") / col("total_crimes"))

    write_to_mysql(robbery_by_location, "transit_vs_commercial_robbery_count", spark)

    df_loc_categorized = df.filter(col("location_description").isNotNull()).withColumn(
        "location_type", 
        when(col("location_description").rlike(r"(?i)AIR(PORT|CRAFT)"), "Airport")
        .when(col("location_description").rlike(r"(?i)(COMMERCIAL|STORE|SHOP|MARKET)"), "Commercial")
        .when(col("location_description").rlike(r"(?i)(RESIDENTIAL|HOME|HOUSE|NEIGHBORHOOD|APARTMENT)"), "Residential")
        .when(col("location_description").rlike(r"(?i)(TRAIN|BUS|TRANSIT|STATION)"), "Public Transit")
        .otherwise("Uncategorized")
    )

    theft_counts = df_loc_categorized.filter(col("primary_type") == "THEFT") \
        .groupBy("location_type") \
        .agg(count("*").alias("theft_count"))

    total_crimes = df_loc_categorized.groupBy("location_type") \
        .agg(count("*").alias("total_crimes"))

    theft_comparison = theft_counts.join(total_crimes, "location_type") \
        .withColumn("theft_rate", col("theft_count") / col("total_crimes"))

    write_to_mysql(theft_comparison, "airport_theft_count_comparison", spark)
    
    elapsed = time.time() - start_total
    
    print()
    print()
    print("----------------------------------------------")
    print("Total runtime: {:.2f} seconds".format(elapsed))
    print("----------------------------------------------")
    print()
    print()

    spark.stop()

    


def write_to_mysql(dataframe, table, spark):
    dataframe.write \
        .format("jdbc") \
        .option("url", JDBC_URL) \
        .option("dbtable", table) \
        .option("user", JDBC_USER) \
        .option("password", JDBC_PASSWORD) \
        .option("driver", JDBC_DRIVER) \
        .mode("overwrite") \
        .save()
    print("Wrote table:", table)


if __name__ == "__main__":
    main()

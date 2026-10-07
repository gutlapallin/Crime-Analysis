import time
from raw_engine import validate_raw_sql, run_raw

good = [
    "SELECT primary_type, COUNT(*) AS n FROM crimes GROUP BY primary_type ORDER BY n DESC LIMIT 5",
    "SELECT COUNT(*) AS n FROM crimes WHERE month(date)=7 AND day(date)=4 AND year=2019",
    "WITH t AS (SELECT community_area, COUNT(*) AS n FROM crimes GROUP BY 1) SELECT * FROM t ORDER BY n DESC LIMIT 3",
    "SELECT location_description, COUNT(*) AS n FROM crimes GROUP BY 1 ORDER BY n DESC LIMIT 10",
]
bad = [
    "DROP TABLE crimes",
    "SELECT * FROM read_parquet('/etc/passwd')",
    "SELECT * FROM other_table",
    "SELECT 1; SELECT 2",
    "SELECT getenv('GEMINI_API_KEY')",
    "COPY crimes TO 'x.csv'",
]

print("=== should run ===")
for q in good:
    t = time.time()
    rows = run_raw(validate_raw_sql(q))
    print(f"{time.time()-t:.1f}s  {rows[:3]}")

print("\n=== should be blocked ===")
for q in bad:
    try:
        validate_raw_sql(q)
        print("NOT BLOCKED:", q)
    except Exception as e:
        print("blocked:", q, "->", e)

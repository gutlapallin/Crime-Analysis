import os
import re
import threading

import duckdb
import sqlglot
from sqlglot import exp

RAW_GLOB = os.getenv("RAW_PARQUET_GLOB", "clean_chicago_crime/*.parquet")

# Typed view over the parquet files. The model only ever sees this table.
VIEW_SQL = """
CREATE VIEW crimes AS
SELECT
  id,
  date,
  TRY_CAST(year AS INTEGER) AS year,
  primary_type,
  description,
  location_description,
  arrest,
  domestic,
  TRY_CAST(community_area AS INTEGER) AS community_area,
  TRY_CAST(x AS DOUBLE) AS longitude,
  TRY_CAST(y AS DOUBLE) AS latitude
FROM read_parquet('{glob}')
"""

RAW_SCHEMA = (
    "crimes(id VARCHAR, date TIMESTAMP, year INTEGER, primary_type VARCHAR, "
    "description VARCHAR, location_description VARCHAR, arrest BOOLEAN, "
    "domestic BOOLEAN, community_area INTEGER, longitude DOUBLE, latitude DOUBLE)"
    " -- one row per reported crime, about 7 million rows"
)

BLOCKED = re.compile(
    r"\b(read_\w+|glob|getenv|current_setting|pragma|install|load|attach|copy|export|"
    r"system|httpfs)\b",
    re.I,
)


def validate_raw_sql(sql):
    sql = sql.strip().strip("`")
    sql = re.sub(r"^sql\s+", "", sql, flags=re.I).strip().rstrip(";")
    if ";" in sql:
        raise ValueError("Multiple statements are not allowed")
    if BLOCKED.search(sql):
        raise ValueError("Query uses a blocked keyword or function")
    tree = sqlglot.parse_one(sql, read="duckdb")
    if not isinstance(tree, exp.Select):
        raise ValueError("Only SELECT queries are allowed")
    cte_names = {c.alias for c in tree.find_all(exp.CTE)}
    for t in tree.find_all(exp.Table):
        if not isinstance(t.this, exp.Identifier):
            raise ValueError("Table functions are not allowed")
        if t.name != "crimes" and t.name not in cte_names:
            raise ValueError(f"Table not allowed: {t.name}")
    if not tree.args.get("limit"):
        tree = tree.limit(200)
    return tree.sql(dialect="duckdb")


def _connect():
    con = duckdb.connect(":memory:")
    con.execute("SET memory_limit='1GB'")
    con.execute("SET threads=2")
    con.execute(VIEW_SQL.format(glob=RAW_GLOB.replace("'", "''")))
    return con


def run_raw(sql, timeout=15):
    con = _connect()
    timer = threading.Timer(timeout, con.interrupt)
    timer.start()
    try:
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        timer.cancel()
        con.close()

"""Forecast monthly Chicago crime from the monthly_trend table in MySQL.

Run after the Spark ETL (part2_analysis.py) has written monthly_trend.
"""
import os

import pandas as pd
import pymysql


def connect():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "cs179g"),
    )


def load_series(conn):
    """Return citywide monthly crime counts as a Series indexed by month start."""
    df = pd.read_sql(
        "SELECT year, month, total_crimes FROM monthly_trend ORDER BY year, month",
        conn,
    )
    dates = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
    series = pd.Series(df["total_crimes"].astype(float).values, index=dates, name="ALL")

    # A regular monthly frequency is required by statsmodels; any missing month
    # would show up as NaN here, so fail loudly instead of forecasting on gaps.
    series = series.asfreq("MS")
    missing = series[series.isna()].index
    if len(missing):
        raise ValueError(f"monthly_trend is missing months: {[d.strftime('%Y-%m') for d in missing]}")
    return series


def main():
    conn = connect()
    try:
        series = load_series(conn)
    finally:
        conn.close()

    print(f"Loaded {len(series)} months: {series.index[0]:%Y-%m} to {series.index[-1]:%Y-%m}")
    print(series.tail(6).to_string())


if __name__ == "__main__":
    main()

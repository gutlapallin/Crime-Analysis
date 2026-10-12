import os
import pandas as pd
import pymysql
BACKTEST_TRAIN_END = "2019-02"
BACKTEST_START = "2019-03"
BACKTEST_END = "2020-02"
TRAIN_END = "2020-02"
COVID_START = "2020-03"
COVID_END = "2020-06"
HORIZON = 12  # months to forecast


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

def split_periods(series,start=None):

    return {
        "backtest_train": series[start:BACKTEST_TRAIN_END],
        "backtest_test": series[BACKTEST_START:BACKTEST_END],
        "train": series[start:TRAIN_END],
        "covid": series[COVID_START:COVID_END],
        "forecast_dates": pd.date_range(start=COVID_START, periods=HORIZON, freq="MS"),
    }

def main():
    conn = connect()
    try:
        series = load_series(conn)
    finally:
        conn.close()

        print(f"Loaded {len(series)} months: {series.index[0]:%Y-%m} to {series.index[-1]:%Y-%m}")

        periods = split_periods(series)
        for name, part in periods.items():
            dates = part if name == "forecast_dates" else part.index
            print(f"  {name:<15} {len(dates):>3} months  {dates[0]:%Y-%m} -> {dates[-1]:%Y-%m}")

if __name__ == "__main__":
    main()

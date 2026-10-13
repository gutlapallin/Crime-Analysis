import os
import pandas as pd
import pymysql
import warnings
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
BACKTEST_TRAIN_END = "2019-02"
BACKTEST_START = "2019-03"
BACKTEST_END = "2020-02"
TRAIN_END = "2020-02"
COVID_START = "2020-03"
COVID_END = "2020-06"
HORIZON = 12  # months to forecast

# Combinations to compare in the backtest. None = start from the first month.
TRAIN_STARTS = [None, "2012-01"]
SEASONAL_TYPES = ["mul", "add"]


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
    with conn.cursor() as cur:
        cur.execute("SELECT year, month, total_crimes FROM monthly_trend ORDER BY year, month")
        rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["year", "month", "total_crimes"])
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

def mae(actual, predicted):
    """Average size of the error, in crimes per month."""
    return float((actual - predicted).abs().mean())


def mape(actual, predicted):
    """Average error as a percentage of the actual value (skips months with 0 crimes)."""
    nonzero = actual != 0
    errors = (actual[nonzero] - predicted[nonzero]).abs() / actual[nonzero]
    return float(errors.mean() * 100)


def seasonal_naive(series, dates):
    """Baseline forecast: each month equals the same month one year earlier."""
    return series.shift(12).reindex(dates)

def fit_and_forecast(train, dates, seasonal="mul", alpha=0.2):
    """Fit Holt-Winters (ETS) on train and forecast the given dates.

    Returns a DataFrame indexed by date with predicted, lower and upper columns;
    alpha=0.2 gives an 80% prediction interval.
    """
    model = ETSModel(
        train,
        error="mul",
        trend="add",
        damped_trend=True,
        seasonal=seasonal,
        seasonal_periods=12,
    )
    # The optimizer often warns about convergence even when the fit is fine;
    # hide that noise and judge the model by its backtest error instead.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = model.fit(disp=False)

    frame = result.get_prediction(start=dates[0], end=dates[-1]).summary_frame(alpha=alpha)
    frame = frame.rename(columns={"mean": "predicted", "pi_lower": "lower", "pi_upper": "upper"})
    return frame[["predicted", "lower", "upper"]]

def choose_model(series):
    """Backtest every training-start / seasonality combination, best (lowest MAPE) first."""
    results = []
    for start in TRAIN_STARTS:
        periods = split_periods(series, start)
        actual = periods["backtest_test"]
        for seasonal in SEASONAL_TYPES:
            forecast = fit_and_forecast(periods["backtest_train"], actual.index, seasonal=seasonal)
            results.append({
                "train_start": start or f"{series.index[0]:%Y-%m}",
                "start": start,
                "seasonal": seasonal,
                "mae": mae(actual, forecast["predicted"]),
                "mape": mape(actual, forecast["predicted"]),
            })
    results = pd.DataFrame(results).sort_values("mape").reset_index(drop=True)
    return results, results.iloc[0]


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

    # Baseline accuracy on the backtest year (Mar 2019 - Feb 2020)
    actual = periods["backtest_test"]
    baseline = seasonal_naive(series, actual.index)
    baseline_mape = mape(actual, baseline)
    print(f"\nBaseline (seasonal naive)  MAE {mae(actual, baseline):,.0f}   MAPE {baseline_mape:.1f}%")

    # Compare training windows and seasonality types on the same backtest year
    results, best = choose_model(series)
    print("\nHolt-Winters (ETS) comparison, backtest Mar 2019 - Feb 2020:")
    print(results[["train_start", "seasonal", "mae", "mape"]]
          .round({"mae": 0, "mape": 2}).to_string(index=False))
    print(f"\nBest: train from {best['train_start']}, seasonal={best['seasonal']}, "
          f"MAPE {best['mape']:.1f}% (baseline {baseline_mape:.1f}%)")

    # Month-by-month view of the best model
    best_periods = split_periods(series, best["start"])
    forecast = fit_and_forecast(best_periods["backtest_train"], actual.index, seasonal=best["seasonal"])
    table = pd.DataFrame({
        "actual": actual,
        "baseline": baseline,
        "model": forecast["predicted"],
        "lower": forecast["lower"],
        "upper": forecast["upper"],
    }).round(0)
    inside = ((actual >= forecast["lower"]) & (actual <= forecast["upper"])).sum()
    print()
    print(table.to_string())
    print(f"\n{inside} of {len(actual)} actual months fall inside the 80% interval")


if __name__ == "__main__":
    main()

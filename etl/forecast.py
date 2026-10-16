import inspect
import os

import numpy as np
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

# Per-crime-type forecasts (3.8): the most common types in the last full
# pre-COVID year; smaller types are too noisy to forecast well.
TOP_TYPES = 8
RANK_YEAR = 2019


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


def load_type_series(conn, index, top_n=TOP_TYPES):
    """Return {crime type: monthly Series} for the top_n types by RANK_YEAR total.

    Months with no crimes of a type have no row in monthly_trend_by_type, so
    they are filled with 0 on the same monthly index as the citywide series.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT primary_type FROM monthly_trend_by_type WHERE year = %s "
            "GROUP BY primary_type ORDER BY SUM(total) DESC LIMIT %s",
            (RANK_YEAR, top_n),
        )
        types = [row[0] for row in cur.fetchall()]
        placeholders = ", ".join(["%s"] * len(types))
        cur.execute(
            "SELECT primary_type, year, month, total FROM monthly_trend_by_type "
            f"WHERE primary_type IN ({placeholders})",
            types,
        )
        rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=["primary_type", "year", "month", "total"])
    df["date"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
    wide = df.pivot(index="date", columns="primary_type", values="total")
    wide = wide.reindex(index).fillna(0).astype(float)
    return {t: wide[t].rename(t).asfreq("MS") for t in types}


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

    # The interval is simulated from random draws; a fixed seed makes it
    # identical on every run. statsmodels renamed the seed argument from
    # random_state to rng, so pass whichever this version accepts.
    seed_arg = "rng" if "rng" in inspect.signature(result.simulate).parameters else "random_state"
    frame = result.get_prediction(
        start=dates[0], end=dates[-1], **{seed_arg: np.random.RandomState(0)}
    ).summary_frame(alpha=alpha)
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


def covid_gap(forecast, actual):
    """Compare actual counts with the forecast for the months where both exist.

    gap_pct is relative to the forecast: -30 means crime was 30% below what the
    model expected without COVID.
    """
    table = forecast.join(actual.rename("actual"), how="inner")
    table["gap"] = table["actual"] - table["predicted"]
    table["gap_pct"] = table["gap"] / table["predicted"] * 100
    table["below_interval"] = table["actual"] < table["lower"]
    overall_pct = (table["actual"].sum() / table["predicted"].sum() - 1) * 100
    return table, float(overall_pct)


def analyze_series(series, start, seasonal):
    """Backtest, forecast and COVID gap for one series with a fixed model setup.

    Returns (summary dict, 12-month forecast, COVID gap table), or None when the
    series has months with no crimes, which a multiplicative-error model can't fit.
    """
    periods = split_periods(series, start)
    if (periods["train"] <= 0).any():
        return None

    actual = periods["backtest_test"]
    baseline = seasonal_naive(series, actual.index)
    backtest = fit_and_forecast(periods["backtest_train"], actual.index, seasonal=seasonal)
    forecast = fit_and_forecast(periods["train"], periods["forecast_dates"], seasonal=seasonal)
    gap_table, overall_gap = covid_gap(forecast, periods["covid"])

    summary = {
        "series": series.name,
        "baseline_mape": mape(actual, baseline),
        "model_mape": mape(actual, backtest["predicted"]),
        "covid_gap_pct": overall_gap,
        "worst_month_gap_pct": float(gap_table["gap_pct"].min()),
        "months_below": int(gap_table["below_interval"].sum()),
    }
    return summary, forecast, gap_table


def main():
    conn = connect()
    try:
        series = load_series(conn)
        type_series = load_type_series(conn, series.index)
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

    # Final model: winning setup trained on everything up to Feb 2020
    final_periods = split_periods(series, best["start"])
    final_forecast = fit_and_forecast(
        final_periods["train"], final_periods["forecast_dates"], seasonal=best["seasonal"]
    )

    # COVID gap: actual Mar-Jun 2020 vs. what the model expected
    gap_table, overall_gap = covid_gap(final_forecast, final_periods["covid"])
    print(f"\nCOVID period (model trained {best['train_start']} to {TRAIN_END}):")
    print(gap_table[["actual", "predicted", "lower", "upper", "gap", "gap_pct", "below_interval"]]
          .round({"actual": 0, "predicted": 0, "lower": 0, "upper": 0, "gap": 0, "gap_pct": 1})
          .to_string())
    print(f"\nOverall Mar-Jun 2020: crime was {abs(overall_gap):.1f}% "
          f"{'below' if overall_gap < 0 else 'above'} the no-COVID forecast")

    # Full 12-month forecast (saved to MySQL in 3.9)
    print("\nForecast Mar 2020 - Feb 2021:")
    print(final_forecast.round(0).to_string())

    # Per-crime-type forecasts, using the setup chosen for the citywide series
    summaries = []
    forecasts = {"ALL": final_forecast}
    for crime_type, type_data in type_series.items():
        analysis = analyze_series(type_data, best["start"], best["seasonal"])
        if analysis is None:
            print(f"Skipping {crime_type}: some months have no crimes")
            continue
        summary, type_forecast, _ = analysis
        summaries.append(summary)
        forecasts[crime_type] = type_forecast

    by_type = pd.DataFrame(summaries).sort_values("covid_gap_pct")
    print(f"\nTop {len(by_type)} crime types (by {RANK_YEAR} count), same model setup:")
    print(by_type.round({"baseline_mape": 1, "model_mape": 1, "covid_gap_pct": 1, "worst_month_gap_pct": 1})
          .rename(columns={"months_below": "months_below_80pct"})
          .to_string(index=False))
    print("\ncovid_gap_pct = Mar-Jun 2020 vs. forecast; worst_month_gap_pct = the largest single-month drop")


if __name__ == "__main__":
    main()

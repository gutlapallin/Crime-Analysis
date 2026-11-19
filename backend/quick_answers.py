"""Built-in answers for common questions, used when the AI model is unavailable.

Each rule matches keywords in the question and runs a fixed query against the
summary tables, so these answers need no Gemini calls at all.
"""
import re

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

CRIME_TYPES = ["motor vehicle theft", "criminal damage", "public peace violation",
               "theft", "burglary", "robbery", "assault", "battery"]

# Average days per year, used to turn holiday totals into per-day rates
YEARS = "(SELECT COUNT(*) FROM yearly_crimes)"


def _n(v):
    return float(v or 0)


def _fmt(v):
    return f"{round(_n(v)):,}"


def _hour(h):
    h = int(h)
    return f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"


def _pct(a, b):
    if not b:
        return ""
    diff = (_n(a) / _n(b) - 1) * 100
    return f"{abs(diff):.0f}% {'higher' if diff >= 0 else 'lower'}"


def _crime_type(q):
    for t in CRIME_TYPES:
        if t in q:
            return t.upper()
    return None


def _top(rows, label, metric, fmt_label=str):
    hi = max(rows, key=lambda r: _n(r[metric]))
    lo = min(rows, key=lambda r: _n(r[metric]))
    return fmt_label(hi[label]), hi[metric], fmt_label(lo[label]), lo[metric]


# --- answer builders -------------------------------------------------------

def _hourly(rows):
    hi, hv, lo, lv = _top(rows, "hour", "crime_count", _hour)
    return (f"The most crime happens at {hi}, with {_fmt(hv)} reported crimes. "
            f"The quietest hour is {lo}, with {_fmt(lv)}.")


def _time_period(rows):
    hi, hv, lo, lv = _top(rows, "time_period", "total_crimes")
    return (f"{hi} (each period covers 8 hours) has the most crime with {_fmt(hv)} reports; "
            f"{lo} has the least with {_fmt(lv)}.")


def _monthly(rows):
    name = lambda m: MONTHS[int(m) - 1]
    hi, hv, lo, lv = _top(rows, "month", "total_crimes", name)
    warm = " Crime is highest in the summer months." if hi in ("June", "July", "August") else ""
    return (f"{hi} has the most crime with {_fmt(hv)} reports, and {lo} has the least "
            f"with {_fmt(lv)}.{warm}")


def _season(rows):
    hi, hv, lo, lv = _top(rows, "season", "per_month")
    return (f"Comparing average crimes per month (seasons have different lengths), {hi} is "
            f"highest at {_fmt(hv)} per month and {lo} is lowest at {_fmt(lv)} per month, "
            f"so {hi} is {_pct(hv, lv)}.")


def _yearly(rows):
    hi, hv, lo, lv = _top(rows, "year", "total_crimes")
    first, last = rows[0], rows[-1]
    return (f"Crime peaked in {hi} with {_fmt(hv)} reports and was lowest in {lo} with "
            f"{_fmt(lv)}. From {first['year']} to {last['year']} it went from "
            f"{_fmt(first['total_crimes'])} to {_fmt(last['total_crimes'])}. "
            f"The most recent year may be incomplete.")


def _top_list(label, metric, what):
    def build(rows):
        top = rows[:3]
        names = ", ".join(f"{r[label]} ({_fmt(r[metric])})" for r in top)
        return f"The {what} are {names}."
    return build


def _two_way(label, metric, what, rate=None):
    def build(rows):
        hi, hv, lo, lv = _top(rows, label, rate or metric)
        show = (lambda v: f"{_n(v):.1%}") if rate else _fmt
        kind = f"{what} rate" if rate else what
        if len(rows) > 2:
            return f"{hi} has the most {kind} ({show(hv)}) and {lo} has the least ({show(lv)})."
        return f"{hi} has {'a higher' if rate else 'more'} {kind} ({show(hv)}) than {lo} ({show(lv)})."
    return build


def _holiday_compare(event, note=""):
    def build(rows):
        by_type = {}
        for r in rows:
            by_type.setdefault(r.get("primary_type", "ALL CRIME"), {})[r["day_type"]] = r["daily_avg"]
        parts = []
        for ctype, vals in by_type.items():
            on = next((v for k, v in vals.items() if not k.startswith("Non")), None)
            off = next((v for k, v in vals.items() if k.startswith("Non")), None)
            if on is None or off is None:
                continue
            parts.append(f"{ctype.title()} averages {_fmt(on)} reports per day on {event} "
                         f"versus {_fmt(off)} on other days ({_pct(on, off)}).")
        return " ".join(parts) + note if parts else "There is no matching data for that comparison."
    return build


# --- rules -----------------------------------------------------------------

def _per_day_sql(table, event_label, event_days, types_col=True, crime=None):
    cols = "day_type, primary_type, total" if types_col else "day_type, total_crimes AS total"
    where = f" WHERE primary_type = '{crime}'" if crime else ""
    return (f"SELECT {cols}, ROUND(total{'' if types_col else '_crimes'} / CASE WHEN day_type = '{event_label}' "
            f"THEN {event_days} ELSE {YEARS} * 365.25 - {event_days} END, 1) AS daily_avg "
            f"FROM {table}{where} ORDER BY {'primary_type, ' if types_col else ''}day_type")


def match(question):
    """Return (sql, build_answer, chart, x, y, table) for a known question, else None."""
    q = question.lower()
    has = lambda *words: any(re.search(rf"\b{w}", q) for w in words)
    crime = _crime_type(q)

    if has("christmas", "december"):
        sql = _per_day_sql("christmas_vs_nonchristmas_by_type", "Christmas", f"{YEARS} * 31", crime=crime)
        return (sql, _holiday_compare("Christmas", " Here \"Christmas\" means the whole month of December."),
                "bar" if crime else "none", "day_type", "daily_avg", "christmas_vs_nonchristmas_by_type")
    if has("halloween"):
        sql = _per_day_sql("halloween_vs_nonhalloween_by_type", "Halloween", YEARS, crime=crime)
        return (sql, _holiday_compare("Halloween"), "bar" if crime else "none",
                "day_type", "daily_avg", "halloween_vs_nonhalloween_by_type")
    if has("thanksgiving"):
        sql = _per_day_sql("thanksgiving_vs_nonthanksgiving_by_type", "Thanksgiving", 21, crime=crime)
        return (sql, _holiday_compare("Thanksgiving"), "bar" if crime else "none",
                "day_type", "daily_avg", "thanksgiving_vs_nonthanksgiving_by_type")
    if has("holiday"):
        sql = _per_day_sql("holiday_vs_nonholiday", "Holiday", "(SELECT COUNT(*) FROM holidays)", types_col=False)
        return (sql, _holiday_compare("holidays"), "bar", "day_type", "daily_avg", "holiday_vs_nonholiday")
    if has("recession", "2008", "2009"):
        return ("SELECT primary_type, total FROM great_recession_by_type ORDER BY total DESC LIMIT 10",
                _top_list("primary_type", "total", "most common crimes during the Great Recession (2007-2009)"),
                "bar", "primary_type", "total", "great_recession_by_type")
    if has("hour"):
        return ("SELECT hour, crime_count FROM hourly_crimes ORDER BY hour",
                _hourly, "bar", "hour", "crime_count", "hourly_crimes")
    if has("morning", "night", "evening", "daytime", "afternoon", "overnight", "time of day"):
        return ("SELECT time_period, total_crimes FROM time_period_crimes ORDER BY total_crimes DESC",
                _time_period, "bar", "time_period", "total_crimes", "time_period_crimes")
    if has("season", "summer", "winter", "spring", "fall", "autumn"):
        return ("SELECT season, total_crimes, ROUND(total_crimes / CASE season WHEN 'Summer' THEN 3 "
                "WHEN 'Late Winter' THEN 2 ELSE 7 END) AS per_month FROM season_crimes ORDER BY per_month DESC",
                _season, "bar", "season", "per_month", "season_crimes")
    if has("month"):
        return ("SELECT month, total_crimes FROM monthly_crimes ORDER BY month",
                _monthly, "bar", "month", "total_crimes", "monthly_crimes")
    if has("year", "trend", "over time", "changed", "decade", "decline", "increas", "decreas"):
        return ("SELECT year, total_crimes FROM yearly_crimes ORDER BY year",
                _yearly, "line", "year", "total_crimes", "yearly_crimes")
    if has("downtown", "residential"):
        return ("SELECT area_type, tr_crimes, total_crimes, rate FROM downtown_vs_residential_theft_robbery",
                _two_way("area_type", "tr_crimes", "theft and robbery", rate="rate"),
                "bar", "area_type", "rate", "downtown_vs_residential_theft_robbery")
    if has("airport"):
        return ("SELECT location_type, theft_count, total_crimes, theft_rate FROM airport_theft_count_comparison "
                "ORDER BY theft_rate DESC",
                _two_way("location_type", "theft_count", "theft", rate="theft_rate"),
                "bar", "location_type", "theft_rate", "airport_theft_count_comparison")
    if has("transit", "cta", "train", "bus", "commercial"):
        return ("SELECT location_type, robbery_count FROM transit_vs_commercial_robbery_count",
                _two_way("location_type", "robbery_count", "robberies"),
                "bar", "location_type", "robbery_count", "transit_vs_commercial_robbery_count")
    if has("stadium", "sport", "wrigley", "soldier field", "arena"):
        return ("SELECT crime_category, total_crimes FROM sport_location_crimes ORDER BY total_crimes DESC",
                _top_list("crime_category", "total_crimes", "most common crimes near sports venues"),
                "bar", "crime_category", "total_crimes", "sport_location_crimes")
    if has("community", "neighborhood", "neighbourhood", "area"):
        return ("SELECT community_area, total_crimes FROM community_area_crimes "
                "ORDER BY total_crimes DESC LIMIT 10",
                _top_list("community_area", "total_crimes", "community areas with the most crime"),
                "bar", "community_area", "total_crimes", "community_area_crimes")
    if crime == "THEFT" and has("where", "location", "place"):
        return ("SELECT location_description, total_thefts, total_crimes FROM theft_by_location "
                "ORDER BY total_thefts DESC LIMIT 10",
                _top_list("location_description", "total_thefts", "places with the most thefts"),
                "bar", "location_description", "total_thefts", "theft_by_location")
    if has("where", "location", "place"):
        return ("SELECT location_category, total_crimes FROM crimes_by_location ORDER BY total_crimes DESC",
                _top_list("location_category", "total_crimes", "location types with the most crime"),
                "bar", "location_category", "total_crimes", "crimes_by_location")
    return None


def quick_answer(question, run_sql):
    """Answer from a built-in rule, or return None if no rule fits."""
    rule = match(question)
    if not rule:
        return None
    sql, build, chart, x, y, table = rule
    rows = run_sql(sql)
    if not rows:
        return None
    return {
        "answer": build(rows),
        "chart": chart,
        "x": x,
        "y": y,
        "sql": sql,
        "rows": rows,
        "tables_used": [table],
        "source": "built-in query",
    }

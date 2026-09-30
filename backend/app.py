from flask import Flask, jsonify, request, send_from_directory, abort
import os
import json
import pymysql
import statistics
import math
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

app = Flask(__name__)

REACT_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

@app.after_request
def cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",
    "database": "cs179g"
}

CATEGORIES = {
    "Time-of-Day": {
        "Hourly Crimes": "hourly_crimes",
        "Time Period Crimes": "time_period_crimes"
    },
    "Seasonal / Monthly / Holiday": {
        "Monthly Crimes": "monthly_crimes",
        "Season Crimes": "season_crimes",
        "Holiday vs Non-Holiday": "holiday_vs_nonholiday",
        # "Christmas": "christmas_by_type",
        "Christmas": "christmas_vs_nonchristmas_by_type",
        "Thanksgiving": "thanksgiving_vs_nonthanksgiving_by_type",
        "Halloween": "halloween_vs_nonhalloween_by_type"
    },
    "Location-Based / Spatial": {
        "Crimes by Location": "crimes_by_location",
        "Crimes by Location & Type": "crimes_by_location_and_type",
        "Community Area Crimes": "community_area_crimes",
        "Airport Theft Comparison": "airport_theft_count_comparison",
        "Downtown vs Residential": "downtown_vs_residential_theft_robbery",
        "Transit vs Commercial": "transit_vs_commercial_robbery_count",
        "Theft by Location": "theft_by_location",
        "Sports Location Crimes": "sport_location_crimes",
    },
    "Long-Term Trends": {
        "Yearly Crimes": "yearly_crimes",
        "Great Recession by Type": "great_recession_by_type"
}
}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = None
if GEMINI_API_KEY:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        api_key=GEMINI_API_KEY,
    )

insight_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a careful data analyst for Chicago crime data. Only use the data that is provided.",
        ),
        (
            "human",
            """
Table key: {table_key}
User question: {question}
User hypothesis: {hypothesis}

Sample rows (JSON): {sample_rows}
Metrics (JSON): {metrics}

Write:
1) 3-5 short bullet points in plain English about the main patterns you see.
2) A 1-2 sentence conclusion that says whether the hypothesis is supported, mixed, or not_supported.

Return ONLY JSON with this format:
{{
  "hypothesis_status": "supported" | "mixed" | "not_supported",
  "bullets": ["...", "..."],
  "conclusion": "..."
}}
""",
        ),
    ]
)

def query_table(table_name):
    try:
        conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        conn.close()
        return data
    except Exception as e:
        print(f"DB ERROR for {table_name}: {e}")
        raise

ALLOWED_TABLES = {t for items in CATEGORIES.values() for t in items.values()}


def get_insight_rows(payload):
    """Use full table data when tableKey is valid; otherwise fall back to payload sampleRows."""
    table_key = payload.get("tableKey")
    if table_key and table_key in ALLOWED_TABLES:
        try:
            return query_table(table_key)
        except Exception as e:
            print(f"Could not fetch full table {table_key} for insights: {e}")
    sample_rows = payload.get("sampleRows") or []
    if not isinstance(sample_rows, list):
        sample_rows = []
    return [row for row in sample_rows if isinstance(row, dict)]


@app.route("/api/categories")
def get_categories():
    return jsonify(CATEGORIES)

@app.route("/api/data")
def get_data():
    table = request.args.get("table")
    if not table or table not in ALLOWED_TABLES:
        return jsonify({"error": "Invalid or missing table name", "data": [], "stats": {}}), 400
    data = query_table(table)

    stats = {}
    if data and "count" in data[0]:
        counts = [row["count"] for row in data]
        stats["total"] = sum(counts)
        stats["average"] = round(statistics.mean(counts), 2)

    return jsonify({
        "data": data,
        "stats": stats
    })

COUNT_KEYS = ["total_crimes", "crime_count", "count", "total", "value"]
LABEL_KEYS = ["time_period", "month", "year", "community_area", "primary_type", "day_type", "location_description"]

def to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def numeric_values(rows, key):
    return [v for v in (to_number(row.get(key)) for row in rows) if v is not None]

def find_count_key(rows):
    if not rows:
        return None
    first = rows[0]
    for key in COUNT_KEYS:
        if key in first:
            return key
    for key in first:
        if to_number(first.get(key)) is not None:
            return key
    return None

def row_label(row):
    for key in LABEL_KEYS:
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    for key, value in row.items():
        if key.lower() in ("id", "index"):
            continue
        if to_number(value) is None and value not in (None, ""):
            return str(value)
    return "Unknown"

def summarize_rows(table_key, rows, count_key):
    if not rows or not count_key:
        return {
            "metrics": {},
            "bullets": ["There is not enough data to say anything meaningful here."],
            "conclusion": "Not enough information to draw a clear conclusion."
        }

    values = numeric_values(rows, count_key)
    if not values:
        return {
            "metrics": {},
            "bullets": ["This view does not contain numeric values that can be summarized."],
            "conclusion": "Not enough numeric information to draw a clear conclusion."
        }

    top_row = max(rows, key=lambda row: to_number(row.get(count_key)) or float("-inf"))
    low_row = min(rows, key=lambda row: to_number(row.get(count_key)) or float("inf"))
    max_value = int(to_number(top_row.get(count_key)) or 0)
    min_value = int(to_number(low_row.get(count_key)) or 0)
    total = sum(values)
    average = total / len(values)
    ratio = (max_value / average) if average > 0 else 0

    metrics = {
        "rows_analyzed": len(rows),
        "total_count": int(total) if math.isfinite(total) else 0,
        "average_count": round(average, 2),
        "highest_label": row_label(top_row),
        "highest_count": max_value,
        "lowest_label": row_label(low_row),
        "lowest_count": min_value,
    }

    bullets = [
        f"The largest value is {max_value} for {metrics['highest_label']}.",
        f"The smallest value is {min_value} for {metrics['lowest_label']}.",
        f"Average across the {len(rows)} groups is about {round(average, 2)}."
    ]

    if ratio >= 1.2:
        conclusion = "Some groups clearly stand out compared to the rest."
    else:
        conclusion = "The values across groups are fairly similar overall."

    return {"metrics": metrics, "bullets": bullets, "conclusion": conclusion}


def build_llm_insight_response(payload):
    table_key = payload.get("tableKey")
    rows = get_insight_rows(payload)
    count_key = find_count_key(rows)
    base_summary = summarize_rows(table_key, rows, count_key)
    question = payload.get("question") or ""
    hypothesis = payload.get("hypothesis") or ""
    if llm is None:
        print("Insight model not configured: GEMINI_API_KEY is missing.")
        return {"error": "Insight service not configured. Set GEMINI_API_KEY to generate insights."}, 503

    try:
        sample_for_llm = json.dumps(rows)[:12000]
        msg = insight_prompt.format_messages(
            table_key=table_key,
            question=question,
            hypothesis=hypothesis,
            sample_rows=sample_for_llm,
            metrics=json.dumps(base_summary["metrics"]),
        )

        raw = llm.invoke(msg)
        content = raw.content if isinstance(raw.content, str) else str(raw.content)

        if "```" in content:
            content = content.replace("```json", "").replace("```", "").strip()

        try:
            data = json.loads(content)
            bullets = data.get("bullets", [])
            conclusion = data.get("conclusion", "")
            status = data.get("hypothesis_status", "mixed")
        except Exception:
            print("Could not parse response as JSON, using raw text instead.")
            bullets = [content.strip()] if content.strip() else []
            conclusion = ""
            status = "mixed"

        return {
            "hypothesis_status": status,
            "metrics": base_summary["metrics"],
            "summary": {
                "bullets": bullets,
                "conclusion": conclusion,
            },
        }
    except Exception as e:
        print(f"Insight request failed: {e}")
        return {"error": "Could not generate insight. The request failed."}, 503


@app.route("/api/insights_llm", methods=["POST"])
def generate_llm_insight():
    payload = request.get_json(silent=True) or {}
    result = build_llm_insight_response(payload)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.route("/")
def serve_react():
    if os.path.isdir(REACT_DIST) and os.path.isfile(os.path.join(REACT_DIST, "index.html")):
        return send_from_directory(REACT_DIST, "index.html")
    return "Run: cd frontend && npm run build", 404


@app.route("/<path:path>")
def serve_react_static(path):
    if path.startswith("api/"):
        abort(404)
    if os.path.isdir(REACT_DIST):
        full = os.path.join(REACT_DIST, path)
        if os.path.isfile(full):
            return send_from_directory(REACT_DIST, path)
        return send_from_directory(REACT_DIST, "index.html")
    abort(404)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=5001, type=int)
    args = parser.parse_args()

    app.run(host=args.host, port=args.port, debug=True)

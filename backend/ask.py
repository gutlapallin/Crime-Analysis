import json
import logging
import os
import re
import time
import pymysql
import sqlglot
from sqlglot import exp
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from raw_engine import RAW_SCHEMA, validate_raw_sql, run_raw
from table_docs import TABLE_DOCS

log = logging.getLogger(__name__)

ALLOWED = {d["table"] for d in TABLE_DOCS}
DOCS_BY_TABLE = {d["table"]: d for d in TABLE_DOCS}

_store = None


def _get_store():
    global _store
    if _store is None:
        emb = GoogleGenerativeAIEmbeddings(
            model=os.getenv("EMBED_MODEL", "models/gemini-embedding-001"),
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )
        _store = FAISS.from_texts(
            [f"{d['table']}: {d['description']}" for d in TABLE_DOCS],
            emb,
            metadatas=[{"table": d["table"]} for d in TABLE_DOCS],
        )
    return _store


def retrieve_tables(question, k=4):
    try:
        hits = _get_store().similarity_search(question, k=k)
        return [DOCS_BY_TABLE[h.metadata["table"]] for h in hits]
    except Exception:
        # The table list is small, so fall back to all of it if embeddings fail
        log.exception("Table retrieval failed; using all tables")
        return TABLE_DOCS


SQL_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You write ONE MySQL SELECT query. Use ONLY these tables and columns:\n{schemas}\n"
     "Rules: SELECT only, no semicolons, no comments. Tables are pre-aggregated, so use SUM/ORDER BY as needed. "
     "If the question cannot be answered from these tables, return exactly: CANNOT_ANSWER\n"
     "Return only the SQL, no markdown."),
    ("human", "{question}"),
])

RAW_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You write ONE DuckDB SELECT query over this table:\n{schema}\n"
     "Rules: SELECT only, no semicolons, no comments. Text values are UPPERCASE "
     "(for example 'THEFT', 'BATTERY', 'STREET', 'RESIDENCE'). community_area is a number 1-77 "
     "and is NULL for about 8% of rows, so add community_area IS NOT NULL when grouping by it. "
     "There are no neighborhood or landmark names, only community_area numbers and latitude/longitude. "
     "Always select the label column(s) and the numeric metric column(s). "
     "If the question cannot be answered from this table, return exactly: CANNOT_ANSWER\n"
     "Return only the SQL, no markdown."),
    ("human", "{question}"),
])

ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a careful Chicago crime data analyst. Use ONLY the rows provided. "
     "Do not invent numbers. If the rows do not answer the question, say so."),
    ("human",
     "Question: {question}\nSQL used: {sql}\nRows (JSON): {rows}\n\n"
     "Return ONLY JSON: {{\"answer\": \"2-4 plain-English sentences\", "
     "\"chart\": \"bar\" | \"line\" | \"none\", "
     "\"x\": \"column name for x axis or empty\", \"y\": \"numeric column name or empty\"}}"),
])


def validate_sql(sql):
    sql = sql.strip().strip("`")
    sql = re.sub(r"^sql\s+", "", sql, flags=re.I).strip().rstrip(";")
    if ";" in sql:
        raise ValueError("Multiple statements are not allowed")
    tree = sqlglot.parse_one(sql, read="mysql")
    if not isinstance(tree, exp.Select):
        raise ValueError("Only SELECT queries are allowed")
    for t in tree.find_all(exp.Table):
        if t.name not in ALLOWED:
            raise ValueError(f"Table not allowed: {t.name}")
    if not tree.args.get("limit"):
        tree = tree.limit(200)
    return tree.sql(dialect="mysql")


def run_readonly(sql):
    # docker-compose passes unset vars as "", so fall back with `or`
    readonly_user = os.getenv("READONLY_USER")
    cfg = {
        "user": readonly_user or os.getenv("DB_USER") or "root",
        "password": (os.getenv("READONLY_PASSWORD") if readonly_user
                     else os.getenv("DB_PASSWORD")) or "",
        "database": os.getenv("DB_NAME", "cs179g"),
        "read_timeout": 10,
        "cursorclass": pymysql.cursors.DictCursor,
    }
    if os.getenv("DB_SOCKET"):
        cfg["unix_socket"] = os.getenv("DB_SOCKET")
    else:
        cfg["host"] = os.getenv("DB_HOST", "127.0.0.1")
        cfg["port"] = int(os.getenv("DB_PORT", "3306"))
    conn = pymysql.connect(**cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    finally:
        conn.close()


def _text(msg):
    c = msg.content
    if isinstance(c, list):
        c = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in c)
    return c.strip()


def _json(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return {"answer": text, "chart": "none", "x": "", "y": ""}


def _invoke(chain, inputs, tries=3):
    for attempt in range(tries):
        try:
            return chain.invoke(inputs)
        except Exception as e:
            transient = any(s in str(e) for s in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"))
            if not transient or attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))

def answer_question(question, llm):
    try:
        return _answer_question(question, llm)
    except Exception as e:
        log.exception("Ask request failed")
        return {"error": f"Could not answer the question: {e}"}, 502


def _answer_question(question, llm):
    question = (question or "").strip()[:500]
    if not question:
        return {"error": "Please enter a question."}, 400
    if llm is None:
        return {"error": "Gemini API key is not configured."}, 503

    tables = retrieve_tables(question)
    schemas = "\n".join(f"- {t['table']}({t['columns']})" for t in tables)
    raw = _text(_invoke(SQL_PROMPT | llm, {"schemas": schemas, "question": question}))
    source = "summary tables"

    if raw.strip().upper().startswith("CANNOT_ANSWER"):
        raw = _text(_invoke(RAW_PROMPT | llm, {"schema": RAW_SCHEMA, "question": question}))
        if raw.strip().upper().startswith("CANNOT_ANSWER"):
            return {"answer": "I can't answer that from the available data.",
                    "sql": None, "rows": [], "tables_used": [], "source": None}, 200
        source = "raw data"

    is_raw = source == "raw data"
    try:
        sql = validate_raw_sql(raw) if is_raw else validate_sql(raw)
    except Exception as e:
        return {"error": f"Blocked unsafe or invalid query: {e}"}, 400

    try:
        rows = run_raw(sql) if is_raw else run_readonly(sql)
    except Exception as e:
        return {"error": f"Query failed: {e}", "sql": sql}, 500

    out = _json(_text(_invoke(ANSWER_PROMPT | llm,
        {"question": question, "sql": sql, "rows": json.dumps(rows, default=str)[:20000]})))
    used = sorted({t.name for t in sqlglot.parse_one(
        sql, read="duckdb" if is_raw else "mysql").find_all(exp.Table)})
    out.update({"sql": sql, "rows": rows, "tables_used": used, "source": source})
    return out, 200

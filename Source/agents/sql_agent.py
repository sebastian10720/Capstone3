import os

import psycopg2
from dotenv import load_dotenv

from bedrock_client import invoke_claude

load_dotenv()

SCHEMA_CONTEXT = """
Tables available:

- clients(id, name, industry, region, contract_value, created_date)
- projects(id, client_id, name, status, start_date, end_date, budget)
- consultants(id, name, grade, specialisation, project_id, billable_hours)
- invoices(id, project_id, amount, status, due_date, paid_date)

All monetary values are in USD. Dates are in ISO 8601 format.
status in projects is one of: 'active', 'completed', 'on-hold'.
"""

BLOCKED_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
    "EXEC", "EXECUTE", "GRANT", "REVOKE",
]


def validate_sql(query: str) -> dict:
    """Block non-SELECT queries, destructive keywords, and stacked statements."""
    query_upper = query.upper().strip()

    for keyword in BLOCKED_KEYWORDS:
        if f" {keyword} " in f" {query_upper} " or query_upper.startswith(keyword):
            return {
                "valid": False,
                "reason": f"Blocked: '{keyword}' is not permitted.",
            }

    if not query_upper.startswith("SELECT"):
        return {"valid": False, "reason": "Only SELECT queries are permitted."}

    # Independently block stacked statements, including two SELECT statements.
    stripped = query.strip().rstrip(";")
    if ";" in stripped:
        return {"valid": False, "reason": "Blocked: multiple statements detected."}

    return {"valid": True, "reason": "OK"}


def generate_sql(question: str) -> tuple[str, dict]:
    prompt = (
        f"{SCHEMA_CONTEXT}\n\n"
        f"Generate a SQL query to answer: {question}\n\n"
        "Return ONLY the SQL query. No explanation, no markdown, no backticks."
    )
    result = invoke_claude(prompt, max_tokens=512)
    sql = result["text"].strip()
    sql = (
        sql.removeprefix("```sql")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    usage = {
        "input": result["input_tokens"],
        "output": result["output_tokens"],
    }
    return sql, usage


def execute_query_safely(sql: str) -> dict:
    validation = validate_sql(sql)
    if not validation["valid"]:
        return {
            "success": False,
            "error": validation["reason"],
            "validation": "BLOCKED",
            "sql": sql,
        }

    try:
        conn = psycopg2.connect(
            host=os.getenv("RDS_HOST"),
            port=int(os.getenv("RDS_PORT")),
            dbname=os.getenv("RDS_DATABASE"),
            user=os.getenv("RDS_USER"),
            password=os.getenv("RDS_PASSWORD"),
        )
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [description[0] for description in cur.description]
        conn.close()
        return {
            "success": True,
            "columns": cols,
            "rows": rows,
            "validation": "PASSED",
            "sql": sql,
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error),
            "validation": "EXECUTION_ERROR",
            "sql": sql,
        }


def validated_sql_agent(question: str) -> dict:
    sql, generation_usage = generate_sql(question)
    result = execute_query_safely(sql)
    interpretation_usage = {"input": 0, "output": 0}

    if not result["success"]:
        answer = f"Query blocked or failed: {result['error']}"
    else:
        prompt = (
            f"Question: {question}\nColumns: {result['columns']}\n"
            f"Data: {result['rows'][:20]}\n\nAnswer concisely."
        )
        interpretation = invoke_claude(prompt, max_tokens=500)
        answer = interpretation["text"]
        interpretation_usage = {
            "input": interpretation["input_tokens"],
            "output": interpretation["output_tokens"],
        }

    return {
        "answer": answer,
        "sql": sql,
        "validation": result["validation"],
        "token_usage": {
            "input": generation_usage["input"] + interpretation_usage["input"],
            "output": generation_usage["output"] + interpretation_usage["output"],
            "sql_generation": generation_usage,
            "sql_interpretation": interpretation_usage,
        },
    }


def run_sql_agent(question: str) -> dict:
    """Return the shared success, answer, sources, metadata interface."""
    result = validated_sql_agent(question)
    return {
        "success": result["validation"] == "PASSED",
        "answer": result["answer"],
        "sources": [f"SQL: {result['sql']}"],
        "metadata": {
            "validation": result["validation"],
            "token_usage": result["token_usage"],
        },
    }
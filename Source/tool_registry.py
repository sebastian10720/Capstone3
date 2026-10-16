from agents.sql_agent import run_sql_agent
from agents.retrieval_agent import run_retrieval_agent

TOOL_REGISTRY = {
    "sql": {
        "description": (
            "Use for structured questions answered from the RDS clients, projects, "
            "consultants, or invoices tables. Do not use for document-based policies, "
            "processes, or procedures."
        ),
        "function": run_sql_agent,
    },
    "retrieval": {
        "description": (
            "Use for policies, processes, procedures, and other answers found in "
            "documents indexed in OpenSearch. Do not use for counts, totals, or other "
            "structured questions requiring RDS data."
        ),
        "function": run_retrieval_agent,
    },
}
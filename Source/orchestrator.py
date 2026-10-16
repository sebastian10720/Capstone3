from typing import Optional, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from agents.retrieval_agent import run_retrieval_agent
from agents.sql_agent import run_sql_agent
from bedrock_client import invoke_claude

load_dotenv()


class OrchestratorState(TypedDict):
    question: str
    route: Optional[str]
    sql_result: Optional[dict]
    retrieval_result: Optional[dict]
    final_answer: Optional[str]
    token_usage: Optional[dict]


TOOL_REGISTRY = {
    "sql": {
        "description": (
            "Use for structured questions answered from the RDS clients, projects, "
            "consultants, or invoices tables. Do not use for document policies, "
            "processes, or procedures."
        ),
        "function": run_sql_agent,
    },
    "retrieval": {
        "description": (
            "Use for policies, processes, procedures, and information in documents "
            "indexed in OpenSearch. Do not use for counts, totals, or other questions "
            "that require structured RDS data."
        ),
        "function": run_retrieval_agent,
    },
}

SQL_KEYWORDS = [
    "how many", "count", "total", "average", "sum", "revenue", "how much",
    "list all", "which clients", "projects", "invoices", "consultants",
    "compare", "trend", "budget",
]
DOC_KEYWORDS = [
    "policy", "process", "procedure", "methodology", "what is", "explain",
    "describe", "guidelines", "approach", "onboarding",
]


def route_question(state: OrchestratorState) -> OrchestratorState:
    question = state["question"].lower()
    needs_sql = any(word in question for word in SQL_KEYWORDS)
    needs_retrieval = any(word in question for word in DOC_KEYWORDS)

    if needs_sql and needs_retrieval:
        route = "both"
    elif needs_sql:
        route = "sql"
    else:
        route = "retrieval"

    return {**state, "route": route}


def call_sql_agent(state: OrchestratorState) -> OrchestratorState:
    if state["route"] not in ("sql", "both"):
        return state
    result = TOOL_REGISTRY["sql"]["function"](state["question"])
    return {**state, "sql_result": result}


def call_retrieval_agent(state: OrchestratorState) -> OrchestratorState:
    if state["route"] not in ("retrieval", "both"):
        return state
    result = TOOL_REGISTRY["retrieval"]["function"](state["question"])
    return {**state, "retrieval_result": result}


def _agent_usage(result: Optional[dict]) -> dict:
    if not result:
        return {"input": 0, "output": 0}
    metadata = result.get("metadata", {})
    usage = metadata.get("token_usage", {})
    return {"input": usage.get("input", 0), "output": usage.get("output", 0)}


def synthesise(state: OrchestratorState) -> OrchestratorState:
    parts = []

    sql_result = state.get("sql_result")
    if sql_result and sql_result.get("success"):
        parts.append(
            f"SQL Agent result:\n{sql_result['answer']}\n"
            f"Sources: {sql_result.get('sources', [])}"
        )

    retrieval_result = state.get("retrieval_result")
    if retrieval_result and retrieval_result.get("success"):
        parts.append(
            f"Retrieval Agent result:\n{retrieval_result['answer']}\n"
            f"Sources: {retrieval_result.get('sources', [])}"
        )

    usage = {
        "classification": {"input": 0, "output": 0},
        "sql": _agent_usage(sql_result),
        "retrieval": _agent_usage(retrieval_result),
        "synthesis": {"input": 0, "output": 0},
    }

    if not parts:
        return {
            **state,
            "final_answer": "I could not find relevant information to answer this question.",
            "token_usage": usage,
        }

    prompt = (
        "Answer the question using the agent results below. Cite the agent and "
        "source for each fact. If only one agent returned a result, use only that "
        "result.\n\n"
        f"Question: {state['question']}\n\n"
        + "\n\n".join(parts)
    )
    result = invoke_claude(prompt, max_tokens=800)
    usage["synthesis"] = {
        "input": result["input_tokens"],
        "output": result["output_tokens"],
    }
    usage["total"] = {
        "input": sum(item["input"] for item in usage.values()),
        "output": sum(item["output"] for item in usage.values()),
    }

    return {**state, "final_answer": result["text"], "token_usage": usage}


def build_orchestrator():
    graph = StateGraph(OrchestratorState)
    graph.add_node("router", route_question)
    graph.add_node("sql_agent", call_sql_agent)
    graph.add_node("retrieval_agent", call_retrieval_agent)
    graph.add_node("synthesiser", synthesise)

    graph.set_entry_point("router")
    graph.add_edge("router", "sql_agent")
    graph.add_edge("sql_agent", "retrieval_agent")
    graph.add_edge("retrieval_agent", "synthesiser")
    graph.add_edge("synthesiser", END)

    return graph.compile()


orchestrator = build_orchestrator()
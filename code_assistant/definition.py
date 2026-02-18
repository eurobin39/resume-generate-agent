from agent_framework import tool
from agent_framework_utils import run_agent_sync, run_workflow_sync
from .agents import (
    explain_code,
    refactor_code,
    document_code,
)
from .workflows.handoff import build_handoff_workflow
from .workflows.concurrent import build_concurrent_workflow
from .workflows.selector import build_selector_agent

_router_agent = None
_handoff_workflow = None
_concurrent_workflow = None


@tool
def explain_code_tool(code: str) -> str:
    """Explain what the provided code does."""
    return explain_code(code, stream=False)


@tool
def refactor_code_tool(code: str, refactor_goal: str = "none") -> str:
    """Refactor code with an optional refactor goal."""
    goal = None if refactor_goal.lower() == "none" else refactor_goal
    return refactor_code(code, refactor_goal=goal, stream=False)


@tool
def document_code_tool(code: str, doc_style: str = "google") -> str:
    """Add documentation to code using a specified docstring style."""
    return document_code(code, doc_style=doc_style, stream=False)


def _get_router_agent():
    global _router_agent
    if _router_agent is None:
        _router_agent = build_selector_agent()
    return _router_agent


def _get_handoff_workflow():
    global _handoff_workflow
    if _handoff_workflow is None:
        _handoff_workflow = build_handoff_workflow()
    return _handoff_workflow


def _get_concurrent_workflow():
    global _concurrent_workflow
    if _concurrent_workflow is None:
        _concurrent_workflow = build_concurrent_workflow()
    return _concurrent_workflow


def _messages_to_text(messages) -> str:
    if not messages:
        return ""
    parts = []
    for msg in messages:
        text = getattr(msg, "text", None) or getattr(msg, "content", None)
        parts.append(text if text is not None else str(msg))
    return "\n\n".join(parts)


def orchestrator(user_request: str, code: str, stream: bool = False) -> str:
    prompt = (
        "User request:\n"
        f"{user_request}\n\n"
        "Code:\n"
        f"{code}\n\n"
        "Decide which operation(s) are needed and respond with the best output."
    )
    selector = _get_router_agent()
    mode = run_agent_sync(
        selector,
        "Choose workflow for this request. Return ONLY HANDOFF or CONCURRENT.\n\n"
        f"{prompt}",
    ).strip().upper()
    if mode == "CONCURRENT":
        outputs = run_workflow_sync(_get_concurrent_workflow(), prompt)
    elif mode == "HANDOFF":
        outputs = run_workflow_sync(_get_handoff_workflow(), prompt)
    else:
        raise ValueError(f"Unknown workflow mode: {mode}")
    response = _messages_to_text(outputs)

    if stream:
        print(response)
    return response

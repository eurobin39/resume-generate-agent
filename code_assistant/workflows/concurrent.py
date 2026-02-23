"""Concurrent workflow builder for code assistant agents."""

from agent_framework.orchestrations import ConcurrentBuilder
from ..agents import get_explainer_agent, get_refactor_agent, get_documenter_agent


def build_concurrent_workflow():
    """Build and return the concurrent multi-agent workflow."""
    return ConcurrentBuilder(name="code_assistant_concurrent").with_participants(
        get_explainer_agent(),
        get_refactor_agent(),
        get_documenter_agent(),
    ).build()

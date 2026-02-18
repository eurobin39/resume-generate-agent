from agent_framework.orchestrations import HandoffBuilder
from agent_framework_utils import create_agent
from ..agents import get_explainer_agent, get_refactor_agent, get_documenter_agent


def build_handoff_workflow():
    triage = create_agent(
        name="code_router",
        instructions=(
            "You are a code triage agent. Choose the best specialist and hand off. "
            "If multiple tasks are requested, pick the most important one."
        ),
    )
    return (
        HandoffBuilder(name="code_assistant_handoff")
        .with_autonomous_mode()
        .with_participants(
            triage,
            get_explainer_agent(),
            get_refactor_agent(),
            get_documenter_agent(),
        )
        .with_start_agent(triage)
        .build()
    )

from agent_framework_utils import create_agent


def build_selector_agent():
    return create_agent(
        name="code_workflow_router",
        instructions=(
            "Decide which workflow to use for a user request.\n"
            "Return ONLY one of: HANDOFF or CONCURRENT."
        ),
    )

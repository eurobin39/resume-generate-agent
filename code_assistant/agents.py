from __future__ import annotations

from agent_framework_utils import create_agent, run_agent_sync

_agent_explainer = None
_agent_refactor = None
_agent_documenter = None


def _get_explainer():
    global _agent_explainer
    if _agent_explainer is None:
        _agent_explainer = create_agent(
            name="code_explainer",
            instructions=(
                "You are a code explanation assistant. When given code:\n"
                "1. Explain what the code does in plain English\n"
                "2. Break down complex logic step by step\n"
                "3. Use clear, beginner-friendly language"
            ),
        )
    return _agent_explainer


def _get_refactor():
    global _agent_refactor
    if _agent_refactor is None:
        _agent_refactor = create_agent(
            name="code_refactor",
            instructions=(
                "You are a code refactoring assistant. When given code:\n"
                "1. Identify code smells and areas for improvement\n"
                "2. Suggest refactored code with better structure, readability, and maintainability\n"
                "3. Explain what changes you made and why\n"
                "4. Follow best practices and design patterns\n"
                "5. Preserve the original functionality while improving code quality\n\n"
                "Format your response as:\n"
                "## Refactored Code\n"
                "[provide the improved code]\n\n"
                "## Changes Made\n"
                "[explain the improvements]\n\n"
                "## Reasoning\n"
                "[explain why these changes improve the code]"
            ),
        )
    return _agent_refactor


def _get_documenter():
    global _agent_documenter
    if _agent_documenter is None:
        _agent_documenter = create_agent(
            name="code_documenter",
            instructions=(
                "You are a code documentation assistant. When given code:\n"
                "1. Add comprehensive docstrings to all functions, classes, and modules\n"
                "2. Add inline comments for complex logic\n"
                "3. Include type hints where appropriate\n"
                "4. Document parameters, return values, exceptions, and usage examples\n"
                "5. Keep comments concise but informative\n"
                "6. Preserve all original functionality - only add documentation\n\n"
                "Format your response as:\n"
                "## Documented Code\n"
                "[provide the fully documented code]\n\n"
                "## Documentation Summary\n"
                "[brief summary of what was documented]"
            ),
        )
    return _agent_documenter


def get_explainer_agent():
    return _get_explainer()


def get_refactor_agent():
    return _get_refactor()


def get_documenter_agent():
    return _get_documenter()


def _build_doc_prompt(code: str, doc_style: str) -> str:
    style_instructions = {
        "google": "Use Google-style docstrings with Args, Returns, Raises sections",
        "numpy": "Use NumPy-style docstrings with Parameters, Returns, Raises sections",
        "sphinx": "Use Sphinx-style docstrings with :param, :return, :raises tags",
        "pep257": "Use PEP 257 compliant docstrings with simple descriptions",
    }
    style_guide = style_instructions.get(doc_style.lower(), style_instructions["google"])
    return f"{style_guide}\n\nAdd documentation to this code:\n\n{code}"


def explain_code(code: str, stream: bool = False) -> str:
    response = run_agent_sync(_get_explainer(), f"Explain this code:\n\n{code}")
    if stream:
        print(response)
    return response


def refactor_code(code: str, refactor_goal: str | None = None, stream: bool = False) -> str:
    if refactor_goal:
        prompt = f"Refactor this code with focus on: {refactor_goal}\n\n{code}"
    else:
        prompt = f"Refactor this code:\n\n{code}"
    response = run_agent_sync(_get_refactor(), prompt)
    if stream:
        print(response)
    return response


def document_code(code: str, doc_style: str = "google", stream: bool = False) -> str:
    response = run_agent_sync(_get_documenter(), _build_doc_prompt(code, doc_style))
    if stream:
        print(response)
    return response

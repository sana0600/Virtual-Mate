from typing import Any

try:
    from .planner import ActionType, PlannedAction
    from ..tools.document_tool import generate_document
    from ..tools.email_tool import generate_email
    from ..tools.summarizer import summarize_research
    from ..tools.web_search import search_web
except ImportError:
    from agents.planner import ActionType, PlannedAction
    from tools.document_tool import generate_document
    from tools.email_tool import generate_email
    from tools.summarizer import summarize_research
    from tools.web_search import search_web


def _content_for_output(context: dict[str, Any], task: str) -> str:
    return str(
        context.get("summary")
        or context.get("research_data")
        or context.get("email_draft")
        or task
    )


def execute_action(
    action: PlannedAction | dict[str, Any],
    task: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    action = (
        action if isinstance(action, PlannedAction) else PlannedAction.model_validate(action)
    )

    if action.type == ActionType.WEB_SEARCH:
        if "research_data" in context:
            return {
                "type": "research",
                "status": "skipped",
                "message": "Research was already completed for this task.",
            }
        research = search_web(task)
        context["research_data"] = research
        return {
            "type": "research",
            "status": "success",
            "content": research,
        }

    if action.type == ActionType.SUMMARIZE:
        source = context.get("research_data", task)
        summary = summarize_research(source, task)
        context["summary"] = summary
        return {
            "type": "summary",
            "status": "success",
            "content": summary,
        }

    if action.type == ActionType.DRAFT_EMAIL:
        email = generate_email(_content_for_output(context, task))
        context["email_draft"] = email
        return {
            "type": "email",
            "status": "success",
            "content": email,
        }

    document_types = {
        ActionType.CREATE_PDF: "pdf",
        ActionType.CREATE_DOCX: "docx",
        ActionType.CREATE_XLSX: "xlsx",
    }
    if action.type in document_types:
        result = generate_document(
            _content_for_output(context, task),
            document_types[action.type],
        )
        return {
            "type": "file",
            "status": "success",
            **result,
        }

    raise ValueError(f"Unsupported action type: {action.type}")

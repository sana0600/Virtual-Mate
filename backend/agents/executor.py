from tools.web_search import search_web
from tools.email_tool import generate_email
from tools.document_tool import generate_document
from tools.summarizer import summarize_research


def is_simple_query(task: str):
    task = task.lower()

    simple_patterns = [
        "what is", "who is", "where is",
        "when is", "define", "meaning of"
    ]

    agent_patterns = [
        "pdf", "document", "email", "excel",
        "report", "generate", "create"
    ]

    if any(p in task for p in agent_patterns):
        return False

    if any(p in task for p in simple_patterns):
        return True

    # default rule
    return len(task.split()) < 10


def execute_action(action: str, task_context: str, context: dict):
    action_lower = action.lower()

    research_keywords = [
        "research", "gather", "analyze",
        "investigate", "identify", "examine",
        "find", "search", "conduct"
    ]

    draft_keywords = ["draft", "write", "compose", "prepare"]
    send_keywords = ["send", "deliver"]
    read_keywords = ["read", "check", "open", "fetch"]

    if is_simple_query(task_context):
        return summarize_research(task_context, task_context)

    # ---------------- RESEARCH ----------------
    if any(keyword in action_lower for keyword in research_keywords):

        if not context.get("research_data"):

            raw_research = search_web(task_context)

            summarized = summarize_research(
                raw_research,
                task_context
            )

            context["research_data"] = summarized

            return summarized

        return "Research already completed."
    # ---------------- FORMAT ----------------
    elif any(word in action_lower for word in ["format", "organize", "summarize", "compile"]):

        formatted = context.get("research_data", [])
        context["formatted_data"] = formatted
        return formatted

    # ---------------- EMAIL ----------------
    elif "email" in action_lower:

        if any(word in action_lower for word in send_keywords):
            return f"Email Drafted, Check below\n{context.get('email_draft')}"

        elif any(word in action_lower for word in draft_keywords):

            if not context.get("email_draft"):
                email = generate_email(
                    str(context.get("formatted_data", context.get("research_data", task_context)))
                )

                context["email_draft"] = email
                return email

            return "Email Draft Already Prepared."

    # ---------------- PDF ----------------
    elif "pdf" in action_lower:
        return generate_document(
            str(context.get("formatted_data", context.get("research_data", task_context))),
            "pdf"
        )

    # ---------------- DOCX ----------------
    elif any(word in action_lower for word in ["document", "doc", "word"]):
        return generate_document(
            str(context.get("formatted_data", context.get("research_data", task_context))),
            "docx"
        )

    # ---------------- XLSX ----------------
    elif any(word in action_lower for word in ["excel", "sheet", "spreadsheet"]):
        return generate_document(
            str(context.get("formatted_data", context.get("research_data", task_context))),
            "xlsx"
        )

    return summarize_research(action, task_context)
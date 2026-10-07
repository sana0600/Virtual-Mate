try:
    from ..config import get_llm, map_provider_error
    from ..errors import AppError
except ImportError:
    from config import get_llm, map_provider_error
    from errors import AppError


def generate_email(task_context: str) -> str:
    prompt = f"""
Write a professional email for this task:

{task_context}

Return a complete draft containing a Subject line and email body. Do not claim
that the email was sent.
"""
    try:
        return get_llm().invoke(prompt).content
    except AppError:
        raise
    except Exception as exc:
        raise map_provider_error(exc) from exc

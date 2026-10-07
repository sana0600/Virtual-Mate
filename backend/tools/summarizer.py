try:
    from ..config import get_llm, map_provider_error
    from ..errors import AppError
except ImportError:
    from config import get_llm, map_provider_error
    from errors import AppError


def summarize_research(research_data, task: str) -> str:
    prompt = f"""
You are a professional research summarizer.

Task:
{task}

Research Data:
{research_data}

Instructions:
- Summarize the research clearly and professionally.
- Do not invent facts that are absent from the research data.
- Remove raw link formatting while retaining useful source names.
- If the task asks for a list or table, structure the result accordingly.
- Format the response as clean Markdown for display in a web interface.
- Start with a concise descriptive heading, use short paragraphs, and use
  subheadings, bullet lists, numbered steps, or a table when they improve clarity.
- Do not wrap the response in a Markdown code fence.
- Return only the final content.
"""
    try:
        return get_llm().invoke(prompt).content
    except AppError:
        raise
    except Exception as exc:
        raise map_provider_error(exc) from exc

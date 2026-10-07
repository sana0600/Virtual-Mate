from enum import Enum

from pydantic import BaseModel, Field, ValidationError

try:
    from ..config import get_llm, map_provider_error
    from ..errors import AppError, PlanningError
except ImportError:  # Support imports when backend/ is the working directory.
    from config import get_llm, map_provider_error
    from errors import AppError, PlanningError


class ActionType(str, Enum):
    WEB_SEARCH = "web_search"
    SUMMARIZE = "summarize"
    DRAFT_EMAIL = "draft_email"
    CREATE_PDF = "create_pdf"
    CREATE_DOCX = "create_docx"
    CREATE_XLSX = "create_xlsx"


class PlannedAction(BaseModel):
    type: ActionType
    instruction: str = Field(min_length=1, max_length=500)


class PlanStep(BaseModel):
    step: int = Field(ge=1)
    subtask: str = Field(min_length=1, max_length=300)
    actions: list[PlannedAction] = Field(min_length=1)


class PlanResponse(BaseModel):
    steps: list[PlanStep] = Field(min_length=1, max_length=12)


def generate_plan(task: str) -> list[PlanStep]:
    prompt = f"""
You are an AI workplace planner. Convert the task into executable actions.

Rules:
- Use only these action types: web_search, summarize, draft_email,
  create_pdf, create_docx, create_xlsx.
- Include web_search before summarize when current or researched information
  is required.
- Include summarize before a document action when research was performed.
- Use exactly the requested document type.
- For email tasks, use draft_email. This application drafts but does not send.
- Do not include physical, manual, consultation, delivery, or send-email steps.
- Keep the plan concise and preserve the user's requested outcome.

Task: {task}
"""

    try:
        planner = get_llm().with_structured_output(
            PlanResponse,
            method="json_schema",
        )
    except AppError:
        raise
    except Exception as exc:
        raise map_provider_error(exc) from exc

    last_error = None
    for attempt in range(2):
        try:
            response = planner.invoke(prompt)
            if isinstance(response, PlanResponse):
                return response.steps
            return PlanResponse.model_validate(response).steps
        except ValidationError as exc:
            last_error = exc
        except AppError:
            raise
        except Exception as exc:
            message = str(exc).lower()
            if attempt == 0 and ("schema" in message or "failed_generation" in message):
                last_error = exc
                continue
            raise map_provider_error(exc) from exc

    raise PlanningError("The AI provider returned an invalid task plan.") from last_error

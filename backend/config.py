import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

try:
    from .errors import AppError, ConfigurationError
except ImportError:  # Support `uvicorn main:app` from backend/.
    from errors import AppError, ConfigurationError


BACKEND_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BACKEND_DIR / "generated"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"

load_dotenv(BACKEND_DIR / ".env")


def get_model_name() -> str:
    return os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip()


def has_groq_key() -> bool:
    key = os.getenv("GROQ_API_KEY", "").strip()
    return bool(key and key != "your_groq_api_key_here")


@lru_cache(maxsize=1)
def get_llm() -> ChatGroq:
    if not has_groq_key():
        raise ConfigurationError(
            "GROQ_API_KEY is not configured. Copy backend/.env.example to "
            "backend/.env and provide a valid key."
        )

    return ChatGroq(
        model=get_model_name(),
        groq_api_key=os.environ["GROQ_API_KEY"].strip(),
        temperature=0.2,
        timeout=45,
        max_retries=2,
    )


def map_provider_error(exc: Exception) -> AppError:
    """Translate provider failures into a stable API error contract."""
    if isinstance(exc, AppError):
        return exc

    name = type(exc).__name__.lower()
    message = str(exc).lower()

    if "authentication" in name or "api_key" in message or "api key" in message:
        return AppError(
            "Groq rejected the configured API key.",
            code="provider_authentication_error",
            status_code=503,
        )
    if "ratelimit" in name or "rate limit" in message:
        return AppError(
            "Groq rate limit reached. Please retry shortly.",
            code="provider_rate_limit",
            status_code=429,
        )
    if "timeout" in name or "timed out" in message:
        return AppError(
            "Groq did not respond before the request timeout.",
            code="provider_timeout",
            status_code=504,
        )
    if "model" in message and ("decommission" in message or "not found" in message):
        return AppError(
            f"The configured Groq model '{get_model_name()}' is unavailable.",
            code="provider_model_unavailable",
            status_code=503,
        )

    return AppError(
        "The AI provider could not complete the request.",
        code="provider_error",
        status_code=502,
    )

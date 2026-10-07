import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

from .agents.executor import execute_action
from .agents.planner import generate_plan
from .config import GENERATED_DIR, get_model_name, has_groq_key
from .errors import AppError, ConfigurationError
from .tools.summarizer import summarize_research
from .tools.web_search import search_web


app = FastAPI(title="VirtualMate API", version="1.1.0")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"

# Mount static files and templates for serving the frontend. The static files are served from the "static" directory within the frontend folder, and Jinja2 templates are used to render HTML pages from the frontend directory.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=FRONTEND_DIR)

# CORS Middleware: This middleware is added to the FastAPI application to handle Cross-Origin Resource Sharing (CORS) requests. It allows requests from specified origins, which are defined in the environment variable "ALLOWED_ORIGINS". The middleware is configured to allow only GET and POST methods and restricts credentials and headers to ensure secure communication between the frontend and backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Pydantic model for task requests. It defines a single field 'task' with validation constraints, ensuring that the task is a non-empty string with a maximum length of 5000 characters. The model also includes a custom validator to normalize the task input by stripping whitespace and checking for emptiness.
class TaskRequest(BaseModel):
    task: str = Field(min_length=1, max_length=5000)

    @field_validator("task")
    @classmethod
    def normalize_task(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Task cannot be empty.")
        return value

#Custom Exception Handler: This handler catches custom application errors defined by the AppError class. It returns a JSON response with the appropriate status code and error details, including an error code and message, allowing for consistent error handling across the application.
@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )

#Validation Error Handler: This handler catches validation errors that occur when the request data does not meet the expected format or constraints defined in the Pydantic model. It returns a 422 Unprocessable Entity response with a specific error message indicating that the task must be non-empty and within the character limit.
@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, _exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Enter a non-empty task of at most 5000 characters.",
            }
        },
    )

#Unexpected Error Handler: This handler catches any unexpected exceptions that occur during request processing. It logs the exception details and returns a generic 500 Internal Server Error response to the client, indicating that the server could not complete the request.
@app.exception_handler(Exception)
async def unexpected_error_handler(_request: Request, _exc: Exception):
    logger.exception("Unexpected request failure", exc_info=_exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "The server could not complete the request.",
            }
        },
    )

#Function to determine if a task is an agent request based on the presence of certain keywords related to document handling and file generation. It checks if any of the specified artifact terms are present in the task string, indicating that the task may require agent capabilities rather than a simple chat response.
def is_agent_request(task: str) -> bool:
    task = task.lower()
    artifact_terms = (
        "pdf",
        "document",
        "docx",
        "word file",
        "excel",
        "xlsx",
        "sheet",
        "spreadsheet",
        "email",
        "report",
        "download",
        "export",
    )
    return any(term in task for term in artifact_terms)

#Home Endpoint: This endpoint serves the home page of the application. It uses Jinja2 templates to render the "index.html" file located in the frontend directory. The endpoint responds with an HTML response when accessed via a GET request.
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

#Health Check Endpoint: This endpoint checks if the GROQ API key is configured and whether the generated directory is writable. It returns a JSON response indicating the readiness status of the application, the model name, and the configuration status of GROQ. If the GROQ API key is not configured, it returns a 503 Service Unavailable status.
@app.get("/health")
def health():
    configured = has_groq_key()
    content = {
        "status": "ready" if configured else "not_ready",
        "model": get_model_name(),
        "groq_configured": configured,
        "generated_directory_writable": os.access(
            GENERATED_DIR if GENERATED_DIR.is_dir() else GENERATED_DIR.parent,
            os.W_OK,
        ),
    }
    if not configured:
        return JSONResponse(status_code=503, content=content)
    return content

#Execute Task Endpoint: This endpoint receives a task request, checks if the GROQ API key is configured, and determines whether to handle the request as a simple chat or as an agent task. If it's a chat request, it performs a web search and summarizes the research. If it's an agent request, it generates a plan, executes each action in the plan, and collects results and any generated files to return in the response.
@app.post("/execute")
def execute_task(req: TaskRequest):
    task = req.task

    if not has_groq_key():
        raise ConfigurationError(
            "GROQ_API_KEY is not configured. Copy backend/.env.example to "
            "backend/.env and provide a valid key."
        )

    if not is_agent_request(task):
        research = search_web(task)
        answer = summarize_research(research, task)
        return {"mode": "chat", "answer": answer}

    plan = generate_plan(task)
    context = {}
    execution_results = []
    files = []

    for step in plan:
        step_result = {
            "step": step.step,
            "subtask": step.subtask,
            "results": [],
        }
        for action in step.actions:
            result = execute_action(action, task, context)
            if result.get("type") == "file":
                files.append(
                    {
                        "filename": result["filename"],
                        "download_url": result["download_url"],
                    }
                )
            step_result["results"].append(result)
        execution_results.append(step_result)

    return {
        "mode": "agent",
        "plan": [step.model_dump(mode="json") for step in plan],
        "execution_results": execution_results,
        "files": files,
    }

# Serve generated agent files only after validating the requested filename and
# confirming that it exists inside GENERATED_DIR.
@app.get("/download/{filename}")
def download_file(filename: str):
    if Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = GENERATED_DIR / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, filename=filename)

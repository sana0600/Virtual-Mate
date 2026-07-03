import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from tools.web_search import search_web
from tools.summarizer import summarize_research
from agents.planner import generate_plan
from agents.executor import execute_action

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=FRONTEND_DIR)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskRequest(BaseModel):
    task: str

def is_agent_request(task: str):
    task = task.lower()

    strict_agent_keywords = [
        "pdf", "document", "excel", "sheet",
        "email", "send email",
        "download", "export",
        "generate pdf", "create document"
    ]

    return any(k in task for k in strict_agent_keywords)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.post("/execute")
def execute_task(req: TaskRequest):

    task = req.task

    # ================= CHAT MODE (DEFAULT) =================
    if not is_agent_request(task):

        research = search_web(task)
        answer = summarize_research(research, task)

        return {
            "mode": "chat",
            "answer": answer
        }

    # ================= AGENT MODE =================
    plan = generate_plan(task)

    context = {}
    execution_results = []
    files = []

    for step in plan:

        step_result = {
            "step": step["step"],
            "subtask": step["subtask"],
            "results": []
        }

        for action in step["actions"]:

            result = execute_action(action, task, context)

            if isinstance(result, dict) and "file_path" in result:
                files.append(os.path.basename(result["file_path"]))

            step_result["results"].append(result)

        execution_results.append(step_result)

    return {
        "mode": "agent",
        "plan": plan,
        "execution_results": execution_results,
        "files": list(set(files))
    }

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_DIR = os.path.join(BASE_DIR, "generated")
    
@app.get("/download/{filename}")
def download_file(filename: str):

    file_path = os.path.join(GENERATED_DIR, filename)

    if not os.path.isfile(file_path):
        return {"error": "File not found"}

    return FileResponse(
        file_path,
        filename=filename
    )
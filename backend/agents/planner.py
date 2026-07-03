from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
import json

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY")
)


def generate_plan(task: str):
    prompt = f"""
    Rules:
- Only include actions an AI software agent can perform.
- Do NOT include physical/manual/human tasks.
- Do NOT include unrealistic steps like interviews/consulting/opening apps.
- Keep actions concise and tool-friendly.

IMPORTANT RULES:
- If task asks for research/information/search:
  ALWAYS include explicit research step first.

- If task asks for document/pdf/excel/report:
  ALWAYS include create/generate/export action.

- If task asks for email:
  ALWAYS include draft email action before send email.
  
  If task asks for excel/sheet:
Return tabular format.
If task asks for pdf/doc:
Return report format.
If task asks for email:
Return professional email format.

You are an AI workplace planner.

Break the given task into structured subtasks.

Return ONLY valid JSON in this format:

[
    {{
        "step": 1,
        "subtask": "Subtask Name",
        "actions": [
            "Action 1",
            "Action 2"
        ]
    }}
]

    Task: {task}
    """

    response = llm.invoke(prompt)

    cleaned = response.content.replace("```json", "").replace("```", "").strip()

    return json.loads(cleaned)
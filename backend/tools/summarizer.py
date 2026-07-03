from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY")
)


def summarize_research(research_data, task):

    prompt = f"""
You are a professional research summarizer.

Task:
{task}

Research Data:
{research_data}

Instructions:
- Summarize the research clearly and professionally.
- Remove links/source formatting.
- Make it human readable.
- Keep only useful information.
- If task asks for list/table, structure accordingly.

Return only final summarized content.
"""

    response = llm.invoke(prompt)

    return response.content
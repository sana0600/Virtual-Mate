from agents.planner import llm


def generate_email(task_context: str):
    prompt = f"""
    Write a professional email for this task:

    {task_context}

    Return only the email body.
    """

    response = llm.invoke(prompt)

    return response.content
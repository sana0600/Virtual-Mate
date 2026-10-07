import pytest # type: ignore
from pydantic import ValidationError

from backend import config, main
from backend.agents.planner import ActionType, PlanStep, PlannedAction
from backend.errors import ConfigurationError

#Tests for the FastAPI application defined in backend/main.py. These tests cover various aspects of the application, including configuration handling, task execution, input validation, and error handling. The tests use pytest for assertions and monkeypatching to simulate different scenarios, such as missing environment variables or mocking external function calls.
def test_app_imports_and_health_reports_missing_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    config.get_llm.cache_clear()

    response = main.health()

    assert response.status_code == 503
    with pytest.raises(ConfigurationError):
        config.get_llm()


#Test to ensure that the execute_task function raises a ConfigurationError when the GROQ_API_KEY environment variable is missing. The test uses monkeypatching to remove the environment variable and mocks the search_web function to ensure it is not called, verifying that the application correctly handles missing configuration before making external calls.
def test_execute_rejects_missing_key_before_external_calls(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(
        main,
        "search_web",
        lambda _task: pytest.fail("Search should not run without provider configuration"),
    )

    with pytest.raises(ConfigurationError):
        main.execute_task(main.TaskRequest(task="What is FastAPI?"))

@pytest.mark.parametrize(
    "task",
    [
        "Generate a report",
        "Draft an email",
        "Create an Excel sheet",
        "Export this as DOCX",
    ],
)

#Test to ensure that artifact requests are handled in agent mode.
def test_artifact_requests_use_agent_mode(task):
    assert main.is_agent_request(task)

#Test to ensure that plain questions or tasks that do not involve generating artifacts are handled in chat mode. The test checks that the is_agent_request function returns False for a simple question, confirming that the application correctly distinguishes between chat and agent tasks based on the input.
def test_plain_question_uses_chat_mode():
    assert not main.is_agent_request("What is FastAPI?")

#Test to ensure that the TaskRequest model trims whitespace from the task input and raises a ValidationError for inputs that are only whitespace. The test verifies that the model correctly normalizes the input and enforces the non-empty constraint, ensuring that users cannot submit invalid tasks.
def test_task_input_is_trimmed_and_rejects_whitespace():
    assert main.TaskRequest(task="  useful task  ").task == "useful task"
    with pytest.raises(ValidationError):
        main.TaskRequest(task="   ")

#Test to ensure that provider errors are mapped to stable status codes. The test checks that specific exceptions related to authentication, rate limiting, and timeouts are correctly translated into consistent error codes and HTTP status codes, allowing for predictable error handling in the application.
def test_provider_errors_have_stable_status_codes():
    auth = config.map_provider_error(Exception("invalid api_key"))
    rate = config.map_provider_error(Exception("rate limit exceeded"))
    timeout = config.map_provider_error(TimeoutError("timed out"))

    assert (auth.code, auth.status_code) == ("provider_authentication_error", 503)
    assert (rate.code, rate.status_code) == ("provider_rate_limit", 429)
    assert (timeout.code, timeout.status_code) == ("provider_timeout", 504)


#Test to ensure that the execute_task function correctly handles a chat request by returning the expected answer. The test uses monkeypatching to set the GROQ_API_KEY environment variable and mock the search_web and summarize_research functions, simulating a successful chat execution and verifying that the output matches the expected result.
def test_chat_execution_contract(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(main, "search_web", lambda _task: [{"title": "Source"}])
    monkeypatch.setattr(main, "summarize_research", lambda _data, _task: "Answer")

    result = main.execute_task(main.TaskRequest(task="What is FastAPI?"))

    assert result == {"mode": "chat", "answer": "Answer"}


#Test to ensure that the execute_task function correctly handles an agent request that generates a file. The test uses monkeypatching to set the GROQ_API_KEY environment variable, mock the generate_plan and execute_action functions, and simulate a successful agent execution that produces a downloadable file. The test verifies that the output includes the expected mode and file information.
def test_agent_execution_contract_uses_filename_downloads(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    plan = [
        PlanStep(
            step=1,
            subtask="Create file",
            actions=[
                PlannedAction(type=ActionType.CREATE_PDF, instruction="Create the PDF")
            ],
        )
    ]
    monkeypatch.setattr(main, "generate_plan", lambda _task: plan)
    monkeypatch.setattr(
        main,
        "execute_action",
        lambda _action, _task, _context: {
            "type": "file",
            "status": "success",
            "filename": "result.pdf",
            "download_url": "/download/result.pdf",
        },
    )

    result = main.execute_task(main.TaskRequest(task="Create a PDF"))

    assert result["mode"] == "agent"
    assert result["files"] == [
        {"filename": "result.pdf", "download_url": "/download/result.pdf"}
    ]

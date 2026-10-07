from backend.agents import executor
from backend.agents.planner import ActionType, PlannedAction


def action(action_type):
    return PlannedAction(type=action_type, instruction="Test action")


def test_research_and_summary_pass_context(monkeypatch):
    monkeypatch.setattr(executor, "search_web", lambda task: [{"title": "Result"}])
    monkeypatch.setattr(executor, "summarize_research", lambda data, task: "Summary")
    context = {}

    research = executor.execute_action(action(ActionType.WEB_SEARCH), "Task", context)
    summary = executor.execute_action(action(ActionType.SUMMARIZE), "Task", context)

    assert research["type"] == "research"
    assert summary["content"] == "Summary"
    assert context["summary"] == "Summary"


def test_email_result_is_typed(monkeypatch):
    monkeypatch.setattr(executor, "generate_email", lambda content: "Subject: Test\n\nBody")

    result = executor.execute_action(
        action(ActionType.DRAFT_EMAIL),
        "Draft an email",
        {},
    )

    assert result == {
        "type": "email",
        "status": "success",
        "content": "Subject: Test\n\nBody",
    }


def test_document_dispatch_does_not_depend_on_instruction_keywords(monkeypatch):
    calls = []

    def fake_generate(content, file_type):
        calls.append(file_type)
        return {
            "message": "ok",
            "filename": f"file.{file_type}",
            "download_url": f"/download/file.{file_type}",
        }

    monkeypatch.setattr(executor, "generate_document", fake_generate)
    result = executor.execute_action(
        PlannedAction(type=ActionType.CREATE_PDF, instruction="Research and prepare output"),
        "Task",
        {"summary": "Content"},
    )

    assert calls == ["pdf"]
    assert result["type"] == "file"
    assert result["filename"] == "file.pdf"

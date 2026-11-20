
import json
import os
from types import SimpleNamespace
from unittest.mock import patch

# main.py checks for an API key during import.
# This dummy key allows offline tests without making API calls.
os.environ.setdefault("OPENROUTER_API_KEY", "offline-test-key")

import main


def make_tool_call(name, arguments, call_id="call-1"):
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(
            name=name,
            arguments=json.dumps(arguments),
        ),
    )


def make_message(content=None, tool_calls=None):
    return SimpleNamespace(
        content=content,
        tool_calls=tool_calls,
    )


def get_tool_messages(messages):
    return [item for item in messages if item["role"] == "tool"]


def setup_function():
    # Keep each test independent.
    main.messages.clear()


def teardown_function():
    main.messages.clear()


def test_normal_conversation_without_tools():
    response = make_message(content="Hello! How can I help?")

    with patch.object(main, "build_system_context", return_value="Test system"):
        with patch.object(main, "ask_agent", return_value=response):
            answer = main.run_agent("Hello")

    assert answer == "Hello! How can I help?"
    assert main.messages[-1]["content"] == answer


def test_agent_executes_calculator_tool():
    tool_response = make_message(
        tool_calls=[
            make_tool_call(
                "calculate",
                {"a": 125, "b": 25, "operation": "add"},
            )
        ]
    )
    final_response = make_message(content="The answer is 150.")

    recorded_messages = []

    def fake_ask_agent(current_messages, **kwargs):
        recorded_messages.append(list(current_messages))
        return [tool_response, final_response][len(recorded_messages) - 1]

    with patch.object(main, "build_system_context", return_value="Test system"):
        with patch.object(main, "ask_agent", side_effect=fake_ask_agent):
            answer = main.run_agent("What is 125 + 25?")

    assert answer == "The answer is 150."

    tool_messages = get_tool_messages(recorded_messages[1])
    assert len(tool_messages) == 1

    result = json.loads(tool_messages[0]["content"])
    assert result["success"] is True
    assert result["result"] == 150


def test_agent_executes_web_search_tool():
    tool_response = make_message(
        tool_calls=[
            make_tool_call(
                "web_search",
                {"query": "Python programming"},
            )
        ]
    )
    final_response = make_message(content="Here are the findings.")

    recorded_messages = []

    def fake_ask_agent(current_messages, **kwargs):
        recorded_messages.append(list(current_messages))
        return [tool_response, final_response][len(recorded_messages) - 1]

    search_result = {
        "success": True,
        "tool": "web_search",
        "result": [{"title": "Python", "url": "https://python.org"}],
    }

    with patch.object(main, "build_system_context", return_value="Test system"):
        with patch.object(main, "ask_agent", side_effect=fake_ask_agent):
            with patch.object(main, "execute_tool", return_value=search_result) as mock_tool:
                answer = main.run_agent("Research Python programming.")

    assert answer == "Here are the findings."
    mock_tool.assert_called_once_with(
        "web_search",
        {"query": "Python programming"},
    )

    tool_messages = get_tool_messages(recorded_messages[1])
    assert len(tool_messages) == 1
    assert json.loads(tool_messages[0]["content"]) == search_result


def test_agent_executes_memory_tool():
    tool_response = make_message(
        tool_calls=[
            make_tool_call(
                "save_memory",
                {"key": "business_idea", "value": "Sell digital products"},
            )
        ]
    )
    final_response = make_message(content="I've saved that information.")

    recorded_messages = []

    def fake_ask_agent(current_messages, **kwargs):
        recorded_messages.append(list(current_messages))
        return [tool_response, final_response][len(recorded_messages) - 1]

    memory_result = {
        "success": True,
        "tool": "save_memory",
        "result": {"success": True, "message": "Memory saved"},
    }

    with patch.object(main, "build_system_context", return_value="Test system"):
        with patch.object(main, "ask_agent", side_effect=fake_ask_agent):
            with patch.object(main, "execute_tool", return_value=memory_result) as mock_tool:
                answer = main.run_agent("Remember my business idea.")

    assert answer == "I've saved that information."
    mock_tool.assert_called_once_with(
        "save_memory",
        {"key": "business_idea", "value": "Sell digital products"},
    )


def test_agent_handles_multiple_tools_in_one_round():
    tool_response = make_message(
        tool_calls=[
            make_tool_call(
                "calculate",
                {"a": 100, "b": 50, "operation": "add"},
                "call-1",
            ),
            make_tool_call(
                "save_memory",
                {"key": "result", "value": "150"},
                "call-2",
            ),
        ]
    )
    final_response = make_message(content="Calculation complete and saved.")

    recorded_messages = []

    def fake_ask_agent(current_messages, **kwargs):
        recorded_messages.append(list(current_messages))
        return [tool_response, final_response][len(recorded_messages) - 1]

    def fake_execute_tool(name, arguments):
        if name == "calculate":
            return {"success": True, "tool": name, "result": 150}
        if name == "save_memory":
            return {"success": True, "tool": name, "result": "Saved"}

    with patch.object(main, "build_system_context", return_value="Test system"):
        with patch.object(main, "ask_agent", side_effect=fake_ask_agent):
            with patch.object(main, "execute_tool", side_effect=fake_execute_tool) as mock_tool:
                answer = main.run_agent("Calculate 100 + 50 and save the result.")

    assert answer == "Calculation complete and saved."
    assert mock_tool.call_count == 2

    tool_messages = get_tool_messages(recorded_messages[1])
    assert len(tool_messages) == 2
    assert [item["tool_call_id"] for item in tool_messages] == ["call-1", "call-2"]


def test_agent_adds_plan_before_execution():
    plan = "1. Research the market.\n2. Compare competitors.\n3. Recommend next steps."

    recorded_messages = []

    def fake_ask_agent(current_messages, **kwargs):
        recorded_messages.append(list(current_messages))
        return make_message(content="Here is the business plan.")

    with patch.object(main, "build_system_context", return_value="Test system"):
        with patch.object(main, "should_create_plan", return_value=True):
            with patch.object(main, "create_plan", return_value=plan):
                with patch.object(main, "ask_agent", side_effect=fake_ask_agent):
                    answer = main.run_agent("Create a business plan.")

    assert answer == "Here is the business plan."

    system_messages = [
        item["content"]
        for item in recorded_messages[0]
        if item["role"] == "system"
    ]

    assert any("Plan for this request:" in item for item in system_messages)
    assert any("Research the market" in item for item in system_messages)

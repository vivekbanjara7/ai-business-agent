
import pytest
from unittest.mock import patch, Mock

from tools import execute_tool


# 1. Unknown tool name
def test_unknown_tool():
    result = execute_tool("unknown_tool", {})

    assert result["success"] is False
    assert result["error_type"] == "unknown_tool"


# 2. Arguments are not a dictionary
def test_invalid_arguments_type():
    result = execute_tool("calculate", "not a dictionary")

    assert result["success"] is False
    assert result["error_type"] == "invalid_arguments"


# 3. Missing required argument
def test_missing_required_argument():
    result = execute_tool(
        "calculate",
        {"a": 10, "operation": "add"}
    )

    assert result["success"] is False
    assert result["error_type"] == "invalid_arguments"


# 4. Unexpected extra argument
def test_unexpected_extra_argument():
    result = execute_tool(
        "calculate",
        {
            "a": 10,
            "b": 5,
            "operation": "add",
            "extra": "unexpected"
        }
    )

    assert result["success"] is False
    assert result["error_type"] == "invalid_arguments"


# 5. Invalid argument value
def test_invalid_argument_value():
    result = execute_tool(
        "calculate",
        {
            "a": 10,
            "b": 0,
            "operation": "divide"
        }
    )

    assert result["success"] is False
    assert result["error_type"] == "invalid_arguments"
    assert "divide by zero" in result["error"]


# 6. Successful calculator execution
def test_successful_calculator_execution():
    result = execute_tool(
        "calculate",
        {
            "a": 250,
            "b": 12,
            "operation": "multiply"
        }
    )

    assert result["success"] is True
    assert result["tool"] == "calculate"
    assert result["result"] == 3000



# 7. Successful memory tool execution
def test_successful_memory_execution():
    mock_save_memory = Mock(
        return_value={
            "success": True,
            "message": "Memory saved"
        }
    )

    with patch.dict(
        "tools.AVAILABLE_FUNCTIONS",
        {"save_memory": mock_save_memory}
    ):
        result = execute_tool(
            "save_memory",
            {
                "key": "test",
                "value": "Testing memory"
            }
        )

    assert result["success"] is True
    assert result["tool"] == "save_memory"
    assert result["result"]["success"] is True

    mock_save_memory.assert_called_once_with(
        key="test",
        value="Testing memory"
    )



# 8. Unexpected internal tool exception
def test_unexpected_tool_exception():
    with patch(
        "tools.AVAILABLE_FUNCTIONS",
        {"fake_tool": lambda: 1 / 0}
    ):
        result = execute_tool("fake_tool", {})

    assert result["success"] is False
    assert result["error_type"] == "tool_execution_error"
    assert "division by zero" in result["error"]

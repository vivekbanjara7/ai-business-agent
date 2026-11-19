
import pytest
from tools import calculate, execute_tool


# 1. Addition
def test_addition():
    assert calculate(15000, 9500, "add") == 24500


# 2. Subtraction
def test_subtraction():
    assert calculate(15000, 9500, "subtract") == 5500


# 3. Multiplication
def test_multiplication():
    assert calculate(250, 12, "multiply") == 3000


# 4. Division
def test_division():
    assert calculate(15000, 3, "divide") == 5000


# 5. Decimal calculation
def test_decimal_calculation():
    assert calculate(125.50, 24.50, "add") == 150


# 6. Negative result
def test_negative_result():
    assert calculate(500, 800, "subtract") == -300


# 7. Division by zero
def test_division_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculate(100, 0, "divide")


# 8. Invalid operation
def test_invalid_operation():
    with pytest.raises(ValueError, match="Unsupported operation"):
        calculate(10, 5, "power")


# 9. Tool executor success
def test_calculator_tool_execution():
    result = execute_tool(
        "calculate",
        {"a": 15000, "b": 9500, "operation": "add"}
    )

    assert result["success"] is True
    assert result["result"] == 24500


# 10. Tool executor handles errors
def test_calculator_tool_error():
    result = execute_tool(
        "calculate",
        {"a": 100, "b": 0, "operation": "divide"}
    )

    assert result["success"] is False
    assert result["error_type"] == "invalid_arguments"

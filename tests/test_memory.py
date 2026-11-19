
import json
import pytest

import memory
import tools


# Use a separate temporary memory file for every test.
@pytest.fixture
def isolated_memory_file(tmp_path, monkeypatch):
    test_file = tmp_path / "test_memory.json"
    monkeypatch.setattr(memory, "MEMORY_FILE", str(test_file))
    return test_file


# 1. Save a memory
def test_save_memory(isolated_memory_file):
    result = memory.save_memory("project", "AI Business Agent")

    assert result["success"] is True
    assert isolated_memory_file.exists()

    with open(isolated_memory_file, "r", encoding="utf-8") as file:
        saved_data = json.load(file)

    assert saved_data["project"] == "AI Business Agent"


# 2. Retrieve a saved memory
def test_get_memory(isolated_memory_file):
    memory.save_memory("language", "Python")

    result = memory.get_memory()

    assert result["success"] is True
    assert result["memory"]["language"] == "Python"


# 3. Save multiple memories
def test_multiple_memories(isolated_memory_file):
    memory.save_memory("project", "AI Business Agent")
    memory.save_memory("language", "Python")
    memory.save_memory("goal", "Build AI agents")

    result = memory.get_memory()

    assert len(result["memory"]) == 3
    assert result["memory"]["language"] == "Python"
    assert result["memory"]["goal"] == "Build AI agents"


# 4. Retrieve when no memories exist
def test_empty_memory(isolated_memory_file):
    result = memory.get_memory()

    assert result["success"] is True
    assert result["memory"] == {}
    assert "No persistent memories" in result["message"]


# 5. Reject an empty memory key
def test_empty_memory_key(isolated_memory_file):
    with pytest.raises(ValueError, match="Memory key"):
        tools.save_memory(" ", "Some information")


# 6. Reject an empty memory value
def test_empty_memory_value(isolated_memory_file):
    with pytest.raises(ValueError, match="Memory value"):
        tools.save_memory("project", " ")


# 7. Reject an invalid key type
def test_invalid_key_type(isolated_memory_file):
    with pytest.raises(ValueError, match="Memory key"):
        tools.save_memory(123, "Some information")


# 8. Reject an invalid value type
def test_invalid_value_type(isolated_memory_file):
    with pytest.raises(ValueError, match="Memory value"):
        tools.save_memory("project", 123)


# 9. Verify data persists when loaded again from disk
def test_memory_persistence(isolated_memory_file):
    memory.save_memory("project", "AI Business Agent")

    # Load the data again from the JSON file.
    reloaded_data = memory.load_memory()

    assert reloaded_data["project"] == "AI Business Agent"


# 10. Test memory through the central tool executor
def test_memory_tool_execution(isolated_memory_file):
    save_result = tools.execute_tool(
        "save_memory",
        {
            "key": "project",
            "value": "AI Business Agent"
        }
    )

    assert save_result["success"] is True

    get_result = tools.execute_tool("get_memory", {})

    assert get_result["success"] is True
    assert get_result["result"]["memory"]["project"] == (
        "AI Business Agent"
    )

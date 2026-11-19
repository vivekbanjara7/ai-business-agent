import json
import os


# --------------------------------------------------
# Memory file
# --------------------------------------------------

MEMORY_FILE = "memory.json"


# --------------------------------------------------
# Load memory
# --------------------------------------------------

def load_memory():

    if not os.path.exists(MEMORY_FILE):
        return {}

    try:

        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):

        return {}


# --------------------------------------------------
# Save memory
# --------------------------------------------------

def save_memory(key: str, value: str):

    memory = load_memory()

    memory[key] = value

    with open(MEMORY_FILE, "w", encoding="utf-8") as file:

        json.dump(
            memory,
            file,
            indent=4,
            ensure_ascii=False
        )

    return {
        "success": True,
        "message": f"Memory saved: {key}"
    }


# --------------------------------------------------
# Get memory
# --------------------------------------------------

def get_memory():

    memory = load_memory()

    if not memory:

        return {
            "success": True,
            "memory": {},
            "message": "No persistent memories have been saved yet."
        }

    return {
        "success": True,
        "memory": memory
    }
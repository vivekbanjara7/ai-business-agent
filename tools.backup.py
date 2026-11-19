
import os
import requests

from memory import save_memory as save_memory_data
from memory import get_memory as get_memory_data


# --------------------------------------------------
# Configuration
# --------------------------------------------------

TINYFISH_API_URL = "https://api.search.tinyfish.ai"
SEARCH_TIMEOUT = 20
MAX_RESULTS = 10
MAX_SNIPPET_LENGTH = 1200


# --------------------------------------------------
# Calculator
# --------------------------------------------------

def calculate(a: float, b: float, operation: str):

    if operation == "add":
        return a + b

    elif operation == "subtract":
        return a - b

    elif operation == "multiply":
        return a * b

    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero.")
        return a / b

    else:
        raise ValueError(
            f"Unsupported operation: {operation}"
        )


# --------------------------------------------------
# Web search
# --------------------------------------------------

def web_search(query: str):

    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty.")

    api_key = os.environ.get("TINYFISH_API_KEY")

    if not api_key:
        raise RuntimeError(
            "TINYFISH_API_KEY is not set in the environment."
        )

    response = requests.get(
        TINYFISH_API_URL,
        params={"query": query},
        headers={"X-API-Key": api_key},
        timeout=SEARCH_TIMEOUT
    )

    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as exc:
        raise ValueError(
            "TinyFish returned invalid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            "TinyFish returned an unexpected response format."
        )

    raw_results = data.get("results", [])

    if not isinstance(raw_results, list):
        raise ValueError(
            "TinyFish response did not contain a valid results list."
        )

    results = []

    for item in raw_results[:MAX_RESULTS]:

        if not isinstance(item, dict):
            continue

        title = item.get("title")
        url = item.get("url")
        snippet = item.get("snippet")
        site_name = item.get("site_name")
        position = item.get("position")

        # Keep only actual fields returned by the search service.
        # Missing fields stay empty instead of being invented.
        results.append({
            "position": position,
            "title": title.strip() if isinstance(title, str) else None,
            "url": url.strip() if isinstance(url, str) else None,
            "site_name": (
                site_name.strip()
                if isinstance(site_name, str)
                else None
            ),
            "snippet": (
                snippet[:MAX_SNIPPET_LENGTH]
                if isinstance(snippet, str)
                else None
            )
        })

    return {
        "success": True,
        "query": data.get("query", query),
        "result_count": len(results),
        "total_results": data.get("total_results"),
        "results": results,
        "evidence_note": (
            "These are search-result titles, URLs, and snippets. "
            "A snippet is preliminary evidence, not proof that every "
            "claim is current or accurate. Prefer official sources "
            "for prices and product details."
        )
    }


# --------------------------------------------------
# Persistent memory
# --------------------------------------------------

def save_memory(key: str, value: str):

    return save_memory_data(key, value)


def get_memory():

    return get_memory_data()


# --------------------------------------------------
# Calculator tool schema
# --------------------------------------------------

calculator_tool = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": (
            "Use for arithmetic calculations only: addition, "
            "subtraction, multiplication, or division. "
            "Division by zero is an error."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "First number."
                },
                "b": {
                    "type": "number",
                    "description": "Second number."
                },
                "operation": {
                    "type": "string",
                    "enum": [
                        "add",
                        "subtract",
                        "multiply",
                        "divide"
                    ],
                    "description": "Arithmetic operation."
                }
            },
            "required": ["a", "b", "operation"],
            "additionalProperties": False
        }
    }
}


# --------------------------------------------------
# Web search tool schema
# --------------------------------------------------

web_search_tool = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for current information or information "
            "that needs external verification. Returns structured "
            "search results containing titles, URLs, site names, "
            "and snippets. Use focused queries. For prices, versions, "
            "or other changing facts, prefer official sources. "
            "Do not treat snippets alone as definitive verification. "
            "Do not repeat a query that already returned useful results."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "One focused search query. For example: "
                        "'site:ynab.com pricing annual subscription'."
                    )
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }
    }
}


# --------------------------------------------------
# Save memory tool schema
# --------------------------------------------------

save_memory_tool = {
    "type": "function",
    "function": {
        "name": "save_memory",
        "description": (
            "Save useful, non-sensitive information likely to remain "
            "relevant across sessions. Never save passwords, API keys, "
            "authentication tokens, or financial secrets."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Short descriptive memory key."
                },
                "value": {
                    "type": "string",
                    "description": "Information to remember."
                }
            },
            "required": ["key", "value"],
            "additionalProperties": False
        }
    }
}


# --------------------------------------------------
# Get memory tool schema
# --------------------------------------------------

get_memory_tool = {
    "type": "function",
    "function": {
        "name": "get_memory",
        "description": (
            "Retrieve saved information when the current request "
            "depends on previous sessions."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    }
}


# --------------------------------------------------
# Register available tools
# --------------------------------------------------

ALL_TOOLS = [
    calculator_tool,
    web_search_tool,
    save_memory_tool,
    get_memory_tool
]


AVAILABLE_FUNCTIONS = {
    "calculate": calculate,
    "web_search": web_search,
    "save_memory": save_memory,
    "get_memory": get_memory
}


# --------------------------------------------------
# Central tool executor
# --------------------------------------------------

def execute_tool(tool_name, arguments):

    tool_function = AVAILABLE_FUNCTIONS.get(tool_name)

    if tool_function is None:
        return {
            "success": False,
            "tool": tool_name,
            "error_type": "unknown_tool",
            "error": f"Unknown tool: {tool_name}"
        }

    if not isinstance(arguments, dict):
        return {
            "success": False,
            "tool": tool_name,
            "error_type": "invalid_arguments",
            "error": "Tool arguments must be a JSON object."
        }

    try:
        result = tool_function(**arguments)

        return {
            "success": True,
            "tool": tool_name,
            "result": result
        }

    except TypeError as exc:
        return {
            "success": False,
            "tool": tool_name,
            "error_type": "invalid_arguments",
            "error": str(exc)
        }

    except ValueError as exc:
        return {
            "success": False,
            "tool": tool_name,
            "error_type": "invalid_arguments",
            "error": str(exc)
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "tool": tool_name,
            "error_type": "timeout",
            "error": "The web request timed out."
        }

    except requests.exceptions.HTTPError as exc:
        status_code = (
            exc.response.status_code
            if exc.response is not None
            else None
        )

        return {
            "success": False,
            "tool": tool_name,
            "error_type": "http_error",
            "status_code": status_code,
            "error": str(exc)
        }

    except requests.exceptions.RequestException as exc:
        return {
            "success": False,
            "tool": tool_name,
            "error_type": "network_error",
            "error": str(exc)
        }

    except Exception as exc:
        return {
            "success": False,
            "tool": tool_name,
            "error_type": "tool_execution_error",
            "error": str(exc)
        }

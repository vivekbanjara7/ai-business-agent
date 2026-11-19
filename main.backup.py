
import os
import json

from openai import OpenAI

from tools import ALL_TOOLS, execute_tool
from memory import load_memory


# ==================================================
# OPENROUTER SETUP
# ==================================================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

MODEL = "openrouter/free"

MAX_TOOL_ROUNDS = 5
MAX_WEB_SEARCHES = 3
MAX_TOOL_CALLS = 5
MAX_HISTORY_MESSAGES = 20


# ==================================================
# SYSTEM INSTRUCTIONS
# ==================================================

SYSTEM_PROMPT = """
You are an AI business assistant.

GENERAL RULES
- Answer directly when tools are unnecessary.
- Use calculate for arithmetic.
- Use web_search for current information and external evidence.
- Use save_memory for useful, non-sensitive long-term information.
- Use get_memory when saved information is relevant.
- Never invent facts, prices, sources, or tool results.

EVIDENCE RULES
- Search snippets are evidence, not automatic proof.
- Prefer official sources for a company's prices, plans, and features.
- Distinguish official-source evidence, secondary-source evidence,
  unverified information, and information not found.
- Include source URLs for important research findings.
- Never claim to have opened or read a complete webpage when you
  only received its search-result snippet.
- If sources conflict, explain the conflict.
- Do not claim a price is current unless the available evidence
  reasonably supports that conclusion.

RESEARCH RULES
- Use focused, distinct search queries.
- Inspect existing results before deciding whether to search again.
- Do not repeat an identical successful search.
- Avoid searches that are unlikely to add new evidence.
- Stop searching when sufficient evidence has been collected
  or the search budget is exhausted.
- If evidence is incomplete, provide the best useful partial answer
  and explain what remains unknown.
- Do not invent information to complete a plan.

CALCULATION RULES
- Use calculate when exact arithmetic is useful.
- Calculate only from supported or user-provided input values.
- Show important inputs and calculations.
- A correct calculation does not verify its input values.

TOOL FAILURE RULES
- A failed tool did not produce a successful result.
- Do not repeatedly retry the same failed operation without reason.
- Explain important failures honestly.

MEMORY RULES
- Save only useful, non-sensitive information likely to matter later.
- Never save passwords, API keys, authentication tokens,
  or financial secrets.

FINAL ANSWERS
For research tasks, include relevant findings, evidence labels,
source URLs, calculations, uncertainties, and practical next steps
as appropriate.

Be accurate, practical, and transparent about uncertainty.
"""


# ==================================================
# LOAD PERSISTENT MEMORY
# ==================================================

def build_system_context():

    context = SYSTEM_PROMPT
    saved_memory = load_memory()

    if saved_memory:
        context += (
            "\n\nRELEVANT SAVED USER INFORMATION:\n"
            + json.dumps(
                saved_memory,
                indent=2,
                ensure_ascii=False
            )
        )

    return context


# ==================================================
# PLAN A MULTI-STEP REQUEST
# ==================================================

def create_plan(user_input):

    planning_messages = [
        {
            "role": "system",
            "content": (
                "You are a planning component for an AI business agent. "
                "For a simple request, return exactly NO_PLAN. "
                "For a genuinely multi-step request, create a numbered "
                "plan of at most 5 concise steps. Include research, "
                "evidence checking, calculations, and reporting only "
                "when relevant. Do not execute tools or invent facts."
            )
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=planning_messages
        )

        content = response.choices[0].message.content

        if not content or content.strip().upper() == "NO_PLAN":
            return None

        return content.strip()

    except Exception as exc:
        print(
            f"[Planning unavailable: {type(exc).__name__}]"
        )
        return None


# ==================================================
# ASK THE MODEL
# ==================================================

def ask_agent(current_messages, use_tools=True):

    arguments = {
        "model": MODEL,
        "messages": current_messages
    }

    if use_tools:
        arguments["tools"] = ALL_TOOLS

    response = client.chat.completions.create(**arguments)

    return response.choices[0].message


# ==================================================
# FINAL ANSWER FALLBACK
# ==================================================

def create_final_answer(current_messages, reason):

    final_messages = current_messages + [
        {
            "role": "system",
            "content": (
                "Now provide the best complete answer possible using "
                "the evidence and tool results already in the conversation. "
                "Do not call more tools. "
                "Do not invent missing facts or sources. "
                "For research, include relevant source URLs and distinguish "
                "official-source evidence, secondary-source evidence, "
                "unverified information, and missing information. "
                "Show supported calculations where useful. "
                "If a tool budget was reached, briefly disclose that "
                "limitation when it affects the answer. "
                "Reason for finalizing: "
                + reason
            )
        }
    ]

    try:
        response = ask_agent(final_messages, use_tools=False)
        answer = response.content

        if answer:
            return answer

        return (
            "I could not produce a complete answer from the available "
            "information. Please try a narrower request."
        )

    except Exception as exc:
        print(
            f"[Final-answer generation failed: {type(exc).__name__}]"
        )

        return (
            "I could not generate the final answer because the model "
            "request failed. Please try again."
        )


# ==================================================
# AGENT LOOP
# ==================================================

def run_agent(user_input):

    # Build a separate context for this request.
    # This prevents temporary planning instructions from leaking
    # into later user requests.
    current_messages = [
        {
            "role": "system",
            "content": build_system_context()
        }
    ]

    # Keep recent conversation history without carrying over
    # previous requests' temporary plans or budget instructions.
    history = messages[-MAX_HISTORY_MESSAGES:]

    current_messages.extend(history)

    current_messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    # ----------------------------------------------
    # Planning
    # ----------------------------------------------

    print("\n[Planning...]")

    plan = create_plan(user_input)

    if plan:
        print("[Plan created]")
        print(plan)

        current_messages.append(
            {
                "role": "system",
                "content": (
                    "Plan for this request:\n"
                    + plan
                    + "\nUse this plan flexibly. Prioritize useful "
                    "evidence and complete the task honestly."
                )
            }
        )
    else:
        print("[No multi-step plan needed]")

    # ----------------------------------------------
    # Per-request counters
    # ----------------------------------------------

    tool_rounds = 0
    tool_calls_used = 0
    web_searches_used = 0

    successful_queries = set()

    # ----------------------------------------------
    # Decision loop
    # ----------------------------------------------

    while True:

        # Check budgets before asking the model for another tool round.
        # The final answer is generated without tools if a hard limit
        # has been reached.
        if tool_rounds >= MAX_TOOL_ROUNDS:
            print("[Tool-round budget reached]")
            return create_final_answer(
                current_messages,
                "Maximum tool rounds reached."
            )

        if tool_calls_used >= MAX_TOOL_CALLS:
            print("[Tool-call budget reached]")
            return create_final_answer(
                current_messages,
                "Maximum total tool calls reached."
            )

        message = ask_agent(current_messages)

        # ------------------------------------------
        # Final answer
        # ------------------------------------------

        if not message.tool_calls:

            answer = message.content or (
                "I could not generate a response for this request."
            )

            # Store only the completed user/assistant exchange
            # in cross-request history.
            messages.append(
                {
                    "role": "user",
                    "content": user_input
                }
            )

            messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            return answer

        tool_rounds += 1

        print(f"\n[Tool round {tool_rounds}]")

        current_messages.append(message)

        # ------------------------------------------
        # Execute requested tools
        # ------------------------------------------

        for tool_call in message.tool_calls:

            tool_name = tool_call.function.name

            try:
                arguments = json.loads(
                    tool_call.function.arguments
                )
            except (json.JSONDecodeError, TypeError):
                arguments = None

            if not isinstance(arguments, dict):

                tool_result = {
                    "success": False,
                    "tool": tool_name,
                    "error_type": "invalid_arguments",
                    "error": "Tool arguments must be a valid JSON object."
                }

            elif tool_calls_used >= MAX_TOOL_CALLS:

                tool_result = {
                    "success": False,
                    "tool": tool_name,
                    "error_type": "tool_budget_reached",
                    "error": "The total tool-call budget is exhausted."
                }

            elif tool_name == "web_search":

                query = arguments.get("query", "")

                if not isinstance(query, str) or not query.strip():

                    tool_result = {
                        "success": False,
                        "tool": tool_name,
                        "error_type": "invalid_arguments",
                        "error": "A non-empty search query is required."
                    }

                else:
                    normalized_query = " ".join(
                        query.casefold().split()
                    )

                    if normalized_query in successful_queries:

                        tool_result = {
                            "success": False,
                            "tool": tool_name,
                            "error_type": "duplicate_search",
                            "error": (
                                "This exact query already succeeded. "
                                "Use the existing results or search for "
                                "a genuinely different missing fact."
                            )
                        }

                    elif web_searches_used >= MAX_WEB_SEARCHES:

                        print("[Web-search budget reached]")

                        tool_result = {
                            "success": False,
                            "tool": tool_name,
                            "error_type": "search_budget_reached",
                            "error": (
                                "The web-search budget is exhausted. "
                                "Use existing evidence and other permitted "
                                "tools, then provide the best supported answer."
                            )
                        }

                    else:
                        web_searches_used += 1
                        tool_calls_used += 1

                        print("[Using tool: web_search]")
                        print(
                            f"[Search {web_searches_used}/"
                            f"{MAX_WEB_SEARCHES}]"
                        )

                        tool_result = execute_tool(
                            tool_name,
                            arguments
                        )

                        if tool_result.get("success") is True:
                            successful_queries.add(normalized_query)
                            print("[Tool succeeded]")
                        else:
                            print(
                                "[Tool failed: "
                                + tool_result.get(
                                    "error_type",
                                    "unknown_error"
                                )
                                + "]"
                            )

            else:

                tool_calls_used += 1

                print(f"[Using tool: {tool_name}]")

                tool_result = execute_tool(
                    tool_name,
                    arguments
                )

                if tool_result.get("success") is True:
                    print("[Tool succeeded]")
                else:
                    print(
                        "[Tool failed: "
                        + tool_result.get(
                            "error_type",
                            "unknown_error"
                        )
                        + "]"
                    )

            # Always respond to each tool call so the model's
            # tool-call history remains structurally valid.
            current_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        tool_result,
                        ensure_ascii=False
                    )
                }
            )


# ==================================================
# CONVERSATION HISTORY
# ==================================================

messages = []


# ==================================================
# MAIN PROGRAM
# ==================================================

print("================================")
print("      AI Business Agent")
print("================================")
print("Type 'exit' to end the session.\n")


while True:

    try:
        user_input = input("You: ")

    except (EOFError, KeyboardInterrupt):
        print("\nSession ended. See you next time!")
        break

    if user_input.strip().lower() == "exit":
        print("\nSession ended. See you next time!")
        break

    if not user_input.strip():
        continue

    try:
        answer = run_agent(user_input)

        print("\nAgent:", answer)
        print()

    except Exception as exc:
        print(
            f"\nError: {type(exc).__name__}: {exc}\n"
        )

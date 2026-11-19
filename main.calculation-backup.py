import json
import os
import re

from openai import OpenAI
from tools import ALL_TOOLS, execute_tool
from memory import load_memory


# ==================================================
# OPENROUTER CONFIGURATION
# ==================================================

api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    raise RuntimeError(
        "OPENROUTER_API_KEY is not set. Set it in your environment "
        "before starting the AI Business Agent."
    )

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
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
- Use get_memory when saved memory is relevant.
- Never invent facts, prices, sources, or tool results.

EVIDENCE RULES
- Search snippets are preliminary evidence, not automatic proof.
- Prefer official sources for company prices, plans, and features.
- Distinguish official-source evidence, secondary-source evidence,
  user-provided information, unverified information, and information
  that could not be found.
- Include actual source URLs from tool results for important claims.
- Never invent a URL, citation ID, line number, or reference marker.
- Do not output unexplained citation tokens such as [1+L1-L3].
- If a usable source URL is not present in the results, say so.
- Never claim to have opened or read a complete webpage when you
  only received its search-result snippet.
- If sources conflict, explain the conflict.
- Do not claim a price is current unless available evidence supports it.
- Attach sources to the claims they actually support.
- A source mentioning a company does not automatically support
  every claim about that company.

RESEARCH RULES
- Use focused, distinct search queries.
- Inspect existing results before deciding whether to search again.
- Do not repeat an identical successful search.
- Avoid searches unlikely to add new evidence.
- Stop searching when sufficient evidence has been collected
  or the search budget is exhausted.
- If evidence is incomplete, provide a useful partial answer and
  explain what remains unknown.
- Do not invent information to complete a plan.

CALCULATION RULES
- Use calculate when exact arithmetic is useful.
- Calculate only from supported or user-provided input values.
- Show important inputs and calculations.
- A correct calculation does not verify its input values.
- Clearly distinguish hypothetical calculations from verified prices.

RESEARCH REPORT FORMAT
For substantial research, comparison, or business-analysis tasks,
use the relevant sections below:
1. Executive summary: the main finding or recommendation.
2. Findings: important facts, with actual source URLs near claims.
3. Comparison and calculations: inputs and calculations, marking
   user-provided or hypothetical values clearly.
4. Evidence quality and limitations: identify source types and
   unverified or missing details.
5. Recommendation and next steps: practical next actions supported
   by the evidence.

Adapt the structure to the request. Do not force every section into
simple questions. Avoid unnecessary repetition and overly long reports.

TOOL FAILURE RULES
- A failed tool did not produce a successful result.
- Do not repeatedly retry the same failed operation without reason.
- Explain important failures honestly.
- Never present an error message as factual research.

MEMORY RULES
- Save only useful, non-sensitive information likely to matter later.
- Never save passwords, API keys, authentication tokens,
  or financial secrets.

FINAL ANSWERS
- Answer the user's actual question.
- Use clear headings and concise, useful language.
- Include relevant source URLs, calculations, uncertainties, and
  practical next steps as appropriate.
- Do not claim an action was completed unless it actually was.

Be accurate, practical, and transparent about uncertainty.
""".strip()


# ==================================================
# LOAD PERSISTENT MEMORY
# ==================================================

def build_system_context():
    context = SYSTEM_PROMPT

    try:
        saved_memory = load_memory()
    except Exception as exc:
        print(f"[Memory unavailable: {type(exc).__name__}]")
        saved_memory = None

    if saved_memory:
        context += (
            "\n\nRELEVANT SAVED USER INFORMATION:\n"
            + json.dumps(saved_memory, indent=2, ensure_ascii=False)
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
                "For a simple request, return exactly NO_PLAN. For a "
                "genuinely multi-step request, create a numbered plan "
                "of at most 5 concise steps. Include research, evidence "
                "checking, calculations, and reporting only when relevant. "
                "Do not execute tools or invent facts. Return only the "
                "plan or NO_PLAN."
            ),
        },
        {"role": "user", "content": user_input},
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=planning_messages,
        )

        if not response.choices:
            return None

        content = response.choices[0].message.content

        if not content or content.strip().upper() == "NO_PLAN":
            return None

        return content.strip()

    except Exception as exc:
        print(f"[Planning unavailable: {type(exc).__name__}]")
        return None


# ==================================================
# ASK THE MODEL
# ==================================================

def ask_agent(current_messages, use_tools=True):
    arguments = {
        "model": MODEL,
        "messages": current_messages,
    }

    if use_tools:
        arguments["tools"] = ALL_TOOLS

    response = client.chat.completions.create(**arguments)

    if not response.choices:
        raise RuntimeError("The model returned no response choices.")

    return response.choices[0].message


# ==================================================
# CLEAN KNOWN PROVIDER ARTIFACTS
# ==================================================

def clean_answer(answer):
    """
    Remove only the specific stray metadata pattern previously seen.
    Do not broadly remove JSON, citations, URLs, or ordinary prose.
    """
    if not isinstance(answer, str):
        return ""

    # Remove the specific JSON metadata pattern seen previously.
    answer = re.sub(
        r'\s*\{"id"\s*:\s*\d+\s*,\s*"cursor"\s*:\s*\d+\s*,'
        r'\s*"loc"\s*:\s*\d+\s*\}',
        "",
        answer,
    )

    # Remove only the unexplained citation-token pattern observed in
    # the agent's output, for example: [1+L1-L3] or [7+L1–L3].
    # This deliberately does not remove normal citations like [1].
    answer = re.sub(
        r'\[\s*\d+\s*\+\s*L\d+\s*[–-]\s*L\d+\s*\]',
        "",
        answer,
    )

    # Collapse spaces left behind where these artifacts were removed.
    answer = re.sub(r'[ \t]{2,}', ' ', answer)

    return answer.strip()


# ==================================================
# SAVE COMPLETED CONVERSATION EXCHANGE
# ==================================================

def save_exchange(user_input, answer):
    """Save one completed user/assistant exchange to session history."""
    messages.append({"role": "user", "content": user_input})
    messages.append({"role": "assistant", "content": answer})

    if len(messages) > MAX_HISTORY_MESSAGES:
        del messages[:-MAX_HISTORY_MESSAGES]


# ==================================================
# FINAL ANSWER FALLBACK
# ==================================================

def create_final_answer(current_messages, reason):
    final_instruction = (
        "Produce the best complete answer possible using only the "
        "conversation and tool results already available. Do not call "
        "tools. Do not invent missing facts or sources. For research, "
        "use relevant findings, actual source URLs, supported calculations, "
        "evidence limitations, and practical next steps as appropriate. "
        "Distinguish official-source evidence, secondary-source evidence, "
        "user-provided information, and unverified or missing information. "
        "Use only URLs actually present in the available tool results. "
        "Never invent citation identifiers, line numbers, or reference "
        "markers. Do not output unexplained tokens such as [1+L1-L3]. "
        "If a source URL is missing, state that it was not available in "
        "the search results. If a tool budget was reached, disclose that "
        "when it affects the answer. Reason for finalizing: "
        + str(reason)
    )

    final_messages = [dict(item) for item in current_messages]

    if final_messages and final_messages[0].get("role") == "system":
        original = final_messages[0].get("content") or ""
        final_messages[0]["content"] = (
            original + "\n\nFINAL RESPONSE INSTRUCTIONS:\n" + final_instruction
        )
    else:
        final_messages.insert(
            0,
            {"role": "system", "content": final_instruction},
        )

    try:
        response = ask_agent(final_messages, use_tools=False)
        answer = clean_answer(response.content or "")

        if answer:
            return answer

        return (
            "I could not produce a complete answer from the available "
            "information. Please try a narrower request."
        )

    except Exception as exc:
        print(f"[Final-answer generation failed: {type(exc).__name__}]")
        return (
            "I could not generate the final answer because the model "
            "request failed. Please try again."
        )


# ==================================================
# AGENT LOOP
# ==================================================

def run_agent(user_input):
    current_messages = [
        {"role": "system", "content": build_system_context()}
    ]

    # Session history contains completed exchanges only.
    current_messages.extend(messages[-MAX_HISTORY_MESSAGES:])
    current_messages.append({"role": "user", "content": user_input})

    # --------------------------------------------------
    # Planning
    # --------------------------------------------------

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
                    + "\nUse this plan flexibly. Prioritize useful evidence "
                    "and complete the task honestly."
                ),
            }
        )
    else:
        print("[No multi-step plan needed]")

    # --------------------------------------------------
    # Per-request budgets
    # --------------------------------------------------

    tool_rounds = 0
    tool_calls_used = 0
    web_searches_used = 0
    successful_queries = set()

    # --------------------------------------------------
    # Decision loop
    # --------------------------------------------------

    while True:
        if tool_rounds >= MAX_TOOL_ROUNDS:
            print("[Tool-round budget reached]")
            answer = create_final_answer(
                current_messages,
                "Maximum tool rounds reached.",
            )
            save_exchange(user_input, answer)
            return answer

        if tool_calls_used >= MAX_TOOL_CALLS:
            print("[Tool-call budget reached]")
            answer = create_final_answer(
                current_messages,
                "Maximum total tool calls reached.",
            )
            save_exchange(user_input, answer)
            return answer

        message = ask_agent(current_messages)

        # --------------------------------------------------
        # Normal final answer
        # --------------------------------------------------

        if not message.tool_calls:
            answer = clean_answer(message.content or "")

            if not answer:
                answer = (
                    "I could not generate a response for this request."
                )

            save_exchange(user_input, answer)
            return answer

        tool_rounds += 1
        print(f"\n[Tool round {tool_rounds}]")
        current_messages.append(message)

        # --------------------------------------------------
        # Execute requested tools
        # --------------------------------------------------

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name

            try:
                arguments = json.loads(tool_call.function.arguments)
            except (json.JSONDecodeError, TypeError):
                arguments = None

            if not isinstance(arguments, dict):
                tool_result = {
                    "success": False,
                    "tool": tool_name,
                    "error_type": "invalid_arguments",
                    "error": "Tool arguments must be a valid JSON object.",
                }

            elif tool_calls_used >= MAX_TOOL_CALLS:
                tool_result = {
                    "success": False,
                    "tool": tool_name,
                    "error_type": "tool_budget_reached",
                    "error": "The total tool-call budget is exhausted.",
                }

            elif tool_name == "web_search":
                query = arguments.get("query", "")

                if not isinstance(query, str) or not query.strip():
                    tool_result = {
                        "success": False,
                        "tool": tool_name,
                        "error_type": "invalid_arguments",
                        "error": "A non-empty search query is required.",
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
                                "This exact query already succeeded. Use "
                                "the existing results or search for a "
                                "genuinely different missing fact."
                            ),
                        }

                    elif web_searches_used >= MAX_WEB_SEARCHES:
                        print("[Web-search budget reached]")
                        tool_result = {
                            "success": False,
                            "tool": tool_name,
                            "error_type": "search_budget_reached",
                            "error": (
                                "The web-search budget is exhausted. Use "
                                "existing evidence and permitted tools, "
                                "then provide the best supported answer."
                            ),
                        }

                    else:
                        web_searches_used += 1
                        tool_calls_used += 1

                        print("[Using tool: web_search]")
                        print(
                            f"[Search {web_searches_used}/"
                            f"{MAX_WEB_SEARCHES}]"
                        )

                        tool_result = execute_tool(tool_name, arguments)

                        if tool_result.get("success") is True:
                            successful_queries.add(normalized_query)
                            print("[Tool succeeded]")
                        else:
                            print(
                                "[Tool failed: "
                                + str(
                                    tool_result.get(
                                        "error_type", "unknown_error"
                                    )
                                )
                                + "]"
                            )

            else:
                tool_calls_used += 1
                print(f"[Using tool: {tool_name}]")

                tool_result = execute_tool(tool_name, arguments)

                if tool_result.get("success") is True:
                    print("[Tool succeeded]")
                else:
                    print(
                        "[Tool failed: "
                        + str(
                            tool_result.get(
                                "error_type", "unknown_error"
                            )
                        )
                        + "]"
                    )

            # Each requested tool call gets a matching result message.
            current_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        tool_result,
                        ensure_ascii=False,
                    ),
                }
            )


# ==================================================
# CONVERSATION HISTORY
# ==================================================

messages = []


# ==================================================
# MAIN PROGRAM
# ==================================================

def main():
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
            print(f"\nError: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()

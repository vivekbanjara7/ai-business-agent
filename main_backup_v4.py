import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

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

COMMUNICATION STYLE
- Write for an intelligent beginner unless the user clearly asks for expert-level detail.
- Use natural, conversational, plain English. Sound like a helpful, knowledgeable person,
  not a corporate report or a technical manual.
- Prefer familiar words and short, clear sentences.
- Avoid jargon, acronyms, and specialist terms when ordinary words work.
- When a technical term is important, explain it the first time in simple words and give
  a short practical example when useful.
- Do not assume the user already understands the subject or industry.
- Explain what an idea means, why it matters, and what the user can do with it.
- Use examples from everyday life or realistic beginner situations.
- Keep the depth appropriate to the question: simple questions get concise answers;
  research and planning tasks can be detailed, but must remain easy to follow.
- Use headings, bullets, and tables only when they improve clarity. Do not turn every
  answer into a formal report.
- Avoid robotic openings, repetitive conclusions, inflated business language, and
  unnecessary phrases that merely make the answer sound impressive.
- Be respectful and clear; do not talk down to the user.

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
- Keep every reported calculation consistent throughout the answer.
- When comparing an annual price with 12 monthly payments, calculate:
  monthly total = monthly price × 12;
  savings amount = monthly total − annual price;
  savings percentage = savings amount ÷ monthly total × 100.
- State the denominator when reporting a savings percentage.
- Use the calculator's returned result for arithmetic and do not
  independently invent or approximate a conflicting percentage.
- If a source advertises a different savings percentage, explain that
  the source may use a different comparison basis; do not silently
  present the source percentage as equivalent to your calculation.
- Reuse the same inputs, difference, and percentage in every section.
- Each calculator tool call must perform exactly one operation.
- Use only the arguments a, b, and operation.
- The operation must be add, subtract, multiply, or divide.
- Never send a list of calculations in one calculator call.
- Never include extra arguments such as description or expression.
- For multiple calculations, make separate valid tool calls, respecting
  the tool-call budget. Prioritize the calculations essential to the answer.
- If the budget is exhausted, do not keep retrying. Finish using the
  results already available and clearly disclose any limitations.

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

def should_create_plan(user_input):
    """
    Avoid an extra model request for straightforward questions.
    Complex requests still use the model-based planner.
    """
    text = (user_input or "").strip().lower()

    if len(text) >= 350:
        return True

    planning_signals = (
        "make a plan", "create a plan", "roadmap", "strategy",
        "business plan", "market research", "competitor analysis",
        "compare", "comparison", "analyze", "analyse", "research",
        "step by step", "step-by-step", "audit", "evaluate",
        "launch", "build a", "develop a", "project",
        "pros and cons", "week-by-week", "month-by-month",
    )
    return any(signal in text for signal in planning_signals)


def create_plan(user_input):
    planning_messages = [
        {
            "role": "system",
            "content": (
                "You are a planning component for an AI business agent. "
                "For a simple request, return exactly NO_PLAN. For a "
                "genuinely multi-step request, create a numbered plan "
                "of at most 5 concise steps. Use plain, beginner-friendly "
                "language and explain specialist terms if they are essential. "
                "Include research, evidence checking, calculations, and "
                "reporting only when relevant. Do not execute tools or invent "
                "facts. Return only the plan or NO_PLAN."
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

    started_at = time.perf_counter()
    response = client.chat.completions.create(**arguments)
    elapsed = time.perf_counter() - started_at
    print(f"[Model response: {elapsed:.2f}s]")

    if not response.choices:
        raise RuntimeError("The model returned no response choices.")

    return response.choices[0].message


def parse_text_tool_calls(content):
    """Convert a limited, recognised XML-like tool request into safe calls.

    Some routed free models print tool requests as text instead of returning
    structured tool_calls. Only the tools and arguments explicitly allowed
    below are accepted; arbitrary function names or parameters are ignored.
    """
    if not isinstance(content, str) or "<tool_call" not in content.lower():
        return []

    parsed_calls = []
    function_pattern = re.compile(
        r"<function\s*=\s*['\"]?([a-zA-Z_][a-zA-Z0-9_]*)['\"]?\s*>(.*?)</function>",
        re.IGNORECASE | re.DOTALL,
    )
    parameter_pattern = re.compile(
        r"<parameter\s*=\s*['\"]?([a-zA-Z_][a-zA-Z0-9_]*)['\"]?\s*>(.*?)</parameter>",
        re.IGNORECASE | re.DOTALL,
    )

    for function_match in function_pattern.finditer(content):
        name = function_match.group(1).lower()
        body = function_match.group(2)
        raw_args = {
            key.lower(): value.strip()
            for key, value in parameter_pattern.findall(body)
        }

        if name == "calculate":
            if set(raw_args) != {"a", "b", "operation"}:
                continue
            try:
                a = float(raw_args["a"])
                b = float(raw_args["b"])
            except (TypeError, ValueError):
                continue
            operation = raw_args["operation"].lower()
            if operation not in {"add", "subtract", "multiply", "divide"}:
                continue
            if not (abs(a) < float("inf") and abs(b) < float("inf")):
                continue
            arguments = {"a": a, "b": b, "operation": operation}

        elif name == "web_search":
            if set(raw_args) != {"query"} or not raw_args["query"]:
                continue
            arguments = {"query": raw_args["query"]}

        elif name in {"save_memory", "get_memory"}:
            # Memory calls are deliberately not inferred from malformed text.
            continue
        else:
            continue

        parsed_calls.append({"name": name, "arguments": arguments})

    return parsed_calls


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
        "when it affects the answer. Write in natural, beginner-friendly "
        "plain English. Explain necessary technical terms the first time "
        "they appear, with a short practical example when useful. Do not "
        "assume specialist knowledge or use unnecessary jargon. "
        "Reason for finalizing: "
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

    if should_create_plan(user_input):
        print("\n[Planning...]")
        plan = create_plan(user_input)
    else:
        print("\n[Skipping planner: straightforward request]")
        plan = None

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
            # Fallback for providers/models that emit the documented tool
            # request in text instead of the structured tool_calls field.
            text_calls = parse_text_tool_calls(message.content or "")
            if text_calls:
                print("[Recognised text-formatted tool request]")
                synthetic_calls = []
                for index, item in enumerate(text_calls):
                    synthetic_calls.append({
                        "id": f"text_tool_{tool_rounds}_{index}",
                        "type": "function",
                        "function": {
                            "name": item["name"],
                            "arguments": json.dumps(item["arguments"]),
                        },
                    })
                message_for_history = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": synthetic_calls,
                }
                tool_calls = synthetic_calls
            else:
                answer = clean_answer(message.content or "")

                if not answer:
                    answer = (
                        "I could not generate a response for this request."
                    )

                save_exchange(user_input, answer)
                return answer
        else:
            message_for_history = message
            tool_calls = message.tool_calls

        tool_rounds += 1
        print(f"\n[Tool round {tool_rounds}]")
        current_messages.append(message_for_history)

        # --------------------------------------------------
        # Execute requested tools
        # --------------------------------------------------

        # Independent web searches requested in the same model response
        # can run concurrently. Results are still added to the conversation
        # in their original tool-call order, as required by the API.
        all_calls_are_web_searches = bool(tool_calls) and all(
            (call["function"]["name"] if isinstance(call, dict)
             else call.function.name) == "web_search"
            for call in tool_calls
        )

        if all_calls_are_web_searches:
            prepared = []
            batch_queries = set()
            batch_search_budget_exhausted = False

            for tool_call in tool_calls:
                if isinstance(tool_call, dict):
                    tool_name = tool_call["function"]["name"]
                    raw_arguments = tool_call["function"]["arguments"]
                    tool_call_id = tool_call["id"]
                else:
                    tool_name = tool_call.function.name
                    raw_arguments = tool_call.function.arguments
                    tool_call_id = tool_call.id

                try:
                    arguments = json.loads(raw_arguments)
                except (json.JSONDecodeError, TypeError):
                    arguments = None

                error_result = None
                normalized_query = None

                if not isinstance(arguments, dict):
                    error_result = {
                        "success": False, "tool": tool_name,
                        "error_type": "invalid_arguments",
                        "error": "Tool arguments must be a valid JSON object.",
                    }
                else:
                    query = arguments.get("query", "")
                    if not isinstance(query, str) or not query.strip():
                        error_result = {
                            "success": False, "tool": tool_name,
                            "error_type": "invalid_arguments",
                            "error": "A non-empty search query is required.",
                        }
                    else:
                        normalized_query = " ".join(query.casefold().split())
                        if normalized_query in successful_queries or normalized_query in batch_queries:
                            error_result = {
                                "success": False, "tool": tool_name,
                                "error_type": "duplicate_search",
                                "error": "This query already exists in the current request. Use existing results or search for a genuinely different missing fact.",
                            }
                        elif tool_calls_used >= MAX_TOOL_CALLS:
                            error_result = {
                                "success": False, "tool": tool_name,
                                "error_type": "tool_budget_reached",
                                "error": "The total tool-call budget is exhausted.",
                            }
                        elif web_searches_used >= MAX_WEB_SEARCHES:
                            batch_search_budget_exhausted = True
                            error_result = {
                                "success": False, "tool": tool_name,
                                "error_type": "search_budget_reached",
                                "error": "The web-search budget is exhausted. Use the evidence already collected and provide the best supported answer.",
                            }
                        else:
                            batch_queries.add(normalized_query)
                            web_searches_used += 1
                            tool_calls_used += 1
                            prepared.append((tool_call_id, arguments, normalized_query))
                            continue

                prepared.append((tool_call_id, error_result, None))

            if prepared:
                valid_searches = [item for item in prepared if item[2] is not None]
                if valid_searches:
                    print(f"[Running {len(valid_searches)} independent web searches in parallel]")
                    search_started = time.perf_counter()
                    with ThreadPoolExecutor(max_workers=min(3, len(valid_searches))) as executor:
                        futures = [
                            executor.submit(execute_tool, "web_search", item[1])
                            for item in valid_searches
                        ]
                        valid_results = [future.result() for future in futures]
                    print(f"[Parallel searches completed in {time.perf_counter() - search_started:.2f}s]")

                    result_by_id = {}
                    for item, result in zip(valid_searches, valid_results):
                        result_by_id[item[0]] = result
                        if result.get("success") is True:
                            successful_queries.add(item[2])

                    for tool_call_id, result_or_args, normalized_query in prepared:
                        result = result_by_id.get(tool_call_id, result_or_args)
                        if normalized_query is not None:
                            print("[Web search succeeded]" if result.get("success") is True else "[Web search failed]")
                        current_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": json.dumps(result, ensure_ascii=False),
                        })
                else:
                    for tool_call_id, result, _ in prepared:
                        current_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": json.dumps(result, ensure_ascii=False),
                        })

            if batch_search_budget_exhausted:
                answer = create_final_answer(
                    current_messages,
                    "Web-search budget exhausted; no further searches are permitted.",
                )
                save_exchange(user_input, answer)
                return answer

            continue

        # If the model requests another search after the per-request
        # search budget is exhausted, finish after this tool batch rather
        # than asking the model for another tool round.
        search_budget_exhausted = False

        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                tool_name = tool_call["function"]["name"]
                raw_arguments = tool_call["function"]["arguments"]
                tool_call_id = tool_call["id"]
            else:
                tool_name = tool_call.function.name
                raw_arguments = tool_call.function.arguments
                tool_call_id = tool_call.id

            try:
                arguments = json.loads(raw_arguments)
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
                        print("[Web-search budget reached; finalizing]")
                        search_budget_exhausted = True
                        tool_result = {
                            "success": False,
                            "tool": tool_name,
                            "error_type": "search_budget_reached",
                            "error": (
                                "The web-search budget is exhausted. No more "
                                "web searches are allowed for this request. "
                                "Use the evidence already collected and provide "
                                "the best supported final answer."
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
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(
                        tool_result,
                        ensure_ascii=False,
                    ),
                }
            )

        # Do not start another model/tool round after the search budget
        # has been exhausted. Generate the final response using the
        # evidence and tool results already present in the conversation.
        if search_budget_exhausted:
            answer = create_final_answer(
                current_messages,
                "Web-search budget exhausted; no further searches are permitted.",
            )
            save_exchange(user_input, answer)
            return answer


# ==================================================
# CONVERSATION HISTORY
# ==================================================

messages = []


# ==================================================
# MAIN PROGRAM
# ==================================================

def read_multiline_input():
    """Read a complete request until the user enters /submit."""
    print("You (enter /submit on a new line when finished):")
    print("      /cancel discards the request | exit ends the session")

    lines = []

    while True:
        try:
            line = input("... ")
        except EOFError:
            if lines:
                return "\n".join(lines).strip()
            raise

        command = line.strip().lower()

        if command == "/submit":
            return "\n".join(lines).strip()

        if command == "/cancel":
            print("[Request cancelled]")
            return None

        # Allow exit immediately, without requiring /submit, only when
        # no request text has been entered.
        if command == "exit" and not lines:
            return "exit"

        lines.append(line)


def main():
    print("================================")
    print("      AI Business Agent")
    print("================================")
    print("Enter your request across as many lines as you need.")
    print("Finish with /submit. Type exit to end the session.\n")

    while True:
        try:
            user_input = read_multiline_input()

        except (EOFError, KeyboardInterrupt):
            print("\nSession ended. See you next time!")
            break

        if user_input is None or not user_input.strip():
            continue

        if user_input.strip().lower() == "exit":
            print("\nSession ended. See you next time!")
            break

        try:
            answer = run_agent(user_input)
            print("\nAgent:", answer)
            print()

        except Exception as exc:
            print(f"\nError: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()

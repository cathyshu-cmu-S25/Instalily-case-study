import json
from collections.abc import AsyncGenerator
from llm.provider import client, ORCHESTRATOR_MODEL
from tools.registry import TOOL_REGISTRY
from tools.base import ToolResult

_SYSTEM = """You are the PartSelect Parts Assistant — an expert on refrigerator and dishwasher parts.

You help customers with:
- Looking up parts by PS number or manufacturer number
- Checking part compatibility with appliance model numbers
- Step-by-step installation guides
- Troubleshooting symptoms and recommending likely parts
- Order status and adding parts to the cart

Rules:
- Always use the provided tools to fetch real data. Never invent part numbers, prices, or compatibility.
- If the customer's request is ambiguous (e.g. "this part" without context), ask a short clarifying question.
- Be concise, friendly, and focused on solving the problem."""


def _build_messages(message: str, history: list[dict]) -> list[dict]:
    msgs = [{"role": "system", "content": _SYSTEM}]
    for h in history:
        msgs.append({"role": h["role"], "content": h["content"]})
    msgs.append({"role": "user", "content": message})
    return msgs


def _assistant_turn(msg) -> dict:
    turn: dict = {"role": "assistant", "content": msg.content}
    if msg.tool_calls:
        turn["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in msg.tool_calls
        ]
    return turn


async def _execute_tool(tc) -> tuple[str, dict | None]:
    fn_name = tc.function.name
    try:
        fn_args = json.loads(tc.function.arguments)
    except json.JSONDecodeError:
        fn_args = {}
    tool = TOOL_REGISTRY.get(fn_name)
    if tool is None:
        return f"Error: tool '{fn_name}' is not available.", None
    result: ToolResult = await tool.execute(**fn_args)
    return result.text, result.ui_block


async def run(message: str, history: list[dict]) -> dict:
    """Non-streaming agent loop. Returns {response, ui_block}."""
    messages = _build_messages(message, history)
    tools = [t.to_openai_schema() for t in TOOL_REGISTRY.values()]
    last_ui_block = None

    for _ in range(8):
        resp = await client.chat.completions.create(
            model=ORCHESTRATOR_MODEL,
            messages=messages,
            tools=tools or None,
            tool_choice="auto" if tools else None,
        )
        msg = resp.choices[0].message
        messages.append(_assistant_turn(msg))

        if not msg.tool_calls:
            return {"response": msg.content or "", "ui_block": last_ui_block}

        for tc in msg.tool_calls:
            result_text, ui_block = await _execute_tool(tc)
            if ui_block:
                last_ui_block = ui_block
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_text})

    return {"response": "I'm having trouble completing that request. Please try again.", "ui_block": last_ui_block}


async def run_stream(message: str, history: list[dict]) -> AsyncGenerator[dict, None]:
    """
    Streaming agent loop. Yields:
      {"type": "text_delta", "content": str}  — one or more times
      {"type": "done", "ui_block": dict | None} — exactly once, at the end
    """
    messages = _build_messages(message, history)
    tools = [t.to_openai_schema() for t in TOOL_REGISTRY.values()]
    last_ui_block = None

    # Tool loop (non-streaming) — runs until the model has no more tool calls
    for _ in range(7):
        resp = await client.chat.completions.create(
            model=ORCHESTRATOR_MODEL,
            messages=messages,
            tools=tools or None,
            tool_choice="auto" if tools else None,
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            # Don't append this turn — we'll re-run it with stream=True below
            break

        messages.append(_assistant_turn(msg))
        for tc in msg.tool_calls:
            result_text, ui_block = await _execute_tool(tc)
            if ui_block:
                last_ui_block = ui_block
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_text})
    else:
        # Exhausted iterations without a clean final response
        yield {"type": "text_delta", "content": "I'm having trouble completing that request. Please try again."}
        yield {"type": "done", "ui_block": None}
        return

    # Streaming final call — tool_choice="none" forces a text response
    stream_kwargs: dict = {
        "model": ORCHESTRATOR_MODEL,
        "messages": messages,
        "stream": True,
    }
    if tools:
        stream_kwargs["tools"] = tools
        stream_kwargs["tool_choice"] = "none"

    stream = await client.chat.completions.create(**stream_kwargs)
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield {"type": "text_delta", "content": delta}

    yield {"type": "done", "ui_block": last_ui_block}

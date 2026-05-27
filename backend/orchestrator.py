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

━━ Context tracking (follow strictly) ━━
• Whenever a part number (PS number like PS11752778, or manufacturer number like WPW10321304)
  appears anywhere in the conversation — from the user OR from a tool result — treat it as the
  "current part". Use it when the user later says "this part", "that part", "the part", or "it".
• Whenever an appliance model number (e.g. WDT780SAEM1, WRS325SDHZ00) appears anywhere in the
  conversation, treat it as the "current model". Use it when the user says "my model", "this model",
  or "my appliance".
• For compound requests ("look up X, check if it fits my model, and add to cart"), chain all the
  necessary tool calls in sequence — do not ask the user to break it into steps.


━━ Clarify, don't guess ━━
• If you need a part number but none has been established in the conversation, ask:
  "Which part number are you asking about? (You can find it on the part itself or your receipt.)"
• If you need a model number but none has been established, ask:
  "What's your appliance model number? (Usually on a sticker inside the door or on the back.)"
• If a symptom is too vague (e.g. "it's broken", "it doesn't work"), ask what specifically is
  happening and on which appliance type (refrigerator or dishwasher).
• Never fabricate part numbers, prices, model numbers, or compatibility results.

━━ Response length ━━
• When a tool returns a ui_block (a card displayed to the user), write at most 1–2 sentences in
  your text response. The card already shows the full details — do not repeat part names, prices,
  steps, compatibility verdicts, or order items that appear in the card.
• When no card is returned, answer fully in text.

━━ General ━━
• Always use tools to retrieve real data.
• Be concise and friendly. One clear answer beats a wall of text."""


def _build_messages(message: str, history: list[dict]) -> list[dict]:
    msgs = [{"role": "system", "content": _SYSTEM}]
    for h in history:
        content = h["content"]
        # If this assistant turn already produced tool cards, tell the LLM so it doesn't repeat them
        if h.get("role") == "assistant":
            tools_used = [b["_tool"] for b in h.get("ui_blocks", []) if "_tool" in b]
            if tools_used:
                note = f"[Tools already called and shown to user this turn: {', '.join(tools_used)}]"
                content = f"{note}\n{content}" if content else note
        msgs.append({"role": h["role"], "content": content})
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
    ui_block = result.ui_block
    if ui_block:
        ui_block = {**ui_block, "_tool": fn_name}
    return result.text, ui_block


def _dedup_ui_blocks(blocks: list[dict]) -> list[dict]:
    """Keep only the last block of each type (prevents duplicate cards in one response)."""
    seen: dict[str, int] = {}
    for i, b in enumerate(blocks):
        seen[b["type"]] = i
    return [blocks[i] for i in sorted(seen.values())]


async def run(message: str, history: list[dict]) -> dict:
    """Non-streaming agent loop. Returns {response, ui_block}."""
    messages = _build_messages(message, history)
    tools = [t.to_openai_schema() for t in TOOL_REGISTRY.values()]
    ui_blocks: list[dict] = []

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
            return {"response": msg.content or "", "ui_blocks": _dedup_ui_blocks(ui_blocks)}

        for tc in msg.tool_calls:
            result_text, ui_block = await _execute_tool(tc)
            if ui_block:
                ui_blocks.append(ui_block)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_text})

    return {"response": "I'm having trouble completing that request. Please try again.", "ui_blocks": _dedup_ui_blocks(ui_blocks)}


async def run_stream(message: str, history: list[dict]) -> AsyncGenerator[dict, None]:
    """
    Streaming agent loop. Yields:
      {"type": "text_delta", "content": str}  — one or more times
      {"type": "done", "ui_block": dict | None} — exactly once at the end
    """
    messages = _build_messages(message, history)
    tools = [t.to_openai_schema() for t in TOOL_REGISTRY.values()]
    ui_blocks: list[dict] = []

    for _ in range(7):
        resp = await client.chat.completions.create(
            model=ORCHESTRATOR_MODEL,
            messages=messages,
            tools=tools or None,
            tool_choice="auto" if tools else None,
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            # No more tool calls — re-run this final step with stream=True
            break

        messages.append(_assistant_turn(msg))
        for tc in msg.tool_calls:
            result_text, ui_block = await _execute_tool(tc)
            if ui_block:
                ui_blocks.append(ui_block)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_text})
    else:
        yield {"type": "text_delta", "content": "I'm having trouble completing that request. Please try again."}
        yield {"type": "done", "ui_blocks": []}
        return

    ui_blocks = _dedup_ui_blocks(ui_blocks)
    stream_kwargs: dict = {"model": ORCHESTRATOR_MODEL, "messages": messages, "stream": True}
    if tools:
        stream_kwargs["tools"] = tools
        stream_kwargs["tool_choice"] = "none"

    stream = await client.chat.completions.create(**stream_kwargs)
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield {"type": "text_delta", "content": delta}

    yield {"type": "done", "ui_blocks": ui_blocks}

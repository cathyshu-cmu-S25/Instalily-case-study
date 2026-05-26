import json
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


async def run(message: str, history: list[dict]) -> dict:
    """
    Agent loop: calls the LLM, executes tool calls, loops until the model
    produces a plain-text reply. Returns {"response": str, "ui_block": dict | None}.
    """
    messages = [{"role": "system", "content": _SYSTEM}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    tools = [t.to_openai_schema() for t in TOOL_REGISTRY.values()]
    last_ui_block = None
    max_iterations = 8

    for _ in range(max_iterations):
        resp = await client.chat.completions.create(
            model=ORCHESTRATOR_MODEL,
            messages=messages,
            tools=tools or None,
            tool_choice="auto" if tools else None,
        )

        msg = resp.choices[0].message

        # Build the assistant turn dict for the next iteration
        assistant_turn: dict = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            assistant_turn["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        messages.append(assistant_turn)

        if not msg.tool_calls:
            return {"response": msg.content or "", "ui_block": last_ui_block}

        # Execute each tool call and append results
        for tc in msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}

            tool = TOOL_REGISTRY.get(fn_name)
            if tool is None:
                result_text = f"Error: tool '{fn_name}' is not available."
            else:
                result: ToolResult = await tool.execute(**fn_args)
                result_text = result.text
                if result.ui_block:
                    last_ui_block = result.ui_block

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_text,
            })

    return {
        "response": "I'm having trouble completing that request. Please try again.",
        "ui_block": last_ui_block,
    }

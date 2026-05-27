from data.provider import get_provider
from tools.base import Tool, ToolResult
from tools.registry import register


@register
class InstallGuide(Tool):
    name = "install_guide"
    description = (
        "Get step-by-step installation instructions for a part. "
        "Use this when the customer asks how to install, replace, or fit a part."
    )
    parameters = {
        "type": "object",
        "properties": {
            "part_id": {
                "type": "string",
                "description": "PS number or manufacturer number of the part",
            }
        },
        "required": ["part_id"],
        "additionalProperties": False,
    }

    async def execute(self, part_id: str) -> ToolResult:
        part = get_provider().get_part(part_id)
        if not part:
            return ToolResult(text=f"Part '{part_id}' not found in our catalog.")

        install = part.get("install", {})
        part_url = part.get("url", "")

        tools_needed = ", ".join(install.get("tools", [])) or "None"
        steps = install.get("steps", [])
        steps_text = "\n".join(f"Step {i+1}: {s}" for i, s in enumerate(steps)) if steps else ""

        if steps_text:
            text = (
                f"Installation guide for {part['name']} ({part['ps_number']}):\n"
                f"Difficulty: {install.get('difficulty', 'Unknown')} | "
                f"Time: {install.get('time', 'Unknown')} | "
                f"Tools needed: {tools_needed}\n\n"
                f"{steps_text}"
            )
        else:
            text = (
                f"Here's what we know about installing the {part['name']} ({part['ps_number']}):\n"
                f"- Difficulty: {install.get('difficulty', 'Unknown')}\n"
                f"- Estimated time: {install.get('time', 'Unknown')}\n"
                f"- Tools needed: {tools_needed}\n\n"
                f"Full step-by-step instructions and video guides are available on PartSelect. "
                f"Click the link in the card below to view them."
            )

        return ToolResult(
            text=text,
            ui_block={
                "type": "install_guide",
                "data": {
                    "part": part,
                    "install": install,
                    "part_url": part_url,
                },
            },
        )

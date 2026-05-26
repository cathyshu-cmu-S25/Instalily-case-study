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
        if not install or not install.get("steps"):
            return ToolResult(
                text=f"No installation guide is available for {part['name']}. "
                     "Please contact PartSelect support for assistance."
            )

        tools_needed = ", ".join(install.get("tools", [])) or "None"
        steps_text = "\n".join(
            f"Step {i + 1}: {s}" for i, s in enumerate(install["steps"])
        )
        return ToolResult(
            text=(
                f"Installation guide for {part['name']} ({part['ps_number']}):\n"
                f"Difficulty: {install.get('difficulty', 'Unknown')} | "
                f"Time: {install.get('time', 'Unknown')} | "
                f"Tools needed: {tools_needed}\n\n"
                f"{steps_text}"
            ),
            ui_block={
                "type": "install_guide",
                "data": {"part": part, "install": install},
            },
        )

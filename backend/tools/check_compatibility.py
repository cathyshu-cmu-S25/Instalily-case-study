from data.provider import get_provider
from tools.base import Tool, ToolResult
from tools.registry import register


@register
class CheckCompatibility(Tool):
    name = "check_compatibility"
    description = (
        "Check whether a specific part is compatible with a given appliance model number. "
        "Returns a definitive yes/no result — do NOT use RAG for this, it is a deterministic lookup."
    )
    parameters = {
        "type": "object",
        "properties": {
            "part_id": {
                "type": "string",
                "description": "PS number or manufacturer number of the part",
            },
            "model_number": {
                "type": "string",
                "description": "The full appliance model number (e.g. WDT780SAEM1)",
            },
        },
        "required": ["part_id", "model_number"],
        "additionalProperties": False,
    }

    async def execute(self, part_id: str, model_number: str) -> ToolResult:
        part = get_provider().get_part(part_id)
        if not part:
            return ToolResult(text=f"Part '{part_id}' not found in our catalog.")

        compatible_models = [m.upper() for m in part.get("compatible_models", [])]
        is_compatible = model_number.strip().upper() in compatible_models

        verdict = "✓ compatible" if is_compatible else "✗ NOT compatible"
        return ToolResult(
            text=(
                f"{part['name']} ({part['ps_number']}) is {verdict} with model {model_number}. "
                + (
                    "It is confirmed to work with this appliance."
                    if is_compatible
                    else f"This part is designed for {part['appliance_type'].lower()}s "
                         f"and is not listed for model {model_number}."
                )
            ),
            ui_block={
                "type": "compatibility_result",
                "data": {
                    "part": part,
                    "model_number": model_number,
                    "compatible": is_compatible,
                },
            },
        )

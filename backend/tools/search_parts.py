from data.provider import get_provider
from tools.base import Tool, ToolResult
from tools.registry import register


@register
class SearchParts(Tool):
    name = "search_parts"
    description = (
        "Search for refrigerator or dishwasher parts by symptom, part description, or keyword. "
        "Use this when the customer describes a problem or uses a general term instead of a part number."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search term, symptom, or part description (e.g. 'ice maker', 'door shelf bin')",
            },
            "appliance": {
                "type": "string",
                "enum": ["Refrigerator", "Dishwasher"],
                "description": "Optional: filter results to a specific appliance type",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    async def execute(self, query: str, appliance: str | None = None) -> ToolResult:
        parts = get_provider().search_parts(query, appliance)
        if not parts:
            return ToolResult(
                text=f"No parts found matching '{query}'. Try a different keyword or describe the symptom."
            )
        summary = "; ".join(
            f"{p['ps_number']} — {p['name']} (${p['price']:.2f})" for p in parts
        )
        return ToolResult(
            text=f"Found {len(parts)} matching part(s): {summary}",
            ui_block={"type": "product_card", "data": parts[0]},
        )

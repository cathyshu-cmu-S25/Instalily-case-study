from data.provider import get_provider
from rag.embed import query_store
from tools.base import Tool, ToolResult
from tools.registry import register


@register
class Troubleshoot(Tool):
    name = "troubleshoot"
    description = (
        "Diagnose an appliance problem using repair guides. Use this for open-ended symptoms "
        "like 'not cooling', 'leaking', 'noisy', 'not cleaning'. "
        "Do NOT use for part lookups or compatibility checks — use the dedicated tools for those."
    )
    parameters = {
        "type": "object",
        "properties": {
            "symptom": {
                "type": "string",
                "description": "The symptom or problem description in the customer's words",
            },
            "brand": {
                "type": "string",
                "description": "Optional: appliance brand (e.g. Whirlpool, Maytag, KitchenAid)",
            },
            "appliance": {
                "type": "string",
                "enum": ["Refrigerator", "Dishwasher"],
                "description": "Optional: appliance type to narrow the search",
            },
        },
        "required": ["symptom"],
        "additionalProperties": False,
    }

    async def execute(
        self, symptom: str, brand: str | None = None, appliance: str | None = None
    ) -> ToolResult:
        # Build a rich query for the vector store
        query_parts = []
        if appliance:
            query_parts.append(appliance)
        if brand:
            query_parts.append(brand)
        query_parts.append(symptom)
        query = " ".join(query_parts)

        guides = await query_store(query, top_k=1)
        if not guides:
            return ToolResult(
                text=(
                    "I couldn't find a specific repair guide for that symptom. "
                    "Could you describe the problem in a bit more detail? "
                    "For example: what appliance, what brand, and exactly what you're seeing."
                )
            )

        guide = guides[0]
        provider = get_provider()

        # Resolve likely_parts names to catalog entries
        recommended_parts: list[dict] = []
        for part_name in guide.get("likely_parts", []):
            matches = provider.search_parts(part_name, guide.get("appliance"))
            if matches:
                recommended_parts.append(matches[0])

        steps_text = "\n".join(
            f"{i + 1}. {s}" for i, s in enumerate(guide["diagnosis_steps"])
        )
        parts_text = (
            ", ".join(p["name"] for p in recommended_parts)
            if recommended_parts
            else "none identified"
        )

        return ToolResult(
            text=(
                f"Here's how to diagnose '{symptom}' on your "
                f"{guide.get('appliance', 'appliance')}:\n\n"
                f"{steps_text}\n\n"
                f"Parts most likely to need replacement: {parts_text}"
            ),
            ui_block={
                "type": "troubleshoot_result",
                "data": {
                    "symptom": symptom,
                    "guide": guide,
                    "recommended_parts": recommended_parts,
                },
            },
        )

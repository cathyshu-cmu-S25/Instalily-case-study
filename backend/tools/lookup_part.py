from data.provider import get_provider
from tools.base import Tool, ToolResult
from tools.registry import register


@register
class LookupPart(Tool):
    name = "lookup_part"
    description = (
        "Look up a refrigerator or dishwasher part by its PS number "
        "(e.g. PS11752778) or manufacturer number (e.g. WPW10321304). "
        "Returns part details: name, price, stock, compatible brands, and install info."
    )
    parameters = {
        "type": "object",
        "properties": {
            "part_id": {
                "type": "string",
                "description": "The PS number or manufacturer number of the part",
            }
        },
        "required": ["part_id"],
        "additionalProperties": False,
    }

    async def execute(self, part_id: str) -> ToolResult:
        part = get_provider().get_part(part_id)
        if not part:
            return ToolResult(
                text=f"No part found for '{part_id}'. Please double-check the number and try again."
            )
        stock = "In Stock" if part["in_stock"] else "Out of Stock"
        return ToolResult(
            text=(
                f"{part['name']} ({part['ps_number']}) — ${part['price']:.2f}, {stock}. "
                f"Compatible brands: {', '.join(part['brands'])}. "
                f"Rating: {part['rating']}/5 ({part['review_count']} reviews)."
            ),
            ui_block={"type": "product_card", "data": part},
        )

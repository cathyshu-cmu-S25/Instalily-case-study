from data.provider import get_provider
from tools.base import Tool, ToolResult
from tools.registry import register


@register
class AddToCart(Tool):
    name = "add_to_cart"
    description = "Add a part to the shopping cart by part ID and optional quantity."
    parameters = {
        "type": "object",
        "properties": {
            "part_id": {
                "type": "string",
                "description": "PS number or manufacturer number of the part to add",
            },
            "qty": {
                "type": "integer",
                "description": "Quantity to add (default: 1)",
                "default": 1,
                "minimum": 1,
            },
        },
        "required": ["part_id"],
        "additionalProperties": False,
    }

    async def execute(self, part_id: str, qty: int = 1) -> ToolResult:
        part = get_provider().get_part(part_id)
        if not part:
            return ToolResult(text=f"Part '{part_id}' not found. Please check the part number.")

        if not part["in_stock"]:
            return ToolResult(
                text=f"{part['name']} ({part['ps_number']}) is currently out of stock "
                     "and cannot be added to your cart."
            )

        subtotal = round(part["price"] * qty, 2)
        return ToolResult(
            text=(
                f"Added {qty}× {part['name']} ({part['ps_number']}) to your cart. "
                f"Subtotal: ${subtotal:.2f}."
            ),
            ui_block={
                "type": "cart_confirmation",
                "data": {"part": part, "qty": qty, "subtotal": subtotal},
            },
        )

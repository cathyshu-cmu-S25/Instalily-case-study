from tools.base import Tool, ToolResult
from tools.registry import register


@register
class LookupPart(Tool):
    name = "lookup_part"
    description = (
        "Look up a refrigerator or dishwasher part by its PS number "
        "(e.g. PS11752778) or manufacturer number (e.g. WPW10321304). "
        "Returns part details including name, price, stock status, and compatible brands."
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
        # Phase 1 stub — replaced with real DataProvider in Phase 2
        return ToolResult(
            text=(
                f"Part {part_id}: Refrigerator Door Shelf Bin — $47.40, In Stock. "
                "Compatible with Whirlpool, KitchenAid, Maytag, Amana, Kenmore. "
                "Rating: 5.0/5 (29 reviews). Easy install, ~15 min, no tools needed."
            ),
            ui_block={
                "type": "product_card",
                "data": {
                    "ps_number": part_id,
                    "name": "Refrigerator Door Shelf Bin (stub)",
                    "price": 47.40,
                    "in_stock": True,
                    "brands": ["Whirlpool", "KitchenAid", "Maytag", "Amana", "Kenmore"],
                    "rating": 5.0,
                    "review_count": 29,
                },
            },
        )

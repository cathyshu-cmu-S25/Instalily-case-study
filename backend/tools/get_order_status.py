from tools.base import Tool, ToolResult
from tools.registry import register

# Demo order data keyed by order ID
_DEMO_ORDERS: dict[str, dict] = {
    "PS-123456": {
        "order_id": "PS-123456",
        "status": "Shipped",
        "items": [{"name": "Refrigerator Door Shelf Bin", "ps_number": "PS11752778", "qty": 1, "price": 47.40}],
        "tracking_number": "1Z999AA10123456784",
        "carrier": "UPS",
        "estimated_delivery": "May 27, 2026",
    },
    "PS-789012": {
        "order_id": "PS-789012",
        "status": "Processing",
        "items": [{"name": "Dishwasher Lower Spray Arm", "ps_number": "PS11739124", "qty": 1, "price": 26.85}],
        "tracking_number": None,
        "carrier": None,
        "estimated_delivery": "May 29–31, 2026",
    },
}

_FALLBACK_STATUS = {
    "status": "Processing",
    "tracking_number": None,
    "carrier": None,
    "estimated_delivery": "3–5 business days",
}


@register
class GetOrderStatus(Tool):
    name = "get_order_status"
    description = "Look up the status of an existing order by order ID (e.g. PS-123456)."
    parameters = {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "The order ID, usually in the format PS-XXXXXX",
            }
        },
        "required": ["order_id"],
        "additionalProperties": False,
    }

    async def execute(self, order_id: str) -> ToolResult:
        order = _DEMO_ORDERS.get(order_id.upper().strip(), None)
        if order is None:
            # Return a generic fallback for unknown IDs (demo behaviour)
            data = {"order_id": order_id, **_FALLBACK_STATUS}
            return ToolResult(
                text=f"Order {order_id} is currently Processing. Estimated delivery: 3–5 business days.",
                ui_block={"type": "order_card", "data": data},
            )

        tracking = (
            f"Tracking: {order['tracking_number']} via {order['carrier']}."
            if order.get("tracking_number")
            else ""
        )
        return ToolResult(
            text=(
                f"Order {order['order_id']} is {order['status']}. "
                f"Estimated delivery: {order['estimated_delivery']}. {tracking}"
            ).strip(),
            ui_block={"type": "order_card", "data": order},
        )

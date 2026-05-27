from tools.base import Tool, ToolResult
from tools.registry import register

_ALLOWED_APPLIANCES = {"Refrigerator", "Dishwasher"}

# Demo orders: email must match (case-insensitive) alongside the order ID
_DEMO_ORDERS: dict[str, dict] = {
    "PS-123456": {
        "order_id": "PS-123456",
        "email": "demo@example.com",
        "status": "Shipped",
        "items": [
            {"name": "Refrigerator Door Shelf Bin", "ps_number": "PS11752778",
             "qty": 1, "price": 47.40, "appliance_type": "Refrigerator"},
        ],
        "tracking_number": "1Z999AA10123456784",
        "carrier": "UPS",
        "estimated_delivery": "May 27, 2026",
    },
    "PS-789012": {
        "order_id": "PS-789012",
        "email": "demo@example.com",
        "status": "Processing",
        "items": [
            {"name": "Dishwasher Lower Spray Arm", "ps_number": "PS11739124",
             "qty": 1, "price": 26.85, "appliance_type": "Dishwasher"},
        ],
        "tracking_number": None,
        "carrier": None,
        "estimated_delivery": "May 29–31, 2026",
    },
    "PS-555000": {
        "order_id": "PS-555000",
        "email": "demo@example.com",
        "status": "Delivered",
        "items": [
            {"name": "Lawn Mower Blade", "ps_number": "PS12345678",
             "qty": 1, "price": 19.99, "appliance_type": "Lawn Mower"},
        ],
        "tracking_number": "1Z999AA10999999999",
        "carrier": "FedEx",
        "estimated_delivery": "May 20, 2026",
    },
}


@register
class GetOrderStatus(Tool):
    name = "get_order_status"
    description = (
        "Look up the status of an existing order. "
        "Requires both the customer's email address AND their order number (e.g. PS-123456). "
        "Ask for both before calling this tool."
    )
    parameters = {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address used to place the order.",
            },
            "order_id": {
                "type": "string",
                "description": "The order number, usually in the format PS-XXXXXX.",
            },
        },
        "required": ["email", "order_id"],
        "additionalProperties": False,
    }

    async def execute(self, email: str, order_id: str) -> ToolResult:
        order = _DEMO_ORDERS.get(order_id.upper().strip())

        # Order not found
        if order is None:
            return ToolResult(
                text=f"I couldn't find an order matching order number {order_id} and that email address. Please double-check your details.",
                ui_block=None,
            )

        # Email mismatch
        if order["email"].lower() != email.lower().strip():
            return ToolResult(
                text=f"I couldn't find an order matching order number {order_id} and that email address. Please double-check your details.",
                ui_block=None,
            )

        # Scope check: at least one item must be a refrigerator or dishwasher part
        appliance_types = {item.get("appliance_type", "") for item in order.get("items", [])}
        if not appliance_types & _ALLOWED_APPLIANCES:
            return ToolResult(
                text=(
                    f"I found order {order_id}, but it contains parts outside my scope "
                    f"(I only assist with refrigerator and dishwasher parts). "
                    f"Please visit partselect.com/order-status for full order details."
                ),
                ui_block=None,
            )

        data = {**order, "demo": True}
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
            ui_block={"type": "order_card", "data": data},
        )

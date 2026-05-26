from tools.base import Tool

TOOL_REGISTRY: dict[str, Tool] = {}


def register(cls):
    """Class decorator — instantiates the tool and adds it to TOOL_REGISTRY."""
    instance = cls()
    TOOL_REGISTRY[instance.name] = instance
    return cls

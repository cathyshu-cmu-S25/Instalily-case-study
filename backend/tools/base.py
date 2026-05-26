from abc import ABC, abstractmethod
from pydantic import BaseModel


class ToolResult(BaseModel):
    text: str
    ui_block: dict | None = None


class Tool(ABC):
    name: str
    description: str
    parameters: dict  # JSON Schema for the function parameters

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass

    def to_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

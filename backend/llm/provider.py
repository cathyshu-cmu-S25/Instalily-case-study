import os
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ORCHESTRATOR_MODEL = "gpt-4.1-mini"
GUARDRAIL_MODEL = "gpt-4.1-nano"

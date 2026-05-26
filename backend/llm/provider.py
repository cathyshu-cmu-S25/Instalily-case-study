import os
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ORCHESTRATOR_MODEL = "gpt-5.4-mini"
GUARDRAIL_MODEL = "gpt-5.4-nano"

from dotenv import load_dotenv
load_dotenv()

import tools  # noqa: F401 — imports __init__.py, which self-registers all tools

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from guardrail import check_scope
from orchestrator import run

app = FastAPI(title="PartSelect Chat Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    response: str
    ui_block: dict | None = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in req.history]

    allowed, refusal = await check_scope(req.message, history)
    if not allowed:
        return ChatResponse(response=refusal)

    result = await run(req.message, history)
    return ChatResponse(**result)

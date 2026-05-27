from dotenv import load_dotenv
load_dotenv()

import tools  # noqa: F401 — triggers __init__.py, self-registers all tools

import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from guardrail import check_scope
from orchestrator import run, run_stream
from rag.embed import initialize_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_store()
    yield


app = FastAPI(title="PartSelect Chat Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str
    ui_blocks: list[dict] = []


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be empty")
        return v


class ChatResponse(BaseModel):
    response: str
    ui_blocks: list[dict] = []


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    history = [{"role": m.role, "content": m.content, "ui_blocks": m.ui_blocks} for m in req.history]
    allowed, refusal = await check_scope(req.message, history)
    if not allowed:
        return ChatResponse(response=refusal)
    result = await run(req.message, history)
    return ChatResponse(**result)


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    history = [{"role": m.role, "content": m.content, "ui_blocks": m.ui_blocks} for m in req.history]

    allowed, refusal = await check_scope(req.message, history)
    if not allowed:
        async def refused_stream():
            yield f"data: {json.dumps({'type': 'text_delta', 'content': refusal})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'ui_blocks': []})}\n\n"
        return StreamingResponse(refused_stream(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    async def generate():
        try:
            async for event in run_stream(req.message, history):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'text_delta', 'content': 'Something went wrong. Please try again.'})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'ui_block': None})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# PartSelect Chat Agent

An AI assistant scoped to **Refrigerator and Dishwasher parts only**, built as a
case study in clean agentic design with extensible tool registration and typed
UI blocks.

## Architecture

```
User → Scope Guardrail → Orchestrator LLM → Tool Registry → Data/RAG
     → Response Composer → UI Renderer
```

See `CLAUDE.md` for the full design doc.

## Prerequisites

- Python 3.11+
- Node 18+
- An OpenAI API key

## Setup & Run

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...

uvicorn main:app --reload
# Runs on http://localhost:8000
```

Health check: `curl http://localhost:8000/health`

### Frontend

```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

Open `http://localhost:5173` — type a message and confirm the echo comes back.

## Adding a new tool

1. Create `backend/tools/my_tool.py`.
2. Define a class that extends `Tool` and implement `execute()`.
3. Decorate it with `@register` — it self-registers on import.
4. Import it in `backend/tools/__init__.py` so the module loads at startup.

That's it. No changes to the orchestrator, guardrail, or chat loop.

## Adding a new UI card

1. Create `frontend/src/components/cards/MyCard.jsx`.
2. Add one entry to the registry in `frontend/src/components/cards/index.js`.

Done.

## Project structure

```
frontend/          Vite + React chat UI
backend/
  main.py          FastAPI entry point (/health, /chat)
  orchestrator.py  Agent loop — GPT-4.1 Mini + function calling
  guardrail.py     Scope enforcement (runs before orchestrator)
  tools/           One file per tool, each self-registering
  data/            catalog.json + repair_guides.json + DataProvider
  rag/             In-memory vector store + embedding helpers
  llm/             LLM adapter (swap providers here)
scraper/           Documents the production ingestion path
```

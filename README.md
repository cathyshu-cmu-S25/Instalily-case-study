# PartSelect Chat Agent

An AI assistant scoped to **Refrigerator and Dishwasher parts only**, built as a
case study in clean agentic design. Key properties:

- **Scope-guardrailed** — a cheap LLM pass refuses everything outside the two
  allowed appliance types before the orchestrator ever runs.
- **Tool-registry architecture** — every capability is a self-registering tool.
  Adding a new feature is one new file; the orchestrator never changes.
- **Typed UI blocks** — tools return `{ text, ui_block }`. The frontend picks
  the right card component from a registry keyed by `ui_block.type`. Adding a
  new card is one new component + one registry entry.
- **RAG for troubleshooting only** — deterministic questions (lookup,
  compatibility) read structured data; open-ended symptoms use cosine-similarity
  search over embedded repair guides.
- **Streaming** — responses stream token-by-token over SSE; tool execution
  happens first, then the final answer streams in.

---

## Architecture

```
User
 │
 ▼
Scope Guardrail (gpt-5.4-nano)
 │  refuses out-of-scope appliances, off-topic requests, jailbreaks
 ▼
Orchestrator (gpt-5.4-mini, function calling)
 │  runs a tool-call loop; chains multiple tools for compound requests
 ▼
Tool Registry  ──►  lookup_part · search_parts · check_compatibility
                    install_guide · troubleshoot (RAG) · get_order_status · add_to_cart
 │
 ▼
Data / RAG layer
 │  catalog.json (17 parts)  ·  repair_guides.json (8 guides, text-embedding-3-small)
 ▼
Response  →  { text, ui_block }
 │
 ▼
Frontend card registry
    product_card · compatibility_result · install_guide
    order_card · cart_confirmation · troubleshoot_result
```

---

## Prerequisites

- Python 3.11+
- Node 18+
- An OpenAI API key (get one at platform.openai.com)

---

## Setup & Run

### 1 — Backend

```bash
cd backend

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Open .env and set:  OPENAI_API_KEY=sk-...

uvicorn main:app --reload
# → http://localhost:8000
# Startup embeds all repair guides into the in-memory vector store (~3 s).
```

Smoke-test: `curl http://localhost:8000/health` → `{"status":"ok"}`

### 2 — Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

Open the browser, type a message, and the response streams back with a typed UI card.

---

## Sample queries to try

| Query | Tools called | Card rendered |
|---|---|---|
| `How do I install part PS11752778?` | `lookup_part` → `install_guide` | InstallSteps |
| `Is PS11752778 compatible with WDT780SAEM1?` | `check_compatibility` | CompatibilityBadge ✗ |
| `My Whirlpool fridge ice maker isn't working` | `troubleshoot` (RAG) | TroubleshootResult |
| `Look up PS11739124, check it fits WDT780SAEM1, add to cart` | 3-tool chain | CartConfirmation |
| `What's the status of order PS-123456?` | `get_order_status` | OrderCard |

Guardrail test: `My Whirlpool washing machine is leaking` → **refused** (washer is out of scope even though Whirlpool is a known brand).

---

## How to add a new tool

1. Create `backend/tools/my_tool.py`:

```python
from tools.base import Tool, ToolResult
from tools.registry import register

@register
class MyTool(Tool):
    name = "my_tool"
    description = "What this tool does, in plain English for the LLM."
    parameters = {
        "type": "object",
        "properties": {
            "arg": {"type": "string", "description": "..."}
        },
        "required": ["arg"],
        "additionalProperties": False,
    }

    async def execute(self, arg: str) -> ToolResult:
        # fetch real data, never fabricate
        return ToolResult(
            text="Human-readable result for the LLM to incorporate.",
            ui_block={"type": "my_card_type", "data": {...}},
        )
```

2. Add one import to `backend/tools/__init__.py`:

```python
from . import my_tool  # noqa: F401
```

**That's it.** The orchestrator, guardrail, and chat endpoint are untouched.

---

## How to add a new UI card

1. Create `frontend/src/components/cards/MyCard.jsx`.
2. Add one entry in `frontend/src/components/cards/index.js`:

```js
import MyCard from "./MyCard";
const CARD_REGISTRY = {
  ...
  my_card_type: MyCard,   // ← one line
};
```

---

## Expanding the appliance scope

`backend/guardrail.py` has a single config list:

```python
ALLOWED_APPLIANCES = ["Refrigerator", "Dishwasher"]
```

Adding `"Washer"` here is the only change needed to open the scope. The guardrail
prompt is generated from this list automatically.

---

## Project structure

```
backend/
  main.py            FastAPI — /health, /chat, /chat/stream (SSE)
  orchestrator.py    Agent loop: tool-call iteration + streaming final response
  guardrail.py       Scope router — runs before orchestrator on every request
  llm/
    provider.py      OpenAI client + model constants (swap models here)
  tools/
    base.py          Tool ABC + ToolResult(text, ui_block)
    registry.py      TOOL_REGISTRY dict + @register decorator
    __init__.py      Imports every tool module → triggers self-registration
    lookup_part.py   Look up by PS / manufacturer number
    search_parts.py  Keyword / symptom search
    check_compatibility.py  Deterministic model-number lookup (never RAG)
    install_guide.py Step-by-step install from catalog
    troubleshoot.py  RAG over repair_guides.json
    get_order_status.py  Order lookup (demo data)
    add_to_cart.py   Cart action (demo)
  data/
    provider.py      DataProvider interface + JSONDataProvider singleton
    catalog.json     17 parts (9 refrigerator, 8 dishwasher)
    repair_guides.json  8 repair guides — RAG corpus
  rag/
    store.py         In-memory cosine-similarity VectorStore
                     (interface matches pgvector for production swap)
    embed.py         text-embedding-3-small + startup initialization
frontend/
  src/
    api/client.js    sendMessage() + streamMessage() (SSE fetch)
    components/
      ChatWindow.jsx   Input, streaming state, follow-up chips
      MessageList.jsx  Renders text bubbles + dispatches to card registry
      cards/
        index.js       Component registry  {type → Component}
        ProductCard.jsx
        CompatibilityBadge.jsx
        InstallSteps.jsx
        OrderCard.jsx
        CartConfirmation.jsx
        TroubleshootResult.jsx
scraper/
  README.md          Documents the production ingestion path (not run in demo)
```

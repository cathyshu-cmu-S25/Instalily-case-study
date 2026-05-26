import json
import os
from pathlib import Path

from openai import AsyncOpenAI
from rag.store import Document, VectorStore

_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBED_MODEL = "text-embedding-3-small"

_store = VectorStore()
_initialized = False


async def _embed(text: str) -> list[float]:
    resp = await _client.embeddings.create(model=EMBED_MODEL, input=text)
    return resp.data[0].embedding


async def initialize_store() -> None:
    """Embed all repair guides and load them into the in-memory vector store."""
    global _initialized
    if _initialized:
        return

    guides_path = Path(__file__).parent.parent / "data" / "repair_guides.json"
    with open(guides_path) as f:
        guides: list[dict] = json.load(f)

    for guide in guides:
        # Build a rich text representation that captures symptom + content
        text = (
            f"{guide['appliance']} symptom: {guide['symptom']}. "
            f"Brands: {', '.join(guide.get('brands', []))}. "
            f"Diagnosis: {' '.join(guide['diagnosis_steps'])} "
            f"Likely parts: {', '.join(guide['likely_parts'])}"
        )
        embedding = await _embed(text)
        _store.add(Document(id=guide["id"], text=text, metadata=guide, embedding=embedding))

    _initialized = True


async def query_store(query: str, top_k: int = 3) -> list[dict]:
    """Return the top-k repair guide dicts closest to query."""
    if not _initialized:
        await initialize_store()
    embedding = await _embed(query)
    docs = _store.search(embedding, top_k=top_k)
    return [doc.metadata for doc in docs]

from dataclasses import dataclass, field
import numpy as np


@dataclass
class Document:
    id: str
    text: str
    metadata: dict
    embedding: list[float] = field(default_factory=list)


class VectorStore:
    def __init__(self):
        self._docs: list[Document] = []

    def add(self, doc: Document) -> None:
        self._docs.append(doc)

    def search(self, query_embedding: list[float], top_k: int = 3) -> list[Document]:
        if not self._docs:
            return []
        q = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return self._docs[:top_k]

        scored: list[tuple[float, Document]] = []
        for doc in self._docs:
            if not doc.embedding:
                continue
            d = np.array(doc.embedding, dtype=np.float32)
            score = float(np.dot(q, d) / (q_norm * np.linalg.norm(d)))
            scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

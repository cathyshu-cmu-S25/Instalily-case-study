from abc import ABC, abstractmethod
import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent


class DataProvider(ABC):
    @abstractmethod
    def get_part(self, part_id: str) -> dict | None:
        pass

    @abstractmethod
    def search_parts(self, query: str, appliance: str | None = None) -> list[dict]:
        pass

    @abstractmethod
    def find_parts_for_symptom(self, symptom: str, appliance: str | None = None) -> list[dict]:
        pass


class JSONDataProvider(DataProvider):
    def __init__(self):
        with open(_DATA_DIR / "catalog.json") as f:
            self._parts: list[dict] = json.load(f)

        # Index by PS number and manufacturer number (case-insensitive)
        self._index: dict[str, dict] = {}
        for p in self._parts:
            self._index[p["ps_number"].upper()] = p
            mfr = p.get("manufacturer_number", "")
            if mfr:
                self._index[mfr.upper()] = p

    def get_part(self, part_id: str) -> dict | None:
        return self._index.get(part_id.strip().upper())

    def find_parts_for_symptom(self, symptom: str, appliance: str | None = None) -> list[dict]:
        """Return parts whose fixes_symptoms field matches the symptom keywords."""
        terms = symptom.lower().split()
        scored: list[tuple[int, dict]] = []
        for p in self._parts:
            if appliance and p.get("appliance_type", "").lower() != appliance.lower():
                continue
            symptom_text = " ".join(p.get("fixes_symptoms", [])).lower()
            score = sum(1 for t in terms if t in symptom_text)
            if score > 0:
                scored.append((score, p))
        scored.sort(key=lambda x: (-x[0], -x[1].get("review_count", 0)))
        return [p for _, p in scored[:5]]

    def search_parts(self, query: str, appliance: str | None = None) -> list[dict]:
        terms = query.lower().split()
        scored: list[tuple[int, dict]] = []

        for p in self._parts:
            if appliance and p.get("appliance_type", "").lower() != appliance.lower():
                continue
            haystack = " ".join([
                p.get("name", ""),
                " ".join(p.get("brands", [])),
                " ".join(p.get("fixes_symptoms", [])),
                p.get("appliance_type", ""),
                p.get("ps_number", ""),
                p.get("manufacturer_number", ""),
            ]).lower()
            score = sum(1 for t in terms if t in haystack)
            if score > 0:
                scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:5]]


# Lazy singleton — loaded on first use
_provider: DataProvider | None = None


def get_provider() -> DataProvider:
    global _provider
    if _provider is None:
        _provider = JSONDataProvider()
    return _provider

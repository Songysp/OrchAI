from __future__ import annotations

import json
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel


ModelT = TypeVar("ModelT", bound=BaseModel)


class JsonCollectionStore(Generic[ModelT]):
    def __init__(self, root_path: Path, collection_name: str, model_type: type[ModelT], id_field: str) -> None:
        self.root_path = root_path
        self.collection_name = collection_name
        self.model_type = model_type
        self.id_field = id_field
        self.collection_path = self.root_path / f"{collection_name}.json"
        self.root_path.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[ModelT]:
        raw_items = self._load()
        return [self.model_type.model_validate(item) for item in raw_items]

    def get(self, identifier: str) -> ModelT | None:
        for item in self.list():
            if getattr(item, self.id_field) == identifier:
                return item
        return None

    def upsert(self, model: ModelT) -> ModelT:
        items = self._load()
        identifier = getattr(model, self.id_field)
        payload = model.model_dump(mode="json")

        replaced = False
        for index, item in enumerate(items):
            if item.get(self.id_field) == identifier:
                items[index] = payload
                replaced = True
                break

        if not replaced:
            items.append(payload)

        self.collection_path.write_text(json.dumps(items, indent=2), encoding="utf-8")
        return model

    def _load(self) -> list[dict]:
        if not self.collection_path.exists():
            return []

        content = self.collection_path.read_text(encoding="utf-8").strip()
        if not content:
            return []
        return json.loads(content)

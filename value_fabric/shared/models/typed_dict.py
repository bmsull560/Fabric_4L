"""Lightweight typed-dict compatible model base used by generated layer code."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class TypedDictModel(BaseModel):
    """A Pydantic-compatible model with dict-like accessors for generated return payloads.

    Several generated service modules subclass this type for structured return
    payloads.  Inheriting from ``BaseModel`` makes these classes valid
    ``response_model`` types for FastAPI while preserving dict-like access
    for existing callers.
    """

    model_config = ConfigDict(extra="allow")

    @classmethod
    def model_validate(cls, data: Any) -> "TypedDictModel":
        """Return an instance from mapping-like data, mirroring pydantic v2."""
        if isinstance(data, cls):
            return data
        if isinstance(data, dict):
            return cls(**data)
        if hasattr(data, "model_dump"):
            dumped = data.model_dump()
            if isinstance(dumped, dict):
                return cls(**dumped)
        raise TypeError(f"{cls.__name__}.model_validate() requires mapping data")

    def model_dump(self) -> dict[str, Any]:
        return super().model_dump()

    def dict(self) -> dict[str, Any]:
        return self.model_dump()

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def __iter__(self):
        return iter(self.model_dump().keys())

    def __len__(self):
        return len(self.model_dump())

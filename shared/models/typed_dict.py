"""Drop-in typed dict replacement using Pydantic BaseModel.

Provides TypedDictModel, a BaseModel subclass that behaves like a dict
for backward compatibility while giving IDE support and runtime validation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class TypedDictModel(BaseModel):
    """BaseModel that supports dict-like access for backward compatibility.

    Use this as the base for auto-generated response models so existing
code that does ``result["key"]`` or ``result.get("key")`` keeps working.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def __iter__(self):
        return iter(self.model_dump())

    def keys(self):
        return self.model_dump().keys()

    def values(self):
        return self.model_dump().values()

    def items(self):
        return self.model_dump().items()

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

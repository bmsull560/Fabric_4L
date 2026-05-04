"""Lightweight typed-dict compatible model base used by generated layer code."""
from __future__ import annotations

from typing import Any


class TypedDictModel(dict):
    """A small mapping model with pydantic-like dump helpers.

    Several generated service modules subclass this type for structured return
    payloads.  Keeping it dependency-free makes production gates deterministic
    while preserving normal ``dict`` behavior for callers.
    """

    def __init__(self, **data: Any) -> None:
        super().__init__(data)
        self.__dict__.update(data)

    @classmethod
    def model_validate(cls, data: Any) -> "TypedDictModel":
        """Return an instance from mapping-like data, mirroring pydantic v2.

        Generated compatibility classes in the layer services call
        ``SomeResult.model_validate({...})`` even though these release gates run
        without pydantic models.  This helper keeps those classes dependency-free
        while preserving the dict-and-attribute access contract expected by the
        services and tests.
        """
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
        return dict(self)

    def dict(self) -> dict[str, Any]:
        return self.model_dump()

"""TypedDict-style model base for shared package.

Provides a Pydantic BaseModel subclass used across the codebase
for type-safe dictionary-like response models.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict


class TypedDictModel(BaseModel):
    """Base model for typed-dict style response objects.

    Subclass this to define structured response shapes that can be
    validated with `.model_validate()` and serialized with `.model_dump()`.

    Supports dict-like access via ``[]``, ``in``, ``.get()``,
    and iteration over keys.
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        strict=False,
    )

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError as exc:
            raise KeyError(key) from exc

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for ``key`` if it exists, else ``default``."""
        return getattr(self, key, default)

    def __iter__(self):
        """Iterate over field names."""
        return iter(self.model_fields)

    def __len__(self) -> int:
        """Return the number of fields."""
        return len(self.model_fields)

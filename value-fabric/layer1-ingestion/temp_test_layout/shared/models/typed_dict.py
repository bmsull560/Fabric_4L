"""TypedDict-style model base for shared package.

Provides a Pydantic BaseModel subclass used across the codebase
for type-safe dictionary-like response models.
"""

from pydantic import BaseModel, ConfigDict


class TypedDictModel(BaseModel):
    """Base model for typed-dict style response objects.

    Subclass this to define structured response shapes that can be
    validated with `.model_validate()` and serialized with `.model_dump()`.
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        strict=False,
    )

"""Focused tenant field checks for Layer 5 TruthObject."""

from layer5_ground_truth.models.truth_object import TruthObject


def test_truth_object_tenant_id_column_is_required() -> None:
    column = TruthObject.__table__.c.tenant_id
    assert column.nullable is False

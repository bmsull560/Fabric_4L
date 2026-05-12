from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from layer5_ground_truth.services import truth_service


@pytest.mark.unit
async def test_add_source_rejects_cross_tenant_source_assignment():
    db = SimpleNamespace(add=AsyncMock(), flush=AsyncMock(), refresh=AsyncMock())
    truth_object = SimpleNamespace(id=uuid4(), tenant_id=uuid4())

    with pytest.raises(ValueError, match="tenant_id does not match TruthObject tenant"):
        await truth_service.add_source(
            db=db,
            truth_object=truth_object,
            tenant_id=uuid4(),
            source_data={"source_type": "document", "source_ref": "doc-1"},
        )

    db.add.assert_not_called()
    db.flush.assert_not_called()
    db.refresh.assert_not_called()

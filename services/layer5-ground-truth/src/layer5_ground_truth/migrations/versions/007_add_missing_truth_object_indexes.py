"""Add missing high-traffic TruthObject composite indexes.

Revision ID: 007
Revises: 006
Create Date: 2026-05-12
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create indexes needed for tenant-scoped list/summary query plans."""
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_truth_objects_tenant_claim_type
        ON truth_objects (tenant_id, claim_type)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_truth_objects_tenant_status
        ON truth_objects (tenant_id, status)
        """
    )


def downgrade() -> None:
    """Drop indexes added in this migration."""
    op.execute("DROP INDEX IF EXISTS ix_truth_objects_tenant_status")
    op.execute("DROP INDEX IF EXISTS ix_truth_objects_tenant_claim_type")

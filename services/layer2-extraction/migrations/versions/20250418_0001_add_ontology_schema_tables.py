"""Add ontology schema tables

Revision ID: 20250418_0001
Revises:
Create Date: 2025-04-18 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250418_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ontology_types table
    op.create_table(
        'ontology_types',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('parent_type_id', sa.String(64), sa.ForeignKey('ontology_types.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.UniqueConstraint('tenant_id', 'name', name='uix_ontology_types_tenant_name')
    )

    # Create indexes for ontology_types
    op.create_index('ix_ontology_types_tenant_id', 'ontology_types', ['tenant_id'])
    op.create_index('ix_ontology_types_parent_type_id', 'ontology_types', ['parent_type_id'])

    # Create ontology_properties table
    op.create_table(
        'ontology_properties',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('type_id', sa.String(64), sa.ForeignKey('ontology_types.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('property_type', sa.String(32), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('required', sa.Boolean(), server_default='false'),
        sa.Column('default_value', sa.JSON(), nullable=True),
        sa.Column('constraints', sa.JSON(), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('type_id', 'name', name='uix_ontology_properties_type_name')
    )

    # Create indexes for ontology_properties
    op.create_index('ix_ontology_properties_type_id', 'ontology_properties', ['type_id'])

    # Create ontology_relationships table
    op.create_table(
        'ontology_relationships',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('source_type_id', sa.String(64), sa.ForeignKey('ontology_types.id'), nullable=False),
        sa.Column('target_type_id', sa.String(64), sa.ForeignKey('ontology_types.id'), nullable=False),
        sa.Column('relationship_type', sa.String(32), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cardinality', sa.String(16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint(
            'tenant_id', 'source_type_id', 'target_type_id', 'relationship_type',
            name='uix_ontology_relationships_tenant_source_target_type'
        )
    )

    # Create indexes for ontology_relationships
    op.create_index('ix_ontology_relationships_tenant_id', 'ontology_relationships', ['tenant_id'])
    op.create_index('ix_ontology_relationships_source_type_id', 'ontology_relationships', ['source_type_id'])
    op.create_index('ix_ontology_relationships_target_type_id', 'ontology_relationships', ['target_type_id'])

    # Create ontology_schema_versions table
    op.create_table(
        'ontology_schema_versions',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('version', sa.String(32), nullable=False),
        sa.Column('schema_json', sa.JSON(), nullable=False),
        sa.Column('published_by', sa.String(64), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.UniqueConstraint('tenant_id', 'version', name='uix_schema_versions_tenant_version')
    )

    # Create indexes for ontology_schema_versions
    op.create_index('ix_ontology_schema_versions_tenant_id', 'ontology_schema_versions', ['tenant_id'])

    # Add check constraints
    op.create_check_constraint(
        'ck_ontology_properties_property_type',
        'ontology_properties',
        "property_type IN ('string', 'number', 'boolean', 'date', 'array', 'object', 'reference')"
    )

    op.create_check_constraint(
        'ck_ontology_relationships_relationship_type',
        'ontology_relationships',
        "relationship_type IN ('depends_on', 'extends', 'relates_to', 'contains')"
    )

    op.create_check_constraint(
        'ck_ontology_relationships_cardinality',
        'ontology_relationships',
        "cardinality IN ('one_to_one', 'one_to_many', 'many_to_many')"
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('ontology_schema_versions')
    op.drop_table('ontology_relationships')
    op.drop_table('ontology_properties')
    op.drop_table('ontology_types')

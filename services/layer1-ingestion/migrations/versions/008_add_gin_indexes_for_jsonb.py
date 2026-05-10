"""Add GIN indexes for JSONB fields to improve query performance (P1-4).

Revision ID: 008
Revises: 007
Create Date: 2026-05-03

This migration adds GIN indexes to frequently queried JSONB fields to enable
efficient containment and existence queries. Per database architecture review P1-4.

GIN indexes are added for:
- scraping_targets: extraction_config, browser_config, schedule, rate_limit, compliance, proxy_config, tags
- scraping_jobs: configuration
- raw_content: metadata, source_headers, meta_og_tags, meta_structured_data, capture_interactions
- extracted_data: data, validation_errors, validation_required_fields_present, 
  validation_required_fields_missing, post_redacted_fields, post_normalized_fields,
  post_enriched_fields, ontology_concept_ids, ontology_relationship_ids
- compliance_logs: robots_txt_check, rate_limit_event, pii_detection, domain_policy, 
  request_headers, metadata
- job_errors: metadata
- job_stage_details: metadata
- proxy_pools: proxies
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_gin_index_if_column_exists(index_name: str, table_name: str, column_name: str) -> None:
    """Create a GIN index only when the JSONB column exists in this schema revision."""
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = '{table_name}'
                  AND column_name = '{column_name}'
            ) THEN
                EXECUTE 'CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} USING GIN ({column_name})';
            END IF;
        END $$;
        """
    )


def upgrade() -> None:
    """Add GIN indexes for JSONB fields that exist in the active schema."""

    for index_name, table_name, column_name in [
        ("idx_scraping_targets_extraction_config_gin", "scraping_targets", "extraction_config"),
        ("idx_scraping_targets_browser_config_gin", "scraping_targets", "browser_config"),
        ("idx_scraping_tags_gin", "scraping_targets", "tags"),
        ("idx_scraping_jobs_configuration_gin", "scraping_jobs", "configuration"),
        ("idx_raw_content_source_headers_gin", "raw_content", "source_headers"),
        ("idx_raw_content_meta_og_tags_gin", "raw_content", "meta_og_tags"),
        ("idx_raw_content_meta_structured_data_gin", "raw_content", "meta_structured_data"),
        ("idx_raw_content_capture_interactions_gin", "raw_content", "capture_interactions"),
        ("idx_extracted_data_data_gin", "extracted_data", "data"),
        ("idx_extracted_data_validation_errors_gin", "extracted_data", "validation_errors"),
        ("idx_extracted_data_validation_required_present_gin", "extracted_data", "validation_required_fields_present"),
        ("idx_extracted_data_validation_required_missing_gin", "extracted_data", "validation_required_fields_missing"),
        ("idx_extracted_data_post_redacted_fields_gin", "extracted_data", "post_redacted_fields"),
        ("idx_extracted_data_post_normalized_fields_gin", "extracted_data", "post_normalized_fields"),
        ("idx_extracted_data_post_enriched_fields_gin", "extracted_data", "post_enriched_fields"),
        ("idx_extracted_data_ontology_concept_ids_gin", "extracted_data", "ontology_concept_ids"),
        ("idx_extracted_data_ontology_relationship_ids_gin", "extracted_data", "ontology_relationship_ids"),
        ("idx_compliance_logs_robots_txt_check_gin", "compliance_logs", "robots_txt_check"),
        ("idx_compliance_logs_rate_limit_event_gin", "compliance_logs", "rate_limit_event"),
        ("idx_compliance_logs_pii_detection_gin", "compliance_logs", "pii_detection"),
        ("idx_compliance_logs_domain_policy_gin", "compliance_logs", "domain_policy"),
        ("idx_compliance_logs_request_headers_gin", "compliance_logs", "request_headers"),
        ("idx_compliance_logs_metadata_gin", "compliance_logs", "metadata"),
        ("idx_job_stage_details_metadata_gin", "job_stage_details", "metadata"),
        ("idx_proxy_pools_proxies_gin", "proxy_pools", "proxies"),
    ]:
        _create_gin_index_if_column_exists(index_name, table_name, column_name)


def downgrade() -> None:
    """Remove GIN indexes."""
    
    # scraping_targets
    op.drop_index('idx_scraping_targets_extraction_config_gin', table_name='scraping_targets')
    op.drop_index('idx_scraping_targets_browser_config_gin', table_name='scraping_targets')
    op.drop_index('idx_scraping_tags_gin', table_name='scraping_targets')
    
    # scraping_jobs
    op.drop_index('idx_scraping_jobs_configuration_gin', table_name='scraping_jobs')
    
    # raw_content
    op.drop_index('idx_raw_content_source_headers_gin', table_name='raw_content')
    op.drop_index('idx_raw_content_meta_og_tags_gin', table_name='raw_content')
    op.drop_index('idx_raw_content_meta_structured_data_gin', table_name='raw_content')
    op.drop_index('idx_raw_content_capture_interactions_gin', table_name='raw_content')
    
    # extracted_data
    op.drop_index('idx_extracted_data_data_gin', table_name='extracted_data')
    op.drop_index('idx_extracted_data_validation_errors_gin', table_name='extracted_data')
    op.drop_index('idx_extracted_data_validation_required_present_gin', table_name='extracted_data')
    op.drop_index('idx_extracted_data_validation_required_missing_gin', table_name='extracted_data')
    op.drop_index('idx_extracted_data_post_redacted_fields_gin', table_name='extracted_data')
    op.drop_index('idx_extracted_data_post_normalized_fields_gin', table_name='extracted_data')
    op.drop_index('idx_extracted_data_post_enriched_fields_gin', table_name='extracted_data')
    op.drop_index('idx_extracted_data_ontology_concept_ids_gin', table_name='extracted_data')
    op.drop_index('idx_extracted_data_ontology_relationship_ids_gin', table_name='extracted_data')
    
    # compliance_logs
    op.drop_index('idx_compliance_logs_robots_txt_check_gin', table_name='compliance_logs')
    op.drop_index('idx_compliance_logs_rate_limit_event_gin', table_name='compliance_logs')
    op.drop_index('idx_compliance_logs_pii_detection_gin', table_name='compliance_logs')
    op.drop_index('idx_compliance_logs_domain_policy_gin', table_name='compliance_logs')
    op.drop_index('idx_compliance_logs_request_headers_gin', table_name='compliance_logs')
    op.drop_index('idx_compliance_logs_metadata_gin', table_name='compliance_logs')
    
    # job_errors
    # job_stage_details
    op.drop_index('idx_job_stage_details_metadata_gin', table_name='job_stage_details')
    
    # proxy_pools
    op.drop_index('idx_proxy_pools_proxies_gin', table_name='proxy_pools')

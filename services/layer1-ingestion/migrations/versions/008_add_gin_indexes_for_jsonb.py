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


def upgrade() -> None:
    """Add GIN indexes for JSONB fields."""
    
    # scraping_targets table
    op.execute("CREATE INDEX idx_scraping_targets_extraction_config_gin ON scraping_targets USING GIN (extraction_config)")
    op.execute("CREATE INDEX idx_scraping_targets_browser_config_gin ON scraping_targets USING GIN (browser_config)")
    op.execute("CREATE INDEX idx_scraping_tags_gin ON scraping_targets USING GIN (tags)")
    
    # scraping_jobs table
    op.execute("CREATE INDEX idx_scraping_jobs_configuration_gin ON scraping_jobs USING GIN (configuration)")
    
    # raw_content table
    op.execute("CREATE INDEX idx_raw_content_metadata_gin ON raw_content USING GIN (metadata)")
    op.execute("CREATE INDEX idx_raw_content_source_headers_gin ON raw_content USING GIN (source_headers)")
    op.execute("CREATE INDEX idx_raw_content_meta_og_tags_gin ON raw_content USING GIN (meta_og_tags)")
    op.execute("CREATE INDEX idx_raw_content_meta_structured_data_gin ON raw_content USING GIN (meta_structured_data)")
    op.execute("CREATE INDEX idx_raw_content_capture_interactions_gin ON raw_content USING GIN (capture_interactions)")
    
    # extracted_data table
    op.execute("CREATE INDEX idx_extracted_data_data_gin ON extracted_data USING GIN (data)")
    op.execute("CREATE INDEX idx_extracted_data_validation_errors_gin ON extracted_data USING GIN (validation_errors)")
    op.execute("CREATE INDEX idx_extracted_data_validation_required_present_gin ON extracted_data USING GIN (validation_required_fields_present)")
    op.execute("CREATE INDEX idx_extracted_data_validation_required_missing_gin ON extracted_data USING GIN (validation_required_fields_missing)")
    op.execute("CREATE INDEX idx_extracted_data_post_redacted_fields_gin ON extracted_data USING GIN (post_redacted_fields)")
    op.execute("CREATE INDEX idx_extracted_data_post_normalized_fields_gin ON extracted_data USING GIN (post_normalized_fields)")
    op.execute("CREATE INDEX idx_extracted_data_post_enriched_fields_gin ON extracted_data USING GIN (post_enriched_fields)")
    op.execute("CREATE INDEX idx_extracted_data_ontology_concept_ids_gin ON extracted_data USING GIN (ontology_concept_ids)")
    op.execute("CREATE INDEX idx_extracted_data_ontology_relationship_ids_gin ON extracted_data USING GIN (ontology_relationship_ids)")
    
    # compliance_logs table
    op.execute("CREATE INDEX idx_compliance_logs_robots_txt_check_gin ON compliance_logs USING GIN (robots_txt_check)")
    op.execute("CREATE INDEX idx_compliance_logs_rate_limit_event_gin ON compliance_logs USING GIN (rate_limit_event)")
    op.execute("CREATE INDEX idx_compliance_logs_pii_detection_gin ON compliance_logs USING GIN (pii_detection)")
    op.execute("CREATE INDEX idx_compliance_logs_domain_policy_gin ON compliance_logs USING GIN (domain_policy)")
    op.execute("CREATE INDEX idx_compliance_logs_request_headers_gin ON compliance_logs USING GIN (request_headers)")
    op.execute("CREATE INDEX idx_compliance_logs_metadata_gin ON compliance_logs USING GIN (metadata)")
    
    # job_errors table
    op.execute("CREATE INDEX idx_job_errors_metadata_gin ON job_errors USING GIN (metadata)")
    
    # job_stage_details table
    op.execute("CREATE INDEX idx_job_stage_details_metadata_gin ON job_stage_details USING GIN (metadata)")
    
    # proxy_pools table
    op.execute("CREATE INDEX idx_proxy_pools_proxies_gin ON proxy_pools USING GIN (proxies)")


def downgrade() -> None:
    """Remove GIN indexes."""
    
    # scraping_targets
    op.drop_index('idx_scraping_targets_extraction_config_gin', table_name='scraping_targets')
    op.drop_index('idx_scraping_targets_browser_config_gin', table_name='scraping_targets')
    op.drop_index('idx_scraping_tags_gin', table_name='scraping_targets')
    
    # scraping_jobs
    op.drop_index('idx_scraping_jobs_configuration_gin', table_name='scraping_jobs')
    
    # raw_content
    op.drop_index('idx_raw_content_metadata_gin', table_name='raw_content')
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
    op.drop_index('idx_job_errors_metadata_gin', table_name='job_errors')
    
    # job_stage_details
    op.drop_index('idx_job_stage_details_metadata_gin', table_name='job_stage_details')
    
    # proxy_pools
    op.drop_index('idx_proxy_pools_proxies_gin', table_name='proxy_pools')

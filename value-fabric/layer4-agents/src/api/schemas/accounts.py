"""
Pydantic schemas for Accounts API.

Request/response models for the accounts surface.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ...models.account import CRMProvider, SyncStatus


# ============================================================================
# Embedded Data Schemas
# ============================================================================

class OpportunitySchema(BaseModel):
    """Opportunity data embedded in account detail response."""
    provider_opportunity_id: str
    name: str
    stage: str
    value: Optional[Decimal] = None
    probability: Optional[float] = None
    close_date: Optional[str] = None
    last_synced_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ContactSchema(BaseModel):
    """Contact data embedded in account detail response."""
    provider_contact_id: str
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_primary: bool = False
    last_synced_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ActivityItemSchema(BaseModel):
    """Activity timeline item from fetch_interaction_history tool."""
    id: str
    type: str  # call, email, meeting, task
    date: str
    subject: Optional[str] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    outcome: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# List/Search Response Schemas
# ============================================================================

class AccountListItemSchema(BaseModel):
    """Account item in list response."""
    id: UUID
    provider: CRMProvider
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[int] = None
    owner_name: Optional[str] = None
    stage: Optional[str] = None
    sync_status: SyncStatus
    last_synced_at: Optional[datetime] = None
    updated_at: datetime
    
    # Source attribution
    provider_badge: str = Field(..., description="Display badge: 'Salesforce' or 'HubSpot'")
    
    model_config = ConfigDict(from_attributes=True)


class AccountListResponse(BaseModel):
    """Paginated account list response."""
    items: List[AccountListItemSchema]
    total: int
    page: int
    page_size: int
    has_more: bool


class AccountSearchRequest(BaseModel):
    """Account search request body."""
    query: Optional[str] = Field(None, description="Search across name, domain, owner")
    provider: Optional[CRMProvider] = None
    stage: Optional[str] = None
    industry: Optional[str] = None
    owner_id: Optional[str] = None
    sync_status: Optional[SyncStatus] = None
    
    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    
    # Sorting
    sort_by: str = Field("updated_at", pattern="^(name|updated_at|company_size|last_synced_at)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


# ============================================================================
# Detail Response Schema
# ============================================================================

class AccountDetailSchema(BaseModel):
    """Full account detail response."""
    # Canonical identity
    id: UUID
    provider: CRMProvider
    provider_record_id: str
    
    # Firmographics
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[int] = None
    annual_revenue: Optional[float] = None
    headquarters: Optional[str] = None
    website: Optional[str] = None
    
    # CRM linkage
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    stage: Optional[str] = None
    
    # Sync metadata
    created_at: datetime
    updated_at: datetime
    last_synced_at: Optional[datetime] = None
    sync_status: SyncStatus
    
    # Source attribution
    source_attribution: str = Field(..., description="Human-readable sync info: 'Synced from Salesforce 2 hours ago'")
    provider_badge: str = Field(..., description="Display badge: 'Salesforce' or 'HubSpot'")
    
    # Embedded related data (Phase 1: subordinate sections)
    opportunities: List[OpportunitySchema] = []
    contacts: List[ContactSchema] = []
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Activity Response Schema
# ============================================================================

class AccountActivityResponse(BaseModel):
    """Account activity timeline response."""
    account_id: UUID
    interactions: List[ActivityItemSchema]
    total_count: int
    summary: Optional[str] = None


# ============================================================================
# Sync Request/Response Schemas
# ============================================================================

class SyncAccountsRequest(BaseModel):
    """Manual sync trigger request."""
    provider: Optional[CRMProvider] = Field(
        None,
        description="Specific provider to sync, or null for all"
    )
    account_ids: Optional[List[str]] = Field(
        None,
        description="Specific account IDs to sync, or null for all"
    )
    force_refresh: bool = Field(
        False,
        description="Force re-sync even if data is fresh"
    )


class SyncAccountsResponse(BaseModel):
    """Sync trigger response."""
    sync_id: str = Field(..., description="Unique sync job identifier")
    status: str = Field(..., description="Sync status: queued, running, completed, failed")
    provider: Optional[CRMProvider] = None
    message: str


class SyncStatusSchema(BaseModel):
    """Per-provider sync status."""
    provider: CRMProvider
    status: str  # idle, running, failed
    last_sync_at: Optional[datetime] = None
    last_successful_sync_at: Optional[datetime] = None
    records_synced: int
    records_updated: int
    records_failed: int
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class SyncStatusListResponse(BaseModel):
    """All providers sync status response."""
    providers: List[SyncStatusSchema]
    overall_status: str  # healthy, degraded, unhealthy


# ============================================================================
# Filter Options Schema
# ============================================================================

class AccountFilterOptionsResponse(BaseModel):
    """Available filter options for account list."""
    industries: List[str]
    stages: List[str]
    providers: List[CRMProvider]
    owners: List[Dict[str, str]]  # [{"id": "...", "name": "..."}]

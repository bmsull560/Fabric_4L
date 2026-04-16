# Backend API Requirements — Frontend Remediation

## Value Fabric Platform — Production Readiness

**Date**: 2026-04-15  
**Status**: P1 Medium Priority — Required for production persistence

---

## 1. Integrations API

### Overview
The Integrations page (`/discover/integrations`) allows admin users to configure CRM connections (Salesforce, HubSpot). Currently, configuration is stored in local component state and **lost on page refresh**. Backend persistence is required for production use.

### Required Endpoints

#### GET /v1/integrations
List all configured integrations for the tenant.

**Response**:
```json
{
  "integrations": [
    {
      "provider": "salesforce",
      "enabled": true,
      "sync_interval_minutes": 60,
      "sync_batch_size": 100,
      "last_sync_at": "2026-04-15T10:30:00Z",
      "last_successful_sync_at": "2026-04-15T10:30:00Z",
      "records_synced": 1500,
      "records_updated": 45,
      "records_failed": 0,
      "status": "idle"
    },
    {
      "provider": "hubspot",
      "enabled": false,
      "sync_interval_minutes": 60,
      "sync_batch_size": 100
    }
  ]
}
```

**Note**: Credentials (`api_key`, `api_secret`) must NOT be returned in the response for security. Return only configuration and status metadata.

---

#### POST /v1/integrations/:provider
Create or update an integration configuration.

**Path Parameters**:
- `provider`: `salesforce` | `hubspot`

**Request Body**:
```json
{
  "enabled": true,
  "api_key": "encrypted_credential",
  "api_secret": "encrypted_credential",
  "instance_url": "https://instance.salesforce.com",
  "sync_interval_minutes": 60,
  "sync_batch_size": 100
}
```

**Validation**:
- `sync_interval_minutes`: min 5, max 1440
- `sync_batch_size`: min 10, max 500
- `api_key`: required when `enabled=true`
- Credentials must be encrypted at rest (AES-256 or equivalent)

**Response**: Same as GET (without credentials)

---

#### DELETE /v1/integrations/:provider
Remove an integration configuration.

**Path Parameters**:
- `provider`: `salesforce` | `hubspot`

**Response**: `204 No Content`

---

#### POST /v1/integrations/:provider/test
Test the connection to the CRM provider.

**Path Parameters**:
- `provider`: `salesforce` | `hubspot`

**Request Body**: Same as POST /v1/integrations/:provider (credentials required)

**Response**:
```json
{
  "success": true,
  "message": "Connection successful. Found 1500 accounts.",
  "details": {
    "accounts_accessible": true,
    "opportunities_accessible": true,
    "rate_limit_remaining": 999
  }
}
```

Or on failure:
```json
{
  "success": false,
  "message": "Authentication failed. Invalid API key.",
  "error_code": "AUTH_FAILED"
}
```

---

#### POST /v1/integrations/:provider/sync
Trigger a manual sync operation.

**Path Parameters**:
- `provider`: `salesforce` | `hubspot`

**Response**:
```json
{
  "sync_id": "sync-uuid",
  "status": "running",
  "started_at": "2026-04-15T10:30:00Z"
}
```

---

### Security Requirements

1. **Credential Encryption**: All API keys, secrets, and tokens must be encrypted at rest using AES-256 or equivalent. Decryption keys must be stored separately (KMS/Vault).

2. **Access Control**: Endpoints require `admin` tier access. Integrations contain sensitive credentials.

3. **Audit Logging**: Log all CRUD operations on integrations including who made the change and when.

4. **Connection Testing**: Never validate credentials by making real API calls in the request thread. Use async jobs or background workers to prevent request timeouts.

---

### Data Model (Suggested)

```sql
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    provider TEXT NOT NULL CHECK (provider IN ('salesforce', 'hubspot')),
    enabled BOOLEAN NOT NULL DEFAULT false,
    
    -- Encrypted credentials (never expose in API responses)
    credentials_encrypted BYTEA NOT NULL,
    encryption_key_id TEXT NOT NULL,
    
    -- Configuration
    instance_url TEXT,
    sync_interval_minutes INTEGER NOT NULL DEFAULT 60,
    sync_batch_size INTEGER NOT NULL DEFAULT 100,
    
    -- Sync status (denormalized for quick reads)
    last_sync_at TIMESTAMP,
    last_successful_sync_at TIMESTAMP,
    records_synced INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    sync_status TEXT DEFAULT 'idle',
    last_error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE(tenant_id, provider)
);
```

---

## 2. C1 Stream API (Already Implemented)

**Status**: ✅ Frontend complete, backend endpoint required

The InteractiveBusinessCase component uses the C1 stream API for conversational what-if analysis.

**Existing Frontend**: `frontend/client/src/api/thesysClient.ts`  
**Required Backend**: `POST /v1/agents/c1/stream`

**Purpose**: Proxy Thesys/OpenAI requests server-side to keep API keys secure.

**Implementation Notes**:
- Endpoint must accept OpenAI-compatible chat completion format
- Support Server-Sent Events (SSE) streaming
- Never expose Thesys API key to frontend
- Validate business_case_id belongs to requesting tenant

---

## Implementation Priority

| API | Priority | Effort | Blocker |
|-----|----------|--------|---------|
| GET /v1/integrations | P1 | Medium | None |
| POST /v1/integrations/:provider | P1 | Medium | Encryption infra |
| DELETE /v1/integrations/:provider | P1 | Low | None |
| POST /v1/integrations/:provider/test | P2 | Medium | Rate limiting |
| POST /v1/integrations/:provider/sync | P2 | High | Background jobs |
| POST /v1/agents/c1/stream | P1 | Medium | Thesys API key |

---

## Frontend Status

| Component | Backend API | Frontend Status | Production Ready |
|-----------|-------------|-----------------|------------------|
| Integrations | ❌ Missing | ✅ Complete | ❌ No (needs persistence) |
| InteractiveBusinessCase | ⚠️ Required | ✅ Complete | ⚠️ Pending L4 endpoint |

---

## Contact

Frontend Remediation Engineer  
Value Fabric Platform Team

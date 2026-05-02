# Salesforce CRM Integration — Engineering Documentation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Integrations │  │ Integration  │  │ IntegrationConfigPanel│  │
│  │    Page      │  │    Grid      │  │                      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼─────────────────┼─────────────────────┼──────────────┘
          │                 │                     │
          ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Layer 4: Agentic Engine                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              API Routes (FastAPI)                       │   │
│  │  GET  /integrations                                     │   │
│  │  GET  /integrations/{provider}                          │   │
│  │  POST /integrations/{provider}          ← OAuth callback│   │
│  │  POST /integrations/{provider}/test                     │   │
│  │  POST /integrations/{provider}/sync                     │   │
│  │  DELETE /integrations/{provider}                        │   │
│  │  POST /webhooks/crm/salesforce          ← Push events   │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              IntegrationService                         │   │
│  │  - encrypt/decrypt credentials (Fernet)                 │   │
│  │  - refresh_salesforce_token()                           │   │
│  │  - validate_config()                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              CRMSyncService                             │   │
│  │  - sync_provider()                                      │   │
│  │  - _get_crm_config()  ← per-tenant only                 │   │
│  │  - _execute_with_retry()                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              CRMSyncScheduler                           │   │
│  │  - Periodic tenant sweep (background tasks)             │   │
│  │  - Uses db_session_for_context() with RLS               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PostgreSQL (RLS-enabled)                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  integrations                                           │   │
│  │  - credentials_encrypted (Fernet)                       │   │
│  │  - refresh_token_encrypted (Fernet)                     │   │
│  │  - salesforce_org_id                                    │   │
│  │  - tenant_id (RLS policy)                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  accounts                                               │   │
│  │  - provider_record_id                                   │   │
│  │  - opportunities (JSONB)                                │   │
│  │  - tenant_id (RLS policy)                               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Salesforce API                              │
│  - REST API v58.0                                               │
│  - OAuth 2.0 token refresh                                      │
│  - Webhook push events                                          │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### OAuth Connect Flow (Planned)

1. Admin clicks **Connect Salesforce** in frontend.
2. Backend generates OAuth state bound to `tenant_id` + `user_id` + expiry.
3. Redirect to Salesforce authorization URL.
4. Salesforce redirects to `SALESFORCE_REDIRECT_URI` with auth code.
5. Backend exchanges code for access + refresh tokens.
6. Tokens encrypted and stored in `integrations` table.
7. Integration status set to `idle`.

### Sync Flow

1. `CRMSyncScheduler` runs tenant sweep every `CRM_SYNC_INTERVAL_MINUTES`.
2. For each enabled integration, creates `RequestContext(tenant_id=...)`.
3. `db_session_for_context()` sets PostgreSQL `app.tenant_id` for RLS.
4. `CRMSyncService.sync_provider()` queries accounts needing sync.
5. For each account, `GetProspectDataTool` calls Salesforce REST API.
6. Results upserted into `accounts` table with `tenant_id`.

### Webhook Flow

1. Salesforce sends platform event to `POST /webhooks/crm/salesforce`.
2. HMAC signature verified (if `salesforce_webhook_secret` configured).
3. Record ID extracted from payload.
4. Sync triggered for specific account ID.

## Security Model

- **Encryption at rest**: Fernet (AES-128-CBC + HMAC) with PBKDF2 key derivation.
- **Tenant isolation**: PostgreSQL RLS policies on `integrations` and `accounts`.
- **No env fallback**: `ALLOW_ENV_CRM_FALLBACK` removed from production code paths.
- **Secret redaction**: Logs never contain tokens, auth codes, or bearer strings.
- **State validation**: OAuth state tokens are tenant-bound and time-limited.

## Known Limitations

1. **OAuth UI not implemented**: Frontend currently uses manual API key entry. OAuth connect flow requires UI work.
2. **No KMS**: Encryption uses Fernet with env-derived key. Production should use AWS KMS / HashiCorp Vault.
3. **Scheduler singleton**: `CRMSyncScheduler` is a Python singleton. For multi-replica deployments, use a distributed lock (Redis) or Celery beat.
4. **No SOQL pagination**: `GetProspectDataTool` does not paginate large result sets.
5. **No deleted record handling**: Salesforce soft-deletes are not synchronized.

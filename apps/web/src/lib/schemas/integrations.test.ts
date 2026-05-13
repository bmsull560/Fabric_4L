import { describe, expect, it } from "vitest";

import {
  parseConnectionTestResult,
  parseIntegration,
  parseIntegrations,
  parseOAuthAuthorizeResult,
  parseSyncTriggerResult,
} from "./integrations";

const integrationPayload = {
  id: "int-1",
  tenant_id: "tenant-1",
  provider: "salesforce",
  enabled: true,
  instance_url: "https://example.my.salesforce.com",
  sync_interval_minutes: 30,
  sync_batch_size: 100,
  last_sync_at: null,
  last_successful_sync_at: null,
  records_synced: 10,
  records_updated: 8,
  records_failed: 2,
  status: "idle",
  last_error_message: null,
  has_refresh_token: true,
  created_at: "2026-05-05T21:00:00.000Z",
  updated_at: "2026-05-05T21:00:00.000Z",
};

describe("integrations runtime boundary schemas", () => {
  it("parses backend-shaped integration detail payloads", () => {
    const parsed = parseIntegration(integrationPayload);

    expect(parsed.provider).toBe("salesforce");
    expect(parsed.records_synced).toBe(10);
  });

  it("parses backend-shaped integration list envelopes", () => {
    const parsed = parseIntegrations({ integrations: [integrationPayload] });

    expect(parsed).toHaveLength(1);
    expect(parsed[0]?.id).toBe("int-1");
  });

  it("parses connection-test and sync-trigger mutation responses", () => {
    expect(
      parseConnectionTestResult({ success: true, message: "connected" })
    ).toMatchObject({
      success: true,
      message: "connected",
    });
    expect(
      parseSyncTriggerResult({
        sync_id: "sync-1",
        job_id: "sync-1",
        status: "queued",
        provider: "salesforce",
      })
    ).toMatchObject({
      sync_id: "sync-1",
      status: "queued",
    });
    expect(
      parseOAuthAuthorizeResult({
        authorization_url: "https://login.salesforce.com/services/oauth2/authorize?client_id=abc",
        state_expires_at: "2026-05-05T21:10:00.000Z",
      })
    ).toMatchObject({
      authorization_url: "https://login.salesforce.com/services/oauth2/authorize?client_id=abc",
      authorize_url: "https://login.salesforce.com/services/oauth2/authorize?client_id=abc",
    });
  });

  it("rejects malformed integration, connection-test, and sync-trigger payloads", () => {
    expect(() =>
      parseIntegration({ ...integrationPayload, provider: "zoho" })
    ).toThrow();
    expect(() =>
      parseIntegrations({
        integrations: [{ ...integrationPayload, status: "offline" }],
      })
    ).toThrow();
    expect(() =>
      parseConnectionTestResult({ success: "yes", message: "connected" })
    ).toThrow();
    expect(() =>
      parseSyncTriggerResult({ sync_id: "sync-1", provider: "salesforce" })
    ).toThrow();
    expect(() =>
      parseOAuthAuthorizeResult({ authorization_url: "not-a-url", state_expires_at: "later" })
    ).toThrow();
  });
});

import { describe, expect, it } from 'vitest';
import { z } from 'zod';
import { buildCreateAccountPayload, createAccountPayloadSchema } from '@/hooks/useAccounts';

const backendCreateAccountRequestSchema = z.object({
  id: z.string().uuid().optional(),
  provider: z.enum(['salesforce', 'hubspot', 'manual']),
  provider_record_id: z.string().min(1).max(100).optional(),
  name: z.string().min(1).max(255),
  domain: z.string().max(255).optional(),
  industry: z.string().max(100).optional(),
  region: z.string().max(100).optional(),
  company_size: z.number().int().min(0).optional(),
  annual_revenue: z.number().min(0).optional(),
  headquarters: z.string().max(255).optional(),
  website: z.string().max(255).optional(),
  owner_id: z.string().max(100).optional(),
  owner_name: z.string().max(255).optional(),
  owner_email: z.string().max(255).optional(),
  stage: z.string().max(50).optional(),
  segment: z.string().max(100).optional(),
});

describe('Contract: POST /accounts create payload', () => {
  it('matches canonical frontend snapshot payload shape', () => {
    const payload = buildCreateAccountPayload({
      provider: 'manual',
      provider_record_id: 'manual-acme-corp',
      name: 'Acme Corp',
      domain: 'acme.example',
      industry: 'Manufacturing',
      region: 'NA',
      company_size: 500,
      annual_revenue: 125000000,
      headquarters: 'Austin, TX',
      website: 'https://acme.example',
      owner_id: 'owner-001',
      owner_name: 'Casey Owner',
      owner_email: 'casey@acme.example',
      stage: 'prospect',
      segment: 'enterprise',
    });

    expect(payload).toMatchInlineSnapshot(`
      {
        "annual_revenue": 125000000,
        "company_size": 500,
        "domain": "acme.example",
        "headquarters": "Austin, TX",
        "industry": "Manufacturing",
        "name": "Acme Corp",
        "owner_email": "casey@acme.example",
        "owner_id": "owner-001",
        "owner_name": "Casey Owner",
        "provider": "manual",
        "provider_record_id": "manual-acme-corp",
        "region": "NA",
        "segment": "enterprise",
        "stage": "prospect",
        "website": "https://acme.example",
      }
    `);
  });

  it('frontend payload schema validates against backend request contract', () => {
    const payload = buildCreateAccountPayload({
      provider: 'manual',
      provider_record_id: 'manual-bravo-industries',
      name: 'Bravo Industries',
      stage: 'prospect',
    });

    expect(() => createAccountPayloadSchema.parse(payload)).not.toThrow();
    expect(() => backendCreateAccountRequestSchema.parse(payload)).not.toThrow();
  });
});

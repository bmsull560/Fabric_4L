import { useCallback } from 'react';
import type {
  CreateSetupResult,
  ProspectSetupPromptPayload,
} from '@/components/workspace/ProspectPromptBuilder';
import {
  buildCreateAccountPayload,
  type CreateAccountParams,
  type CreateAccountPayload,
  useCreateAccount,
} from './useAccounts';

function slugify(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'account';
}

function normalizeDomain(value?: string): string | undefined {
  const normalized = value
    ?.trim()
    .replace(/^https?:\/\//i, '')
    .replace(/^www\./i, '')
    .replace(/\/.*$/, '')
    .toLowerCase();
  return normalized || undefined;
}

export function buildProspectSetupCreateAccountPayload(
  payload: ProspectSetupPromptPayload,
): CreateAccountPayload {
  const name = payload.companyName?.trim() || 'Unknown Account';
  const domain = normalizeDomain(payload.companyDomain) ?? `${slugify(name)}.com`;
  const params: CreateAccountParams = {
    name,
    provider: 'manual',
    provider_record_id: `manual-${slugify(domain)}`,
    domain,
    industry: payload.industry?.trim() || undefined,
    stage: 'prospect',
    website: domain,
  };

  return buildCreateAccountPayload(params);
}

export function useProspectSetupAccountCreate() {
  const createAccount = useCreateAccount();

  const createSetup = useCallback(async (payload: ProspectSetupPromptPayload): Promise<CreateSetupResult> => {
    const result = await createAccount.mutateAsync(buildProspectSetupCreateAccountPayload(payload));
    return { accountId: result.account.id };
  }, [createAccount]);

  return {
    createSetup,
    isSubmitting: createAccount.isPending,
  };
}

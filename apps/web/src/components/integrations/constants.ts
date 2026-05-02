import React from 'react';
import { Cloud } from 'lucide-react';
import type { CRMProvider } from '@/hooks/useIntegrations';

export const PROVIDER_NAMES: Record<CRMProvider, string> = {
  salesforce: 'Salesforce',
  hubspot: 'HubSpot',
};

export interface ProviderField {
  key: string;
  label: string;
  type: string;
  required: boolean;
  placeholder: string;
}

export interface ProviderStyle {
  name: string;
  description: string;
  headerBg: string;
  iconBg: string;
  iconText: string;
  toggleFocus: string;
  toggleBg: string;
  icon: React.ReactNode;
  gridIconBg: string;
  gridIconText: string;
  fields: ProviderField[];
}

export const PROVIDER_STYLES: Record<CRMProvider, ProviderStyle> = {
  salesforce: {
    name: 'Salesforce',
    description: 'Sync accounts, opportunities, and activities from Salesforce CRM',
    headerBg: 'bg-blue-50/50',
    iconBg: 'bg-blue-100',
    iconText: 'text-blue-600',
    toggleFocus: 'peer-focus:ring-blue-300',
    toggleBg: 'peer-checked:bg-blue-600',
    icon: React.createElement(Cloud, { size: 24 }),
    gridIconBg: 'bg-blue-100',
    gridIconText: 'text-blue-600',
    fields: [
      {
        key: 'apiKey',
        label: 'Access Token',
        type: 'password',
        required: true,
        placeholder: '00D...!ARQA...',
      },
      {
        key: 'apiSecret',
        label: 'Refresh Token (optional)',
        type: 'password',
        required: false,
        placeholder: 'For automatic token refresh',
      },
      {
        key: 'instanceUrl',
        label: 'Instance URL',
        type: 'text',
        required: true,
        placeholder: 'https://yourinstance.salesforce.com',
      },
    ],
  },
  hubspot: {
    name: 'HubSpot',
    description: 'Sync companies, deals, and engagements from HubSpot CRM',
    headerBg: 'bg-orange-50/50',
    iconBg: 'bg-orange-100',
    iconText: 'text-orange-600',
    toggleFocus: 'peer-focus:ring-orange-300',
    toggleBg: 'peer-checked:bg-orange-600',
    icon: React.createElement(Cloud, { size: 24 }),
    gridIconBg: 'bg-orange-100',
    gridIconText: 'text-orange-600',
    fields: [
      {
        key: 'apiKey',
        label: 'Private App Token',
        type: 'password',
        required: true,
        placeholder: 'pat-na1-...',
      },
    ],
  },
};

// Validation constants
export const VALIDATION = {
  SYNC_INTERVAL: { MIN: 5, MAX: 1440, DEFAULT: 60 },
  BATCH_SIZE: { MIN: 10, MAX: 500, DEFAULT: 100 },
} as const;

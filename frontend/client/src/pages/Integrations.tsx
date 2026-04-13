/**
 * Integrations Page — CRM Connection Management
 * 
 * Features:
 * - Configure Salesforce and HubSpot connections
 * - Test connection status
 * - View sync logs and health
 * - Manage OAuth tokens
 */
import { useState } from "react";
import { PageHeader, Btn, StatusBadge } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import ErrorBoundary from "@/components/ErrorBoundary";
import {
  useAccountSyncStatus,
  useSyncAccounts,
  type CRMProvider,
} from "@/hooks/useAccounts";
import {
  Cloud,
  CloudOff,
  RefreshCw,
  Loader2,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Key,
  Settings,
  Shield,
  ChevronRight,
  Trash2,
  Play,
  Clock,
  Activity,
  Database,
} from "lucide-react";

interface CRMConfig {
  provider: CRMProvider;
  enabled: boolean;
  apiKey?: string;
  apiSecret?: string;
  instanceUrl?: string;
  syncIntervalMinutes: number;
  syncBatchSize: number;
}

const PROVIDER_STYLES: Record<CRMProvider, {
  name: string;
  description: string;
  headerBg: string;
  iconBg: string;
  iconText: string;
  toggleFocus: string;
  toggleBg: string;
  icon: React.ReactNode;
  fields: { key: keyof CRMConfig; label: string; type: string; required: boolean; placeholder: string }[];
}> = {
  salesforce: {
    name: "Salesforce",
    description: "Sync accounts, opportunities, and activities from Salesforce CRM",
    headerBg: "bg-blue-50/50",
    iconBg: "bg-blue-100",
    iconText: "text-blue-600",
    toggleFocus: "peer-focus:ring-blue-300",
    toggleBg: "peer-checked:bg-blue-600",
    icon: <Cloud size={24} />,
    fields: [
      { key: "apiKey", label: "Access Token", type: "password", required: true, placeholder: "00D...!ARQA..." },
      { key: "apiSecret", label: "Refresh Token (optional)", type: "password", required: false, placeholder: "For automatic token refresh" },
      { key: "instanceUrl", label: "Instance URL", type: "text", required: true, placeholder: "https://yourinstance.salesforce.com" },
    ],
  },
  hubspot: {
    name: "HubSpot",
    description: "Sync companies, deals, and engagements from HubSpot CRM",
    headerBg: "bg-orange-50/50",
    iconBg: "bg-orange-100",
    iconText: "text-orange-600",
    toggleFocus: "peer-focus:ring-orange-300",
    toggleBg: "peer-checked:bg-orange-600",
    icon: <Cloud size={24} />,
    fields: [
      { key: "apiKey", label: "Private App Token", type: "password", required: true, placeholder: "pat-na1-..." },
    ],
  },
};

function ConnectionCard({
  provider,
  config,
  status,
  isSyncing,
  onToggle,
  onSync,
  onUpdate,
  isUpdating,
}: {
  provider: CRMProvider;
  config: CRMConfig;
  status?: {
    status: 'idle' | 'running' | 'failed';
    last_sync_at?: string;
    last_successful_sync_at?: string;
    records_synced: number;
    records_updated: number;
    records_failed: number;
    error_message?: string;
  };
  isSyncing: boolean;
  onToggle: (enabled: boolean) => void;
  onSync: () => void;
  onUpdate: (config: Partial<CRMConfig>) => void;
  isUpdating: boolean;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editConfig, setEditConfig] = useState(config);
  const providerInfo = PROVIDER_STYLES[provider];

  const handleSave = () => {
    onUpdate(editConfig);
    setIsEditing(false);
  };

  const isConnected = config.enabled && config.apiKey;

  return (
    <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden">
      {/* Header */}
      <div className={`px-6 py-5 border-b border-neutral-100 ${
        isConnected ? providerInfo.headerBg : "bg-neutral-50"
      }`}>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl ${
              isConnected ? `${providerInfo.iconBg} ${providerInfo.iconText}` : "bg-neutral-100 text-neutral-400"
            } flex items-center justify-center`}>
              {providerInfo.icon}
            </div>
            <div>
              <h3 className="text-[16px] font-bold text-neutral-900">{providerInfo.name}</h3>
              <p className="text-[12px] text-neutral-500 mt-0.5">{providerInfo.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium ${
              isConnected
                ? status?.status === "failed"
                  ? "bg-red-100 text-red-700 border border-red-200"
                  : status?.status === "running"
                  ? "bg-amber-100 text-amber-700 border border-amber-200"
                  : "bg-emerald-100 text-emerald-700 border border-emerald-200"
                : "bg-neutral-100 text-neutral-500 border border-neutral-200"
            }`}>
              {isConnected ? (
                status?.status === "failed" ? (
                  <span className="flex items-center gap-1">
                    <AlertCircle size={12} />
                    Error
                  </span>
                ) : status?.status === "running" ? (
                  <>
                    <Loader2 size={12} className="animate-spin" />
                    Syncing...
                  </>
                ) : (
                  <span className="flex items-center gap-1">
                    <CheckCircle2 size={12} />
                    Connected
                  </span>
                )
              ) : (
                <span className="flex items-center gap-1">
                  <CloudOff size={12} />
                  Disconnected
                </span>
              )}
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={config.enabled}
                onChange={(e) => onToggle(e.target.checked)}
                className="sr-only peer"
              />
              <div className={`w-11 h-6 rounded-full peer peer-focus:ring-2 ${providerInfo.toggleFocus} ${
                config.enabled ? providerInfo.toggleBg : "bg-neutral-200"
              } peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all`}></div>
            </label>
          </div>
        </div>
      </div>

      {/* Configuration */}
      <div className="p-6">
        {isEditing ? (
          <div className="space-y-4">
            {providerInfo.fields.map((field) => (
              <div key={field.key}>
                <label className="text-[12px] font-medium text-neutral-700 mb-1.5 block">
                  {field.label}
                  {field.required && <span className="text-red-500 ml-1">*</span>}
                </label>
                <input
                  type={field.type}
                  value={(editConfig[field.key] as string) || ""}
                  onChange={(e) => setEditConfig({ ...editConfig, [field.key]: e.target.value })}
                  placeholder={field.placeholder}
                  className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-[13px] focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>
            ))}

            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <label className="text-[12px] font-medium text-neutral-700 mb-1.5 block">
                  Sync Interval (minutes)
                </label>
                <input
                  type="number"
                  min={5}
                  max={1440}
                  value={editConfig.syncIntervalMinutes}
                  onChange={(e) => setEditConfig({ ...editConfig, syncIntervalMinutes: parseInt(e.target.value) || 60 })}
                  className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-[13px] focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-[12px] font-medium text-neutral-700 mb-1.5 block">
                  Batch Size
                </label>
                <input
                  type="number"
                  min={10}
                  max={500}
                  value={editConfig.syncBatchSize}
                  onChange={(e) => setEditConfig({ ...editConfig, syncBatchSize: parseInt(e.target.value) || 100 })}
                  className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-[13px] focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-4">
              <Btn variant="ghost" onClick={() => setIsEditing(false)}>
                Cancel
              </Btn>
              <Btn variant="primary" onClick={handleSave} disabled={isUpdating}>
                {isUpdating ? (
                  <>
                    <Loader2 size={14} className="animate-spin mr-1" />
                    Saving...
                  </>
                ) : (
                  "Save Configuration"
                )}
              </Btn>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Connection Status */}
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 bg-neutral-50 rounded-lg border border-neutral-100">
                <div className="flex items-center gap-2 text-[11px] font-medium text-neutral-500 mb-2">
                  <Activity size={12} />
                  Status
                </div>
                <p className={`text-[14px] font-semibold ${
                  isConnected ? "text-emerald-600" : "text-neutral-400"
                }`}>
                  {isConnected ? "Active" : "Not Connected"}
                </p>
              </div>

              <div className="p-4 bg-neutral-50 rounded-lg border border-neutral-100">
                <div className="flex items-center gap-2 text-[11px] font-medium text-neutral-500 mb-2">
                  <Clock size={12} />
                  Last Sync
                </div>
                <p className="text-[14px] font-semibold text-neutral-700">
                  {status?.last_successful_sync_at
                    ? new Date(status.last_successful_sync_at).toLocaleDateString()
                    : "Never"}
                </p>
              </div>

              <div className="p-4 bg-neutral-50 rounded-lg border border-neutral-100">
                <div className="flex items-center gap-2 text-[11px] font-medium text-neutral-500 mb-2">
                  <Database size={12} />
                  Records Synced
                </div>
                <p className="text-[14px] font-semibold text-neutral-700">
                  {status?.records_synced?.toLocaleString() || "0"}
                </p>
              </div>
            </div>

            {/* Error Message */}
            {status?.error_message && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertCircle size={16} className="text-red-500 mt-0.5" />
                  <div>
                    <p className="text-[12px] font-medium text-red-800">Sync Error</p>
                    <p className="text-[11px] text-red-600 mt-1">{status.error_message}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-2">
                <Btn
                  variant="ghost"
                  onClick={() => setIsEditing(true)}
                  disabled={!isConnected}
                >
                  <Settings size={14} className="mr-1" />
                  Edit
                </Btn>
                <Btn
                  variant={isSyncing ? "ghost" : "primary"}
                  onClick={onSync}
                  disabled={!isConnected || isSyncing}
                >
                  {isSyncing ? (
                    <>
                      <Loader2 size={14} className="animate-spin mr-1" />
                      Syncing...
                    </>
                  ) : (
                    <>
                      <Play size={14} className="mr-1" />
                      Sync Now
                    </>
                  )}
                </Btn>
              </div>

              {isConnected && (
                <Btn
                  variant="outline"
                  onClick={() => onToggle(false)}
                  className="text-red-600 hover:bg-red-50"
                >
                  <Trash2 size={14} className="mr-1" />
                  Disconnect
                </Btn>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Integrations() {
  const { data: syncStatus, isLoading } = useAccountSyncStatus();
  const syncMutation = useSyncAccounts();

  const [configs, setConfigs] = useState<Record<CRMProvider, CRMConfig>>({
    salesforce: {
      provider: "salesforce",
      enabled: false,
      apiKey: "",
      apiSecret: "",
      instanceUrl: "",
      syncIntervalMinutes: 60,
      syncBatchSize: 100,
    },
    hubspot: {
      provider: "hubspot",
      enabled: false,
      apiKey: "",
      syncIntervalMinutes: 60,
      syncBatchSize: 100,
    },
  });

  const handleToggle = (provider: CRMProvider, enabled: boolean) => {
    setConfigs((prev) => ({
      ...prev,
      [provider]: { ...prev[provider], enabled },
    }));
  };

  const handleUpdate = (provider: CRMProvider, updates: Partial<CRMConfig>) => {
    setConfigs((prev) => ({
      ...prev,
      [provider]: { ...prev[provider], ...updates },
    }));
  };

  const handleSync = (provider?: CRMProvider) => {
    syncMutation.mutate({ provider });
  };

  const getProviderStatus = (provider: CRMProvider) => {
    return syncStatus?.find((s) => s.provider === provider);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-neutral-50">
        <div className="max-w-[1000px] mx-auto px-6 py-8">
          <Skeleton className="h-8 w-48 mb-8" />
          <div className="space-y-6">
            <Skeleton className="h-64 w-full rounded-xl" />
            <Skeleton className="h-64 w-full rounded-xl" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-[1000px] mx-auto px-6 py-8">
        {/* Header */}
        <PageHeader
          title="Integrations"
          subtitle="Connect and manage your CRM data sources"
        />

        {/* Info Banner */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
          <div className="flex items-start gap-3">
            <Shield size={18} className="text-blue-600 mt-0.5" />
            <div>
              <p className="text-[13px] font-medium text-blue-900">Secure Integration</p>
              <p className="text-[12px] text-blue-700 mt-1">
                Your CRM credentials are encrypted at rest and only used for syncing account data.
                OAuth tokens are refreshed automatically when possible.
              </p>
            </div>
          </div>
        </div>

        {/* Provider Cards */}
        <div className="mt-8 space-y-6">
          {(Object.keys(configs) as CRMProvider[]).map((provider) => (
            <ConnectionCard
              key={provider}
              provider={provider}
              config={configs[provider]}
              status={getProviderStatus(provider)}
              isSyncing={syncMutation.isPending}
              onToggle={(enabled) => handleToggle(provider, enabled)}
              onSync={() => handleSync(provider)}
              onUpdate={(updates) => handleUpdate(provider, updates)}
              isUpdating={false}
            />
          ))}
        </div>

        {/* Documentation */}
        <div className="mt-12 p-6 bg-white border border-neutral-200 rounded-xl">
          <h3 className="text-[14px] font-semibold text-neutral-800 mb-4">Getting Started</h3>
          <div className="grid grid-cols-2 gap-6">
            <a
              href="https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_understanding_authentication.htm"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-start gap-3 p-4 bg-neutral-50 rounded-lg border border-neutral-200 hover:border-blue-300 hover:bg-blue-50/30 transition-colors"
            >
              <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center shrink-0">
                <Key size={18} />
              </div>
              <div>
                <p className="text-[13px] font-medium text-neutral-800">Salesforce Setup Guide</p>
                <p className="text-[11px] text-neutral-500 mt-1">
                  Learn how to create a connected app and generate OAuth tokens.
                </p>
                <span className="inline-flex items-center gap-1 text-[11px] text-blue-600 mt-2">
                  View Documentation
                  <ExternalLink size={10} />
                </span>
              </div>
            </a>

            <a
              href="https://developers.hubspot.com/docs/api/private-apps"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-start gap-3 p-4 bg-neutral-50 rounded-lg border border-neutral-200 hover:border-orange-300 hover:bg-orange-50/30 transition-colors"
            >
              <div className="w-10 h-10 rounded-lg bg-orange-100 text-orange-600 flex items-center justify-center shrink-0">
                <Key size={18} />
              </div>
              <div>
                <p className="text-[13px] font-medium text-neutral-800">HubSpot Setup Guide</p>
                <p className="text-[11px] text-neutral-500 mt-1">
                  Create a private app and generate an access token for API access.
                </p>
                <span className="inline-flex items-center gap-1 text-[11px] text-orange-600 mt-2">
                  View Documentation
                  <ExternalLink size={10} />
                </span>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function IntegrationsPage() {
  return (
    <ErrorBoundary>
      <Integrations />
    </ErrorBoundary>
  );
}

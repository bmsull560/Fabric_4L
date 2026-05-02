import React, { useState, useEffect } from 'react';
import { Btn } from '@/components/WfPrimitives';
import {
  Cloud,
  CloudOff,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Settings,
  Trash2,
  Play,
  Activity,
  Clock,
  Database,
  MousePointerClick,
} from 'lucide-react';
import type {
  Integration,
  IntegrationCreateRequest,
  CRMProvider,
} from '@/hooks/useIntegrations';
import { PROVIDER_STYLES, VALIDATION, PROVIDER_NAMES } from './constants';
import { getStatusBadgeClasses, formatLastSync, formatRecordCount } from './utils';

interface EditingConfig {
  enabled: boolean;
  apiKey: string;
  apiSecret: string;
  instanceUrl: string;
  syncIntervalMinutes: number;
  syncBatchSize: number;
}

interface IntegrationConfigPanelProps {
  integration: Integration | undefined;
  onUpdate: (data: IntegrationCreateRequest) => void;
  onDelete: () => void;
  onTest: () => void;
  onSync: () => void;
  isUpdating: boolean;
  isTesting: boolean;
  isSyncing: boolean;
}

export function IntegrationConfigPanel({
  integration,
  onUpdate,
  onDelete,
  onTest,
  onSync,
  isUpdating,
  isTesting,
  isSyncing,
}: IntegrationConfigPanelProps) {
  const provider = (integration?.provider || 'salesforce') as CRMProvider;
  const providerInfo = PROVIDER_STYLES[provider];
  const [isEditing, setIsEditing] = useState(false);
  const [editConfig, setEditConfig] = useState<EditingConfig>({
    enabled: integration?.enabled || false,
    apiKey: '',
    apiSecret: '',
    instanceUrl: integration?.instance_url || '',
    syncIntervalMinutes: integration?.sync_interval_minutes || 60,
    syncBatchSize: integration?.sync_batch_size || 100,
  });

  useEffect(() => {
    if (integration) {
      setEditConfig(prev => ({
        ...prev,
        enabled: integration.enabled,
        instanceUrl: integration.instance_url || '',
        syncIntervalMinutes: integration.sync_interval_minutes,
        syncBatchSize: integration.sync_batch_size,
      }));
    }
  }, [integration?.id]);

  const handleSave = () => {
    const requestData: IntegrationCreateRequest = {
      enabled: editConfig.enabled,
      api_key: editConfig.apiKey,
      api_secret: editConfig.apiSecret || undefined,
      instance_url: editConfig.instanceUrl,
      sync_interval_minutes: editConfig.syncIntervalMinutes,
      sync_batch_size: editConfig.syncBatchSize,
    };
    onUpdate(requestData);
    setIsEditing(false);
    setEditConfig(prev => ({ ...prev, apiKey: '', apiSecret: '' }));
  };

  const isConnected = integration?.enabled || false;
  const status = integration?.status || 'idle';
  const errorMessage = integration?.last_error_message;

  // Empty state
  if (!integration) {
    return (
      <div className="bg-white border border-neutral-200 rounded-xl p-8 h-full min-h-[400px] flex flex-col items-center justify-center text-center">
        <div className="w-16 h-16 rounded-full bg-neutral-100 flex items-center justify-center mb-4">
          <MousePointerClick size={32} className="text-neutral-400" />
        </div>
        <h3 className="text-[16px] font-semibold text-neutral-800 mb-2">
          Select an integration
        </h3>
        <p className="text-[13px] text-neutral-500 max-w-xs">
          Choose an integration from the grid to view and configure its settings
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden sticky top-6">
      {/* Header */}
      <div className={`px-6 py-5 border-b border-neutral-100 ${
        isConnected ? providerInfo.headerBg : "bg-neutral-50"
      }`}>
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
      </div>

      {/* Status Badge */}
      <div className="px-6 py-4 border-b border-neutral-100">
        <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium ${getStatusBadgeClasses(status, isConnected)}`}>
          {isConnected ? (
            status === "failed" ? (
              <span className="flex items-center gap-1">
                <AlertCircle size={12} />
                Error
              </span>
            ) : status === "running" ? (
              <>
                <Loader2 size={12} className="animate-spin" />
                Syncing...
              </>
            ) : status === "degraded" ? (
              <span className="flex items-center gap-1">
                <AlertCircle size={12} />
                Degraded
              </span>
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
                  value={editConfig[field.key as keyof EditingConfig] as string}
                  onChange={(e) => setEditConfig({ ...editConfig, [field.key]: e.target.value })}
                  placeholder={field.placeholder}
                  className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-[13px] focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>
            ))}

            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <label className="text-[12px] font-medium text-neutral-700 mb-1.5 block">
                  Sync Interval (min)
                </label>
                <input
                  type="number"
                  min={VALIDATION.SYNC_INTERVAL.MIN}
                  max={VALIDATION.SYNC_INTERVAL.MAX}
                  value={editConfig.syncIntervalMinutes}
                  onChange={(e) => {
                    const value = parseInt(e.target.value) || VALIDATION.SYNC_INTERVAL.DEFAULT;
                    const clamped = Math.min(Math.max(value, VALIDATION.SYNC_INTERVAL.MIN), VALIDATION.SYNC_INTERVAL.MAX);
                    setEditConfig({ ...editConfig, syncIntervalMinutes: clamped });
                  }}
                  className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-[13px] focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-[12px] font-medium text-neutral-700 mb-1.5 block">
                  Batch Size
                </label>
                <input
                  type="number"
                  min={VALIDATION.BATCH_SIZE.MIN}
                  max={VALIDATION.BATCH_SIZE.MAX}
                  value={editConfig.syncBatchSize}
                  onChange={(e) => {
                    const value = parseInt(e.target.value) || VALIDATION.BATCH_SIZE.DEFAULT;
                    const clamped = Math.min(Math.max(value, VALIDATION.BATCH_SIZE.MIN), VALIDATION.BATCH_SIZE.MAX);
                    setEditConfig({ ...editConfig, syncBatchSize: clamped });
                  }}
                  className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-[13px] focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 pt-4">
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={editConfig.enabled}
                  onChange={(e) => setEditConfig({ ...editConfig, enabled: e.target.checked })}
                  className="sr-only peer"
                />
                <div className={`w-11 h-6 rounded-full peer peer-focus:ring-2 ${providerInfo.toggleFocus} ${
                  editConfig.enabled ? providerInfo.toggleBg : "bg-neutral-200"
                } peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all`}></div>
                <span className="ml-3 text-[13px] text-neutral-700">Enable integration</span>
              </label>
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
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-100">
                <div className="flex items-center gap-1.5 text-[10px] font-medium text-neutral-500 mb-1">
                  <Activity size={10} />
                  Status
                </div>
                <p className={`text-[13px] font-semibold ${
                  isConnected ? "text-emerald-600" : "text-neutral-400"
                }`}>
                  {isConnected ? "Active" : "Not Connected"}
                </p>
              </div>

              <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-100">
                <div className="flex items-center gap-1.5 text-[10px] font-medium text-neutral-500 mb-1">
                  <Clock size={10} />
                  Last Sync
                </div>
                <p className="text-[13px] font-semibold text-neutral-700">
                  {formatLastSync(integration?.last_successful_sync_at)}
                </p>
              </div>

              <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-100">
                <div className="flex items-center gap-1.5 text-[10px] font-medium text-neutral-500 mb-1">
                  <Database size={10} />
                  Records
                </div>
                <p className="text-[13px] font-semibold text-neutral-700">
                  {formatRecordCount(integration?.records_synced)}
                </p>
              </div>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertCircle size={14} className="text-red-500 mt-0.5" />
                  <div>
                    <p className="text-[11px] font-medium text-red-800">Sync Error</p>
                    <p className="text-[10px] text-red-600 mt-0.5">{errorMessage}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-col gap-2 pt-2">
              <div className="flex items-center gap-2">
                <Btn
                  variant="ghost"
                  onClick={() => setIsEditing(true)}
                  className="flex-1"
                >
                  <Settings size={14} className="mr-1" />
                  Edit
                </Btn>
                <Btn
                  variant={isSyncing ? "ghost" : "primary"}
                  onClick={onSync}
                  disabled={!isConnected || isSyncing}
                  className="flex-1"
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
              <div className="flex items-center gap-2">
                <Btn
                  variant="outline"
                  onClick={onTest}
                  disabled={!isConnected || isTesting}
                  className="flex-1"
                >
                  {isTesting ? (
                    <>
                      <Loader2 size={14} className="animate-spin mr-1" />
                      Testing...
                    </>
                  ) : (
                    "Test Connection"
                  )}
                </Btn>
                {isConnected && (
                  <Btn
                    variant="outline"
                    onClick={onDelete}
                    className="flex-1 text-red-600 hover:bg-red-50"
                  >
                    <Trash2 size={14} className="mr-1" />
                    Disconnect
                  </Btn>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

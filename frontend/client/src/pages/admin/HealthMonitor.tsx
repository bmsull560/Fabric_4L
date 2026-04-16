/**
 * HealthMonitor — Admin Tier 3 Page
 * 
 * System health monitoring dashboard:
 * - Real-time service status grid (L1-L6 layers)
 * - Health alerts and incidents
 * - Response time metrics
 * - Uptime statistics
 * - Auto-refresh every 30 seconds
 * 
 * Connected to Layer 4 health endpoints
 */

import { useState, useMemo } from "react";
import {
  Activity, AlertCircle, CheckCircle2, Clock, RefreshCw,
  AlertTriangle, XCircle, Server, Database, Zap,
  Globe, Shield, Loader2, Bell, ExternalLink,
  ChevronDown, ChevronUp, Filter
} from "lucide-react";
import { PageHeader, Btn } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import ErrorBoundary from "@/components/ErrorBoundary";
import { cn } from "@/lib/utils";
import {
  useSystemHealth,
  useHealthAlerts,
  type ServiceStatus,
  type ServiceHealth,
  type HealthAlert,
} from "@/hooks/useHealthMonitor";

// ── Types ────────────────────────────────────────────────────────────────────

type FilterStatus = "all" | ServiceStatus;
type AlertSeverity = "all" | "critical" | "warning" | "info";

// ── Styling Constants ─────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<ServiceStatus, {
  label: string;
  color: string;
  bgColor: string;
  icon: React.ReactNode;
}> = {
  healthy: {
    label: "Healthy",
    color: "text-emerald-600",
    bgColor: "bg-emerald-50",
    icon: <CheckCircle2 size={16} />,
  },
  degraded: {
    label: "Degraded",
    color: "text-amber-600",
    bgColor: "bg-amber-50",
    icon: <AlertTriangle size={16} />,
  },
  unhealthy: {
    label: "Unhealthy",
    color: "text-red-600",
    bgColor: "bg-red-50",
    icon: <XCircle size={16} />,
  },
  unknown: {
    label: "Unknown",
    color: "text-neutral-500",
    bgColor: "bg-neutral-100",
    icon: <AlertCircle size={16} />,
  },
};

const ALERT_SEVERITY_CONFIG: Record<HealthAlert['severity'], {
  color: string;
  bgColor: string;
  icon: React.ReactNode;
}> = {
  critical: {
    color: "text-red-600",
    bgColor: "bg-red-50",
    icon: <XCircle size={14} />,
  },
  warning: {
    color: "text-amber-600",
    bgColor: "bg-amber-50",
    icon: <AlertTriangle size={14} />,
  },
  info: {
    color: "text-blue-600",
    bgColor: "bg-blue-50",
    icon: <Bell size={14} />,
  },
};

const SERVICE_ICONS: Record<string, React.ReactNode> = {
  "l1-ingestion": <Globe size={18} />,
  "l2-extraction": <Zap size={18} />,
  "l3-knowledge": <Database size={18} />,
  "l4-agents": <Server size={18} />,
  "l5-truth": <Shield size={18} />,
  "l6-benchmarks": <Activity size={18} />,
};

// ── Helper Functions ────────────────────────────────────────────────────────

function formatDuration(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function formatTimeAgo(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${Math.floor(diffHours / 24)}d ago`;
}

// ── Sub-components ───────────────────────────────────────────────────────────

function ServiceCard({ service }: { service: ServiceHealth }) {
  const status = STATUS_CONFIG[service.status];
  const icon = SERVICE_ICONS[service.name] || <Server size={18} />;

  return (
    <div className="bg-white border border-neutral-200 rounded-xl p-4 hover:border-neutral-300 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={cn(
            "w-10 h-10 rounded-lg flex items-center justify-center",
            status.bgColor, status.color
          )}>
            {icon}
          </div>
          <div>
            <h4 className="text-[13px] font-semibold text-neutral-800">
              {service.name.replace(/-/g, ' ').replace(/^l\d-/, 'L$1 ')}
            </h4>
            <p className="text-[11px] text-neutral-500">v{service.version}</p>
          </div>
        </div>
        <span className={cn(
          "inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full",
          status.bgColor, status.color
        )}>
          {status.icon} {status.label}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-[11px]">
        <div className="bg-neutral-50 rounded-lg p-2">
          <span className="text-neutral-400 block">Uptime</span>
          <span className="text-neutral-700 font-medium">
            {formatDuration(service.uptime_seconds)}
          </span>
        </div>
        <div className="bg-neutral-50 rounded-lg p-2">
          <span className="text-neutral-400 block">Response</span>
          <span className={cn(
            "font-medium",
            service.response_time_ms > 1000 ? "text-amber-600" : "text-neutral-700"
          )}>
            {service.response_time_ms}ms
          </span>
        </div>
      </div>

      {service.error_message && (
        <div className="mt-3 p-2 bg-red-50 border border-red-100 rounded-lg text-[11px] text-red-600">
          {service.error_message}
        </div>
      )}

      <div className="mt-3 flex items-center justify-between text-[10px] text-neutral-400">
        <span>Last check: {formatTimeAgo(service.last_check_at)}</span>
        <button className="text-blue-600 hover:underline flex items-center gap-0.5">
          Details <ExternalLink size={10} />
        </button>
      </div>
    </div>
  );
}

function AlertCard({ alert }: { alert: HealthAlert }) {
  const severity = ALERT_SEVERITY_CONFIG[alert.severity];

  return (
    <div className={cn(
      "flex items-start gap-3 p-3 rounded-lg border",
      alert.resolved_at
        ? "bg-neutral-50 border-neutral-200 opacity-60"
        : severity.bgColor.replace('bg-', 'bg-opacity-50 bg-') + " " + severity.bgColor.replace('bg-', 'border-')
    )}>
      <span className={cn("shrink-0 mt-0.5", severity.color)}>
        {severity.icon}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-[12px] font-medium text-neutral-800">
            {alert.service_name}
          </span>
          <span className={cn(
            "text-[9px] px-1.5 py-0.5 rounded font-semibold uppercase",
            severity.bgColor, severity.color
          )}>
            {alert.severity}
          </span>
        </div>
        <p className="text-[11px] text-neutral-600 mt-0.5 truncate">
          {alert.message}
        </p>
        <div className="flex items-center gap-3 mt-1.5 text-[10px] text-neutral-400">
          <span>Started: {formatTimeAgo(alert.started_at)}</span>
          {alert.resolved_at && (
            <span className="text-emerald-600">
              Resolved: {formatTimeAgo(alert.resolved_at)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  status,
  icon,
}: {
  label: string;
  value: number;
  status: ServiceStatus;
  icon: React.ReactNode;
}) {
  const config = STATUS_CONFIG[status];

  return (
    <div className="bg-white border border-neutral-200 rounded-xl px-4 py-3">
      <div className="flex items-center gap-2 mb-1">
        <span className={config.color}>{icon}</span>
        <span className="text-[10px] uppercase tracking-wider text-neutral-400 font-semibold">
          {label}
        </span>
      </div>
      <p className={cn("text-[22px] font-extrabold", config.color)}>
        {value}
      </p>
    </div>
  );
}

function HealthMonitorSkeleton() {
  return (
    <div className="p-6 max-w-6xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-72" />
        </div>
        <Skeleton className="h-9 w-28" />
      </div>

      {/* Summary Skeleton */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map(i => (
          <Skeleton key={i} className="h-20 rounded-xl" />
        ))}
      </div>

      {/* Services Grid Skeleton */}
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map(i => (
          <Skeleton key={i} className="h-36 rounded-xl" />
        ))}
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────

function HealthMonitorContent() {
  const [statusFilter, setStatusFilter] = useState<FilterStatus>("all");
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity>("all");
  const [showResolved, setShowResolved] = useState(false);

  const {
    data: health,
    isLoading: healthLoading,
    error: healthError,
    refetch: refetchHealth,
    dataUpdatedAt,
  } = useSystemHealth();

  const {
    data: alerts,
    isLoading: alertsLoading,
    error: alertsError,
    refetch: refetchAlerts,
  } = useHealthAlerts();

  const isLoading = healthLoading || alertsLoading;
  const error = healthError || alertsError;

  const filteredServices = useMemo(() => {
    if (!health?.services) return [];
    if (statusFilter === "all") return health.services;
    return health.services.filter(s => s.status === statusFilter);
  }, [health?.services, statusFilter]);

  const filteredAlerts = useMemo(() => {
    if (!alerts) return [];
    return alerts.filter(a => {
      if (!showResolved && a.resolved_at) return false;
      if (severityFilter !== "all" && a.severity !== severityFilter) return false;
      return true;
    });
  }, [alerts, severityFilter, showResolved]);

  const lastUpdated = useMemo(() => {
    if (!dataUpdatedAt) return "Never";
    return formatTimeAgo(new Date(dataUpdatedAt).toISOString());
  }, [dataUpdatedAt]);

  const handleRefresh = () => {
    refetchHealth();
    refetchAlerts();
  };

  if (isLoading) {
    return <HealthMonitorSkeleton />;
  }

  if (error) {
    return (
      <div className="p-6 max-w-6xl">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-8 h-8 text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-[14px] font-semibold text-red-800 mb-1">
                Failed to load health data
              </h3>
              <p className="text-[12px] text-red-600">
                {error instanceof Error ? error.message : "An unexpected error occurred"}
              </p>
              <button
                onClick={handleRefresh}
                className="mt-4 flex items-center gap-1.5 px-3 py-1.5 bg-red-100 text-red-700 text-[12px] font-medium rounded-lg hover:bg-red-200 transition-colors"
              >
                <RefreshCw size={14} /> Try again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!health) {
    return (
      <div className="p-6 max-w-6xl">
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
          <h3 className="text-[14px] font-semibold text-amber-800">No Health Data</h3>
          <p className="text-[12px] text-amber-600 mt-1">
            System health information is unavailable. Please check the API status.
          </p>
        </div>
      </div>
    );
  }

  const overallStatus = STATUS_CONFIG[health.overall_status];

  return (
    <div className="p-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <PageHeader
          title="System Health"
          subtitle="Monitor real-time status of all platform services"
        />
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-neutral-400">
            Updated {lastUpdated}
          </span>
          <Btn variant="outline" onClick={handleRefresh}>
            <RefreshCw size={14} className="mr-1" />
            Refresh
          </Btn>
        </div>
      </div>

      {/* Overall Status Banner */}
      <div className={cn(
        "mb-6 p-4 rounded-xl border flex items-center gap-3",
        overallStatus.bgColor, overallStatus.bgColor.replace('bg-', 'border-')
      )}>
        <div className={cn("w-12 h-12 rounded-full flex items-center justify-center bg-white", overallStatus.color)}>
          {overallStatus.icon}
        </div>
        <div className="flex-1">
          <h3 className={cn("text-[16px] font-bold", overallStatus.color)}>
            System {overallStatus.label}
          </h3>
          <p className="text-[12px] text-neutral-600">
            {health.summary.healthy} of {health.summary.total} services operating normally
            {health.summary.degraded > 0 && ` • ${health.summary.degraded} degraded`}
            {health.summary.unhealthy > 0 && ` • ${health.summary.unhealthy} unhealthy`}
          </p>
        </div>
        <div className="text-right">
          <p className="text-[11px] text-neutral-400">Last check</p>
          <p className="text-[12px] font-medium text-neutral-700">
            {formatTimeAgo(health.checked_at)}
          </p>
        </div>
      </div>

      {/* Summary Grid */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <SummaryCard
          label="Healthy"
          value={health.summary.healthy}
          status="healthy"
          icon={<CheckCircle2 size={14} />}
        />
        <SummaryCard
          label="Degraded"
          value={health.summary.degraded}
          status="degraded"
          icon={<AlertTriangle size={14} />}
        />
        <SummaryCard
          label="Unhealthy"
          value={health.summary.unhealthy}
          status="unhealthy"
          icon={<XCircle size={14} />}
        />
        <SummaryCard
          label="Unknown"
          value={health.summary.unknown}
          status="unknown"
          icon={<AlertCircle size={14} />}
        />
      </div>

      {/* Services Section */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[14px] font-semibold text-neutral-800">Services</h3>
          <div className="flex items-center gap-2">
            <Filter size={14} className="text-neutral-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as FilterStatus)}
              className="text-[11px] px-2 py-1.5 border border-neutral-200 rounded-lg bg-white text-neutral-600 outline-none"
            >
              <option value="all">All Status</option>
              <option value="healthy">Healthy</option>
              <option value="degraded">Degraded</option>
              <option value="unhealthy">Unhealthy</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {filteredServices.map(service => (
            <ServiceCard key={service.name} service={service} />
          ))}
        </div>

        {filteredServices.length === 0 && (
          <div className="text-center py-8 text-neutral-400 text-[12px]">
            <Server size={32} className="mx-auto mb-2 text-neutral-300" />
            No services match the selected filter.
          </div>
        )}
      </div>

      {/* Alerts Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[14px] font-semibold text-neutral-800">
            Active Alerts {filteredAlerts.length > 0 && `(${filteredAlerts.length})`}
          </h3>
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-1.5 text-[11px] text-neutral-600">
              <input
                type="checkbox"
                checked={showResolved}
                onChange={(e) => setShowResolved(e.target.checked)}
                className="rounded border-neutral-300"
              />
              Show resolved
            </label>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value as AlertSeverity)}
              className="text-[11px] px-2 py-1.5 border border-neutral-200 rounded-lg bg-white text-neutral-600 outline-none"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
          </div>
        </div>

        <div className="space-y-2">
          {filteredAlerts.map(alert => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </div>

        {filteredAlerts.length === 0 && (
          <div className="text-center py-8 text-neutral-400 text-[12px]">
            <Bell size={32} className="mx-auto mb-2 text-neutral-300" />
            {showResolved ? "No alerts found." : "No active alerts. Great!"}
          </div>
        )}
      </div>
    </div>
  );
}

export default function HealthMonitor() {
  return (
    <ErrorBoundary>
      <HealthMonitorContent />
    </ErrorBoundary>
  );
}

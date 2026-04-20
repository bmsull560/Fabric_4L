/**
 * PermissionsAdmin — Admin Tier 3 Page
 *
 * Tenant governance and RBAC management:
 * - Users (invite, role, deactivate)
 * - API Keys (create, revoke)
 *
 * Features:
 * - User listing with role badges
 * - API key listing with enable/revoke
 * - Connected to L4 governance endpoints
 */

import { useState, useMemo } from "react";
import { useLocation } from "wouter";
import {
  Users, Key, Plus, Search, Shield, UserPlus,
  CheckCircle2, Clock, AlertCircle, RefreshCw,
  Trash2, Eye, EyeOff,
} from "lucide-react";
import { PageHeader, Btn } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/formatters";
import ErrorBoundary from "@/components/ErrorBoundary";
import { cn } from "@/lib/utils";
import {
  useUsers,
  useApiKeys,
  useRevokeApiKey,
  type User,
  type ApiKey,
} from "@/hooks/useGovernance";

// ── Styling Constants ───────────────────────────────────────────────────────────

const ROLE_STYLES: Record<string, string> = {
  super_admin:  "bg-red-50 text-red-700 border-red-200",
  tenant_admin: "bg-amber-50 text-amber-700 border-amber-200",
  member:       "bg-blue-50 text-blue-700 border-blue-200",
  viewer:       "bg-neutral-100 text-neutral-600 border-neutral-200",
};

const STATUS_STYLES: Record<string, string> = {
  active:      "bg-emerald-50 text-emerald-700 border-emerald-200",
  invited:     "bg-amber-50 text-amber-700 border-amber-200",
  deactivated: "bg-red-50 text-red-500 border-red-200",
};

// ── Sub-components ─────────────────────────────────────────────────────────────

function RoleBadge({ role }: { role: string }) {
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${ROLE_STYLES[role] || ROLE_STYLES.viewer}`}>
      <Shield size={10} /> {role.replace("_", " ")}
    </span>
  );
}

function StatusChip({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-full border ${STATUS_STYLES[status] || STATUS_STYLES.deactivated}`}>
      {status}
    </span>
  );
}


function PermissionsSkeleton() {
  return (
    <div className="p-6 max-w-6xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-72" />
        </div>
        <Skeleton className="h-9 w-32" />
      </div>
      <div className="bg-white border border-neutral-200 rounded-xl shadow-sm overflow-hidden">
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} className="px-4 py-4 border-b border-neutral-100 flex gap-4">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-16" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────

type TabType = "users" | "api-keys";

function PermissionsContent() {
  const [location] = useLocation();
  const initialTab: TabType = location.includes("/api-keys") ? "api-keys" : "users";
  const [activeTab, setActiveTab] = useState<TabType>(initialTab);
  const [search, setSearch] = useState("");

  const {
    data: users = [],
    isLoading: usersLoading,
    error: usersError,
    refetch: refetchUsers,
  } = useUsers();

  const {
    data: apiKeys = [],
    isLoading: keysLoading,
    error: keysError,
    refetch: refetchKeys,
  } = useApiKeys();

  const revokeMutation = useRevokeApiKey();

  const isLoading = usersLoading || keysLoading;
  const error = usersError || keysError;

  const filteredUsers = useMemo(() =>
    search
      ? users.filter(u =>
          u.email.toLowerCase().includes(search.toLowerCase()) ||
          (u.display_name || "").toLowerCase().includes(search.toLowerCase())
        )
      : users,
    [users, search]
  );

  const filteredKeys = useMemo(() =>
    search
      ? apiKeys.filter(k => k.name.toLowerCase().includes(search.toLowerCase()))
      : apiKeys,
    [apiKeys, search]
  );

  if (isLoading) return <PermissionsSkeleton />;

  if (error) {
    return (
      <div className="p-6 max-w-6xl">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-8 h-8 text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-[14px] font-semibold text-red-800 mb-1">Failed to load permissions data</h3>
              <p className="text-[12px] text-red-600">
                {error instanceof Error ? error.message : "An unexpected error occurred"}
              </p>
              <button
                onClick={() => { refetchUsers(); refetchKeys(); }}
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

  return (
    <div className="p-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <PageHeader
          title="Permissions & Access"
          subtitle="Manage users, roles, and API keys for your tenant."
        />
        <Btn variant="primary">
          {activeTab === "users"
            ? <><UserPlus size={13} className="mr-1" /> Invite User</>
            : <><Plus size={13} className="mr-1" /> New API Key</>
          }
        </Btn>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-neutral-200 mb-4">
        {[
          { id: "users" as const, label: "Users", count: users.length, icon: <Users size={13} /> },
          { id: "api-keys" as const, label: "API Keys", count: apiKeys.length, icon: <Key size={13} /> },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-4 py-2.5 text-[12px] font-medium transition-colors relative",
              activeTab === tab.id
                ? "text-blue-700"
                : "text-neutral-500 hover:text-neutral-700"
            )}
          >
            <span className="flex items-center gap-2">
              {tab.icon} {tab.label}
              <span className={cn(
                "px-1.5 py-0.5 rounded text-[10px]",
                activeTab === tab.id ? "bg-blue-100 text-blue-700" : "bg-neutral-100 text-neutral-600"
              )}>
                {tab.count}
              </span>
            </span>
            {activeTab === tab.id && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-t-full" />
            )}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="flex items-center gap-2 bg-white border border-neutral-200 rounded-lg px-3 py-2 max-w-sm mb-4">
        <Search size={12} className="text-neutral-400 shrink-0" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder={activeTab === "users" ? "Search users..." : "Search API keys..."}
          className="flex-1 text-[12px] bg-transparent outline-none text-neutral-600 placeholder:text-neutral-400"
        />
      </div>

      {activeTab === "users" ? (
        /* Users Table */
        <div className="bg-white border border-neutral-200 rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-[12px]">
            <thead>
              <tr className="border-b border-neutral-100 bg-neutral-50">
                {["User", "Role", "Status", "Created", "Last Login", ""].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-[10px] uppercase tracking-wider text-neutral-400 font-semibold">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {filteredUsers.map(u => (
                <tr key={u.id} className="hover:bg-neutral-50 transition-colors group">
                  <td className="px-4 py-3">
                    <div>
                      <span className="font-medium text-neutral-800 block">{u.display_name || u.email}</span>
                      {u.display_name && <span className="text-[10px] text-neutral-400">{u.email}</span>}
                    </div>
                  </td>
                  <td className="px-4 py-3"><RoleBadge role={u.role} /></td>
                  <td className="px-4 py-3"><StatusChip status={u.status} /></td>
                  <td className="px-4 py-3 text-neutral-400">{formatDate(u.created_at)}</td>
                  <td className="px-4 py-3 text-neutral-400">{formatDate(u.last_login_at)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="p-1.5 rounded hover:bg-neutral-100 text-neutral-400 hover:text-neutral-700" title="View">
                        <Eye size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredUsers.length === 0 && (
            <div className="text-center py-12 text-neutral-400 text-[12px]">
              <Users size={32} className="mx-auto mb-3 text-neutral-300" />
              No users match your search.
            </div>
          )}
        </div>
      ) : (
        /* API Keys Table */
        <div className="bg-white border border-neutral-200 rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-[12px]">
            <thead>
              <tr className="border-b border-neutral-100 bg-neutral-50">
                {["Key Name", "Prefix", "Enabled", "Created", "Last Used", ""].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-[10px] uppercase tracking-wider text-neutral-400 font-semibold">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {filteredKeys.map(k => (
                <tr key={k.id} className="hover:bg-neutral-50 transition-colors group">
                  <td className="px-4 py-3 font-medium text-neutral-800">{k.name}</td>
                  <td className="px-4 py-3 font-mono text-[11px] text-neutral-500">{k.prefix}•••</td>
                  <td className="px-4 py-3">
                    {k.is_enabled
                      ? <span className="inline-flex items-center gap-1 text-emerald-600"><CheckCircle2 size={12} /> Active</span>
                      : <span className="inline-flex items-center gap-1 text-neutral-400"><EyeOff size={12} /> Disabled</span>
                    }
                  </td>
                  <td className="px-4 py-3 text-neutral-400">{formatDate(k.created_at)}</td>
                  <td className="px-4 py-3 text-neutral-400">{formatDate(k.last_used_at)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        className="p-1.5 rounded hover:bg-red-50 text-neutral-400 hover:text-red-500"
                        title="Revoke"
                        onClick={() => revokeMutation.mutate(k.id)}
                        disabled={revokeMutation.isPending}
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredKeys.length === 0 && (
            <div className="text-center py-12 text-neutral-400 text-[12px]">
              <Key size={32} className="mx-auto mb-3 text-neutral-300" />
              No API keys found.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function PermissionsAdmin() {
  return (
    <ErrorBoundary>
      <PermissionsContent />
    </ErrorBoundary>
  );
}

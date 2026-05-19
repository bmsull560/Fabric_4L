import { useQuery } from "@tanstack/react-query";
import { apiGet, apiPost, apiDelete } from "@/api/typedClient";
import { QK } from "@/hooks/queryKeys";
import { STALE_TIME } from "@/hooks/useApiShared";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

interface IngestionTarget {
  id: string;
  domain: string;
  name: string;
  status: string;
  last_synced_at: string | null;
}

function useIngestionTargets() {
  return useQuery<IngestionTarget[]>({
    queryKey: QK.targets.all,
    queryFn: async () => {
      const response = await apiGet<IngestionTarget[]>("l1", "/targets");
      return response.data;
    },
    staleTime: STALE_TIME.list,
  });
}

export function DataSources() {
  const { data: targets, isLoading, refetch } = useIngestionTargets();
  const [newDomain, setNewDomain] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  const handleAdd = async () => {
    if (!newDomain.trim()) return;
    setIsAdding(true);
    try {
      await apiPost("l1", "/targets", {
        domain: newDomain.trim(),
        name: newDomain.trim(),
      });
      toast.success("Source added", { description: newDomain.trim() });
      setNewDomain("");
      refetch();
    } catch (err) {
      toast.error("Failed to add source", {
        description: err instanceof Error ? err.message : "Unknown error",
      });
    } finally {
      setIsAdding(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiDelete("l1", `/targets/${id}`);
      toast.success("Source removed");
      refetch();
    } catch (err) {
      toast.error("Failed to remove source", {
        description: err instanceof Error ? err.message : "Unknown error",
      });
    }
  };

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold">Connection Hub</h3>
            <p className="text-xs text-muted-foreground">Data sources and external business systems.</p>
          </div>
        </div>

        <div className="mt-4 flex gap-2">
          <Input
            placeholder="Enter domain (e.g., example.com)"
            value={newDomain}
            onChange={(e) => setNewDomain(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            className="flex-1"
          />
          <Button onClick={handleAdd} disabled={isAdding || !newDomain.trim()}>
            {isAdding ? "Adding…" : "Add source"}
          </Button>
        </div>

        <div className="mt-4 space-y-2">
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading sources…</p>
          ) : targets && targets.length > 0 ? (
            targets.map((s) => (
              <div key={s.id} className="flex items-center justify-between rounded-md border p-3">
                <div>
                  <p className="text-sm font-medium">{s.name}</p>
                  <p className="text-xs text-muted-foreground">
                    Web Ingestion • Last sync {s.last_synced_at ? new Date(s.last_synced_at).toLocaleString() : "—"}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={s.status === "active" ? "text-xs font-medium text-primary" : "text-xs font-medium text-muted-foreground"}>
                    {s.status}
                  </span>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(s.id)}>
                    Remove
                  </Button>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-lg border border-dashed border-border p-6 text-center">
              <p className="text-sm text-muted-foreground">No data sources configured.</p>
              <p className="text-xs text-muted-foreground/60 mt-1">Add a domain above to start ingestion.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

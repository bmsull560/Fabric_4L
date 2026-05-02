/**
 * WorkspaceErrorState — Shown when a tab encounters an error
 */
import { AlertTriangle } from "lucide-react";

interface Props {
  error?: Error | string;
  onRetry?: () => void;
}

export default function WorkspaceErrorState({ error, onRetry }: Props) {
  const message = typeof error === "string" ? error : error?.message ?? "An error occurred";

  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[300px] gap-4 text-destructive">
      <AlertTriangle size={40} className="opacity-70" />
      <div className="text-center">
        <p className="text-sm font-medium">Something went wrong</p>
        <p className="text-xs mt-1 text-muted-foreground max-w-md">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-xs px-3 py-1.5 rounded-md border border-border hover:bg-muted transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  );
}

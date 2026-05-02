/**
 * WorkspaceLoadingState — Suspense fallback for tab loading
 */
export default function WorkspaceLoadingState() {
  return (
    <div className="flex items-center justify-center h-full min-h-[200px]">
      <div className="w-6 h-6 rounded-full border-2 border-border border-t-primary animate-spin" />
    </div>
  );
}

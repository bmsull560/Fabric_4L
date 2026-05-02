/**
 * CenteredLoader — Consistent centered loading spinner + text across all screens.
 *
 * Rules:
 * - Uses lucide-react's Loader2 icon.
 * - Container uses flex h-full w-full items-center justify-center to center in any parent layout.
 * - Text uses text-muted-foreground (the project's secondary text color).
 */
import { Loader2 } from "lucide-react";

interface CenteredLoaderProps {
  message?: string;
}

export function CenteredLoader({ message = "Loading..." }: CenteredLoaderProps) {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span>{message}</span>
      </div>
    </div>
  );
}

export default CenteredLoader;

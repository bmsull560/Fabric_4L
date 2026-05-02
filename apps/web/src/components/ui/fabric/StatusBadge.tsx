import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type StatusVariant = "default" | "secondary" | "outline" | "destructive" | "success" | "warning" | "info" | "pending";

export interface StatusBadgeProps {
  children: React.ReactNode;
  variant?: StatusVariant;
  className?: string;
}

const variantStyles: Record<string, string> = {
  success: "bg-emerald-100 text-emerald-800 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-300",
  warning: "bg-amber-100 text-amber-800 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-300",
  info: "bg-sky-100 text-sky-800 hover:bg-sky-100 dark:bg-sky-900/30 dark:text-sky-300",
  pending: "bg-orange-100 text-orange-800 hover:bg-orange-100 dark:bg-orange-900/30 dark:text-orange-300",
};

export function StatusBadge({ children, variant = "default", className }: StatusBadgeProps) {
  const isCustom = variant === "success" || variant === "warning" || variant === "info" || variant === "pending";
  return (
    <Badge
      variant={isCustom ? "secondary" : variant as "default" | "secondary" | "outline" | "destructive"}
      className={cn("text-[11px] px-2 py-0.5 rounded-full font-medium", isCustom && variantStyles[variant], className)}
    >
      {children}
    </Badge>
  );
}

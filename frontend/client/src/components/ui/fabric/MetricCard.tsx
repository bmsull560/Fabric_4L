import { FabricCard } from "./FabricCard";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

export interface MetricCardProps {
  label: string;
  value: string;
  trend?: { value: string; positive: boolean | null };
  className?: string;
}

export function MetricCard({ label, value, trend, className }: MetricCardProps) {
  return (
    <FabricCard padding="normal" shadow="sm" className={cn("h-full", className)}>
      <p className="text-[12px] font-medium text-muted-foreground uppercase tracking-wider">
        {label}
      </p>
      <p className="text-[28px] font-bold tracking-[-0.02em] text-foreground mt-1 leading-[1.1]">
        {value}
      </p>
      {trend && (
        <div className={cn("flex items-center gap-1 mt-2 text-[12px] font-medium",
          trend.positive === true && "text-emerald-600 dark:text-emerald-400",
          trend.positive === false && "text-red-600 dark:text-red-400",
          trend.positive === null && "text-muted-foreground"
        )}>
          {trend.positive === true && <TrendingUp className="h-3.5 w-3.5" />}
          {trend.positive === false && <TrendingDown className="h-3.5 w-3.5" />}
          {trend.positive === null && <Minus className="h-3.5 w-3.5" />}
          {trend.value}
        </div>
      )}
    </FabricCard>
  );
}

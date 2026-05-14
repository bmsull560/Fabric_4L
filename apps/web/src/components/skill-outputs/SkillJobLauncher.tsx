/**
 * SkillJobLauncher — Form for launching a Layer 1 skill job.
 *
 * UI Contract (Data):
 *   - `variant` : "licensing_company" | "prospect_research"
 *   - `targetId` : ScrapingTarget ID to crawl (required)
 *   - `onSuccess` : callback with the created SkillJobResponse
 *   - `onCancel` : optional cancel callback
 *
 * UI Contract (Rendering):
 *   - Licensing company variant: company name + optional company ID
 *   - Prospect research variant: account name + optional account ID
 *   - Submit button shows loading state while mutation is in flight
 *   - Inline error display on failure
 *   - Follows existing form patterns from AccountIntakeModal
 */
import { useState } from 'react';
import { Building2, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  useCreateLicensingCompanyIntakeJob,
  useCreateProspectResearchJob,
  type SkillJobResponse,
} from '@/hooks/useSkillJobs';

export type SkillJobVariant = 'licensing_company' | 'prospect_research';

export interface SkillJobLauncherProps {
  variant: SkillJobVariant;
  targetId: string;
  onSuccess?: (job: SkillJobResponse) => void;
  onCancel?: () => void;
  className?: string;
}

export function SkillJobLauncher({
  variant,
  targetId,
  onSuccess,
  onCancel,
  className,
}: SkillJobLauncherProps) {
  const [primaryName, setPrimaryName] = useState('');
  const [secondaryId, setSecondaryId] = useState('');
  const [error, setError] = useState<string | null>(null);

  const licenseIntake = useCreateLicensingCompanyIntakeJob();
  const prospectResearch = useCreateProspectResearchJob();

  const isPending = licenseIntake.isPending || prospectResearch.isPending;

  const isLicensing = variant === 'licensing_company';
  const primaryLabel = isLicensing ? 'Company name' : 'Account name';
  const secondaryLabel = isLicensing ? 'Company ID (optional)' : 'Account ID (optional)';
  const primaryPlaceholder = isLicensing ? 'e.g. Allego' : 'e.g. Acme Manufacturing';
  const secondaryPlaceholder = isLicensing ? 'e.g. allego-001' : 'e.g. acme-001';

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!primaryName.trim()) {
      setError(`${primaryLabel} is required`);
      return;
    }

    try {
      if (isLicensing) {
        const result = await licenseIntake.mutateAsync({
          target_id: targetId,
          company_name: primaryName.trim(),
          company_id: secondaryId.trim() || undefined,
        });
        onSuccess?.(result);
      } else {
        const result = await prospectResearch.mutateAsync({
          target_id: targetId,
          account_name: primaryName.trim(),
          account_id: secondaryId.trim() || undefined,
        });
        onSuccess?.(result);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create job');
    }
  }

  return (
    <form onSubmit={handleSubmit} className={cn('space-y-4', className)}>
      <div className="space-y-1">
        <label className="text-xs font-medium text-foreground" htmlFor="skill-primary-name">
          {primaryLabel}
        </label>
        <div className="relative">
          <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
          <input
            id="skill-primary-name"
            type="text"
            value={primaryName}
            onChange={(e) => setPrimaryName(e.target.value)}
            placeholder={primaryPlaceholder}
            disabled={isPending}
            className={cn(
              'w-full pl-9 pr-3 py-2 text-sm rounded-lg border bg-background',
              'placeholder:text-muted-foreground/60',
              'focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'border-border',
            )}
          />
        </div>
      </div>

      <div className="space-y-1">
        <label className="text-xs font-medium text-foreground" htmlFor="skill-secondary-id">
          {secondaryLabel}
        </label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
          <input
            id="skill-secondary-id"
            type="text"
            value={secondaryId}
            onChange={(e) => setSecondaryId(e.target.value)}
            placeholder={secondaryPlaceholder}
            disabled={isPending}
            className={cn(
              'w-full pl-9 pr-3 py-2 text-sm rounded-lg border bg-background',
              'placeholder:text-muted-foreground/60',
              'focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'border-border',
            )}
          />
        </div>
      </div>

      {error && (
        <p className="text-xs text-destructive" role="alert">
          {error}
        </p>
      )}

      <div className="flex items-center gap-2 pt-1">
        {onCancel && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onCancel}
            disabled={isPending}
          >
            Cancel
          </Button>
        )}
        <Button
          type="submit"
          size="sm"
          disabled={isPending || !primaryName.trim()}
          className="ml-auto"
        >
          {isPending ? 'Starting…' : isLicensing ? 'Start intake' : 'Start research'}
        </Button>
      </div>
    </form>
  );
}

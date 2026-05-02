import * as React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Radar, Building2, BrainCircuit, GitFork, Database, Calculator, FileText, ChevronRight, Sparkles, LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useWorkflowStore } from '../store/workflowStore';
import { WORKFLOW_STEPS } from '../types';

type IconName = 'Radar' | 'Building2' | 'BrainCircuit' | 'GitFork' | 'Database' | 'Calculator' | 'FileText';

const iconMap: Record<IconName, LucideIcon> = {
  Radar, Building2, BrainCircuit, GitFork, Database, Calculator, FileText,
};

/** Safely get icon component by name, fallback to Sparkles */
function getIcon(name: string): LucideIcon {
  return (iconMap as Record<string, LucideIcon>)[name] || Sparkles;
}

export function WorkflowLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation().pathname;
  const { sessionId, initSession } = useWorkflowStore();

  React.useEffect(() => {
    if (!sessionId) initSession();
  }, [sessionId, initSession]);

  const currentStepIndex = WORKFLOW_STEPS.findIndex(s => location === s.path || location.startsWith(s.path + '/'));

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h1 className="text-sm font-semibold text-foreground">Workflow</h1>
                <p className="text-[10px] text-muted-foreground">Guided value-case creation</p>
              </div>
            </div>

            <div className="hidden md:flex items-center gap-1">
              {WORKFLOW_STEPS.map((step, idx) => (
                <React.Fragment key={step.path}>
                  <Link to={step.path}>
                    <div className={cn(
                      'flex items-center gap-2 px-2 py-1 rounded-lg cursor-pointer transition-colors',
                      idx === currentStepIndex ? 'bg-primary/10' : 'hover:bg-muted'
                    )}>
                      {React.createElement(getIcon(step.icon), {
                        className: cn('w-4 h-4', idx <= currentStepIndex ? 'text-primary' : 'text-muted-foreground')
                      })}
                      <span className={cn('text-xs font-medium hidden lg:block', idx === currentStepIndex ? 'text-foreground' : 'text-muted-foreground')}>
                        {step.label}
                      </span>
                    </div>
                  </Link>
                  {idx < WORKFLOW_STEPS.length - 1 && <ChevronRight className="w-4 h-4 text-muted-foreground/40" />}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}

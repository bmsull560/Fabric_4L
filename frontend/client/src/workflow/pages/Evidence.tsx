import { useCallback } from 'react';
import { useLocation } from 'wouter';
import { Database, ArrowRight, CheckCircle2, XCircle } from 'lucide-react';
import { StepCard } from '../components/StepCard';
import { WorkflowLayout } from '../components/WorkflowLayout';
import { useWorkflowStore } from '../store/workflowStore';
import { Button } from '@/components/ui/button';
import { STEPS } from '../constants';

interface EvidenceItem {
  id: string;
  claim: string;
  verified: boolean;
  source: string;
}

const MOCK_EVIDENCE: EvidenceItem[] = [
  { id: '1', claim: '15% downtime reduction achieved at similar facilities', verified: true, source: 'Industry benchmark' },
  { id: '2', claim: 'Average implementation timeline: 6 months', verified: true, source: 'Case studies' },
  { id: '3', claim: 'ROI typically exceeds 300% within 24 months', verified: false, source: 'Projected model' },
];

export default function Evidence() {
  const [, navigate] = useLocation();
  const { setCurrentStep } = useWorkflowStore();

  const handleContinue = useCallback(() => {
    setCurrentStep(STEPS.CALCULATOR);
    navigate('/workflow/calculator');
  }, [setCurrentStep, navigate]);

  return (
    <WorkflowLayout>
      <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Evidence Matching</h1>
        <p className="text-muted-foreground mt-1">Verify claims with supporting evidence.</p>
      </div>

      <StepCard title="Evidence Claims" description="Matched evidence from knowledge base">
        <div className="space-y-3">
          {MOCK_EVIDENCE.map((ev) => (
            <div key={ev.id} className="flex items-start gap-3 p-4 border border-border rounded-lg bg-card">
              <div className={`mt-0.5 ${ev.verified ? 'text-emerald-500' : 'text-muted-foreground'}`}>
                {ev.verified ? <CheckCircle2 className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
              </div>
              <div className="flex-1">
                <p className="text-foreground">{ev.claim}</p>
                <p className="text-xs text-muted-foreground mt-1">Source: {ev.source}</p>
              </div>
              <span className={`text-xs px-2 py-1 rounded ${ev.verified ? 'bg-emerald-500/10 text-emerald-500' : 'bg-muted text-muted-foreground'}`}>
                {ev.verified ? 'Verified' : 'Unverified'}
              </span>
            </div>
          ))}
        </div>
      </StepCard>

      <div className="flex justify-end mt-6">
        <Button onClick={handleContinue} className="flex items-center gap-2">
          Continue to Calculator <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
      </div>
    </WorkflowLayout>
  );
}

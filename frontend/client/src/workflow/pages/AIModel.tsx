import { useCallback } from 'react';
import { useLocation } from 'wouter';
import { BrainCircuit, ArrowRight } from 'lucide-react';
import { StepCard } from '../components/StepCard';
import { WorkflowLayout } from '../components/WorkflowLayout';
import { useWorkflowStore } from '../store/workflowStore';
import { Button } from '@/components/ui/button';
import { STEPS } from '../constants';

interface Hypothesis {
  title: string;
  impact: string;
  confidence: number;
}

const MOCK_HYPOTHESES: Hypothesis[] = [
  { title: 'Reduce machine downtime by 15%', impact: '$3.2M annually', confidence: 85 },
  { title: 'Optimize inventory turnover', impact: '$2.1M annually', confidence: 78 },
  { title: 'Streamline quality workflows', impact: '$1.8M annually', confidence: 72 },
];

export default function AIModel() {
  const [, navigate] = useLocation();
  const { setCurrentStep } = useWorkflowStore();

  const handleContinue = useCallback(() => {
    setCurrentStep(STEPS.DRIVER_TREE);
    navigate('/workflow/driver-tree');
  }, [setCurrentStep, navigate]);

  return (
    <WorkflowLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-foreground">AI Model Generation</h1>
          <p className="text-muted-foreground mt-1">AI-generated hypotheses for value creation.</p>
        </div>

        <StepCard title="Generated Hypotheses" description="AI-suggested value creation opportunities">
          <div className="space-y-3">
            {[
              { title: 'Reduce machine downtime by 15%', impact: '$3.2M annually', confidence: 85 },
              { title: 'Optimize inventory turnover', impact: '$2.1M annually', confidence: 78 },
              { title: 'Streamline quality workflows', impact: '$1.8M annually', confidence: 72 },
            ].map((h, i) => (
              <div key={i} className="p-4 border border-border rounded-lg bg-card">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-foreground">{h.title}</p>
                    <p className="text-sm text-muted-foreground mt-1">{h.impact}</p>
                  </div>
                  <span className="text-xs font-medium px-2 py-1 bg-primary/10 text-primary rounded">
                    {h.confidence}% confidence
                  </span>
                </div>
              </div>
            ))}
          </div>
        </StepCard>

        <div className="flex justify-end mt-6">
          <Button onClick={handleContinue} className="flex items-center gap-2">
            Continue to Driver Tree <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </WorkflowLayout>
  );
}

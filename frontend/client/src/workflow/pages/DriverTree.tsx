import { useCallback, useState } from 'react';
import { useLocation } from 'wouter';
import { GitFork, ArrowRight, CheckCircle2 } from 'lucide-react';
import { StepCard } from '../components/StepCard';
import { WorkflowLayout } from '../components/WorkflowLayout';
import { useWorkflowStore } from '../store/workflowStore';
import { Button } from '@/components/ui/button';
import { STEPS } from '../constants';

const MOCK_TREES = [
  { id: '1', name: 'Manufacturing Efficiency', drivers: 8, totalValue: '$14.2M' },
  { id: '2', name: 'Supply Chain Optimization', drivers: 6, totalValue: '$8.7M' },
  { id: '3', name: 'Quality & Compliance', drivers: 5, totalValue: '$5.3M' },
];

export default function DriverTree() {
  const [, navigate] = useLocation();
  const { setSelectedTreeId, setCurrentStep } = useWorkflowStore();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const handleContinue = useCallback(() => {
    if (!selectedId) return;
    setSelectedTreeId(selectedId);
    setCurrentStep(STEPS.EVIDENCE);
    navigate('/workflow/evidence');
  }, [selectedId, setSelectedTreeId, setCurrentStep, navigate]);

  return (
    <WorkflowLayout>
      <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Value Driver Tree</h1>
        <p className="text-muted-foreground mt-1">Select a driver tree structure for your value case.</p>
      </div>

      <StepCard title="Available Driver Trees" description="Choose the most relevant structure">
        <div className="grid gap-3">
          {MOCK_TREES.map((tree) => (
            <button
              key={tree.id}
              onClick={() => setSelectedId(tree.id)}
              className={`flex items-center justify-between p-4 rounded-xl border transition-all text-left ${
                selectedId === tree.id
                  ? 'border-primary bg-primary/5'
                  : 'border-border bg-card hover:border-primary/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  selectedId === tree.id ? 'bg-primary text-primary-foreground' : 'bg-muted'
                }`}>
                  {selectedId === tree.id ? <CheckCircle2 className="w-5 h-5" /> : <GitFork className="w-5 h-5" />}
                </div>
                <div>
                  <p className="font-medium text-foreground">{tree.name}</p>
                  <p className="text-xs text-muted-foreground">{tree.drivers} value drivers</p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-semibold text-primary">{tree.totalValue}</p>
                <p className="text-xs text-muted-foreground">potential value</p>
              </div>
            </button>
          ))}
        </div>
      </StepCard>

      <div className="flex justify-end mt-6">
        <Button onClick={handleContinue} disabled={!selectedId} className="flex items-center gap-2">
          Continue to Evidence <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
      </div>
    </WorkflowLayout>
  );
}

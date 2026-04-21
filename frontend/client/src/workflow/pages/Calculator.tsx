import { useState, useCallback, useMemo } from 'react';
import { useLocation } from 'wouter';
import { Calculator as CalcIcon, ArrowRight, DollarSign } from 'lucide-react';
import { StepCard } from '../components/StepCard';
import { WorkflowLayout } from '../components/WorkflowLayout';
import { useWorkflowStore } from '../store/workflowStore';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { STEPS } from '../constants';

/** Base value for calculations (in millions) */
const BASE_VALUE_MILLIONS = 14.2;

/** Maximum improvement percentage for slider */
const MAX_IMPROVEMENT_PERCENT = 50;

export default function Calculator() {
  const [, navigate] = useLocation();
  const { setGeneratedCaseId, setCurrentStep } = useWorkflowStore();
  const [improvement, setImprovement] = useState(15);
  const [calculated, setCalculated] = useState(false);

  const handleCalculate = useCallback(() => {
    setCalculated(true);
  }, []);

  const handleContinue = useCallback(() => {
    setGeneratedCaseId(`case_${Date.now()}`);
    setCurrentStep(STEPS.VALUE_CASE);
    navigate('/workflow/value-case');
  }, [setGeneratedCaseId, setCurrentStep, navigate]);

  const annualValue = useMemo(
    () => Math.round(BASE_VALUE_MILLIONS * (improvement / 100) * 10) / 10,
    [improvement]
  );

  return (
    <WorkflowLayout>
      <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Value Calculator</h1>
        <p className="text-muted-foreground mt-1">Model financial scenarios and calculate total value.</p>
      </div>

      <StepCard title="Scenario Modeling" description="Adjust parameters to model value creation">
        <div className="space-y-6">
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-medium">Efficiency Improvement</label>
              <span className="text-sm font-semibold text-primary">{improvement}%</span>
            </div>
            <Slider
              value={[improvement]}
              onValueChange={([v]) => setImprovement(v)}
              max={MAX_IMPROVEMENT_PERCENT}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between mt-2 text-xs text-muted-foreground">
              <span>0%</span>
              <span>{MAX_IMPROVEMENT_PERCENT / 2}%</span>
              <span>{MAX_IMPROVEMENT_PERCENT}%</span>
            </div>
          </div>

          <Button onClick={handleCalculate} className="w-full">
            <CalcIcon className="w-4 h-4 mr-2" /> Calculate Impact
          </Button>

          {calculated && (
            <div className="p-6 bg-primary/5 border border-primary/20 rounded-xl">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-5 h-5 text-primary" />
                <span className="font-semibold text-foreground">Projected Annual Value</span>
              </div>
              <p className="text-3xl font-bold text-primary">${annualValue}M</p>
              <p className="text-sm text-muted-foreground mt-1">
                Based on {improvement}% efficiency improvement
              </p>
            </div>
          )}
        </div>
      </StepCard>

      <div className="flex justify-end mt-6">
        <Button onClick={handleContinue} disabled={!calculated} className="flex items-center gap-2">
          Generate Value Case <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
      </div>
    </WorkflowLayout>
  );
}

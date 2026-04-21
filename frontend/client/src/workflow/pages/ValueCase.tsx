import { FileText, Download, Share2, CheckCircle2 } from 'lucide-react';
import { StepCard } from '../components/StepCard';
import { WorkflowLayout } from '../components/WorkflowLayout';
import { useWorkflowStore } from '../store/workflowStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface CaseSection {
  title: string;
  content: string;
}

const CASE_SECTIONS: CaseSection[] = [
  { title: 'Executive Summary', content: 'Manufacturing efficiency improvements through automated workflow orchestration...' },
  { title: 'Business Problem', content: 'Current manufacturing operations face significant downtime...' },
  { title: 'Proposed Solution', content: 'Implementation of intelligent automation platform...' },
  { title: 'Value Drivers', content: 'Three primary value drivers identified: downtime reduction...' },
  { title: 'Financial Model', content: 'Conservative estimate based on 15% efficiency improvement...' },
];

const TOTAL_VALUE_DISPLAY = '$14.2M';

export default function ValueCase() {
  const { prospect, generatedCaseId } = useWorkflowStore();

  return (
    <WorkflowLayout>
      <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Generated Value Case</h1>
        <p className="text-muted-foreground mt-1">Review and export your complete value case.</p>
      </div>

      <StepCard>
        <div className="flex items-start justify-between mb-6 pb-6 border-b border-border">
          <div>
            <h2 className="text-xl font-bold text-foreground">Value Case: {prospect?.companyName}</h2>
            <p className="text-muted-foreground mt-1">Prepared for {prospect?.contactName}, {prospect?.contactTitle}</p>
            <div className="flex items-center gap-2 mt-3">
              <Badge variant="default" className="flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Complete
              </Badge>
              <span className="text-xs text-muted-foreground">Case ID: {generatedCaseId}</span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-primary">{TOTAL_VALUE_DISPLAY}</p>
            <p className="text-sm text-muted-foreground">annual value opportunity</p>
          </div>
        </div>

        <div className="space-y-4">
          {CASE_SECTIONS.map((section, i) => (
            <div key={i} className="p-4 border border-border rounded-lg bg-muted/30">
              <h3 className="font-semibold text-foreground mb-2">{section.title}</h3>
              <p className="text-sm text-muted-foreground">{section.content}</p>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-3 mt-6 pt-6 border-t border-border">
          <Button className="flex items-center gap-2">
            <Download className="w-4 h-4" /> Export PDF
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Share2 className="w-4 h-4" /> Share
          </Button>
          <Button variant="ghost">Save to Library</Button>
        </div>
      </StepCard>
      </div>
    </WorkflowLayout>
  );
}

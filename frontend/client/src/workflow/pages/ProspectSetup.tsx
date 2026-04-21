import { useState, useCallback } from 'react';
import { useLocation } from 'wouter';
import { Building2, Sparkles, Briefcase, Globe, Users } from 'lucide-react';
import { StepCard } from '../components/StepCard';
import { WorkflowLayout } from '../components/WorkflowLayout';
import { useWorkflowStore } from '../store/workflowStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ANALYSIS_DELAY_MS, VALIDATION, STEPS } from '../constants';

interface ValidationError {
  field: string;
  message: string;
}

function validateProspectInput(company: string, contact: string): ValidationError | null {
  const trimmedCompany = company.trim();
  const trimmedContact = contact.trim();

  if (trimmedCompany.length < VALIDATION.MIN_COMPANY_NAME_LENGTH) {
    return { field: 'company', message: `Company name must be at least ${VALIDATION.MIN_COMPANY_NAME_LENGTH} characters` };
  }
  if (trimmedCompany.length > VALIDATION.MAX_COMPANY_NAME_LENGTH) {
    return { field: 'company', message: `Company name must be less than ${VALIDATION.MAX_COMPANY_NAME_LENGTH} characters` };
  }
  if (trimmedContact.length < VALIDATION.MIN_CONTACT_NAME_LENGTH) {
    return { field: 'contact', message: `Contact name must be at least ${VALIDATION.MIN_CONTACT_NAME_LENGTH} characters` };
  }
  if (trimmedContact.length > VALIDATION.MAX_CONTACT_NAME_LENGTH) {
    return { field: 'contact', message: `Contact name must be less than ${VALIDATION.MAX_CONTACT_NAME_LENGTH} characters` };
  }
  return null;
}

export default function ProspectSetup() {
  const [, navigate] = useLocation();
  const { setProspect, setCurrentStep } = useWorkflowStore();
  
  const [company, setCompany] = useState('');
  const [contact, setContact] = useState('');
  const [title, setTitle] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<ValidationError | null>(null);

  const handleGenerate = useCallback(() => {
    const validationError = validateProspectInput(company, contact);
    if (validationError) {
      setError(validationError);
      return;
    }
    
    setError(null);
    setIsAnalyzing(true);
    
    const trimmedTitle = title.trim();
    
    setProspect({
      companyId: `temp_${Date.now()}`,
      companyName: company.trim(),
      contactName: contact.trim(),
      contactTitle: trimmedTitle.length > 0 ? trimmedTitle : undefined,
    });
    
    // Simulate async analysis with cleanup
    const timer = setTimeout(() => {
      setCurrentStep(STEPS.INTELLIGENCE);
      navigate('/workflow/intelligence');
    }, ANALYSIS_DELAY_MS);
    
    return () => clearTimeout(timer);
  }, [company, contact, title, setProspect, setCurrentStep, navigate]);

  return (
    <WorkflowLayout>
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-10">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Generate a Value Model</h1>
          <p className="text-muted-foreground">Enter prospect details. Workflow will research, analyze, and auto-generate a tailored value model.</p>
        </div>

        <StepCard>
          <div className="space-y-5">
            <div className="px-8 py-6 border-b border-border/60 bg-muted/50 -mx-6 -mt-6 mb-5">
              <h2 className="font-semibold text-card-foreground flex items-center gap-2">
                <Building2 className="w-4 h-4 text-primary" />
                Prospect Information
              </h2>
              <p className="text-xs text-muted-foreground mt-1">Minimum required. We'll enrich the rest automatically.</p>
            </div>

            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertDescription>{error.message}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-4">
              <div>
                <Label className="flex items-center gap-1.5">
                  Company Name
                  <span className="text-[10px] px-1.5 py-0.5 bg-destructive/10 text-destructive rounded font-medium">Required</span>
                </Label>
                <Input
                  value={company}
                  onChange={(e) => {
                    setCompany(e.target.value);
                    if (error?.field === 'company') setError(null);
                  }}
                  placeholder="e.g. Meridian Automotive Components"
                  className={`mt-1.5 ${error?.field === 'company' ? 'border-destructive' : ''}`}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="flex items-center gap-1.5">
                    Main Contact
                    <span className="text-[10px] px-1.5 py-0.5 bg-destructive/10 text-destructive rounded font-medium">Required</span>
                  </Label>
                  <Input
                    value={contact}
                    onChange={(e) => {
                      setContact(e.target.value);
                      if (error?.field === 'contact') setError(null);
                    }}
                    placeholder="e.g. Patricia Chen"
                    className={`mt-1.5 ${error?.field === 'contact' ? 'border-destructive' : ''}`}
                  />
                </div>
                <div>
                  <Label>Contact Title</Label>
                  <Input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. VP Manufacturing Operations"
                    className="mt-1.5"
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 pt-2">
              {[
                { icon: Globe, label: 'Company enrichment ready' },
                { icon: Briefcase, label: 'CRM integration active' },
                { icon: Users, label: 'Stakeholder mapping enabled' },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-2 px-3 py-2.5 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                  <item.icon className="w-4 h-4 text-emerald-500 shrink-0" />
                  <span className="text-[11px] text-emerald-500 font-medium">{item.label}</span>
                </div>
              ))}
            </div>

            <div className="flex items-center gap-4 pt-4">
              <Button
                onClick={handleGenerate}
                disabled={!company || !contact || isAnalyzing}
                className="flex items-center gap-2"
              >
                {isAnalyzing ? (
                  <>
                    <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <><Sparkles className="w-4 h-4" /> Generate Value Model</>
                )}
              </Button>
              <Button variant="ghost" className="text-muted-foreground hover:text-foreground">Save as draft</Button>
            </div>
          </div>
        </StepCard>
      </div>
    </WorkflowLayout>
  );
}

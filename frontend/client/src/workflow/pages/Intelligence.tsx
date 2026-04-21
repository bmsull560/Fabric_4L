import { useState, useCallback, useRef, useEffect } from 'react';
import { useLocation } from 'wouter';
import { Search, Building2, ArrowRight, Database } from 'lucide-react';
import { StepCard } from '../components/StepCard';
import { WorkflowLayout } from '../components/WorkflowLayout';
import { useWorkflowStore } from '../store/workflowStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { SIMULATION, STEPS } from '../constants';
import type { EnrichedEntity } from '../types';

export default function Intelligence() {
  const [, navigate] = useLocation();
  const { prospect, setEnrichedEntities, setCurrentStep } = useWorkflowStore();
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [entities, setEntities] = useState<EnrichedEntity[]>([]);
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleSearch = useCallback(() => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery) return;

    setIsSearching(true);

    // Cleanup any pending timer
    if (searchTimerRef.current) {
      clearTimeout(searchTimerRef.current);
    }

    // Simulate API call - will be replaced with real useEntitySearch
    searchTimerRef.current = setTimeout(() => {
      const mockEntities: EnrichedEntity[] = [
        { id: '1', name: 'Manufacturing Operations', type: 'Process', confidence: 0.92 },
        { id: '2', name: 'Supply Chain', type: 'Domain', confidence: 0.88 },
        { id: '3', name: 'Quality Control', type: 'Function', confidence: 0.85 },
      ];
      setEntities(mockEntities);
      setEnrichedEntities(mockEntities);
      setIsSearching(false);
    }, SIMULATION.SEARCH_DELAY_MS);
  }, [query, setEnrichedEntities]);

  const handleContinue = useCallback(() => {
    setCurrentStep(STEPS.AI_MODEL);
    navigate('/workflow/ai-model');
  }, [setCurrentStep, navigate]);

  // Cleanup pending timers on unmount
  useEffect(() => {
    return () => {
      if (searchTimerRef.current) {
        clearTimeout(searchTimerRef.current);
      }
    };
  }, []);

  return (
    <WorkflowLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-foreground">Intelligence & Enrichment</h1>
          <p className="text-muted-foreground mt-1">Research {prospect?.companyName || 'the prospect'} and discover relevant entities.</p>
        </div>

        <StepCard title="Entity Discovery" description="Search the knowledge graph for relevant entities">
          <div className="flex gap-3 mb-6">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search entities, domains, processes..."
                className="pl-10"
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
          </div>
            <Button onClick={handleSearch} disabled={isSearching || !query}>
              {isSearching ? 'Searching...' : 'Search'}
            </Button>
        </div>

        {entities.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-foreground mb-3">Discovered Entities</h3>
            {entities.map((entity) => (
              <div key={entity.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border border-border">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Building2 className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{entity.name}</p>
                    <p className="text-xs text-muted-foreground">{entity.type}</p>
                  </div>
                </div>
                <Badge variant={entity.confidence > 0.9 ? 'default' : 'secondary'}>
                  {(entity.confidence * 100).toFixed(0)}%
                </Badge>
              </div>
            ))}
          </div>
        )}
      </StepCard>

      <div className="flex justify-end mt-6 gap-3">
        <Button onClick={handleContinue} disabled={entities.length === 0} className="flex items-center gap-2">
          Continue to AI Model <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
      </div>
    </WorkflowLayout>
  );
}

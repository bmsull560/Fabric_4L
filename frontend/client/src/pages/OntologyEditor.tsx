/**
 * OntologyEditor — Visual ontology schema editing environment
 *
 * Three-panel layout matching the wireframe:
 * - Left: Type Tree (hierarchical type browser)
 * - Center: Property Editor (type definition editing)
 * - Right: Relationship Map (visual relationship graph)
 *
 * Features:
 * - Add/Edit/Delete type definitions
 * - Add/Edit/Delete properties
 * - Visual relationship management
 * - Validate and Publish workflow
 * - Undo/Redo support
 * - Import/Export ontology
 */

import { useEffect, useCallback, useState } from 'react';
import { Check, X, AlertCircle, Undo2, Redo2, Download, Upload, Plus, GitBranch, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';
import { PageHeader, Btn, SectionCard } from '@/components/WfPrimitives';
import { TypeTree, PropertyEditor, RelationshipMap } from '@/components/ontology';
import { useOntologySchema, useValidateOntology, usePublishOntology, useImportOntology } from '@/hooks/useOntology';
import useOntologyStore from '@/stores/ontologyStore';
import { toast } from 'sonner';

export default function OntologyEditor() {
  // Data fetching
  const { data: schema, isLoading, error } = useOntologySchema();

  // Mutations
  const validateMutation = useValidateOntology();
  const publishMutation = usePublishOntology();
  const importMutation = useImportOntology();

  // Local state
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [importJson, setImportJson] = useState('');

  // Store state and actions
  const {
    selectedTypeId,
    hasUnsavedChanges,
    canUndo,
    canRedo,
    validationResult,
    isValidating,
    isPublishing,
    showRelationshipMap,
    draftTypes,
    draftRelationships,
    initializeFromSchema,
    selectType,
    undo,
    redo,
    setValidationResult,
    setIsValidating,
    setIsPublishing,
    toggleRelationshipMap,
    setImportDialogOpen,
  } = useOntologyStore();

  // Initialize store when schema loads
  useEffect(() => {
    if (schema) {
      initializeFromSchema(schema.types, schema.relationships);
    }
  }, [schema, initializeFromSchema]);

  // Get selected type
  const selectedType = selectedTypeId
    ? draftTypes.get(selectedTypeId) || null
    : null;

  // Convert draft maps to arrays for components
  const types = Array.from(draftTypes.values());
  const relationships = Array.from(draftRelationships.values());

  // Handle validate
  const handleValidate = useCallback(async () => {
    if (!schema) return;

    setIsValidating(true);
    try {
      const currentSchema = {
        ...schema,
        types,
        relationships,
      };
      const result = await validateMutation.mutateAsync(currentSchema);
      setValidationResult(result);

      if (result.valid) {
        toast.success('Ontology is valid', {
          description: result.warnings.length > 0
            ? `${result.warnings.length} warning${result.warnings.length > 1 ? 's' : ''} found`
            : 'No issues found',
        });
      } else {
        toast.error('Validation failed', {
          description: `${result.errors.length} error${result.errors.length > 1 ? 's' : ''} found`,
        });
      }
    } catch (err) {
      toast.error('Validation failed', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    } finally {
      setIsValidating(false);
    }
  }, [schema, types, relationships, validateMutation, setValidationResult, setIsValidating]);

  // Handle publish
  const handlePublish = useCallback(async () => {
    if (!schema) return;

    // First validate
    await handleValidate();
    if (validationResult && !validationResult.valid) {
      toast.error('Cannot publish', { description: 'Please fix validation errors first' });
      return;
    }

    setIsPublishing(true);
    try {
      const currentSchema = {
        ...schema,
        types,
        relationships,
      };
      const result = await publishMutation.mutateAsync(currentSchema);
      toast.success('Ontology published', {
        description: `Version ${result.version} published at ${new Date(result.publishedAt).toLocaleString()}`,
      });
    } catch (err) {
      toast.error('Publish failed', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    } finally {
      setIsPublishing(false);
    }
  }, [schema, types, relationships, validationResult, publishMutation, setIsPublishing, handleValidate]);

  // Handle import
  const handleImport = useCallback(async () => {
    if (!importJson.trim()) {
      toast.error('No data to import');
      return;
    }

    try {
      const importedSchema = await importMutation.mutateAsync(importJson);
      initializeFromSchema(importedSchema.types, importedSchema.relationships);
      setShowImportDialog(false);
      setImportJson('');
      toast.success('Ontology imported successfully');
    } catch (err) {
      toast.error('Import failed', {
        description: err instanceof Error ? err.message : 'Invalid JSON',
      });
    }
  }, [importJson, importMutation, initializeFromSchema]);

  // Loading state
  if (isLoading) {
    return (
      <div className="p-6">
        <PageHeader
          breadcrumbs={[{ label: "Discover" }, { label: "Knowledge" }, { label: "Ontology" }]}
          title="Ontology Editor"
          subtitle="Define and manage the knowledge model ontology"
        />
        <div className="flex items-center justify-center h-[400px]">
          <div className="w-8 h-8 rounded-full border-2 border-neutral-300 border-t-neutral-700 animate-spin" />
          <span className="ml-3 text-sm text-muted-foreground">Loading ontology schema...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-6">
        <PageHeader
          breadcrumbs={[{ label: "Discover" }, { label: "Knowledge" }, { label: "Ontology" }]}
          title="Ontology Editor"
          subtitle="Define and manage the knowledge model ontology"
        />
        <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-destructive mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-destructive">Failed to load ontology</h3>
              <p className="text-sm text-destructive/80 mt-1">
                {error instanceof Error ? error.message : 'Unknown error'}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 h-[calc(100vh-64px)] flex flex-col">
      {/* Header */}
      <PageHeader
        breadcrumbs={[{ label: "Discover" }, { label: "Knowledge" }, { label: "Ontology" }]}
        title="Ontology Editor"
        subtitle="Define and manage the knowledge model ontology"
        actions={
          <div className="flex items-center gap-2">
            {/* Validation indicator */}
            {validationResult && (
              <div className={cn(
                "flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-medium",
                validationResult.valid
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-destructive/10 text-destructive"
              )}>
                {validationResult.valid ? <Check size={12} /> : <X size={12} />}
                {validationResult.valid ? 'Valid' : `${validationResult.errors.length} errors`}
              </div>
            )}

            {/* Undo/Redo */}
            <div className="flex items-center gap-1 border-r border-border pr-2 mr-1">
              <Btn variant="ghost" onClick={undo} disabled={!canUndo}>
                <Undo2 size={12} />
              </Btn>
              <Btn variant="ghost" onClick={redo} disabled={!canRedo}>
                <Redo2 size={12} />
              </Btn>
            </div>

            {/* Validate button */}
            <Btn variant="outline" onClick={handleValidate} disabled={isValidating}>
              {isValidating ? (
                <>
                  <div className="w-3 h-3 rounded-full border border-current border-t-transparent animate-spin mr-1" />
                  Validating...
                </>
              ) : (
                <>
                  <Shield size={12} className="mr-1" />
                  Validate
                </>
              )}
            </Btn>

            {/* Publish button */}
            <Btn
              variant="primary"
              onClick={handlePublish}
              disabled={isPublishing || !hasUnsavedChanges}
            >
              {isPublishing ? (
                <>
                  <div className="w-3 h-3 rounded-full border border-current border-t-transparent animate-spin mr-1" />
                  Publishing...
                </>
              ) : (
                <>
                  <Check size={12} className="mr-1" />
                  Publish
                </>
              )}
            </Btn>
          </div>
        }
      />

      {/* Toolbar */}
      <div className="flex items-center gap-2 mb-4 py-2 border-b border-border">
        <Btn variant="ghost" onClick={() => setShowImportDialog(true)}>
          <Plus size={12} className="mr-1" />
          Add Relation
        </Btn>
        <Btn variant="ghost" onClick={() => setShowImportDialog(true)}>
          <Upload size={12} className="mr-1" />
          Import
        </Btn>
        <div className="flex-1" />
        <Btn variant="ghost" onClick={undo} disabled={!canUndo}>
          <Undo2 size={12} className="mr-1" />
          Undo
        </Btn>
        <Btn variant="ghost" onClick={redo} disabled={!canRedo}>
          <Redo2 size={12} className="mr-1" />
          Redo
        </Btn>
        <Btn variant="ghost" onClick={toggleRelationshipMap}>
          <GitBranch size={12} className="mr-1" />
          {showRelationshipMap ? 'Hide Map' : 'Show Map'}
        </Btn>
      </div>

      {/* Three-panel layout */}
      <div className="flex-1 grid gap-4 min-h-0" style={{ gridTemplateColumns: showRelationshipMap ? '280px 1fr 280px' : '280px 1fr' }}>
        {/* Left: Type Tree */}
        <SectionCard noPad className="h-full overflow-hidden">
          <TypeTree types={types} />
        </SectionCard>

        {/* Center: Property Editor */}
        <SectionCard noPad className="h-full overflow-hidden">
          <PropertyEditor type={selectedType} />
        </SectionCard>

        {/* Right: Relationship Map (conditional) */}
        {showRelationshipMap && (
          <SectionCard noPad className="h-full overflow-hidden">
            <RelationshipMap
              types={types}
              relationships={relationships}
              selectedTypeId={selectedTypeId}
              onSelectType={selectType}
            />
          </SectionCard>
        )}
      </div>

      {/* Validation Results Panel */}
      {validationResult && (validationResult.errors.length > 0 || validationResult.warnings.length > 0) && (
        <div className="mt-4 p-3 border rounded-lg bg-muted/30">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle size={14} className={validationResult.errors.length > 0 ? "text-destructive" : "text-amber-500"} />
            <span className="text-[12px] font-semibold">
              {validationResult.errors.length > 0
                ? `${validationResult.errors.length} error${validationResult.errors.length > 1 ? 's' : ''}`
                : `${validationResult.warnings.length} warning${validationResult.warnings.length > 1 ? 's' : ''}`}
            </span>
          </div>
          <div className="space-y-1 max-h-[120px] overflow-y-auto">
            {validationResult.errors.map((error, idx) => (
              <div key={idx} className="flex items-start gap-2 text-[11px] text-destructive">
                <X size={12} className="mt-0.5 shrink-0" />
                <span>{error.message}</span>
              </div>
            ))}
            {validationResult.warnings.map((warning, idx) => (
              <div key={idx} className="flex items-start gap-2 text-[11px] text-amber-600">
                <AlertCircle size={12} className="mt-0.5 shrink-0" />
                <span>{warning.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Import Dialog */}
      {showImportDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded-lg shadow-lg w-[500px] max-w-[90vw]">
            <div className="p-4 border-b border-border">
              <h3 className="text-sm font-semibold">Import Ontology</h3>
              <p className="text-[12px] text-muted-foreground mt-1">
                Paste JSON ontology schema to import
              </p>
            </div>
            <div className="p-4">
              <textarea
                value={importJson}
                onChange={(e) => setImportJson(e.target.value)}
                placeholder={`{\n  "types": [...],\n  "relationships": [...]\n}`}
                rows={10}
                className="w-full px-3 py-2 text-[12px] bg-muted/50 border border-border rounded-md font-mono resize-none"
              />
            </div>
            <div className="p-4 border-t border-border flex justify-end gap-2">
              <Btn variant="ghost" onClick={() => setShowImportDialog(false)}>
                Cancel
              </Btn>
              <Btn variant="primary" onClick={handleImport} disabled={importMutation.isPending}>
                {importMutation.isPending ? 'Importing...' : 'Import'}
              </Btn>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

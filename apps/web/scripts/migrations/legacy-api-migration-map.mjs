#!/usr/bin/env node

const migrationMap = [
  {
    legacy: "WorkflowSchema",
    replacement: "@/api/workflows (canonical workflow schema/types)",
  },
  {
    legacy: "WorkflowExecutionSchema",
    replacement: "@/api/workflows (execution schema/types)",
  },
  {
    legacy: "Workflow (interface)",
    replacement: "@/hooks/useWorkflows (UI-facing workflow types)",
  },
  {
    legacy: "WorkflowExecution (interface)",
    replacement: "generated API clients + DTO/domain mappers",
  },
];

console.log("Legacy API migration map (@/api/legacy -> canonical modules)\n");
for (const { legacy, replacement } of migrationMap) {
  console.log(`- ${legacy} -> ${replacement}`);
}

console.log("\nRemediation order:");
console.log("1) Prefer '@/api/workflows' for workflow API contracts.");
console.log("2) Prefer generated clients for endpoint DTOs.");
console.log("3) Prefer '@/hooks/useWorkflows' for workflow hook abstractions.");

---
name: resolve-value-tree
description: Build complete Value Tree from any starting node
---

# Value Tree Resolver Workflow

Use this workflow to build a complete Value Tree from any starting node.

## Parameters

- `start_node_id`: Starting entity ID (string, required)
- `direction`: UP (to Value Drivers) | DOWN (to Capabilities) | BOTH (default: BOTH)
- `include_formulas`: Boolean - Include mathematical formulas (default: true)

## Steps

1. Identify the starting node
2. Traverse relationships based on direction parameter
3. Build hierarchical tree structure
4. Include formulas if requested
5. Return: Capabilities → Use Cases → Personas → Value Drivers

## Output

Hierarchical tree structure:
- Capabilities → Use Cases → Personas → Value Drivers
- Mathematical formulas (if requested)
- Relationship confidence scores

## Example Use

"Show me the complete value proposition for this capability"

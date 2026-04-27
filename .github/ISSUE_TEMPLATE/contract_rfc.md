---
name: Contract Change RFC
about: Propose a change to the DIL API contracts (OpenAPI or JSON Schema)
title: 'RFC: [Short description of contract change]'
labels: 'contract-rfc, needs-council-review'
assignees: ''
---

# Contract Change Request for Comments (RFC)

## 1. Summary
<!-- Provide a 1-2 sentence summary of the proposed contract change. -->

## 2. Motivation
<!-- Why is this change necessary? What problem does it solve? -->

## 3. Proposed Changes
<!-- Detail the exact changes to the OpenAPI spec or JSON Schema. -->
<!-- Include the endpoint path, method, and schema changes. -->
- **Layer:** [e.g., L1 Ingestion, L3 Knowledge, L4 Agents]
- **Endpoint(s):** [e.g., `POST /api/v1/accounts`]
- **Schema(s):** [e.g., `AccountCreateRequest`]

### Before
```json
// Current schema or endpoint definition
```

### After
```json
// Proposed schema or endpoint definition
```

## 4. Breaking Change Assessment
<!-- Is this a breaking change? (e.g., removing a field, changing a type, adding a required field) -->
- [ ] **Non-breaking:** Safe to deploy without coordinating frontend/backend releases.
- [ ] **Breaking:** Requires coordinated release and migration plan.

### Migration Plan (If Breaking)
<!-- How will existing clients migrate to the new contract? -->

## 5. Security & Governance Impact
<!-- Does this change affect tenant isolation, PII handling, or RBAC? -->
- [ ] Exposes new data fields
- [ ] Changes authentication/authorization requirements
- [ ] Modifies tenant scoping

## 6. Alternatives Considered
<!-- What other approaches did you consider and why were they rejected? -->

---
*Note: All contract RFCs must be approved by the Contract Council before the corresponding PR can be merged.*

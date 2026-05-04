# UI Architecture & Testing Strategy Recommendation

**Date:** April 27, 2026  
**Author:** Manus AI  
**Project:** Fabric_4L Value Studio

This document synthesizes an audit of the `_ui-prototype` directory, an evaluation of the AG-UI Protocol and UI Contracts methodologies, and an assessment of the current Fabric_4L frontend routing and testing infrastructure. It provides a comprehensive recommendation for integrating these concepts into the production application.

## 1. Prototype Design Concepts for Extraction

The `_ui-prototype` contains several high-value design patterns that elevate the application from a standard SaaS dashboard to a true "Agentic UI." These concepts should be extracted and formalized in the main frontend.

### Agentic Co-Pilot Integration
The `AgentMockup.tsx` implementation demonstrates a sophisticated approach to human-AI collaboration. Rather than a simple chat interface, it provides a contextual right-rail that understands the current workspace. The most valuable extractable pattern is the **Process Step Visualization**. When the agent is working, it displays a structured list of steps with `done`, `active`, and `pending` states, providing transparency into the agent's reasoning process. This builds user trust far more effectively than a generic loading spinner.

### Confidence and Provenance Scoring
Throughout the prototype (specifically in `ProspectIntelligence.tsx` and `EvidenceMatch.tsx`), data is rarely presented as absolute truth. Instead, it is accompanied by confidence scores (e.g., "94% match") and provenance indicators (e.g., "AI-inferred" vs. "User-confirmed"). This pattern is critical for enterprise decision-support tools. The `StatusChip` component that visually distinguishes between these states should be extracted into the core design system.

### Scenario Modeling Interface
The `ValueCalculator.tsx` introduces a clean pattern for scenario modeling. It presents three distinct scenarios (Conservative, Expected, Optimistic) as selectable cards that instantly recalculate the underlying value levers. This interaction model is far superior to requiring users to manually adjust individual sliders to see different outcomes, though it preserves the ability to do so via the `ModelInputsTracker` component.

## 2. The AG-UI Protocol Evaluation

The Agent-User Interaction (AG-UI) Protocol offers a standardized, event-based architecture for connecting AI agents to frontend applications [1]. Adopting this protocol would significantly improve the current Fabric_4L implementation.

### Current State vs. AG-UI
Currently, Fabric_4L relies on custom Server-Sent Events (SSE) parsing in `thesysClient.ts` and `useAgentStream.ts`. This ad-hoc approach requires manual string manipulation and custom type definitions for every new agent capability.

AG-UI replaces this with a standardized set of 16 event types categorized into Lifecycle, Text Messages, Tool Calls, and State Management [2].

### Implementation Recommendation
Fabric_4L should adopt the AG-UI protocol for all agent-to-frontend communication. The most immediate benefit will come from implementing the Lifecycle events (`RunStarted`, `StepStarted`, `StepFinished`, `RunFinished`). These map perfectly to the Process Step Visualization identified in the prototype audit. 

Furthermore, AG-UI's State Management events (`STATE_SNAPSHOT` and `STATE_DELTA` using JSON Patch RFC 6902) provide an elegant solution for synchronizing the complex, hierarchical Value Tree models between the backend agent and the frontend SVG canvas [3].

## 3. UI Contracts and Testing Strategy

The concept of "UI Contracts" shifts frontend development from focusing on implementation details to focusing on the agreements between components regarding data, behavior, and rendering assumptions [4].

### Formalizing Flow Contracts
Fabric_4L already utilizes TypeScript interfaces, which serve as strong Data Contracts. However, the application lacks formalized Behavior and Rendering Contracts. A "Flow Contract" mindset requires defining exactly what a component guarantees to output or trigger [5]. 

For example, the `ValueDriverTree` component's contract should explicitly state that it guarantees to emit a specific event payload when a node is dragged, regardless of how the internal SVG manipulation is implemented.

### TDD vs. Route Audit Strategy
The current frontend contains 177 routes defined in `App.tsx`, but only 17 Playwright End-to-End (E2E) tests and 44 unit tests. The canonical `CONTRACT.md` specifies a strict state-machine-driven routing model (Section 2.6), but the current `App.tsx` still uses standard React Router definitions.

**Recommendation: Test-Driven Development (TDD) via UI Contracts**

Rather than performing a manual audit of all 177 routes, the team should adopt a TDD approach grounded in UI Contracts. The strategy should proceed as follows:

1. **Define the Contract:** Before migrating a route or component, write a Playwright test that defines its expected behavior and state transitions.
2. **Ensure Initial Failure:** As per agent workflow testing best practices, the initial state of these newly written tests must be to fail.
3. **Implement to Pass:** Refactor the component or route to satisfy the contract. If the test passes 100%, there must be absolute certainty that the application is functioning as intended.

### The Role of Playwright
Playwright is the ideal tool for enforcing these UI Contracts at the integration level. The existing `.windsurf/skills/playwright/SKILL.md` already establishes excellent patterns for resilient, accessibility-first selectors. 

Playwright should be used to test the *Flow Contracts* of the agentic workflows. For instance, a test should verify that when a user submits a domain in the Command Center, the UI transitions to the loading state, receives the AG-UI `StepStarted` events, and eventually renders the extracted knowledge graph. This tests the contract between the user, the UI, and the agent backend, rather than testing the specific CSS classes used for the loading spinner.

## Conclusion

By extracting the trust-building design patterns from the prototype, standardizing agent communication via the AG-UI protocol, and enforcing component behavior through Playwright-driven UI Contract testing, Fabric_4L can transition from a standard React application to a robust, future-proof Agentic SaaS platform.

## References

[1] AG-UI Protocol Documentation. "The Agent–User Interaction (AG-UI) Protocol." https://docs.ag-ui.com/introduction
[2] AG-UI Protocol Documentation. "Events." https://docs.ag-ui.com/concepts/events
[3] AG-UI Protocol Documentation. "Core architecture." https://docs.ag-ui.com/concepts/architecture
[4] Scripting Soul. "The Hidden Power of UI Contracts: How Great Front-End Devs Keep Their Code Future-Proof." Medium, June 16, 2025.
[5] Scripting Soul. "Rethinking Props: The “Flow Contract” Mindset That Makes You a Better React Developer." Medium, June 17, 2025.

# Value Fabric Wireframes — Design Brainstorm

## Context
This is a wireframe prototype site for an enterprise AI platform (Value Fabric Intelligence Platform).
The audience is product designers, engineers, and stakeholders reviewing the UX architecture.
The goal: communicate layout and information hierarchy clearly, while feeling polished and purposeful.

---

<response>
<probability>0.07</probability>
<idea>

**Design Movement:** Swiss International Typographic Style meets Technical Blueprint

**Core Principles:**
1. Strict greyscale palette — colour used only as semantic signal (entity types)
2. Monospaced type for data/code areas; geometric sans for UI chrome
3. Grid-ruled structure — every element sits on an 8px baseline grid
4. Annotation-first — callout labels and red-line markers visible throughout

**Color Philosophy:**
Background: near-white (#F7F7F5). Surface: white. Borders: #D4D4D0.
Accent ink: #1A1A1A. Four semantic tints only: violet (Capability), cyan (Use Case), amber (Persona), emerald (Value Driver).
No decorative colour — colour = meaning.

**Layout Paradigm:**
Left sidebar (200px fixed) + top breadcrumb bar + scrollable main canvas.
Screens rendered as "frames" with a thin outer border and screen number label — like a design spec sheet.

**Signature Elements:**
- Monospaced terminal block for Extraction Engine log
- SVG graph canvas with labelled nodes
- Thin horizontal rules separating every section

**Interaction Philosophy:**
Click sidebar items to navigate between screens. Hover states are subtle (background tint only).
No animations — this is a spec document, not a demo.

**Animation:** None intentional. Instant transitions.

**Typography System:**
- UI chrome: `IBM Plex Sans` 13px/400 and 600
- Data/code: `IBM Plex Mono` 11px
- Headings: `IBM Plex Sans` 700, 20–28px
</idea>
</response>

<response>
<probability>0.06</probability>
<idea>

**Design Movement:** Brutalist Data Dashboard — raw structure made beautiful

**Core Principles:**
1. Heavy borders and stark contrast — no soft shadows
2. Large, bold metric numbers as visual anchors
3. Exposed grid lines — tables and cards show their structure
4. Functional density — pack information without clutter

**Color Philosophy:**
Background: #FAFAFA. Borders: #222. Primary ink: #111.
Accent: a single electric indigo (#4F46E5) for interactive elements only.
Entity badges use flat, high-contrast fills.

**Layout Paradigm:**
Full-bleed sidebar with thick left border. Content area uses a strict 12-column grid.
Section headers are ALL-CAPS with a thick bottom rule.

**Signature Elements:**
- Oversized stat numbers (48px bold) in metric cards
- Terminal log with thick border frame
- Graph canvas with visible grid lines

**Interaction Philosophy:**
Navigation via sidebar. Active state = inverted (white on black).
Hover = border thickens.

**Animation:** Minimal — only progress bar fill animates.

**Typography System:**
- All UI: `Space Grotesk` 700/500/400
- Code: `JetBrains Mono`
</idea>
</response>

<response>
<probability>0.08</probability>
<idea>

**Design Movement:** Refined Enterprise SaaS — clean, confident, credible

**Core Principles:**
1. Light background with subtle depth via card shadows
2. Clear typographic hierarchy — three distinct text sizes
3. Colour used sparingly: one primary blue for actions, four entity tints for taxonomy
4. Consistent 16px/24px spacing rhythm

**Color Philosophy:**
Background: #F5F5F4 (warm off-white). Surface: #FFFFFF. Border: #E5E5E3.
Primary action: #1D4ED8 (blue-700). Text: #111827 / #6B7280.
Entity tints: violet, cyan, amber, emerald — all at 15% opacity backgrounds.

**Layout Paradigm:**
Fixed 200px sidebar + sticky header (52px) + scrollable main.
Each screen is a self-contained section with a labelled divider.
Top navigation strip lets users jump between screens.

**Signature Elements:**
- Terminal block with syntax-coloured log output
- SVG force-directed graph with colour-coded node types
- Provenance timeline with numbered step dots

**Interaction Philosophy:**
Sidebar navigation with active highlight. Buttons have clear primary/ghost hierarchy.
Tabs switch content panels. Hover states use background tint.

**Animation:** Subtle — cursor blink in terminal, smooth hover transitions.

**Typography System:**
- UI: `Inter` 13–20px, weights 400/500/700
- Code/mono: `JetBrains Mono` 11px
</idea>
</response>

---

## Selected Approach

**Refined Enterprise SaaS** — clean, confident, credible.

This fits the audience (enterprise product stakeholders) and the content (dense data, technical workflows).
The design communicates professionalism without being sterile. The four entity colours provide
semantic clarity throughout all 10 screens without adding visual noise.

# Design

## Source of truth
- Status: Active
- Last refreshed: 2026-07-20
- Primary product surfaces: EMR masking workbench single-page application
- Evidence reviewed: `frontend/src/App.tsx`, `frontend/src/App.css`, `frontend/src/index.css`, `frontend/src/components/*`, `frontend/src/colors.ts`

## Brand
- Personality: Calm, technical, trustworthy, and focused.
- Trust signals: Clear hierarchy, restrained color, readable metrics, and explicit error/network states.
- Avoid: Bright consumer styling, decorative gradients, excessive motion, and low-contrast gray text.

## Product goals
- Goals: Make module comparison, span inspection, labeling, and evaluation comfortable during long work sessions.
- Non-goals: Marketing presentation or a consumer-facing visual identity.
- Success signals: Dense information remains scannable and interactive states are immediately distinguishable.

## Personas and jobs
- Primary personas: Engineers and data reviewers evaluating EMR privacy detectors.
- User jobs: Select detectors, inspect results, promote or create labels, and compare metrics.
- Key contexts of use: Desktop-first, extended technical work sessions.

## Information architecture
- Primary navigation: None; a single three-column workspace.
- Core routes/screens: Input/modules, detection viewer/labeling, confirmed labels/evaluation.
- Content hierarchy: Page title, task panels, panel controls, results, supporting metadata.

## Design principles
- Preserve focus with dark neutral surfaces and restrained accents.
- Use borders and surface elevation to separate dense information.
- Tradeoffs: Desktop information density takes priority over spacious presentation.

## Visual language
- Color: Deep navy-charcoal canvas, layered slate panels, cyan-blue primary accent, semantic amber/red states.
- Typography: System UI with Korean platform fonts; tabular numerals for metrics.
- Spacing/layout rhythm: Existing compact 6/8/12px rhythm.
- Shape/radius/elevation: 8-10px radii, subtle borders, restrained shadows.
- Motion: Short hover/focus transitions only.
- Imagery/iconography: None required.

## Components
- Existing components to reuse: All current panels, lists, viewer, controls, badges, notices, and metrics table.
- New/changed components: `HighlightViewer` supports manual selection labeling; `DetectionPanel` shows only pending detections; `ConfirmedSpanPanel` receives both detection-confirmed and manually selected labels for editing or reversal.
- Variants and states: Primary, danger, link, disabled, hover, focus, error, blocked, selected span, confirmed label.
- Token/component ownership: Global tokens in `frontend/src/index.css`; component styling in `frontend/src/App.css`.

## Accessibility
- Target standard: WCAG AA contrast for core text and controls.
- Keyboard/focus behavior: All native controls retain keyboard operation and receive visible `focus-visible` rings; Escape closes the selection popover.
- Contrast/readability: Primary text is near-white; muted text remains legible against every surface.
- Screen-reader semantics: Preserve existing semantic controls, labels, tables, and ARIA labels.
- Reduced motion and sensory considerations: No essential animation; honor reduced-motion preference.

## Responsive behavior
- Supported breakpoints/devices: Desktop primary; single-column layout below 1200px.
- Layout adaptations: Existing three-column grid collapses without changing task order.
- Touch/hover differences: Native control sizing and non-hover focus states remain available.

## Interaction states
- Loading: Button text changes and controls become disabled.
- Empty: Muted explanatory copy.
- Error: Dark red semantic surface with high-contrast text.
- Success: Confirming a detection moves it from the pending detection list to the confirmed span list; manual selections enter the same confirmed list, and evaluation remains visible below.
- Disabled: Reduced opacity without removing labels.
- Offline/slow network, if applicable: Existing error banner and per-module failures communicate failure.

## Content voice
- Tone: Concise, direct, technical Korean.
- Terminology: Preserve domain terms such as 탐지, 스팬, 확정 라벨, P/R/F1.
- Microcopy rules: State the required next action in empty and disabled contexts.

## Implementation constraints
- Framework/styling system: React and plain CSS; no new dependencies.
- Design-token constraints: Theme values must use shared CSS custom properties where practical.
- Performance constraints: No runtime theme library or image assets.
- Compatibility constraints: Modern Chromium/Firefox/Safari and Korean system fonts.
- Test/screenshot expectations: Lint, TypeScript, and production build must pass after visual changes.

## Open questions
- [ ] Whether a user-selectable light/dark toggle is needed later; current requirement is dark mode only.

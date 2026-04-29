# Theme Fast Start

Use this guide when the request changes theme behavior, theme tokens, component
surfaces, appearance modes, or a UI surface that likely needs a theme decision.

Treat this as the fast-access drawer for theme work. Start here before reading
unrelated pages or scanning the full app.

## Mandatory Clarification

Before implementation, confirm all of these with the user:

1. scope
   - app-wide
   - one component family
   - one page
   - one local section
2. target surface
   - which component, page, or state changes
3. appearance
   - light
   - dark
   - both
4. implementation layer
   - global token
   - component token
   - named preset
   - local scoped override
5. guardrails
   - what must stay unchanged

Do not inspect unrelated pages or components before this confirmation is
resolved.

## First Read Order

Read in this order:

1. `docs/ant-design/08-theme-architecture.md`
2. this file
3. the first-pass code map below

## First-Pass Code Map

Start only with these files unless the confirmed scope requires more:

- `src/theme/index.ts`
  - public theme entry point used by app code
- `src/theme/registry.ts`
  - registry of named themes and default selection
- `src/theme/create-theme.ts`
  - merges shared seed tokens, component tokens, and appearance algorithms
- `src/theme/global/shared-seed.ts`
  - shared app-wide seed values such as font family
- `src/theme/components/shared.ts`
  - shared component token overrides, best first stop for Card/Button/Table family changes
- `src/theme/presets/default.ts`
  - default preset and appearance-specific overrides
- `src/main.tsx`
  - `ConfigProvider` mount point and runtime theme wiring

## Decision Map

Use this quick rule:

- app-wide color, font, radius, spacing, or layout surface language
  - start in shared global tokens or a preset
- one Ant Design component family across the app
  - start in `src/theme/components/shared.ts`
- one named theme or appearance preset
  - start in `src/theme/presets/`
- one local exception after explicit confirmation
  - use a local scoped override only after proving the theme layer is too broad

## Expand Scope Only When

Expand past the first-pass files only if one of these is true:

- the user confirmed a specific page or component outside `src/theme/`
- a page already uses local visual overrides and they are winning over theme tokens
- verification shows the theme wiring is correct but the visual output still comes from local markup or styles

## Expected Output

Before saying theme work is complete, be able to explain:

- what changed for the user
- which theme layer was changed
- what was intentionally left untouched
- what risk remains for other pages or components

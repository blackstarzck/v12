---
name: theme-clarification-fast-path
description: Use when a request changes theme structure, tokens, presets, or component appearance and the agent must confirm scope before broad repo exploration or execution.
---

# theme-clarification-fast-path

## Purpose

Capture the repository's theme workflow as a reusable operating rule.
Treat it like a front desk for theme work: confirm the exact room to change
before walking the whole building.

## Trigger

- user requests theme, token, preset, appearance, light/dark mode, or component visual changes
- target paths include `src/theme/**`, `src/styles/**`, or `src/main.tsx`
- the request implies Ant Design token changes even if the user did not say `theme`

## Workflow

1. Ask for clarification before planning, implementation, or broad repository scanning.
2. Confirm:
   - scope: whole app, one component family, one page, or one local section
   - target surface: which component, page, or visual state changes
   - appearance mode: light, dark, or both
   - implementation layer: global token, component token, preset, or local override
   - guardrails: what must not change
3. Read only this first-pass set before expanding scope:
   - `docs/harness/theme-fast-start.md`
   - `docs/ant-design/08-theme-architecture.md`
   - `src/theme/index.ts`
   - `src/theme/registry.ts`
   - `src/theme/create-theme.ts`
   - `src/theme/global/shared-seed.ts`
   - `src/theme/components/shared.ts`
   - `src/theme/presets/default.ts`
   - `src/main.tsx`
4. Expand to page or component files only when:
   - the confirmed scope names that surface
   - a local override is masking the theme result
   - verification shows the change leaking or not applying
5. Keep theme decisions centralized and prefer Ant Design tokens over inline styling.

## Validation

- Confirm the clarification answer is recorded before mutating tools run.
- Confirm first-pass reading stayed inside the fast-start file set unless an allowed expansion reason exists.
- Confirm the final change matches the confirmed scope and does not spill into unrelated surfaces.

## Notes

- Pair this skill with the harness clarification events:
  `requirements.analyzed` -> `clarification.required` -> `clarification.resolved` -> `docs.required`.
- This skill does not bypass document acknowledgement or review gates.

# AI Development Workflow

This file defines the required workflow for AI-assisted UI development in this
project.

## Before Coding

1. Read the product docs in `docs/`.
2. Read `docs/ant-design/README.md`.
3. Read all files listed in the required reading order.
4. Identify the page pattern:
   - dashboard/workbench
   - form page
   - problem solving page
   - writing editor
   - list page
   - detail page
   - result page
   - exception page
   - exam workspace
5. Choose AntD components before writing custom UI.

## During Coding

Use this order:

1. Structure with AntD layout and components.
2. Configure global theme tokens.
3. Use component tokens for targeted customization.
4. Add local CSS only for project layout glue.
5. Add responsive behavior.
6. Add loading, empty, success, error, and disabled states.
7. Verify accessibility labels and keyboard behavior.

## AntD MCP Usage

Use MCP when:

- A component prop is uncertain.
- A demo pattern is needed.
- A design token is needed.
- Semantic DOM hooks are needed.
- A component has changed across versions.

If MCP is unavailable:

- Read `https://ant.design/llms-full.txt`.
- Read single component markdown, for example:
  - `https://ant.design/components/button.md`
  - `https://ant.design/components/form.md`
  - `https://ant.design/components/table.md`
- Read semantic docs where relevant, for example:
  - `https://ant.design/components/button/semantic.md`

## Theme Implementation Rule

When app code exists, create a single theme source such as:

```text
src/theme/antdTheme.ts
```

It should own:

- `token`
- `components`
- optional algorithm choice
- font family
- brand color
- border radius

Do not spread theme decisions across unrelated components.

## CSS Rule

Custom CSS should not compete with AntD's component system.

Allowed:

- app shell layout
- page-level responsive layout
- local font registration
- domain-specific editor/exam surface sizing
- print/export styling when needed

Avoid:

- rebuilding AntD buttons
- rebuilding AntD inputs
- custom dropdowns
- custom modals
- custom table behavior
- arbitrary color/radius/shadow values

## Verification Rule

For UI work, verify:

- desktop viewport
- mobile viewport
- no horizontal overflow
- no overlapping text
- loading state
- empty state
- error state
- primary workflow interaction
- console errors

When a dev server is available, use browser verification and screenshots.

## Conflict Rule

If old docs mention shadcn/ui or Tailwind as the UI system but the current user
direction says Ant Design, follow Ant Design for new UI work. Keep old docs as
product context unless the user asks to rewrite them.


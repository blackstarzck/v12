# AGENTS.md

This project uses Ant Design as the UI design system for new UI development.

## Required Reading Before UI Work

Read these local project docs first:

1. `docs/prd.md` - product requirements.
2. `docs/spec.md` - frontend implementation expectations.
3. `docs/ia.md` - information architecture.
4. `docs/user-flow.md` - user flows.
5. `docs/sitemap.md` - page map.

Then read the Ant Design AI development rules:

1. `docs/ant-design/README.md`
2. `docs/ant-design/00-source-map.md`
3. `docs/ant-design/01-design-values.md`
4. `docs/ant-design/02-global-styles.md`
5. `docs/ant-design/03-patterns-and-components.md`
6. `docs/ant-design/04-page-patterns-for-talkpik.md`
7. `docs/ant-design/05-visual-motion-illustration.md`
8. `docs/ant-design/06-ai-development-workflow.md`
9. `docs/ant-design/07-review-checklist.md`
10. `docs/ant-design/08-theme-architecture.md`

## Theme Reading Gate

Before implementing or modifying any UI work that can affect theme structure,
token usage, or styled output, read `docs/ant-design/08-theme-architecture.md`.

This applies especially to new pages, reusable components, AntD component
customization, global style changes, CSS variable changes, and new visual
states such as loading, empty, error, success, selected, or disabled.

If that document is missing, outdated, or insufficient, use the fallback order
documented inside `docs/ant-design/08-theme-architecture.md` and update
conflicting local docs before finalizing work.

## AntD Component Gate

Before implementing or modifying any user-facing page, section, feature UI, or
reusable UI component, read:

1. `docs/ant-design/03-patterns-and-components.md`
2. `docs/ant-design/06-ai-development-workflow.md`

This applies especially to navigation, forms, tables, lists, cards, drawers,
modals, tabs, steps, result/empty/loading/error states, and layout decisions.

Do not create custom UI first. Check whether Ant Design already provides the
component or pattern before writing custom markup, custom interaction logic, or
custom layout CSS.

If those local docs are missing, outdated, or insufficient, use AntD MCP or the
official Ant Design component docs before inventing a custom component or
pattern.

## Official Ant Design Sources

Use these official sources when more detail is needed:

- `https://ant.design/docs/spec/introduce`
- `https://ant.design/docs/spec/values`
- `https://ant.design/docs/spec/colors`
- `https://ant.design/docs/spec/layout`
- `https://ant.design/docs/spec/font`
- `https://ant.design/docs/spec/feedback`
- `https://ant.design/docs/spec/navigation`
- `https://ant.design/docs/spec/data-entry`
- `https://ant.design/docs/spec/data-display`
- `https://ant.design/docs/spec/motion`
- `https://ant.design/docs/spec/illustration`
- `https://ant.design/docs/react/llms`
- `https://ant.design/docs/react/mcp`
- `https://ant.design/docs/react/customize-theme`
- `https://ant.design/llms-full.txt`
- `https://ant.design/llms-semantic.md`

## AntD MCP

If the AntD MCP server is available, use it for component API, examples, tokens,
and semantic DOM checks.

Expected MCP server:

```json
{
  "mcpServers": {
    "antd": {
      "command": "antd",
      "args": ["mcp"]
    }
  }
}
```

## Local Harness

A requirement-gated Python harness is installed in this repository root.

Use it when you need durable session logging, required-document
acknowledgement, audited tool flow, or a pre-final audit.

If you change `generated_harness/`, also update `docs/harness/execution-flow.md`
and run the harness tests.

For the actual day-to-day operator flow, read `docs/harness/quickstart.md`.

## UI Implementation Policy

- Use Ant Design components before custom UI.
- Use Ant Design theme tokens before hardcoded CSS.
- Treat visual inline styles in JSX as custom styling, not as an exception.
- Do not restyle Ant Design components in `style={{...}}` when AntD props, tokens, or documented patterns already solve the problem.
- Keep theme decisions centralized.
- Use the local font from `fonts/` as the default app font when app code exists.
- Build the actual learning workspace first, not a landing page.
- Include loading, empty, error, success, and disabled states.
- Verify desktop and mobile layouts before calling UI work complete.

## Conflict Policy

Some existing project docs may mention shadcn/ui, Tailwind, or an older design
skill. Treat those as historical implementation notes unless the user explicitly
asks to use them. For new UI work, follow the Ant Design rules in
`docs/ant-design/`.

## Completion Policy

Before finalizing UI work, apply `docs/ant-design/07-review-checklist.md`.
Report what works, what does not work yet, and what risk remains.

## Review Reporting Policy

When reviewing UI work, do not only check the review checklist internally.
Report the checklist result directly to the user in the chat response.

Do not create a separate review document unless the user explicitly asks for
one. The default review output must be a concise prompt response with:

- checklist items that passed,
- checklist items that failed or need work,
- remaining risks,
- and the next recommended action.

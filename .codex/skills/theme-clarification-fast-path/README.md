# theme-clarification-fast-path

## What this skill is

This is the project's saved playbook for theme work.
It exists so the agent does not immediately scan the whole codebase or guess
scope when a request touches appearance, tokens, or presets.

## When it should run

- Theme or token requests
- Component appearance changes that likely belong in theme files
- Light mode or dark mode adjustments
- Ant Design `ConfigProvider` or `src/theme/**` changes

## Files

- `SKILL.md`: the reusable instructions the agent should follow
- `README.md`: a plain-language explanation for maintainers

## Operating rule

Clarify first, then read the fast-start map, then widen scope only if the
confirmed request or verification requires it.
The skill speeds up repeat work, but it does not bypass harness safety gates.

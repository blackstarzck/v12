# Theme Architecture

This file explains how theme configuration is organized in the TALKPIK AI codebase.

Use this document when:

- adding a new named theme such as `retro`, `glass`, or `pink`
- changing global Ant Design tokens
- changing component-specific Ant Design tokens
- importing values from Ant Design Theme Editor
- deciding whether a value belongs in AntD tokens or app CSS variables

## Why This Exists

Ant Design supports two important theme layers:

1. Global theme values
   - configured through `theme.token`
   - includes brand color, font, radius, global surfaces, spacing-related values, and algorithm choice
2. Component theme values
   - configured through `theme.components`
   - includes adjustments for specific components such as `Button`, `Menu`, `Layout`, and `Table`

The TALKPIK AI project follows that model directly.

We do **not** keep all theme decisions in one long file anymore.
We keep:

- one public theme entry point
- one registry of available theme presets
- one preset file per theme
- separate global and component shared rules
- a small adapter that turns AntD tokens into app CSS variables

## Current Theme Folder

```text
src/theme/
  index.ts
  themes.ts
  registry.ts
  create-theme.ts
  app-vars.ts
  types.ts
  antdTheme.ts
  global/
    algorithms.ts
    shared-seed.ts
  components/
    shared.ts
  presets/
    default.ts
```

## File Responsibilities

### Public entry points

- `src/theme/index.ts`
  - the main import entry for theme APIs
  - new code should import from here
- `src/theme/themes.ts`
  - compatibility re-export
  - kept so old imports do not break immediately
- `src/theme/antdTheme.ts`
  - helper that exposes the default AntD theme config
  - acceptable for static use, but app runtime theme selection should use `getAppTheme`

### Theme assembly

- `src/theme/registry.ts`
  - registers available theme presets
  - exposes `themes`, `themePresets`, `defaultThemeName`, `defaultAppearance`, and `getAppTheme`
- `src/theme/create-theme.ts`
  - builds the final `ThemeConfig` from shared rules plus a preset
  - merges global token values and component token values

### Shared theme inputs

- `src/theme/global/shared-seed.ts`
  - shared global seed tokens such as font family, border radius, and control heights
  - keep this structural and neutral
- `src/theme/global/algorithms.ts`
  - maps `light` and `dark` appearance to Ant Design algorithms
- `src/theme/components/shared.ts`
  - shared component-level token defaults used across all presets
  - good place for common `Button`, `Card`, or `Menu` adjustments

### Theme presets

- `src/theme/presets/default.ts`
  - the current theme preset
  - stores theme-specific global token values, component token overrides, and optional app variable overrides

### App-specific adaptation

- `src/theme/app-vars.ts`
  - converts resolved Ant Design tokens into app CSS variables such as `--app-bg` and `--app-brand`
  - use this to keep layout glue CSS aligned with the active AntD theme

### Types

- `src/theme/types.ts`
  - shared types for appearances, presets, definitions, and CSS variable records

## Theme Flow

The runtime theme flow is:

1. a preset such as `defaultThemePreset` defines appearance-specific values
2. `createThemeFamily` builds final `ThemeConfig` objects for `light` and `dark`
3. `registry.ts` exposes the available themes
4. `main.tsx` calls `getAppTheme(themeName, appearance)`
5. `ConfigProvider` receives `activeTheme.antd`
6. root CSS variables are updated from `activeTheme.cssVars`

This gives the app one source of truth at runtime even though the files are split for maintainability.

## Global vs Component Rules

Use this decision rule:

### Put a value in global tokens when it changes the app's overall design language

Examples:

- `colorPrimary`
- `fontFamily`
- `borderRadius`
- `colorBgLayout`
- `colorBgContainer`

### Put a value in component tokens when it only changes one AntD component family

Examples:

- `Button.primaryShadow`
- `Menu.itemSelectedBg`
- `Layout.headerBg`
- `Table.rowHoverBg`

### Put a value in app CSS variables only when it is app-shell glue or a non-AntD surface concern

Examples:

- sticky app shell surface colors
- custom answer option border color
- a layout-only background used in project CSS

Do not use CSS variables as the first choice if AntD tokens already express the same decision.

## How To Add A New Theme

Example target:

- `retro`
- `glass`
- `black`
- `pink`

Steps:

1. Create a new preset file in `src/theme/presets/`
   - example: `src/theme/presets/retro.ts`
2. Export a preset object that satisfies `AppThemePreset<'retro'>`
3. Define `light` and `dark` appearances inside that preset
4. Register the preset in `src/theme/registry.ts`
5. If the user should be able to choose it, extend theme selection state and settings UI
6. Verify desktop and mobile layouts after switching themes

Example shape:

```ts
import type { AppThemePreset } from '../types';

export const retroThemePreset = {
  name: 'retro',
  label: 'Retro',
  description: 'Warm and editorial theme',
  appearances: {
    light: {
      token: {
        colorPrimary: '#b45309',
      },
      components: {
        Menu: {
          itemSelectedBg: '#b45309',
        },
      },
    },
    dark: {
      token: {
        colorPrimary: '#f59e0b',
      },
    },
  },
} satisfies AppThemePreset<'retro'>;
```

## How To Use Ant Design Theme Editor

Reference:

- `https://ant.design/theme-editor`

Use Theme Editor as a design tool, not as a dump target for every possible token.

Recommended workflow:

1. Start with global brand and surface decisions in Theme Editor
2. Export the values
3. Move the relevant global values into `token`
4. Move component-specific values into `components`
5. Only keep overrides that are actually needed by the project

Do **not** blindly paste every exported value if many of them are just derived alias tokens.

Prefer this order:

1. keep shared structural rules in `global/shared-seed.ts`
2. keep per-theme brand values in the preset file
3. keep per-component theme overrides in `components` or in the preset's `components` block
4. use `appVars` only for project CSS that cannot read AntD tokens directly

## Rules For Future Edits

- New theme work should import from `src/theme/index.ts`
- Do not turn `registry.ts` into a long token file
- Do not put all preset values back into one giant `themes.ts`
- Do not duplicate the same color in three places without reason
- If a shared component token starts growing large, split it into per-component files under `src/theme/components/`
- If a preset becomes large, keep its values inside the preset file instead of spreading them across random UI components

## Review Checklist For Theme Changes

Before calling theme work complete, verify:

- global brand, font, and radius still come from AntD tokens
- component-specific overrides still live in `theme.components`
- app shell CSS variables still reflect the active theme
- dark mode still uses AntD dark algorithm unless there is a documented reason otherwise
- no new hardcoded color values were scattered into unrelated components
- desktop and mobile layouts still render correctly


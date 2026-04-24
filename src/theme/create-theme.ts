import type { ThemeConfig } from 'antd';
import { sharedComponentTokens } from './components/shared';
import { appearanceAlgorithms } from './global/algorithms';
import { sharedSeedTokens } from './global/shared-seed';
import type {
  AppAppearance,
  AppThemeAppearanceConfig,
  AppThemeDefinition,
  AppThemePreset,
} from './types';

function mergeComponentTokens(
  base: ThemeConfig['components'] = {},
  overrides: ThemeConfig['components'] = {},
): ThemeConfig['components'] {
  const mergedEntries = new Map<string, Record<string, unknown>>();

  for (const [componentName, componentTokens] of Object.entries(base)) {
    mergedEntries.set(componentName, { ...(componentTokens as Record<string, unknown>) });
  }

  for (const [componentName, componentTokens] of Object.entries(overrides)) {
    mergedEntries.set(componentName, {
      ...(mergedEntries.get(componentName) ?? {}),
      ...(componentTokens as Record<string, unknown>),
    });
  }

  return Object.fromEntries(mergedEntries);
}

function createThemeConfig(
  appearance: AppAppearance,
  appearanceConfig: AppThemeAppearanceConfig,
): ThemeConfig {
  return {
    algorithm: appearanceConfig.algorithm ?? appearanceAlgorithms[appearance],
    token: {
      ...sharedSeedTokens,
      ...(appearanceConfig.token ?? {}),
    },
    components: mergeComponentTokens(sharedComponentTokens, appearanceConfig.components),
  };
}

function createThemeDefinition<Name extends string>(
  preset: AppThemePreset<Name>,
  appearance: AppAppearance,
): AppThemeDefinition<Name> {
  const appearanceConfig = preset.appearances[appearance];
  const antd = createThemeConfig(appearance, appearanceConfig);

  return {
    name: preset.name,
    appearance,
    label: preset.label,
    description: preset.description,
    antd,
  };
}

export function createThemeFamily<Name extends string>(
  preset: AppThemePreset<Name>,
): Record<AppAppearance, AppThemeDefinition<Name>> {
  return {
    light: createThemeDefinition(preset, 'light'),
    dark: createThemeDefinition(preset, 'dark'),
  };
}

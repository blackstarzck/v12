import { createThemeFamily } from './create-theme';
import { defaultThemePreset } from './presets/default';
import { liquidGlassThemePreset } from './presets/liquid-glass';
import type { AppAppearance, AppAppearanceOption, AppThemeOption, AppThemeRegistry } from './types';

export const appearanceOptions: AppAppearanceOption[] = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
];

export const themePresets = {
  default: defaultThemePreset,
  liquidGlass: liquidGlassThemePreset,
};

export type AppThemeName = keyof typeof themePresets;

export const themeOptions: AppThemeOption<AppThemeName>[] = Object.values(themePresets).map((preset) => ({
  value: preset.name,
  label: preset.label,
  description: preset.description,
}));

export const themes: AppThemeRegistry<AppThemeName> = {
  default: createThemeFamily(defaultThemePreset),
  liquidGlass: createThemeFamily(liquidGlassThemePreset),
};

export const defaultThemeName: AppThemeName = 'default';
export const defaultAppearance: AppAppearance = 'light';

export function getAppTheme(themeName: AppThemeName, appearance: AppAppearance) {
  return themes[themeName][appearance];
}

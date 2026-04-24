import { createThemeFamily } from './create-theme';
import { defaultThemePreset } from './presets/default';
import type { AppAppearance, AppAppearanceOption, AppThemeRegistry } from './types';

export const appearanceOptions: AppAppearanceOption[] = [
  { value: 'light', label: '라이트' },
  { value: 'dark', label: '다크' },
];

export const themePresets = {
  default: defaultThemePreset,
};

export type AppThemeName = keyof typeof themePresets;

export const themes: AppThemeRegistry<AppThemeName> = {
  default: createThemeFamily(defaultThemePreset),
};

export const defaultThemeName: AppThemeName = 'default';
export const defaultAppearance: AppAppearance = 'light';

export function getAppTheme(themeName: AppThemeName, appearance: AppAppearance) {
  return themes[themeName][appearance];
}

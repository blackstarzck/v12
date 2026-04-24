import type { ThemeConfig } from 'antd';

export type AppAppearance = 'light' | 'dark';

export type AppCssVars = Record<`--${string}`, string>;

export interface AppAppearanceOption {
  value: AppAppearance;
  label: string;
}

export interface AppThemeAppearanceConfig {
  algorithm?: ThemeConfig['algorithm'];
  token?: ThemeConfig['token'];
  components?: ThemeConfig['components'];
  appVars?: Partial<AppCssVars>;
}

export interface AppThemePreset<Name extends string = string> {
  name: Name;
  label: string;
  description: string;
  appearances: Record<AppAppearance, AppThemeAppearanceConfig>;
}

export interface AppThemeDefinition<Name extends string = string> {
  name: Name;
  appearance: AppAppearance;
  label: string;
  description: string;
  antd: ThemeConfig;
  cssVars: AppCssVars;
}

export type AppThemeRegistry<Name extends string = string> = Record<
  Name,
  Record<AppAppearance, AppThemeDefinition<Name>>
>;

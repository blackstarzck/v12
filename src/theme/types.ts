import type { ThemeConfig } from 'antd';

export type AppAppearance = 'light' | 'dark';

export interface AppAppearanceOption {
  value: AppAppearance;
  label: string;
}

export interface AppThemeAppearanceConfig {
  algorithm?: ThemeConfig['algorithm'];
  token?: ThemeConfig['token'];
  components?: ThemeConfig['components'];
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
}

export type AppThemeRegistry<Name extends string = string> = Record<
  Name,
  Record<AppAppearance, AppThemeDefinition<Name>>
>;

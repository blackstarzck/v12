import { theme as antdThemeApi } from 'antd';
import type { AppAppearance } from '../types';

export const appearanceAlgorithms = {
  light: antdThemeApi.defaultAlgorithm,
  dark: antdThemeApi.darkAlgorithm,
} satisfies Record<AppAppearance, typeof antdThemeApi.defaultAlgorithm>;

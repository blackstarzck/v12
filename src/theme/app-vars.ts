import { theme as antdThemeApi, type ThemeConfig } from 'antd';
import type { AppAppearance, AppCssVars } from './types';

type ResolvedToken = ReturnType<typeof antdThemeApi.getDesignToken>;

function getComponentTokenGroup(
  config: ThemeConfig,
  componentName: string,
): Record<string, string | number | undefined> {
  const components = (config.components ?? {}) as Record<string, unknown>;
  const group = components[componentName];

  if (!group || typeof group !== 'object') {
    return {};
  }

  return group as Record<string, string | number | undefined>;
}

function pickString(value: string | number | undefined, fallback: string) {
  if (typeof value === 'string') {
    return value;
  }

  if (typeof value === 'number') {
    return String(value);
  }

  return fallback;
}

export function createAppCssVars(appearance: AppAppearance, config: ThemeConfig): AppCssVars {
  const resolvedToken: ResolvedToken = antdThemeApi.getDesignToken(config);
  const layoutTokens = getComponentTokenGroup(config, 'Layout');

  return {
    '--app-color-scheme': appearance,
    '--app-bg': pickString(layoutTokens.bodyBg, resolvedToken.colorBgLayout),
    '--app-surface': resolvedToken.colorBgContainer,
    '--app-surface-muted': resolvedToken.colorFillAlter,
    '--app-header-bg': pickString(layoutTokens.headerBg, resolvedToken.colorBgContainer),
    '--app-sidebar-bg': pickString(
      layoutTokens.siderBg ?? layoutTokens.lightSiderBg,
      resolvedToken.colorBgContainer,
    ),
    '--app-border': resolvedToken.colorSplit,
    '--app-border-strong': resolvedToken.colorBorder,
    '--app-answer-border': resolvedToken.colorBorderSecondary,
    '--app-text': resolvedToken.colorText,
    '--app-text-secondary': resolvedToken.colorTextSecondary,
    '--app-text-muted': resolvedToken.colorTextTertiary,
    '--app-brand': resolvedToken.colorPrimary,
    '--app-hover-bg': resolvedToken.controlItemBgHover,
  };
}

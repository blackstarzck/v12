import { theme as antdThemeApi, type ThemeConfig } from 'antd';

export type AppThemeName = 'default';
export type AppAppearance = 'light' | 'dark';

export type AppCssVars = Record<`--${string}`, string>;

export interface AppThemeDefinition {
  name: AppThemeName;
  appearance: AppAppearance;
  label: string;
  description: string;
  antd: ThemeConfig;
  cssVars: AppCssVars;
}

export interface AppAppearanceOption {
  value: AppAppearance;
  label: string;
}

const fontFamily = 'Pretendard, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

const sharedTokens: ThemeConfig['token'] = {
  colorPrimary: '#0f766e',
  colorSuccess: '#16a34a',
  colorWarning: '#d97706',
  colorError: '#e11d48',
  colorInfo: '#2563eb',
  borderRadius: 8,
  borderRadiusLG: 8,
  controlHeight: 40,
  controlHeightLG: 48,
  fontFamily,
};

const sharedComponents: ThemeConfig['components'] = {
  Button: {
    borderRadius: 8,
    primaryShadow: 'none',
  },
  Card: {
    borderRadiusLG: 8,
    headerFontSize: 16,
  },
  Menu: {
    itemBorderRadius: 8,
    itemActiveBg: '#ccfbf1',
    itemHoverBg: '#ecfdf5',
    itemHoverColor: '#0f766e',
    itemSelectedBg: '#0f766e',
    itemSelectedColor: '#ffffff',
    darkItemColor: '#aab9b5',
    darkItemHoverBg: '#1f302d',
    darkItemHoverColor: '#ccfbf1',
    darkItemSelectedBg: '#0f766e',
    darkItemSelectedColor: '#ffffff',
  },
};

export const appearanceOptions: AppAppearanceOption[] = [
  { value: 'light', label: '라이트' },
  { value: 'dark', label: '다크' },
];

export const themes: Record<AppThemeName, Record<AppAppearance, AppThemeDefinition>> = {
  default: {
    light: {
      name: 'default',
      appearance: 'light',
      label: '기본',
      description: '읽기 중심의 안정적인 학습 화면',
      antd: {
        algorithm: antdThemeApi.defaultAlgorithm,
        token: {
          ...sharedTokens,
          colorBgLayout: '#f6f8f7',
          colorBgContainer: '#ffffff',
          colorBgElevated: '#ffffff',
          colorBorder: '#dfe7e4',
          colorTextBase: '#1f2933',
        },
        components: {
          ...sharedComponents,
          Layout: {
            bodyBg: '#f6f8f7',
            siderBg: '#ffffff',
            headerBg: '#ffffff',
          },
          Table: {
            headerBg: '#f3f6f5',
            rowHoverBg: '#f7fbfa',
          },
        },
      },
      cssVars: {
        '--app-color-scheme': 'light',
        '--app-bg': '#f6f8f7',
        '--app-surface': '#ffffff',
        '--app-surface-muted': '#fbfdfc',
        '--app-header-bg': '#ffffff',
        '--app-sidebar-bg': '#ffffff',
        '--app-border': 'rgba(15, 23, 42, 0.08)',
        '--app-border-strong': '#dfe7e4',
        '--app-answer-border': '#d9e2df',
        '--app-text': '#172026',
        '--app-text-secondary': '#667085',
        '--app-text-muted': '#4b5563',
        '--app-brand': '#0f766e',
        '--app-hover-bg': '#f7fbfa',
      },
    },
    dark: {
      name: 'default',
      appearance: 'dark',
      label: '기본',
      description: '읽기 중심의 안정적인 학습 화면',
      antd: {
        algorithm: antdThemeApi.darkAlgorithm,
        token: {
          ...sharedTokens,
          colorBgLayout: '#101514',
          colorBgContainer: '#171d1c',
          colorBgElevated: '#1f2725',
          colorBorder: '#2f3b38',
          colorTextBase: '#eef7f5',
        },
        components: {
          ...sharedComponents,
          Layout: {
            bodyBg: '#101514',
            siderBg: '#171d1c',
            headerBg: '#171d1c',
          },
          Table: {
            headerBg: '#202a28',
            rowHoverBg: '#1b2523',
          },
        },
      },
      cssVars: {
        '--app-color-scheme': 'dark',
        '--app-bg': '#101514',
        '--app-surface': '#171d1c',
        '--app-surface-muted': '#1d2523',
        '--app-header-bg': '#171d1c',
        '--app-sidebar-bg': '#171d1c',
        '--app-border': 'rgba(238, 247, 245, 0.1)',
        '--app-border-strong': '#2f3b38',
        '--app-answer-border': '#32413e',
        '--app-text': '#eef7f5',
        '--app-text-secondary': '#aab9b5',
        '--app-text-muted': '#c0ceca',
        '--app-brand': '#5eead4',
        '--app-hover-bg': '#1f302d',
      },
    },
  },
};

export const defaultThemeName: AppThemeName = 'default';
export const defaultAppearance: AppAppearance = 'light';

export function getAppTheme(themeName: AppThemeName, appearance: AppAppearance) {
  return themes[themeName][appearance];
}

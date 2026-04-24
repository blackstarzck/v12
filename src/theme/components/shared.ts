import type { ThemeConfig } from 'antd';

// Shared component tokens should stay mostly structural.
export const sharedComponentTokens: ThemeConfig['components'] = {
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
  },
};

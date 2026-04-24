import type { ThemeConfig } from 'antd';

export const fontFamily =
  'Pretendard, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

// Keep only the app font here. Other design values should follow Ant Design
// defaults unless there is a documented reason to override them.
export const sharedSeedTokens: ThemeConfig['token'] = {
  fontFamily,
};

import type { ThemeConfig } from 'antd';

export const fontFamily =
  'Pretendard, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

// Shared global tokens should stay structural so each preset can own its brand colors.
export const sharedSeedTokens: ThemeConfig['token'] = {
  borderRadius: 8,
  borderRadiusLG: 8,
  controlHeight: 40,
  controlHeightLG: 48,
  fontFamily,
};

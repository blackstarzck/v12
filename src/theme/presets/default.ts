import type { AppThemePreset } from '../types';

export const defaultThemePreset = {
  name: 'default',
  label: 'Default',
  description: 'Use the stock Ant Design system with only light and dark mode.',
  appearances: {
    light: {},
    dark: {},
  },
} satisfies AppThemePreset<'default'>;

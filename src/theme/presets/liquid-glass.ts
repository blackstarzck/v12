import type { AppThemePreset } from '../types';

export const liquidGlassThemePreset = {
  name: 'liquidGlass',
  label: 'Liquid Glass',
  description: 'Glass-like Card surfaces inspired by the reference demo with a layered blur treatment.',
  appearances: {
    light: {
      components: {
        Card: {
          colorBgContainer: 'transparent',
          colorFillAlter: 'transparent',
          colorBorderSecondary: 'transparent',
          colorText: '#ffffff',
          colorTextHeading: '#ffffff',
          colorTextDescription: 'rgba(255, 255, 255, 0.82)',
          colorIcon: 'rgba(255, 255, 255, 0.82)',
          boxShadowTertiary: '0 12px 40px rgba(0, 0, 0, 0.25)',
          lineWidth: 0,
          headerBg: 'transparent',
          actionsBg: 'transparent',
          extraColor: 'rgba(255, 255, 255, 0.92)',
          headerFontSize: 20,
          headerPadding: 32,
          bodyPadding: 24,
        },
        Modal: {
          contentBg: 'transparent',
          headerBg: 'transparent',
          footerBg: 'transparent',
          titleColor: '#ffffff',
        },
      },
    },
    dark: {
      components: {
        Card: {
          colorBgContainer: 'transparent',
          colorFillAlter: 'transparent',
          colorBorderSecondary: 'transparent',
          colorText: 'rgba(235, 245, 255, 0.92)',
          colorTextHeading: '#f5faff',
          colorTextDescription: 'rgba(214, 230, 248, 0.76)',
          colorIcon: 'rgba(214, 230, 248, 0.76)',
          boxShadowTertiary: '0 12px 40px rgba(0, 0, 0, 0.35)',
          lineWidth: 0,
          headerBg: 'transparent',
          actionsBg: 'transparent',
          extraColor: 'rgba(235, 245, 255, 0.92)',
          headerFontSize: 20,
          headerPadding: 32,
          bodyPadding: 24,
        },
        Modal: {
          contentBg: 'transparent',
          headerBg: 'transparent',
          footerBg: 'transparent',
          titleColor: '#f5faff',
        },
      },
    },
  },
} satisfies AppThemePreset<'liquidGlass'>;

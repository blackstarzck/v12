import type { AppThemePreset } from '../types';

const structuralGlassStyles = `
@keyframes liquid-glass-aurora {
  from {
    background-position:
      50% 50%,
      50% 50%;
  }
  to {
    background-position:
      350% 50%,
      350% 50%;
  }
}

@property --liquid-card-button-angle-border {
  syntax: '<angle>';
  inherits: false;
  initial-value: -75deg;
}

@property --liquid-card-button-angle-shine {
  syntax: '<angle>';
  inherits: false;
  initial-value: -45deg;
}

html[data-theme='liquidGlass'] body {
  background: var(--liquid-aurora-bg) !important;
}

html[data-theme='liquidGlass'] body::before {
  content: '';
  position: fixed;
  inset: -12px;
  z-index: 0;
  pointer-events: none;
  background-image: var(--liquid-aurora-mask), var(--liquid-aurora);
  background-size:
    300% 100%,
    200% 100%;
  background-position:
    50% 50%,
    50% 50%;
  filter: blur(14px) saturate(115%);
  opacity: var(--liquid-aurora-opacity);
  mix-blend-mode: var(--liquid-aurora-blend-mode);
  animation: liquid-glass-aurora 60s linear infinite;
  will-change: background-position;
  mask-image: radial-gradient(ellipse at 100% 0%, #000 12%, transparent 72%);
  -webkit-mask-image: radial-gradient(ellipse at 100% 0%, #000 12%, transparent 72%);
}

html[data-theme='liquidGlass'] body::after {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 20% 18%, var(--liquid-aurora-glow-a), transparent 30%),
    radial-gradient(circle at 84% 16%, var(--liquid-aurora-glow-b), transparent 34%),
    linear-gradient(180deg, transparent 0%, var(--liquid-aurora-vignette) 100%);
}

html[data-theme='liquidGlass'] #root {
  position: relative;
  z-index: 1;
  min-height: 100dvh;
}

html[data-theme='liquidGlass'] .app-shell,
html[data-theme='liquidGlass'] .app-shell.ant-layout,
html[data-theme='liquidGlass'] .app-shell>.ant-layout {
  background: transparent !important;
}

html[data-theme='liquidGlass'] .app-card,
html[data-theme='liquidGlass'] .app-modal .ant-modal-content {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  background: transparent !important;
  border: 0 !important;
  box-shadow: var(--liquid-surface-shadow) !important;
}

html[data-theme='liquidGlass'] .app-drawer .ant-drawer-content-wrapper {
  overflow: hidden;
  isolation: isolate;
  background: transparent !important;
  box-shadow: var(--liquid-surface-shadow) !important;
  will-change: transform;
  contain: paint;
}

html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-left-enter,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-left-enter-active,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-left-appear,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-left-appear-active,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-right-enter,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-right-enter-active,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-right-appear,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-right-appear-active,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-top-enter,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-top-enter-active,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-top-appear,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-top-appear-active,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-bottom-enter,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-bottom-enter-active,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-bottom-appear,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-panel-motion-bottom-appear-active {
  opacity: 1 !important;
}

html[data-theme='liquidGlass'] .app-card::before,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-content-wrapper::before,
html[data-theme='liquidGlass'] .app-modal .ant-modal-content::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
  backdrop-filter: blur(20px) saturate(140%);
  -webkit-backdrop-filter: blur(20px) saturate(140%);
}

html[data-theme='liquidGlass'] .app-card::after,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-content-wrapper::after,
html[data-theme='liquidGlass'] .app-modal .ant-modal-content::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
  pointer-events: none;
  background: rgba(255, 255, 255, 0.3);
  box-shadow:
    rgba(255, 255, 255, 0.3) 1px 1px 1px 0px inset,
    rgba(255, 255, 255, 0.3) -1px -1px 1px 0px inset
}

html[data-theme='liquidGlass'] .app-drawer .ant-drawer-content {
  height: 100%;
  position: relative;
  z-index: 1;
  background: transparent !important;
  box-shadow: none !important;
}

html[data-theme='liquidGlass'] .app-card>*,
html[data-theme='liquidGlass'] .app-card .ant-card-body,
html[data-theme='liquidGlass'] .app-card .ant-card-cover,
html[data-theme='liquidGlass'] .app-card .ant-card-actions,
html[data-theme='liquidGlass'] .app-card .ant-card-grid,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-content>*,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-header,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-body,
html[data-theme='liquidGlass'] .app-drawer .ant-drawer-footer,
html[data-theme='liquidGlass'] .ant-modal-content>*,
html[data-theme='liquidGlass'] .app-modal .ant-modal-header,
html[data-theme='liquidGlass'] .app-modal .ant-modal-body,
html[data-theme='liquidGlass'] .app-modal .ant-modal-footer {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.15) !important;
}

html[data-theme='liquidGlass'] .app-card .ant-card-actions>li:not(:last-child) {
  border-inline-end-color: var(--liquid-surface-divider) !important;
}

html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text) {
  --liquid-card-button-border-width: clamp(1px, 1px, 4px);
  --liquid-card-button-duration: 0.4s;
  --liquid-card-button-ease: cubic-bezier(0.25, 1, 0.5, 1);
  position: relative;
  isolation: isolate;
  overflow: hidden;
  border-color: transparent !important;
  border-radius: 9999px !important;
  color: var(--liquid-card-button-text) !important;
  background:
    linear-gradient(
      -75deg,
      var(--liquid-card-button-bg-low),
      var(--liquid-card-button-bg-high),
      var(--liquid-card-button-bg-low)
    ) !important;
  box-shadow:
    inset 0 2px 2px var(--liquid-card-button-inset-top),
    inset 0 -2px 2px var(--liquid-card-button-inset-bottom),
    0 4px 2px -2px var(--liquid-card-button-drop),
    0 0 2px 4px inset var(--liquid-card-button-inner-glow),
    0 4px 10px var(--liquid-card-button-outer-glow) !important;
  text-shadow: 0 4px 0.8px var(--liquid-card-button-text-shadow);
  transform: translateZ(0);
  transform-style: preserve-3d;
  backdrop-filter: blur(clamp(1px, 2px, 4px));
  -webkit-backdrop-filter: blur(clamp(1px, 2px, 4px));
  transition:
    background var(--liquid-card-button-duration) var(--liquid-card-button-ease),
    box-shadow var(--liquid-card-button-duration) var(--liquid-card-button-ease),
    color var(--liquid-card-button-duration) var(--liquid-card-button-ease),
    transform var(--liquid-card-button-duration) var(--liquid-card-button-ease),
    backdrop-filter var(--liquid-card-button-duration) var(--liquid-card-button-ease),
    -webkit-backdrop-filter var(--liquid-card-button-duration) var(--liquid-card-button-ease);
  -webkit-tap-highlight-color: transparent;
}

html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text)::before,
html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text)::after {
  content: '';
  position: absolute;
  pointer-events: none;
  border-radius: inherit;
}

html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text)::before {
  inset: 0;
  z-index: 1;
  padding: var(--liquid-card-button-border-width);
  background:
    conic-gradient(
      from var(--liquid-card-button-angle-border) at 50% 50%,
      var(--liquid-card-button-border-glow) 0%,
      transparent 5% 40%,
      var(--liquid-card-button-border-glow) 50%,
      transparent 60% 95%,
      var(--liquid-card-button-border-glow) 100%
    ),
    linear-gradient(180deg, var(--liquid-card-button-border-fill), var(--liquid-card-button-border-fill));
  box-shadow: inset 0 0 0 calc(var(--liquid-card-button-border-width) / 2) var(--liquid-card-button-border-inset);
  transition:
    --liquid-card-button-angle-border 0.5s ease,
    box-shadow var(--liquid-card-button-duration) var(--liquid-card-button-ease),
    background var(--liquid-card-button-duration) var(--liquid-card-button-ease);
  -webkit-mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  mask-composite: exclude;
}

html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text)::after {
  inset: calc(var(--liquid-card-button-border-width) / 2);
  z-index: 1;
  background:
    linear-gradient(
      var(--liquid-card-button-angle-shine),
      transparent 0%,
      var(--liquid-card-button-shine) 40% 50%,
      transparent 55%
    );
  background-position: 0%;
  background-size: 200% 200%;
  mix-blend-mode: screen;
  transition:
    background-position calc(var(--liquid-card-button-duration) * 1.25) var(--liquid-card-button-ease),
    --liquid-card-button-angle-shine calc(var(--liquid-card-button-duration) * 1.25) var(--liquid-card-button-ease);
}

html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text)>span,
html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text)>.ant-btn-icon {
  position: relative;
  z-index: 2;
}

html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text):not(:disabled):not(.ant-btn-disabled):hover {
  color: var(--liquid-card-button-hover-text) !important;
  transform: scale(0.975);
  backdrop-filter: blur(0.16px);
  -webkit-backdrop-filter: blur(0.16px);
  box-shadow:
    inset 0 2px 2px var(--liquid-card-button-inset-top),
    inset 0 -2px 2px var(--liquid-card-button-inset-bottom),
    0 2.4px 0.8px -1.6px var(--liquid-card-button-hover-drop),
    0 0 0.8px 1.6px inset var(--liquid-card-button-hover-inner-glow),
    0 5.6px 14.4px var(--liquid-card-button-hover-outer-glow) !important;
}

html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text):not(:disabled):not(.ant-btn-disabled):hover::before {
  --liquid-card-button-angle-border: -125deg;
}

html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text):not(:disabled):not(.ant-btn-disabled):hover::after {
  background-position: 25%;
}

html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text):not(:disabled):not(.ant-btn-disabled):active {
  --liquid-card-button-angle-shine: -15deg;
  transform: scale(0.965) rotateX(8deg);
  box-shadow:
    inset 0 2px 2px var(--liquid-card-button-inset-top),
    inset 0 -2px 2px var(--liquid-card-button-inset-bottom),
    0 2px 2px -2px var(--liquid-card-button-drop),
    0 0 1.6px 4px inset var(--liquid-card-button-inner-glow),
    0 3.6px 0.8px var(--liquid-card-button-press-glow),
    0 4px var(--liquid-card-button-press-surface),
    inset 0 4px 0.8px var(--liquid-card-button-press-inset) !important;
}

html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text):not(:disabled):not(.ant-btn-disabled):active::before {
  --liquid-card-button-angle-border: -75deg;
}

html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text):not(:disabled):not(.ant-btn-disabled):active::after {
  background-position: 50% 15%;
}

html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text):focus-visible {
  outline: 0;
  box-shadow:
    inset 0 2px 2px var(--liquid-card-button-inset-top),
    inset 0 -2px 2px var(--liquid-card-button-inset-bottom),
    0 0 0 3px var(--liquid-card-button-focus-ring),
    0 8px 21.6px var(--liquid-card-button-outer-glow) !important;
}

html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text):disabled,
html[data-theme='liquidGlass'] .app-card .ant-btn.ant-btn-disabled:not(.ant-btn-link):not(.ant-btn-text) {
  color: var(--liquid-card-button-disabled-text) !important;
  opacity: 0.62;
  transform: none;
  box-shadow:
    inset 0 2px 2px var(--liquid-card-button-inset-top),
    inset 0 -2px 2px var(--liquid-card-button-inset-bottom),
    0 0 1.6px 2.88px inset var(--liquid-card-button-inner-glow) !important;
}

html[data-theme='liquidGlass'] .app-drawer .ant-drawer-header {
  border-bottom-color: var(--liquid-surface-divider) !important;
}

html[data-theme='liquidGlass'] .app-drawer .ant-drawer-footer {
  border-top-color: var(--liquid-surface-divider) !important;
}

html[data-theme='liquidGlass'] .app-modal .ant-modal-header {
  border-bottom-color: var(--liquid-surface-divider) !important;
}

html[data-theme='liquidGlass'] .app-modal .ant-modal-footer {
  border-top-color: var(--liquid-surface-divider) !important;
}

html[data-theme='liquidGlass'] .app-drawer .ant-drawer-mask,
html[data-theme='liquidGlass'] .app-modal .ant-modal-mask {
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

@media (prefers-reduced-motion: reduce) {
  html[data-theme='liquidGlass'] body::before {
    animation: none;
  }

  html[data-theme='liquidGlass'] .app-card .ant-btn:not(.ant-btn-link):not(.ant-btn-text) {
    transition: none;
  }
}
`;

const lightGlassStyles = `
html[data-theme='liquidGlass'][data-appearance='light'] {
  --liquid-aurora-bg: #f8fbff;
  --liquid-aurora:
    repeating-linear-gradient(
      100deg,
      rgba(96, 165, 250, 0.32) 10%,
      rgba(199, 210, 254, 0.34) 15%,
      rgba(147, 197, 253, 0.32) 20%,
      rgba(221, 214, 254, 0.34) 25%,
      rgba(125, 211, 252, 0.28) 30%
    );
  --liquid-aurora-mask:
    repeating-linear-gradient(
      100deg,
      rgba(255, 255, 255, 0.95) 0%,
      rgba(255, 255, 255, 0.95) 7%,
      transparent 10%,
      transparent 12%,
      rgba(255, 255, 255, 0.95) 16%
    );
  --liquid-aurora-opacity: 0.72;
  --liquid-aurora-blend-mode: normal;
  --liquid-aurora-glow-a: rgba(219, 234, 254, 0.55);
  --liquid-aurora-glow-b: rgba(237, 233, 254, 0.55);
  --liquid-aurora-vignette: rgba(255, 255, 255, 0.64);
  --liquid-surface-shadow: rgba(0, 0, 0, 0.05) 0px 4px 4px, rgba(0, 0, 0, 0.05) 0px 0px 12px;
  --liquid-surface-divider: rgba(255, 255, 255, 0.2);
  --liquid-surface-text-shadow: 0 2px 12px rgba(0, 0, 0, 0.28);
  --liquid-card-button-text: rgba(15, 23, 42, 0.92);
  --liquid-card-button-hover-text: rgba(2, 6, 23, 0.96);
  --liquid-card-button-disabled-text: rgba(15, 23, 42, 0.4);
  --liquid-card-button-bg-low: rgba(255, 255, 255, 0.08);
  --liquid-card-button-bg-high: rgba(255, 255, 255, 0.52);
  --liquid-card-button-inset-top: rgba(15, 23, 42, 0.05);
  --liquid-card-button-inset-bottom: rgba(255, 255, 255, 0.58);
  --liquid-card-button-drop: rgba(15, 23, 42, 0.2);
  --liquid-card-button-hover-drop: rgba(15, 23, 42, 0.25);
  --liquid-card-button-inner-glow: rgba(255, 255, 255, 0.24);
  --liquid-card-button-hover-inner-glow: rgba(255, 255, 255, 0.5);
  --liquid-card-button-outer-glow: rgba(15, 23, 42, 0.14);
  --liquid-card-button-hover-outer-glow: rgba(15, 23, 42, 0.18);
  --liquid-card-button-text-shadow: rgba(15, 23, 42, 0.12);
  --liquid-card-button-border-glow: rgba(15, 23, 42, 0.5);
  --liquid-card-button-border-fill: rgba(255, 255, 255, 0.46);
  --liquid-card-button-border-inset: rgba(255, 255, 255, 0.52);
  --liquid-card-button-shine: rgba(255, 255, 255, 0.7);
  --liquid-card-button-press-glow: rgba(15, 23, 42, 0.05);
  --liquid-card-button-press-surface: rgba(255, 255, 255, 0.76);
  --liquid-card-button-press-inset: rgba(15, 23, 42, 0.16);
  --liquid-card-button-focus-ring: rgba(37, 99, 235, 0.28);
}
`;

const darkGlassStyles = `
html[data-theme='liquidGlass'][data-appearance='dark'] {
  --liquid-aurora-bg: #07111f;
  --liquid-aurora:
    repeating-linear-gradient(
      100deg,
      rgba(14, 165, 233, 0.26) 10%,
      rgba(79, 70, 229, 0.24) 15%,
      rgba(56, 189, 248, 0.24) 20%,
      rgba(124, 58, 237, 0.22) 25%,
      rgba(20, 184, 166, 0.2) 30%
    );
  --liquid-aurora-mask:
    repeating-linear-gradient(
      100deg,
      rgba(2, 6, 23, 0.92) 0%,
      rgba(2, 6, 23, 0.92) 7%,
      transparent 10%,
      transparent 12%,
      rgba(2, 6, 23, 0.92) 16%
    );
  --liquid-aurora-opacity: 0.82;
  --liquid-aurora-blend-mode: screen;
  --liquid-aurora-glow-a: rgba(14, 165, 233, 0.2);
  --liquid-aurora-glow-b: rgba(124, 58, 237, 0.18);
  --liquid-aurora-vignette: rgba(2, 6, 23, 0.42);
  --liquid-surface-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
  --liquid-surface-divider: rgba(255, 255, 255, 0.12);
  --liquid-surface-text-shadow: 0 2px 12px rgba(0, 0, 0, 0.4);
  --liquid-card-button-text: rgba(248, 250, 252, 0.92);
  --liquid-card-button-hover-text: #ffffff;
  --liquid-card-button-disabled-text: rgba(248, 250, 252, 0.42);
  --liquid-card-button-bg-low: rgba(255, 255, 255, 0.04);
  --liquid-card-button-bg-high: rgba(255, 255, 255, 0.2);
  --liquid-card-button-inset-top: rgba(248, 250, 252, 0.06);
  --liquid-card-button-inset-bottom: rgba(255, 255, 255, 0.32);
  --liquid-card-button-drop: rgba(0, 0, 0, 0.34);
  --liquid-card-button-hover-drop: rgba(0, 0, 0, 0.42);
  --liquid-card-button-inner-glow: rgba(255, 255, 255, 0.18);
  --liquid-card-button-hover-inner-glow: rgba(255, 255, 255, 0.34);
  --liquid-card-button-outer-glow: rgba(0, 0, 0, 0.24);
  --liquid-card-button-hover-outer-glow: rgba(0, 0, 0, 0.32);
  --liquid-card-button-text-shadow: rgba(0, 0, 0, 0.32);
  --liquid-card-button-border-glow: rgba(248, 250, 252, 0.48);
  --liquid-card-button-border-fill: rgba(255, 255, 255, 0.18);
  --liquid-card-button-border-inset: rgba(255, 255, 255, 0.24);
  --liquid-card-button-shine: rgba(255, 255, 255, 0.42);
  --liquid-card-button-press-glow: rgba(248, 250, 252, 0.08);
  --liquid-card-button-press-surface: rgba(255, 255, 255, 0.18);
  --liquid-card-button-press-inset: rgba(248, 250, 252, 0.12);
  --liquid-card-button-focus-ring: rgba(125, 211, 252, 0.3);
}
`;

export const liquidGlassThemePreset = {
  name: 'liquidGlass',
  label: 'Liquid Glass',
  description: 'Glass-like Card surfaces inspired by the reference demo with a layered blur treatment.',
  appearances: {
    light: {
      globalStyles: `${lightGlassStyles}${structuralGlassStyles}`,
      components: {
        Card: {
          colorBgContainer: 'transparent',
          colorFillAlter: 'transparent',
          colorBorderSecondary: 'transparent',
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
      globalStyles: `${darkGlassStyles}${structuralGlassStyles}`,
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

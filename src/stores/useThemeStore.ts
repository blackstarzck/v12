import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { defaultAppearance, defaultThemeName, type AppAppearance, type AppThemeName } from '../theme';

interface ThemeState {
  appearance: AppAppearance;
  themeName: AppThemeName;
  setAppearance: (appearance: AppAppearance) => void;
  setThemeName: (themeName: AppThemeName) => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      appearance: defaultAppearance,
      themeName: defaultThemeName,
      setAppearance: (appearance) => set({ appearance }),
      setThemeName: (themeName) => set({ themeName }),
    }),
    {
      name: 'talkpik-theme-preferences',
    },
  ),
);

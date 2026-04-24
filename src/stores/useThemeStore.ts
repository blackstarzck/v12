import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { defaultAppearance, type AppAppearance } from '../theme';

interface ThemeState {
  appearance: AppAppearance;
  setAppearance: (appearance: AppAppearance) => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      appearance: defaultAppearance,
      setAppearance: (appearance) => set({ appearance }),
    }),
    {
      name: 'talkpik-theme-preferences',
    },
  ),
);

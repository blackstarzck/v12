import { create } from 'zustand';
import type { Locale } from '../types/domain';

interface UserState {
  name: string;
  plan: string;
  targetGrade: string;
  examDate: string;
  locale: Locale;
  setLocale: (locale: Locale) => void;
  updateTarget: (targetGrade: string, examDate: string) => void;
}

export const useUserStore = create<UserState>((set) => ({
  name: '김토픽',
  plan: 'Premium Plan',
  targetGrade: 'TOPIK II 5급',
  examDate: '2026-07-12',
  locale: 'KO',
  setLocale: (locale) => set({ locale }),
  updateTarget: (targetGrade, examDate) => set({ targetGrade, examDate }),
}));

import { create } from 'zustand';
import { skillScores } from '../data/mockData';

interface LearningState {
  weeklyHours: number;
  solvedQuestions: number;
  attendanceDays: number;
  xp: number;
  skillScores: typeof skillScores;
}

export const useLearningStore = create<LearningState>(() => ({
  weeklyHours: 8.5,
  solvedQuestions: 42,
  attendanceDays: 5,
  xp: 1240,
  skillScores,
}));

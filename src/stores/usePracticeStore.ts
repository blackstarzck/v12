import { create } from 'zustand';
import { practiceQuestions } from '../data/mockData';
import type { PracticeArea, ProblemType, TopikLevel } from '../types/domain';

interface PracticeState {
  area?: PracticeArea;
  topikLevel: TopikLevel;
  targetGrade: string;
  problemType?: ProblemType;
  questionCount: number;
  currentIndex: number;
  selectedAnswers: Record<number, string>;
  checkedAnswers: Record<number, boolean>;
  isGenerating: boolean;
  questions: typeof practiceQuestions;
  setArea: (area: PracticeArea) => void;
  setTopikLevel: (level: TopikLevel) => void;
  setTargetGrade: (grade: string) => void;
  setProblemType: (type: ProblemType) => void;
  setQuestionCount: (count: number) => void;
  setGenerating: (isGenerating: boolean) => void;
  startProblemSet: () => void;
  selectAnswer: (questionId: number, answer: string) => void;
  checkAnswer: (questionId: number) => void;
  goToQuestion: (index: number) => void;
}

export const usePracticeStore = create<PracticeState>((set, get) => ({
  area: undefined,
  topikLevel: 'TOPIK II',
  targetGrade: '5급',
  problemType: undefined,
  questionCount: 5,
  currentIndex: 0,
  selectedAnswers: {},
  checkedAnswers: {},
  isGenerating: false,
  questions: practiceQuestions,
  setArea: (area) => set({ area }),
  setTopikLevel: (topikLevel) => set({ topikLevel }),
  setTargetGrade: (targetGrade) => set({ targetGrade }),
  setProblemType: (problemType) => set({ problemType }),
  setQuestionCount: (questionCount) => set({ questionCount }),
  setGenerating: (isGenerating) => set({ isGenerating }),
  startProblemSet: () =>
    set({
      currentIndex: 0,
      selectedAnswers: {},
      checkedAnswers: {},
      questions: practiceQuestions.slice(0, Math.min(get().questionCount, practiceQuestions.length)),
    }),
  selectAnswer: (questionId, answer) =>
    set((state) => ({
      selectedAnswers: { ...state.selectedAnswers, [questionId]: answer },
    })),
  checkAnswer: (questionId) =>
    set((state) => ({
      checkedAnswers: { ...state.checkedAnswers, [questionId]: true },
    })),
  goToQuestion: (index) =>
    set((state) => ({
      currentIndex: Math.max(0, Math.min(index, state.questions.length - 1)),
    })),
}));

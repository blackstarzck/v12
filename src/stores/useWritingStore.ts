import { create } from 'zustand';
import type { WritingType } from '../types/domain';

interface WritingState {
  selectedType?: WritingType;
  selectedTopic?: string;
  drafts: Record<WritingType, string>;
  autosavedAt?: string;
  submittedTypes: WritingType[];
  selectWritingType: (type: WritingType) => void;
  setTopic: (topic: string) => void;
  updateDraft: (type: WritingType, value: string) => void;
  markSubmitted: (type: WritingType) => void;
}

export const useWritingStore = create<WritingState>((set) => ({
  selectedType: undefined,
  selectedTopic: undefined,
  drafts: {
    '51': '',
    '52': '',
    '53': '',
    '54': '',
  },
  autosavedAt: undefined,
  submittedTypes: [],
  selectWritingType: (selectedType) => set({ selectedType }),
  setTopic: (selectedTopic) => set({ selectedTopic }),
  updateDraft: (type, value) =>
    set((state) => ({
      drafts: { ...state.drafts, [type]: value },
      autosavedAt: new Intl.DateTimeFormat('ko-KR', {
        hour: '2-digit',
        minute: '2-digit',
      }).format(new Date()),
    })),
  markSubmitted: (type) =>
    set((state) => ({
      submittedTypes: Array.from(new Set([...state.submittedTypes, type])),
    })),
}));

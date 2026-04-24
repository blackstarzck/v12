import { create } from 'zustand';

export type AiTutorTab = 'home' | 'chat' | 'notifications';

interface TutorMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface AiTutorState {
  open: boolean;
  activeTab: AiTutorTab;
  messages: TutorMessage[];
  openPanel: (tab?: AiTutorTab) => void;
  closePanel: () => void;
  setTab: (tab: AiTutorTab) => void;
  sendMessage: (content: string) => void;
}

export const useAiTutorStore = create<AiTutorState>((set) => ({
  open: false,
  activeTab: 'home',
  messages: [
    {
      id: 'm-1',
      role: 'assistant',
      content:
        '안녕하세요. 지금 보는 화면에서 막히는 TOPIK 문제나 쓰기 표현을 물어보세요.',
    },
  ],
  openPanel: (activeTab = 'home') => set({ open: true, activeTab }),
  closePanel: () => set({ open: false }),
  setTab: (activeTab) => set({ activeTab }),
  sendMessage: (content) =>
    set((state) => ({
      activeTab: 'chat',
      messages: [
        ...state.messages,
        {
          id: `u-${Date.now()}`,
          role: 'user',
          content,
        },
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content:
            '좋습니다. 답안을 먼저 구조로 나누고, 핵심 표현을 한 번 더 확인해 보겠습니다.',
        },
      ],
    })),
}));

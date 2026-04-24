import { create } from 'zustand';

interface FeedbackState {
  search: string;
  statusFilter: string;
  sortKey: string;
  setSearch: (search: string) => void;
  setStatusFilter: (statusFilter: string) => void;
  setSortKey: (sortKey: string) => void;
}

export const useFeedbackStore = create<FeedbackState>((set) => ({
  search: '',
  statusFilter: 'all',
  sortKey: 'latest',
  setSearch: (search) => set({ search }),
  setStatusFilter: (statusFilter) => set({ statusFilter }),
  setSortKey: (sortKey) => set({ sortKey }),
}));

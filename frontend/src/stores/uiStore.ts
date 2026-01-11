import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  activeModal: string | null;
  isLoading: boolean;
  toggleSidebar: () => void;
  openModal: (modalName: string) => void;
  closeModal: () => void;
  setLoading: (loading: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  activeModal: null,
  isLoading: false,
  
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  
  openModal: (modalName: string) => set({ activeModal: modalName }),
  
  closeModal: () => set({ activeModal: null }),
  
  setLoading: (loading: boolean) => set({ isLoading: loading }),
}));
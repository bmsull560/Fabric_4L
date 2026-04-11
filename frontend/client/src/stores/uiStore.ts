import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  activeModal: string | null;
  modalData: unknown;
  toastQueue: Array<{ id: string; message: string; type: 'success' | 'error' | 'info' }>;
  theme: 'light' | 'dark';

  toggleSidebar: () => void;
  openModal: (modalName: string, data?: unknown) => void;
  closeModal: () => void;
  addToast: (message: string, type?: 'success' | 'error' | 'info') => void;
  removeToast: (id: string) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  /** Reset store to initial state - primarily for testing */
  _reset: () => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  sidebarOpen: true,
  activeModal: null,
  modalData: null,
  toastQueue: [],
  theme: 'light',

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  openModal: (modalName, data = null) => set({ activeModal: modalName, modalData: data }),
  closeModal: () => set({ activeModal: null, modalData: null }),

  addToast: (message, type = 'info') => {
    const id = Math.random().toString(36).substring(7);
    set((state) => ({
      toastQueue: [...state.toastQueue, { id, message, type }],
    }));
    setTimeout(() => get().removeToast(id), 5000);
  },

  removeToast: (id) => {
    set((state) => ({
      toastQueue: state.toastQueue.filter((t) => t.id !== id),
    }));
  },

  setTheme: (theme) => set({ theme }),

  _reset: () => set({
    sidebarOpen: true,
    activeModal: null,
    modalData: null,
    toastQueue: [],
    theme: 'light',
  }),
}));

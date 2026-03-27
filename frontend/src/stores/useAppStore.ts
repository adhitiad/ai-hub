import { create } from "zustand";

interface AppState {
  isInitialized: boolean;
  setInitialized: (val: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  isInitialized: false,
  setInitialized: (val) => set({ isInitialized: val }),
}));

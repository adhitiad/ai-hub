import { create } from "zustand";
import { persist } from "zustand/middleware";

interface User {
  email: string;
  role: string;
  subscription_status?: string;
}

interface AuthState {
  user: User | null;
  apiKey: string | null;
  isAuthenticated: boolean;
  login: (userData: User, apiKey: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      apiKey: null,
      isAuthenticated: false,

      login: (userData, apiKey) =>
        set({
          user: userData,
          apiKey,
          isAuthenticated: true,
        }),

      logout: () =>
        set({
          user: null,
          apiKey: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: "auth-storage", // name of the item in the storage (must be unique)
    }
  )
);

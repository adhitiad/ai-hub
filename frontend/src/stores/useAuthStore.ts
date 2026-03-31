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
          apiKey, // API key hanya disimpan di memori selama sesi aktif (opsional)
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
      name: "auth-storage",
      // KEAMANAN KRITIS: Hanya simpan data non-sensitif ke localStorage.
      // API Key / Token akan dikelola secara aman oleh HttpOnly Cookies di browser.
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

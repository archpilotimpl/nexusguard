import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  isAuthenticated: boolean;
  user: {
    id: string;
    email: string;
    role: string;
    region?: string;
  } | null;
  accessToken: string | null;
  refreshToken: string | null;
  login: (tokens: { access_token: string; refresh_token: string }, user: AuthState['user']) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      user: null,
      accessToken: null,
      refreshToken: null,
      login: (tokens, user) => {
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);
        set({
          isAuthenticated: true,
          user,
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
        });
      },
      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({
          isAuthenticated: false,
          user: null,
          accessToken: null,
          refreshToken: null,
        });
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);

interface UIState {
  sidebarOpen: boolean;
  selectedRegion: string | null;
  refreshInterval: number;
  toggleSidebar: () => void;
  setSelectedRegion: (region: string | null) => void;
  setRefreshInterval: (interval: number) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  selectedRegion: null,
  refreshInterval: 30000, // 30 seconds
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSelectedRegion: (region) => set({ selectedRegion: region }),
  setRefreshInterval: (interval) => set({ refreshInterval: interval }),
}));

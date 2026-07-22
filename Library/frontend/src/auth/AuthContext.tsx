import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { api, ApiError, type Me } from '../services/api';

interface AuthState {
  user: Me | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<Me>;
  loginTemporary: (username: string, temporaryPassword: string) => Promise<Me>;
  changePassword: (newPassword: string, currentPassword?: string) => Promise<Me>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      const me = await api.me();
      setUser(me);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      loading,
      login: async (username, password) => {
        const me = await api.login(username, password);
        setUser(me);
        return me;
      },
      loginTemporary: async (username, temporaryPassword) => {
        const me = await api.loginTemporary(username, temporaryPassword);
        setUser(me);
        return me;
      },
      changePassword: async (newPassword, currentPassword) => {
        const me = await api.changePassword(newPassword, currentPassword);
        setUser(me);
        return me;
      },
      logout: async () => {
        await api.logout();
        setUser(null);
      },
      refresh,
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

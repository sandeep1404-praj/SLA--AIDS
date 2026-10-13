import { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('cf_token');
    if (token) {
      authService.getMe()
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('cf_token');
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const res = await authService.login({ email, password });
    localStorage.setItem('cf_token', res.data.access_token);
    const me = await authService.getMe();
    setUser(me.data);
    return me.data;
  };

  const register = async (name, email, password) => {
    const res = await authService.register({ name, email, password });
    localStorage.setItem('cf_token', res.data.access_token);
    const me = await authService.getMe();
    setUser(me.data);
    return me.data;
  };

  const logout = async () => {
    try { await authService.logout(); } catch {}
    localStorage.removeItem('cf_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
